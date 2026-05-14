from dataclasses import dataclass

from django.db import connections, transaction

from .models import Partner


@dataclass
class PartnerSyncResult:
    loaded: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped: int = 0


def clean_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def residency_from_country(country):
    country = (country or "").strip().upper()
    if not country or country in {"RS", "SRB", "SRBIJA", "SERBIA"}:
        return Partner.DOMESTIC
    return Partner.FOREIGN


BANK_GROUPS = {11, 13, 14}


def parse_finance_group(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def partner_type_from_finance_group(group):
    group = parse_finance_group(group)
    if group == 10:
        return Partner.PERSON
    if group in BANK_GROUPS:
        return Partner.BANK
    return Partner.LEGAL_ENTITY


def get_finance_partner(sif_par, source_db="server_db"):
    rows = fetch_finance_partners(source_db=source_db, sif_par=sif_par)
    return rows[0] if rows else None


def count_finance_partners(source_db="server_db"):
    with connections[source_db].cursor() as cursor:
        cursor.execute("SELECT COUNT(DISTINCT sif_par) FROM dbo.partneri WHERE sif_par IS NOT NULL")
        return int(cursor.fetchone()[0] or 0)


def fetch_finance_partners(source_db="server_db", limit=None, offset=None, sif_par=None):
    use_offset = offset is not None
    top_sql = f"TOP ({int(limit)}) " if limit and not use_offset else ""
    where = ["rn = 1"]
    params = []
    if sif_par is not None:
        where.append("sif_par = %s")
        params.append(sif_par)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    paging_sql = ""
    if use_offset:
        offset_value = max(int(offset or 0), 0)
        limit_value = max(int(limit or 250), 1)
        paging_sql = "OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
        params.extend([offset_value, limit_value])

    sql = f"""
        WITH ranked_partners AS (
            SELECT
                naz_grup,
                grupa,
                sif_par,
                naz_par,
                ulica_par,
                mesto_par,
                mb,
                telefon,
                email,
                lice,
                pib,
                zemlja,
                ROW_NUMBER() OVER (
                    PARTITION BY sif_par
                    ORDER BY
                        CASE
                            WHEN grupa = 1 THEN 1
                            WHEN grupa = 10 THEN 2
                            WHEN grupa IN (11, 13, 14) THEN 3
                            ELSE 4
                        END,
                        grupa
                ) AS rn
            FROM dbo.partneri
            WHERE sif_par IS NOT NULL
        )
        SELECT {top_sql}
            naz_grup,
            grupa,
            sif_par,
            naz_par,
            ulica_par,
            mesto_par,
            mb,
            telefon,
            email,
            lice,
            pib,
            zemlja
        FROM ranked_partners
        {where_sql}
        ORDER BY sif_par
        {paging_sql}
    """

    with connections[source_db].cursor() as cursor:
        cursor.execute(sql, params)
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def partner_defaults_from_finance(row):
    return {
        "name": clean_text(row["naz_par"]) or f"Partner {row['sif_par']}",
        "partner_type": partner_type_from_finance_group(row.get("grupa")),
        "residency": residency_from_country(row["zemlja"]),
        "pib": clean_text(row["pib"]),
        "maticni_broj": clean_text(row["mb"]),
        "country": clean_text(row["zemlja"]),
        "city": clean_text(row["mesto_par"]),
        "address": clean_text(row["ulica_par"]),
        "email": clean_text(row["email"]),
        "phone": clean_text(row["telefon"]),
        "contact_person": clean_text(row["lice"]),
        "is_active": True,
    }


def sync_partner_from_finance(sif_par, source_db="server_db", target_db="default", commit=True):
    return sync_finance_partners(
        source_db=source_db,
        target_db=target_db,
        sif_par=sif_par,
        commit=commit,
    )


def sync_finance_partners(source_db="server_db", target_db="default", limit=None, sif_par=None, commit=True):
    rows = fetch_finance_partners(source_db=source_db, limit=limit, sif_par=sif_par)
    return sync_finance_partner_rows(rows, target_db=target_db, commit=commit)


def sync_finance_partner_batch(source_db="server_db", target_db="default", offset=0, limit=250, commit=True):
    rows = fetch_finance_partners(source_db=source_db, limit=limit, offset=offset)
    return sync_finance_partner_rows(rows, target_db=target_db, commit=commit)


def sync_finance_partner_rows(rows, target_db="default", commit=True):
    result = PartnerSyncResult(loaded=len(rows))
    sif_values = []
    seen_sif_values = set()
    for row in rows:
        sif_par = row["sif_par"]
        if sif_par is not None and sif_par not in seen_sif_values:
            sif_values.append(sif_par)
            seen_sif_values.add(sif_par)

    with transaction.atomic(using=target_db):
        existing_partners = {}
        if sif_values:
            partners = (
                Partner.objects.using(target_db)
                .filter(external_sif_par__in=sif_values)
                .order_by("id")
            )
            for partner in partners:
                existing_partners.setdefault(partner.external_sif_par, partner)

        for row in rows:
            if row["sif_par"] is None:
                result.skipped += 1
                continue

            defaults = partner_defaults_from_finance(row)
            partner = existing_partners.get(row["sif_par"])

            if partner is None:
                result.created += 1
                if commit:
                    partner = Partner.objects.using(target_db).create(
                        external_sif_par=row["sif_par"],
                        **defaults,
                    )
                    existing_partners[row["sif_par"]] = partner
                continue

            changed_fields = []
            for field, value in defaults.items():
                if getattr(partner, field) != value:
                    setattr(partner, field, value)
                    changed_fields.append(field)

            if changed_fields:
                result.updated += 1
                if commit:
                    partner.save(using=target_db, update_fields=[*changed_fields, "updated_at"])
            else:
                result.unchanged += 1

        if not commit:
            transaction.set_rollback(True, using=target_db)

    return result
