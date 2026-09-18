"""One-way legacy operations import; local edits are never silently overwritten."""
from django.utils import timezone

from potrazivanja.models import (
    CollectionActivity, CollectionContact, CollectionNotice, CollectionProfile,
    CollectionSyncStep, LegacyImportMap, LegalCaseLink,
)
from .source import day, digest, integer, money, payload, text, timestamp
from .sync import bulk_create, issue

TABLES = {"kontakti": CollectionContact, "napomene": CollectionActivity,
          "pozivi_tel": CollectionActivity, "opomene": CollectionNotice,
          "poziv_pismo": CollectionNotice, "tuzbe": CollectionNotice}


def values_for(table, row, identity):
    common = {"identity_id": identity.pk if identity else None}
    if table == "kontakti":
        # kontakt is free-form (person and/or telephone); do not truncate or split it.
        return dict(common, name=text(row.get("kontakt")), email=text(row.get("email")),
                    note=text(row.get("napomena")), legacy_partner_name=text(row.get("naz_par")), active=True)
    if table in ("napomene", "pozivi_tel"):
        return dict(common, kind="note" if table == "napomene" else "phone",
                    occurred_at=timestamp(row.get("datum")), text=text(row.get("napomene", row.get("napomena"))),
                    legacy_partner_name=text(row.get("naz_par")), archived=False)
    return dict(common, kind={"opomene": "reminder", "poziv_pismo": "letter", "tuzbe": "legacy_claim"}[table],
                year=integer(row.get("god")), number=text(row.get("br_pisma", row.get("br_opomene"))),
                issued_on=day(row.get("datum")), total_amount=money(row["iznos"]) if row.get("iznos") is not None else None,
                currency="", partner_name_snapshot=text(row.get("naz_par")),
                original_invoice_text=text(row.get("fakture")), note=text(row.get("napomene")), archived=False)


def sync_operations(data, run, partners):
    # Only the confirmed catalog identifies legacy operational partners. A missing
    # code, fractional float or missing catalog match remains unlinked and visible.
    confirmed = {integer(r["sif_par"]) for r in data["partneri"]
                 if integer(r["sif_pred"]) == 1 and integer(r["grupa"]) == 1}
    for table, model in TABLES.items():
        old = {m.source_key: m for m in LegacyImportMap.objects.filter(source_system="ims_erp", source_table=table)}
        targets = {obj.pk: obj for obj in model.objects.all()}
        new_maps, seen, created, updated = [], set(), 0, 0
        for row in data[table]:
            key = text(row["id"])
            if key in seen:
                raise ValueError(f"Dupliran ID u {table}.")
            seen.add(key)
            code = integer(row.get("sif_par"))
            identity = partners.get(code) if code in confirmed else None
            values = values_for(table, row, identity)
            signature = digest(row)
            mapped = old.get(key)
            if identity is None:
                issue(run, "unlinked_operation", table, key, "Sačuvan original; partner nije jednoznačno povezan.", row)
            if mapped is None:
                obj = model.objects.create(**values)
                new_maps.append(LegacyImportMap(source_table=table, source_key=key,
                    target_model=model._meta.label_lower, target_pk=obj.pk, source_hash=signature,
                    raw_data={"source": payload(row), "target": payload(values)}, first_run=run, last_run=run))
                created += 1
                continue
            obj = targets.get(mapped.target_pk)
            if obj is None or mapped.target_model != model._meta.label_lower:
                raise ValueError(f"Nedostaje uvezeni red {table}/{key}; potrebno razrešenje.")
            previous_values = mapped.raw_data.get("target", {})
            current_values = payload({name: getattr(obj, name) for name in previous_values})
            if current_values != previous_values:
                issue(run, "local_edit_conflict", table, key, "Lokalna izmena je zadržana. Nova izvorna verzija je u arhivi.", row)
                continue
            if mapped.source_hash != signature or previous_values != payload(values):
                model.objects.filter(pk=obj.pk).update(**values, updated_at=timezone.now())
                mapped.source_hash = signature
                mapped.raw_data = {"source": payload(row), "target": payload(values)}
                mapped.last_run = run
                mapped.save()
                updated += 1
        bulk_create(LegacyImportMap, new_maps)
        absent = set(old) - seen
        for key in absent:
            # Retain both the record and all source snapshots. Do not delete history
            # or silently treat a deleted note as a current operational instruction.
            mapped = old[key]
            obj = targets.get(mapped.target_pk)
            field = "active" if table == "kontakti" else "archived"
            value = False if field == "active" else True
            if obj and getattr(obj, field) != value:
                previous = mapped.raw_data.get("target", {})
                if payload({name: getattr(obj, name) for name in previous}) == previous:
                    model.objects.filter(pk=obj.pk).update(**{field: value})
                    mapped.raw_data["target"][field] = value
                    mapped.save(update_fields=["raw_data", "updated_at"])
                else:
                    issue(run, "local_edit_conflict", table, key, "Red više nije u izvoru; lokalna izmena je zadržana.")
        CollectionSyncStep.objects.create(run=run, code=f"import_{table}", status="success",
            source_rows=len(seen), created_rows=created, updated_rows=updated, inactive_rows=len(absent),
            finished_at=timezone.now(), details={"mapped_source_rows": len(seen), "missing_source_rows_retained": len(absent)})
    # Partner properties: the MAX/any legacy flag means an important CUSTOMER.
    important, review = set(), {}
    for row in data["napomene"]:
        if text(row.get("veliki")).casefold() == "da":
            important.add(integer(row.get("sif_par")))
    for row in data["avans_klijent"]:
        code = integer(row.get("sif_par"))
        review.setdefault(code, []).append(text(row.get("note")))
        if code not in confirmed:
            issue(run, "unlinked_review", "avans_klijent", row["id"], "Spisak za proveru: partner nije povezan; original sačuvan.", row)
    existing = {p.identity.partner_code: p for p in CollectionProfile.objects.select_related("identity").filter(identity__company=1, identity__partner_group=1)}
    for code in (important | set(review) | set(existing)) & confirmed:
        values = {"important_customer": code in important, "needs_review": code in review,
                  "review_note": "\n".join(review.get(code, []))}
        obj = existing.get(code)
        if obj is None:
            CollectionProfile.objects.create(identity=partners[code], **values)
            obj = CollectionProfile.objects.get(identity=partners[code])
        mapping = LegacyImportMap.objects.filter(source_system="ims_erp", source_table="customer_profile", source_key=str(code)).first()
        if mapping:
            previous = mapping.raw_data.get("target", {})
            if payload({name: getattr(obj, name) for name in previous}) != previous:
                issue(run, "local_profile_conflict", "napomene/avans_klijent", code, "Lokalna svojstva partnera zadržana.")
                continue
            CollectionProfile.objects.filter(pk=obj.pk).update(**values)
            mapping.raw_data = {"target": payload(values)}
            mapping.source_hash = digest(values)
            mapping.last_run = run
            mapping.save()
        elif any(getattr(obj, k) != v for k, v in values.items()):
            issue(run, "local_profile_conflict", "napomene/avans_klijent", code, "Postojeća lokalna svojstva partnera zadržana.")
        else:
            LegacyImportMap.objects.create(source_table="customer_profile", source_key=str(code),
                target_model=CollectionProfile._meta.label_lower, target_pk=obj.pk, source_hash=digest(values),
                raw_data={"target": payload(values)}, first_run=run, last_run=run)
    # Cases and their changes stay in the existing Django tables. A protected link
    # avoids copying legal cases into an independently editable second truth.
    for row in data["postupak"]:
        code = integer(row.get("sifra_partnera"))
        if code in confirmed:
            obj, created = LegalCaseLink.objects.get_or_create(legacy_case_id=row["id"], defaults={"identity": partners[code]})
            if not created and obj.identity_id != partners[code].pk:
                issue(run, "legal_partner_changed", "postupak", row["id"], "Partner postupka promenjen; proveriti vezu.", row)
        else:
            issue(run, "unlinked_legal_case", "postupak", row["id"], "Postupak ostaje u Naplati i arhivi; partner nije povezan.", row)
