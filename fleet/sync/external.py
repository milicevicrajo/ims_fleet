import logging
from datetime import date, datetime
from decimal import Decimal

from django.db import connections, transaction
from django.utils.dateparse import parse_datetime

from core.models import OrganizationalUnit

from fleet.models import (
    DraftInsurance,
    DraftPolicy,
    Insurance,
    JobCode,
    Policy,
    TrafficCard,
    Vehicle,
)

logger = logging.getLogger(__name__)

INS_VIEW = "dbo.fleet_potrazivanje_ddor"
DB_ALIAS = "server_db"
KEY_FIELDS = ("god", "sif_vrs", "br_naloga", "stavka", "knt")


def fetch_policy_data(last_24_hours=True, days=None):
    try:
        logger.info("Starting data fetching process...")

        base_query = """
            SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate,
                   VrstaOsiguranja, BrojPolise, IznosPremije, RegistraskaOznaka,
                   PeriodOd, PeriodDo, IznosPrveRate, IznosOstalihRata, BrojRata
            FROM dbo.fleet_polise
        """
        params = []
        where_clauses = []

        if days is not None:
            where_clauses.append("issuedate > DATEADD(day, -%s, GETDATE())")
            params.append(days)
            logger.info("Filtering data for last %s days", days)
        elif last_24_hours:
            where_clauses.append("issuedate > DATEADD(day, -1, GETDATE())")
            logger.info("Filtering data for last 24 hours")

        query = base_query
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        with connections["server_db"].cursor() as cursor:
            logger.info("Executing SQL query...")
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            logger.info("Fetched %s rows", len(rows))
            if not rows:
                return "No new data found"

        new_policies = 0
        new_drafts = 0
        errors = 0

        with transaction.atomic():
            for row in rows:
                row_data = dict(zip(columns, row))
                invoice_id_from_db = row_data["ID"]

                try:
                    exists = (
                        Policy.objects.filter(invoice_id=invoice_id_from_db).exists()
                        or DraftPolicy.objects.filter(invoice_id=invoice_id_from_db).exists()
                    )
                    if exists:
                        logger.debug("Skipping existing invoice %s", invoice_id_from_db)
                        continue

                    vehicle = None
                    if reg_plate := row_data.get("RegistraskaOznaka"):
                        vehicle = Vehicle.objects.filter(registration_number=reg_plate).first()

                    model_field_map = {
                        "PartnerPIB": "partner_pib",
                        "PartnerIme": "partner_name",
                        "ID": "invoice_id",
                        "BrojFakture": "invoice_number",
                        "issuedate": "issue_date",
                        "VrstaOsiguranja": "insurance_type",
                        "BrojPolise": "policy_number",
                        "IznosPremije": "premium_amount",
                        "PeriodOd": "start_date",
                        "PeriodDo": "end_date",
                        "IznosPrveRate": "first_installment_amount",
                        "IznosOstalihRata": "other_installments_amount",
                        "BrojRata": "number_of_installments",
                    }

                    policy_data_to_save = {}
                    for sql_col, model_field in model_field_map.items():
                        value = row_data.get(sql_col)

                        if model_field in ["issue_date", "start_date", "end_date"]:
                            if value is None:
                                value = None
                            elif isinstance(value, str):
                                if not value.strip():
                                    value = None
                                else:
                                    try:
                                        value = datetime.strptime(value, "%Y-%m-%d").date()
                                    except ValueError:
                                        logger.warning(
                                            "Invalid date format for %s: %r. Setting to None for invoice %s.",
                                            model_field,
                                            value,
                                            invoice_id_from_db,
                                        )
                                        value = None
                            elif not isinstance(value, date):
                                logger.warning(
                                    "Unexpected date type for %s: %s. Setting to None for invoice %s.",
                                    model_field,
                                    type(value),
                                    invoice_id_from_db,
                                )
                                value = None

                        elif model_field in ["premium_amount", "first_installment_amount", "other_installments_amount"]:
                            if value is None:
                                value = None
                            elif isinstance(value, str):
                                if not value.strip():
                                    value = None
                                else:
                                    try:
                                        value = Decimal(value)
                                    except Exception:
                                        logger.warning(
                                            "Invalid decimal format for %s: %r. Setting to None for invoice %s.",
                                            model_field,
                                            value,
                                            invoice_id_from_db,
                                        )
                                        value = None
                            elif not isinstance(value, (Decimal, int, float)):
                                logger.warning(
                                    "Unexpected numeric type for %s: %s. Setting to None for invoice %s.",
                                    model_field,
                                    type(value),
                                    invoice_id_from_db,
                                )
                                value = None
                            else:
                                try:
                                    value = Decimal(value)
                                except Exception:
                                    logger.warning(
                                        "Could not convert %s %r to Decimal. Setting to None for invoice %s.",
                                        model_field,
                                        value,
                                        invoice_id_from_db,
                                    )
                                    value = None

                        elif model_field in ["partner_pib", "invoice_id", "number_of_installments"]:
                            if value is None:
                                value = None
                            elif isinstance(value, str):
                                if not value.strip():
                                    value = None
                                else:
                                    try:
                                        value = int(value)
                                    except ValueError:
                                        logger.warning(
                                            "Invalid integer format for %s: %r. Setting to None for invoice %s.",
                                            model_field,
                                            value,
                                            invoice_id_from_db,
                                        )
                                        value = None
                            elif not isinstance(value, int):
                                logger.warning(
                                    "Unexpected integer type for %s: %s. Setting to None for invoice %s.",
                                    model_field,
                                    type(value),
                                    invoice_id_from_db,
                                )
                                value = None

                        policy_data_to_save[model_field] = value

                    policy_data_to_save["vehicle"] = vehicle

                    temp_draft_policy = DraftPolicy(**policy_data_to_save)
                    if temp_draft_policy.is_complete():
                        Policy.objects.create(**policy_data_to_save)
                        new_policies += 1
                        logger.info("Created complete Policy for invoice %s.", invoice_id_from_db)
                    else:
                        DraftPolicy.objects.create(**policy_data_to_save)
                        new_drafts += 1
                        logger.info("Created DraftPolicy for invoice %s (incomplete).", invoice_id_from_db)

                except Exception as exc:
                    logger.error("Error processing invoice %s: %s", invoice_id_from_db, exc, exc_info=True)
                    errors += 1

        msg = f"Successfully processed {new_policies} policies, {new_drafts} drafts. Errors: {errors}"
        logger.info(msg)
        return msg

    except Exception as exc:
        logger.error("Critical error in data fetch: %s", exc, exc_info=True)
        return f"Critical error: {exc}"


def process_vehicle_retirements():
    try:
        logger.info("Pokrećem funkciju za obradu otpisanih vozila...")
        query = """
            SELECT inv_br
            FROM dbo.otpis;
        """

        retired_vehicles_from_db = []
        with connections["server_db"].cursor() as cursor:
            logger.info("Izvršavam SQL upit za preuzimanje otpisanih vozila: %s", query)
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info("Broj povučenih redova iz dbo.otpis: %s", len(rows))

            for row in rows:
                if row[0] is not None:
                    retired_vehicles_from_db.append(str(row[0]).strip())

        if not retired_vehicles_from_db:
            logger.info("Nema inventarnih brojeva u dbo.otpis za obradu.")
            return "Nema otpisanih vozila za obradu."

        updated_count = 0
        skipped_count = 0

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
                    logger.info(
                        "Uspešno otpisano vozilo: %s - %s %s.",
                        vehicle.inventory_number,
                        vehicle.brand,
                        vehicle.model,
                    )

                except Vehicle.DoesNotExist:
                    logger.warning("Vozilo sa inventarnim brojem %r iz dbo.otpis nije pronađeno u Django bazi.", inv_br_from_db)
                except Exception as exc:
                    logger.error("Greška pri obradi vozila %r: %s", inv_br_from_db, exc, exc_info=True)

        message = (
            "Proces otpisa završen: "
            f"Ažurirano vozila: {updated_count}, "
            f"Već otpisana (preskočena): {skipped_count}, "
            f"Nije pronađeno u Django bazi: {len(retired_vehicles_from_db) - updated_count - skipped_count}"
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


def update_job_codes_from_view():
    today = date.today()
    updated = 0

    with connections["server_db"].cursor() as cursor:
        cursor.execute("SELECT regbr, sifpos FROM dbo.sif_pos_trenutno")
        rows = cursor.fetchall()

    for regbr, sifpos in rows:
        try:
            traffic_card = TrafficCard.objects.select_related("vehicle").get(registration_number=regbr)
            vehicle = traffic_card.vehicle
        except TrafficCard.DoesNotExist:
            continue

        try:
            org_unit = OrganizationalUnit.objects.get(code=sifpos)
        except OrganizationalUnit.DoesNotExist:
            continue

        latest_job = vehicle.job_codes.order_by("-assigned_date").first()

        if not latest_job or latest_job.organizational_unit != org_unit:
            JobCode.objects.create(
                vehicle=vehicle,
                organizational_unit=org_unit,
                assigned_date=today,
            )
            updated += 1

    return updated


def sync_organizational_units_from_view():
    with connections["server_db"].cursor() as cursor:
        cursor.execute("SELECT sif_pos, naz_pos, blok FROM dbo.v_organizationalunit")
        rows = cursor.fetchall()

    created = 0
    updated = 0

    for sif_pos, naz_pos, blok in rows:
        _, created_flag = OrganizationalUnit.objects.update_or_create(
            code=sif_pos,
            defaults={
                "name": naz_pos,
                "center": blok,
            },
        )
        if created_flag:
            created += 1
        else:
            updated += 1

    logger.info("Organizacione jedinice: %s dodatih, %s ažuriranih.", created, updated)


def fetch_ddor_insurance_data():
    try:
        logger.info("Pokrećem fetch_ddor_insurance_data...")

        query = f"""
            SELECT
                god, sif_vrs, br_naloga, stavka, oj, knt, datum, vez_dok, potrazuje, kola
            FROM {INS_VIEW}
        """

        with connections[DB_ALIAS].cursor() as cursor:
            logger.info("Izvršavam SQL upit...")
            cursor.execute(query)
            rows = cursor.fetchall()
            logger.info("Preuzeto redova: %s", len(rows))

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
                    logger.warning("[%s] Postoji (final/draft): %s - preskačem.", i, key_filter)
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
                logger.info("[%s] Sačuvan draft: %s/%s (%s)", i, br_naloga, stavka, god)

            except Exception as exc:
                logger.info("[%s] Greška u obradi reda: %s", i, exc)

        return "DDOR: podaci uspešno povučeni u draft; duplikati preskočeni."

    except Exception as exc:
        logger.info("Greška u fetch_ddor_insurance_data: %s", exc)
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
