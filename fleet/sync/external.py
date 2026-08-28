import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import connections, transaction
from django.db.models import Q
from django.utils.dateparse import parse_datetime

from core.models import OrganizationalUnit
from nabavka.models import ProcurementInvoice

from fleet.models import (
    DraftInsurance,
    Insurance,
    JobCode,
    Policy,
    TrafficCard,
    Vehicle,
)
from fleet.support.vehicle import format_license_plate

logger = logging.getLogger(__name__)

INS_VIEW = "dbo.fleet_potrazivanje_ddor"
DB_ALIAS = "server_db"
ORG_UNIT_SOURCE_VIEW = "Vozila.dbo.v_sifre_posla"
VEHICLE_JOB_CODE_SOURCE_VIEW = "Vozila.dbo.sif_pos_trenutno"
KEY_FIELDS = ("god", "sif_vrs", "br_naloga", "stavka", "knt")

POLICY_DATE_FIELDS = {"issue_date", "start_date", "end_date"}
POLICY_DECIMAL_FIELDS = {"premium_amount", "first_installment_amount", "other_installments_amount"}
POLICY_INTEGER_FIELDS = {"partner_pib", "invoice_id", "number_of_installments"}
POLICY_REQUIRED_FIELDS = {
    "vehicle",
    "partner_pib",
    "partner_name",
    "invoice_number",
    "issue_date",
    "insurance_type",
    "policy_number",
    "premium_amount",
    "start_date",
    "end_date",
    "first_installment_amount",
    "other_installments_amount",
    "number_of_installments",
}
POLICY_INVOICE_SUPPLIER_Q = Q(supplier_name__icontains="osiguranje") | Q(supplier_name__icontains="ddor")


def _normalize_policy_value(model_field, value, invoice_id, stats):
    if model_field in POLICY_DATE_FIELDS:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            if not value.strip():
                return None
            try:
                return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
            except ValueError:
                stats["normalization_issues"] += 1
                logger.debug(
                    "Policy sync invalid date: field=%s value=%r invoice=%s",
                    model_field,
                    value,
                    invoice_id,
                )
                return None
        stats["normalization_issues"] += 1
        logger.debug("Policy sync unexpected date type: field=%s type=%s invoice=%s", model_field, type(value), invoice_id)
        return None

    if model_field in POLICY_DECIMAL_FIELDS:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        try:
            return Decimal(str(value).strip())
        except Exception:
            stats["normalization_issues"] += 1
            logger.debug(
                "Policy sync invalid decimal: field=%s value=%r invoice=%s",
                model_field,
                value,
                invoice_id,
            )
            return None

    if model_field in POLICY_INTEGER_FIELDS:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        try:
            return int(Decimal(str(value).strip()))
        except Exception:
            stats["normalization_issues"] += 1
            logger.debug(
                "Policy sync invalid integer: field=%s value=%r invoice=%s",
                model_field,
                value,
                invoice_id,
            )
            return None

    if isinstance(value, str):
        value = value.strip()
    return value if value != "" else None


def _policy_data_is_complete(policy_data):
    return all(policy_data.get(field) is not None and policy_data.get(field) != "" for field in POLICY_REQUIRED_FIELDS)


def _policy_insurance_type_from_supplier(supplier_name):
    if not supplier_name:
        return None
    supplier_name_lower = supplier_name.lower()
    if "ddor" in supplier_name_lower:
        return "DDOR"
    if "osiguranje" in supplier_name_lower:
        return "Osiguranje"
    return None


def _policy_invoice_queryset(last_24_hours=True, days=None):
    queryset = (
        ProcurementInvoice.objects.select_related("vehicle")
        .filter(is_garage=True, vehicle__isnull=False)
        .filter(POLICY_INVOICE_SUPPLIER_Q)
        .order_by("id")
    )

    if days is not None:
        queryset = queryset.filter(invoice_date__gt=date.today() - timedelta(days=days))
        logger.debug("Policy sync invoice filter: last %s days", days)
    elif last_24_hours:
        queryset = queryset.filter(invoice_date__gt=date.today() - timedelta(days=1))
        logger.debug("Policy sync invoice filter: last 24 hours")

    return queryset


def _policy_data_from_invoice(invoice, stats):
    invoice_id = invoice.pk
    invoice_date = _normalize_policy_value("issue_date", invoice.invoice_date, invoice_id, stats)
    end_date = invoice_date + timedelta(days=365) if invoice_date else None
    amount = _normalize_policy_value("premium_amount", invoice.amount, invoice_id, stats)

    return {
        "vehicle": invoice.vehicle,
        "partner_pib": None,
        "partner_name": _normalize_policy_value("partner_name", invoice.supplier_name, invoice_id, stats),
        "invoice_id": _normalize_policy_value("invoice_id", invoice_id, invoice_id, stats),
        "invoice_number": _normalize_policy_value("invoice_number", invoice.invoice_number, invoice_id, stats),
        "issue_date": invoice_date,
        "insurance_type": _policy_insurance_type_from_supplier(invoice.supplier_name),
        "policy_number": None,
        "premium_amount": amount,
        "start_date": invoice_date,
        "end_date": end_date,
        "first_installment_amount": amount,
        "other_installments_amount": Decimal("0.00"),
        "number_of_installments": 1,
        "is_renewable": True,
    }


def _merged_policy_defaults(existing_policy, incoming_data):
    if existing_policy is None:
        return incoming_data

    merged = {}
    for field, incoming_value in incoming_data.items():
        if incoming_value is not None and incoming_value != "":
            merged[field] = incoming_value
        else:
            merged[field] = getattr(existing_policy, field)
    return merged


def fetch_policy_data(last_24_hours=True, days=None):
    try:
        logger.debug("Policy sync start")

        stats = {
            "created": 0,
            "updated": 0,
            "incomplete": 0,
            "missing_invoice_id": 0,
            "normalization_issues": 0,
            "errors": 0,
        }
        invoices = list(_policy_invoice_queryset(last_24_hours=last_24_hours, days=days))

        logger.debug("Policy sync fetched invoices=%s", len(invoices))
        if not invoices:
            result = {
                "fetched": 0,
                "created": 0,
                "updated": 0,
                "incomplete": 0,
                "missing_invoice_id": 0,
                "normalization_issues": 0,
                "errors": 0,
            }
            logger.info("Policy sync summary: %s", result)
            return "Policy sync: povuceno=0, kreirano=0, azurirano=0, nepotpuno=0, problemi=0"

        with transaction.atomic():
            for invoice in invoices:
                invoice_id_from_db = invoice.pk

                try:
                    policy_data_to_save = _policy_data_from_invoice(invoice, stats)
                    invoice_id = policy_data_to_save.pop("invoice_id")
                    if invoice_id is None:
                        stats["missing_invoice_id"] += 1
                        logger.debug("Policy sync invoice skipped without invoice ID: invoice=%s", invoice_id_from_db)
                        continue

                    existing_policy = Policy.objects.filter(invoice_id=invoice_id).first()
                    defaults = _merged_policy_defaults(existing_policy, policy_data_to_save)
                    _policy, created = Policy.objects.update_or_create(
                        invoice_id=invoice_id,
                        defaults=defaults,
                    )
                    if created:
                        stats["created"] += 1
                        logger.debug("Policy sync created invoice %s.", invoice_id)
                    else:
                        stats["updated"] += 1
                        logger.debug("Policy sync updated invoice %s.", invoice_id)

                    policy_check_data = defaults.copy()
                    policy_check_data["invoice_id"] = invoice_id
                    if not _policy_data_is_complete(policy_check_data):
                        stats["incomplete"] += 1
                        logger.debug("Policy sync incomplete Policy invoice %s.", invoice_id)

                except Exception as exc:
                    stats["errors"] += 1
                    logger.debug("Policy sync error processing invoice %s: %s", invoice_id_from_db, exc, exc_info=True)

        result = {
            "fetched": len(invoices),
            "created": stats["created"],
            "updated": stats["updated"],
            "incomplete": stats["incomplete"],
            "missing_invoice_id": stats["missing_invoice_id"],
            "normalization_issues": stats["normalization_issues"],
            "errors": stats["errors"],
        }
        logger.info("Policy sync summary: %s", result)
        msg = (
            "Policy sync: "
            f"povuceno={len(invoices)}, kreirano={stats['created']}, azurirano={stats['updated']}, "
            f"nepotpuno={stats['incomplete']}, bez_id_fakture={stats['missing_invoice_id']}, "
            f"problemi={stats['normalization_issues'] + stats['errors']}"
        )
        return msg

    except Exception as exc:
        logger.error("Critical error in data fetch: %s", exc, exc_info=True)
        return f"Critical error: {exc}"


def process_vehicle_retirements():
    try:
        logger.debug("Otpis vozila sync start")
        query = """
            SELECT inv_br
            FROM dbo.fleet_otpis;
        """

        retired_vehicles_from_db = []
        with connections["server_db"].cursor() as cursor:
            logger.debug("Otpis vozila sync SQL: %s", query)
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.debug("Otpis vozila sync fetched rows=%s", len(rows))

            for row in rows:
                if row[0] is not None:
                    retired_vehicles_from_db.append(str(row[0]).strip())

        if not retired_vehicles_from_db:
            logger.info("Proces otpisa završen: Ažurirano vozila: 0, Već otpisana (preskočena): 0, Nije pronađeno u Django bazi: 0, Greške: 0")
            return "Nema otpisanih vozila za obradu."

        updated_count = 0
        skipped_count = 0
        not_found_count = 0
        errors = 0

        with transaction.atomic():
            for inv_br_from_db in retired_vehicles_from_db:
                try:
                    vehicle = Vehicle.objects.get(inventory_number__iexact=inv_br_from_db)

                    if vehicle.otpis:
                        logger.debug("Vozilo sa inventarnim brojem %r je već otpisano. Preskačem.", inv_br_from_db)
                        skipped_count += 1
                        continue

                    vehicle.otpis = True
                    vehicle.save(update_fields=["otpis"])
                    updated_count += 1
                    logger.debug(
                        "Uspešno otpisano vozilo: %s - %s %s.",
                        vehicle.inventory_number,
                        vehicle.brand,
                        vehicle.model,
                    )

                except Vehicle.DoesNotExist:
                    not_found_count += 1
                    logger.debug("Vozilo sa inventarnim brojem %r iz dbo.fleet_otpis nije pronađeno u Django bazi.", inv_br_from_db)
                except Exception as exc:
                    errors += 1
                    logger.debug("Greška pri obradi vozila %r: %s", inv_br_from_db, exc, exc_info=True)

        message = (
            "Proces otpisa završen: "
            f"Ažurirano vozila: {updated_count}, "
            f"Već otpisana (preskočena): {skipped_count}, "
            f"Nije pronađeno u Django bazi: {not_found_count}, "
            f"Greške: {errors}"
        )
        logger.info(message)
        return message

    except Exception as exc:
        logger.critical("Kritična greška u funkciji 'process_vehicle_retirements': %s", exc, exc_info=True)
        return f"Kritična greška prilikom obrade otpisanih vozila: {exc}"


def update_vehicle_values():
    updated_vehicles_count = 0

    try:
        with connections["server_db"].cursor() as cursor:
            cursor.execute(
                """
                SELECT sif_osn, sad_vrednost FROM dbo.vrednost_vozila
                """
            )
            rows = cursor.fetchall()

        vehicles_to_update = []
        for row in rows:
            sif_osn = row[0].strip()
            vrednost = row[1]

            try:
                vehicle = Vehicle.objects.get(inventory_number=sif_osn)
                vehicle.value = vrednost
                vehicles_to_update.append(vehicle)
            except Vehicle.DoesNotExist:
                logger.warning("Vozilo sa inventory_number %s nije pronađeno.", sif_osn)
            except Exception as exc:
                logger.error("Greška prilikom ažuriranja vozila %s: %s", sif_osn, exc)

        Vehicle.objects.bulk_update(vehicles_to_update, ["value"])
        updated_vehicles_count = len(vehicles_to_update)

    except Exception as exc:
        logger.error("Greška prilikom povlačenja podataka iz baze: %s", exc)

    return updated_vehicles_count


def _clean_source_value(value):
    return "" if value is None else str(value).strip()


def update_job_codes_from_view():
    today = date.today()
    stats = {
        "fetched": 0,
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "missing_vehicle": 0,
        "missing_org_unit": 0,
        "skipped_invalid": 0,
    }

    with connections[DB_ALIAS].cursor() as cursor:
        cursor.execute(f"SELECT regbr, sifpos FROM {VEHICLE_JOB_CODE_SOURCE_VIEW}")
        rows = cursor.fetchall()
    stats["fetched"] = len(rows)

    traffic_cards_by_plate = {
        format_license_plate(card.registration_number): card
        for card in TrafficCard.objects.select_related("vehicle").all()
    }
    units_by_code = {
        _clean_source_value(unit.code): unit
        for unit in OrganizationalUnit.objects.all()
    }

    for regbr, sifpos in rows:
        plate = format_license_plate(_clean_source_value(regbr))
        org_code = _clean_source_value(sifpos)
        if not plate or not org_code:
            stats["skipped_invalid"] += 1
            continue

        traffic_card = traffic_cards_by_plate.get(plate)
        if not traffic_card:
            stats["missing_vehicle"] += 1
            logger.debug("Sifra posla vozila: registracija nije nadjena regbr=%r plate=%s", regbr, plate)
            continue

        org_unit = units_by_code.get(org_code)
        if not org_unit:
            stats["missing_org_unit"] += 1
            logger.debug("Sifra posla vozila: OJ nije nadjena sifpos=%r code=%s", sifpos, org_code)
            continue

        vehicle = traffic_card.vehicle
        latest_job = vehicle.job_codes.order_by("-assigned_date", "-id").first()

        if latest_job and latest_job.organizational_unit_id == org_unit.id:
            stats["unchanged"] += 1
            continue

        if latest_job and latest_job.assigned_date == today:
            latest_job.organizational_unit = org_unit
            latest_job.save(update_fields=["organizational_unit"])
            stats["updated"] += 1
            continue

        JobCode.objects.create(
            vehicle=vehicle,
            organizational_unit=org_unit,
            assigned_date=today,
        )
        stats["created"] += 1

    message = (
        "Sifre posla vozila: "
        f"povuceno={stats['fetched']}, kreirano={stats['created']}, azurirano={stats['updated']}, "
        f"bez_promene={stats['unchanged']}, bez_vozila={stats['missing_vehicle']}, "
        f"bez_oj={stats['missing_org_unit']}, preskoceno={stats['skipped_invalid']}"
    )
    logger.info(message)
    return message


def sync_organizational_units_from_view():
    with connections[DB_ALIAS].cursor() as cursor:
        cursor.execute(f"SELECT sif_pos, naz_pos, blok FROM {ORG_UNIT_SOURCE_VIEW}")
        rows = cursor.fetchall()

    created = 0
    updated = 0
    skipped = 0

    for sif_pos, naz_pos, blok in rows:
        code = _clean_source_value(sif_pos)
        if not code:
            skipped += 1
            continue
        _, created_flag = OrganizationalUnit.objects.update_or_create(
            code=code,
            defaults={
                "name": _clean_source_value(naz_pos),
                "center": _clean_source_value(blok),
            },
        )
        if created_flag:
            created += 1
        else:
            updated += 1

    message = f"Organizacione jedinice: dodatih={created}, azuriranih={updated}, preskoceno={skipped}"
    logger.info(message)
    return message


def sync_vehicle_job_codes_with_org_units():
    org_units_message = sync_organizational_units_from_view()
    vehicle_job_codes_message = update_job_codes_from_view()
    message = f"{org_units_message}; {vehicle_job_codes_message}"
    logger.info("Sifre posla vozila sync zavrsen: %s", message)
    return message


def fetch_ddor_insurance_data():
    try:
        logger.debug("DDOR sync start")

        query = f"""
            SELECT
                god, sif_vrs, br_naloga, stavka, oj, knt, datum, vez_dok, potrazuje, kola
            FROM {INS_VIEW}
        """

        with connections[DB_ALIAS].cursor() as cursor:
            logger.debug("DDOR sync executing SQL query")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.debug("DDOR sync fetched rows=%s", len(rows))

        created = 0
        skipped_existing = 0
        errors = 0

        for i, row in enumerate(rows, start=1):
            try:
                god, sif_vrs, br_naloga, stavka, oj, knt, datum_dt, vez_dok, potrazuje, kola = row

                if datum_dt is not None:
                    if hasattr(datum_dt, "date"):
                        datum = datum_dt.date()
                    else:
                        dt = parse_datetime(str(datum_dt))
                        datum = dt.date() if dt else None
                else:
                    datum = None

                god = int(god) if god is not None else None
                sif_vrs = str(sif_vrs).strip() if sif_vrs is not None else None
                br_naloga = str(br_naloga).strip() if br_naloga is not None else ""
                stavka = str(stavka).strip() if stavka is not None else None
                oj = str(oj).strip() if oj is not None else None
                knt = str(knt).strip() if knt is not None else None
                vez_dok = str(vez_dok).strip() if vez_dok is not None else None
                kola = str(kola).strip() if kola is not None else None
                potrazuje = None if potrazuje in (None, "") else float(potrazuje)

                key_filter = dict(god=god, sif_vrs=sif_vrs, br_naloga=br_naloga, stavka=stavka, knt=knt)
                if Insurance.objects.filter(**key_filter).exists() or DraftInsurance.objects.filter(**key_filter).exists():
                    skipped_existing += 1
                    logger.debug("[%s] Postoji (final/draft): %s - preskačem.", i, key_filter)
                    continue

                DraftInsurance.objects.create(
                    god=god,
                    sif_vrs=sif_vrs,
                    br_naloga=br_naloga,
                    stavka=stavka,
                    oj=oj,
                    knt=knt,
                    datum=datum,
                    vez_dok=vez_dok,
                    potrazuje=potrazuje,
                    kola=kola,
                )
                created += 1
                logger.debug("[%s] Sačuvan draft: %s/%s (%s)", i, br_naloga, stavka, god)

            except Exception as exc:
                errors += 1
                logger.debug("[%s] Greška u obradi reda: %s", i, exc, exc_info=True)

        result = {
            "fetched": len(rows),
            "created": created,
            "skipped_existing": skipped_existing,
            "errors": errors,
        }
        logger.info("DDOR sync summary: %s", result)
        return (
            "DDOR sync: "
            f"povuceno={len(rows)}, kreirano={created}, preskoceno={skipped_existing}, problemi={errors}"
        )

    except Exception as exc:
        logger.error("Greška u fetch_ddor_insurance_data: %s", exc, exc_info=True)
        return f"Greška u fetch_ddor_insurance_data: {exc}"


def migrate_draft_to_insurance_single(draft_id: int, vehicle_id: int):
    try:
        draft = DraftInsurance.objects.get(id=draft_id)

        if not vehicle_id:
            raise ValueError("Nedostaje vehicle_id.")

        if not (draft.vehicle or vehicle_id) or draft.datum is None:
            raise ValueError("Draft nije kompletan (potrebni: vehicle i datum).")

        with transaction.atomic():
            key_kwargs = dict(
                god=draft.god,
                sif_vrs=draft.sif_vrs,
                br_naloga=draft.br_naloga,
                stavka=draft.stavka,
                knt=draft.knt,
            )

            ins, created = Insurance.objects.get_or_create(
                **key_kwargs,
                defaults=dict(
                    vehicle_id=vehicle_id,
                    oj=draft.oj,
                    datum=draft.datum,
                    vez_dok=draft.vez_dok,
                    potrazuje=draft.potrazuje,
                    kola=draft.kola,
                ),
            )

            if not created:
                ins.vehicle_id = vehicle_id
                ins.oj = draft.oj
                ins.datum = draft.datum
                ins.vez_dok = draft.vez_dok
                ins.potrazuje = draft.potrazuje
                ins.kola = draft.kola
                ins.save()

            draft.delete()

        return ins

    except DraftInsurance.DoesNotExist:
        raise ValueError("Draft zapis ne postoji.")
