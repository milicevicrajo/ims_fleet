import logging
from datetime import date, datetime
from decimal import Decimal

from django.db import connections, transaction

from fleet.models import (
    DraftServiceTransaction,
    Requisition,
    ServiceTransaction,
    ServiceType,
    TrafficCard,
    Vehicle,
)
from fleet.support.vehicle import format_license_plate

logger = logging.getLogger(__name__)


def _clean(value):
    return str(value or "").strip()


def _int_or_none(value):
    if value is None or _clean(value) == "":
        return None
    return int(Decimal(str(value).strip()))


def _decimal_or_none(value):
    if value is None or _clean(value) == "":
        return None
    return Decimal(str(value).strip())


def _date_or_none(value):
    if value is None or _clean(value) == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value).strip()[:10]).date()


def _plate_key(value):
    formatted = format_license_plate(_clean(value))
    return formatted.replace("-", "")


def fetch_service_data(last_24_hours=True, days=None):
    try:
        logger.debug("Servisi sync start")

        query = """
            SELECT god, sif_par_pl, naz_par_pl, datum, sif_vrs, br_naloga, vez_dok, knt_pl, potrazuje,
                   sif_par_npl, knt_npl, duguje, sif_pos, konto_vozila, kom, RegOzn, kilometraza,
                   poptavka_kategorija, nije_garaza, napomena
            FROM dbo.fleet_servisi
        """

        if days is not None:
            query += f" WHERE datum > DATEADD(day, -{days}, GETDATE())"
            logger.debug("Servisi sync filter: poslednjih %s dana", days)
        elif last_24_hours:
            query += " WHERE datum > DATEADD(day, -1, GETDATE())"
            logger.debug("Servisi sync filter: poslednja 24 sata")

        with connections["server_db"].cursor() as cursor:
            logger.debug("Servisi sync SQL: %s", query)
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.debug("Servisi sync fetched rows=%s", len(rows))

        expected_columns = 20
        created = 0
        skipped_existing_final = 0
        skipped_existing_draft = 0
        skipped_bad_columns = 0
        missing_service_types = 0
        conversion_errors = 0
        errors = 0

        for index, row in enumerate(rows):
            if len(row) != expected_columns:
                skipped_bad_columns += 1
                logger.debug(
                    "Servisi sync row skipped bad columns: row=%s columns=%s expected=%s data=%s",
                    index + 1,
                    len(row),
                    expected_columns,
                    row,
                )
                continue

            try:
                god = str(row[0]).strip() if row[0] else None
                vez_dok = str(row[6]).strip() if row[6] else None
                br_naloga = str(row[5]).strip() if row[5] else None
                sif_vrs = str(row[4]).strip() if row[4] else None

                transaction_exists = ServiceTransaction.objects.filter(
                    god=god,
                    vez_dok__iexact=vez_dok,
                    br_naloga__iexact=br_naloga,
                    sif_vrs=sif_vrs,
                ).exists()

                unique_fields = {
                    "god": row[0],
                    "sif_vrs": row[4],
                    "vez_dok": row[6],
                    "br_naloga": row[5],
                }
                draft_exists = DraftServiceTransaction.objects.filter(**unique_fields).exists()

                if transaction_exists:
                    skipped_existing_final += 1
                    logger.debug(
                        "Servisi sync row skipped existing final: br_naloga=%s",
                        row[5],
                    )
                    continue
                if draft_exists:
                    skipped_existing_draft += 1
                    logger.debug(
                        "Servisi sync row skipped existing draft: br_naloga=%s",
                        row[5],
                    )
                    continue

                potrazuje = float(row[8]) if row[8] is not None and str(row[8]).strip() != "" else None
                duguje = float(row[11]) if row[11] is not None and str(row[11]).strip() != "" else None
                kilometraza = int(row[16]) if row[16] is not None and str(row[16]).strip() != "" else 0

                nije_garaza_val = False
                if isinstance(row[18], bool):
                    nije_garaza_val = row[18]
                elif isinstance(row[18], str):
                    nije_garaza_val = row[18].strip().upper() == "DA"
                elif row[18] is not None:
                    try:
                        nije_garaza_val = bool(int(row[18]))
                    except (ValueError, TypeError):
                        pass

                service_type_value = row[17]
                service_type_instance = None
                if service_type_value is not None and str(service_type_value).strip() != "":
                    try:
                        service_type_instance = ServiceType.objects.get(name=str(service_type_value).strip())
                    except ServiceType.DoesNotExist:
                        missing_service_types += 1
                        logger.debug(
                            "Servisi sync missing ServiceType: value=%s",
                            service_type_value,
                        )
                    except Exception as exc:
                        missing_service_types += 1
                        logger.debug(
                            "Servisi sync ServiceType lookup error: value=%s error=%s",
                            service_type_value,
                            exc,
                            exc_info=True,
                        )

                vehicle = Vehicle.objects.filter(traffic_cards__registration_number=row[15]).first() if row[15] else None

                logger.debug("Servisi sync creating draft: br_naloga=%s", row[5])

                draft_transaction = DraftServiceTransaction(
                    vehicle=vehicle,
                    god=row[0],
                    sif_par_pl=row[1],
                    naz_par_pl=row[2],
                    datum=row[3],
                    sif_vrs=row[4],
                    br_naloga=row[5],
                    vez_dok=row[6],
                    knt_pl=row[7],
                    potrazuje=potrazuje,
                    sif_par_npl=row[9],
                    knt_npl=row[10],
                    duguje=duguje,
                    konto_vozila=row[13],
                    kom=row[14],
                    kilometraza=kilometraza,
                    popravka_kategorija=service_type_instance,
                    nije_garaza=nije_garaza_val,
                    napomena=row[19],
                )
                draft_transaction.save()
                created += 1
                logger.debug("Servisi sync draft saved: br_naloga=%s", row[5])

            except ValueError as exc:
                conversion_errors += 1
                logger.debug(
                    "Servisi sync conversion error: row=%s br_naloga=%s error=%s data=%s",
                    index + 1,
                    row[5],
                    exc,
                    row,
                    exc_info=True,
                )
            except Exception as exc:
                errors += 1
                logger.debug(
                    "Servisi sync row error: row=%s br_naloga=%s error=%s data=%s",
                    index + 1,
                    row[5],
                    exc,
                    row,
                    exc_info=True,
                )

        skipped = skipped_existing_final + skipped_existing_draft + skipped_bad_columns
        problems = missing_service_types + conversion_errors + errors
        result = {
            "fetched": len(rows),
            "created": created,
            "skipped": skipped,
            "skipped_existing_final": skipped_existing_final,
            "skipped_existing_draft": skipped_existing_draft,
            "skipped_bad_columns": skipped_bad_columns,
            "missing_service_types": missing_service_types,
            "conversion_errors": conversion_errors,
            "errors": errors,
        }
        logger.info("Servisi sync summary: %s", result)
        return (
            "Servisi sync: "
            f"povuceno={len(rows)}, kreirano={created}, preskoceno={skipped}, problemi={problems}"
        )

    except Exception as exc:
        logger.error("Servisi sync failed: %s", exc, exc_info=True)
        return f"Servisi sync failed: {exc}"


def migrate_draft_to_service_transaction(draft_id):
    try:
        draft = DraftServiceTransaction.objects.get(id=draft_id)

        if draft.is_complete():
            with transaction.atomic():
                service_transaction = ServiceTransaction.objects.create(
                    vehicle_id=draft.vehicle_id,
                    god=draft.god,
                    sif_par_pl=draft.sif_par_pl,
                    naz_par_pl=draft.naz_par_pl,
                    datum=draft.datum,
                    sif_vrs=draft.sif_vrs,
                    br_naloga=draft.br_naloga,
                    vez_dok=draft.vez_dok,
                    knt_pl=draft.knt_pl,
                    potrazuje=draft.potrazuje,
                    sif_par_npl=draft.sif_par_npl,
                    knt_npl=draft.knt_npl,
                    duguje=draft.duguje,
                    konto_vozila=draft.konto_vozila,
                    kom=draft.kom,
                    popravka_kategorija=draft.popravka_kategorija,
                    kilometraza=draft.kilometraza,
                )
                draft.delete()
            return service_transaction
        raise ValueError("Podaci nisu kompletni za migraciju")

    except DraftServiceTransaction.DoesNotExist:
        raise ValueError("Nepotpuni zapis ne postoji ili nije validan")


def fetch_requisition_data(last_24_hours=True, days=None):
    try:
        logger.debug("Trebovanja sync start")

        query = """
            SELECT sif_pred, god, br_dok, sif_vrsart, stavka, sif_art, naz_art, kol, cena, vrednost_nab,
                   datum_trebovanja, napomena, registracija
            FROM dbo.fleet_trebovanja
        """
        params = []

        if days is not None:
            query += " WHERE datum_trebovanja > DATEADD(day, -%s, GETDATE())"
            params.append(days)
            logger.debug("Trebovanja sync filter: poslednjih %s dana", days)
        elif last_24_hours:
            query += " WHERE datum_trebovanja > DATEADD(day, -1, GETDATE())"
            logger.debug("Trebovanja sync filter: poslednja 24 sata")

        with connections["server_db"].cursor() as cursor:
            logger.debug("Trebovanja sync SQL: %s", query)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            logger.debug("Trebovanja sync fetched rows=%s", len(rows))

        reg_to_vehicle = {
            _plate_key(card.registration_number): card.vehicle_id
            for card in TrafficCard.objects.only("registration_number", "vehicle_id")
            if _plate_key(card.registration_number)
        }

        created = 0
        updated = 0
        skipped_bad_columns = 0
        missing_vehicle = 0
        conversion_errors = 0
        errors = 0

        for index, row in enumerate(rows):
            logger.debug("Trebovanja sync row start: row=%s columns=%s", index + 1, len(row))

            if len(row) < 13:
                skipped_bad_columns += 1
                logger.debug("Trebovanja sync row skipped bad columns: row=%s data=%s", index + 1, row)
                continue

            try:
                sif_pred = _int_or_none(row[0])
                god = _int_or_none(row[1])
                br_dok = _clean(row[2])
                sif_vrsart = _clean(row[3])
                stavka = _int_or_none(row[4])
                sif_art = _clean(row[5])
                datum_trebovanja = _date_or_none(row[10])
                registration = _clean(row[12])
                vehicle_id = reg_to_vehicle.get(_plate_key(registration)) if registration else None

                if vehicle_id is None:
                    missing_vehicle += 1

                lookup = {
                    "sif_pred": sif_pred,
                    "god": god,
                    "br_dok": br_dok,
                    "sif_vrsart": sif_vrsart,
                    "stavka": stavka,
                }
                defaults = {
                    "sif_art": sif_art,
                    "naz_art": _clean(row[6]),
                    "kol": _decimal_or_none(row[7]),
                    "cena": _decimal_or_none(row[8]),
                    "vrednost_nab": _decimal_or_none(row[9]),
                    "mesec_unosa": datum_trebovanja.month,
                    "datum_trebovanja": datum_trebovanja,
                    "napomena": _clean(row[11]) or None,
                }
                if vehicle_id is not None:
                    defaults["vehicle_id"] = vehicle_id

                _requisition, was_created = Requisition.objects.update_or_create(
                    **lookup,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                    logger.debug("Trebovanja sync requisition created: br_dok=%s sif_art=%s", br_dok, sif_art)
                else:
                    updated += 1
                    logger.debug("Trebovanja sync requisition updated: br_dok=%s sif_art=%s", br_dok, sif_art)

            except ValueError as exc:
                conversion_errors += 1
                logger.debug("Trebovanja sync conversion error: row=%s error=%s", index + 1, exc, exc_info=True)
            except Exception as exc:
                errors += 1
                logger.debug("Trebovanja sync row error: row=%s error=%s", index + 1, exc, exc_info=True)

        skipped = skipped_bad_columns
        problems = conversion_errors + errors
        result = {
            "fetched": len(rows),
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "skipped_bad_columns": skipped_bad_columns,
            "missing_vehicle": missing_vehicle,
            "conversion_errors": conversion_errors,
            "errors": errors,
        }
        logger.info("Trebovanja sync summary: %s", result)
        return (
            "Trebovanja sync: "
            f"povuceno={len(rows)}, kreirano={created}, azurirano={updated}, "
            f"bez_vozila={missing_vehicle}, preskoceno={skipped}, problemi={problems}"
        )

    except Exception as exc:
        logger.error("Trebovanja sync failed: %s", exc, exc_info=True)
        return f"Trebovanja sync failed: {exc}"
