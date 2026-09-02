# fleet/management/commands/fetch_servisi.py
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from fleet.models import (
    DraftServiceTransaction,
    ServiceTransaction,
    ServiceType,
    Vehicle,
)
from datetime import datetime, date

DEFAULT_SOURCE_ALIAS = "default"
DEFAULT_TARGET_ALIAS = "server_db"
DEFAULT_SOURCE_OBJECT = "dbo.servisi"   # možeš promeniti na "dbo.v_servisi" po potrebi

def to_int(val):
    if val is None:
        return None
    try:
        # Decimal, int, float, ili string '2024.0' / '2024,0'
        s = str(val).strip().replace(',', '.')
        return int(float(s))
    except (ValueError, TypeError):
        return None

def to_date(val):
    if val is None:
        return None
    # Ako već dođe kao datetime/date iz pyodbc
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val

    # Ako je string – očisti navodnike i parsiraj
    s = str(val).strip().strip('"').strip('“”').strip("'")
    # Probaj najčešće formate
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None  # nevalidno

class Command(BaseCommand):
    help = (
        "Povlači servisne transakcije iz izvora (default, npr. dbo.servisi) "
        "i upisuje u DraftServiceTransaction na odredištu (server_db). "
        "Preskače duplikate (ako već postoji u ServiceTransaction ili DraftServiceTransaction)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source-alias",
            default=DEFAULT_SOURCE_ALIAS,
            help=f"Alias izvora iz settings.DATABASES (default: {DEFAULT_SOURCE_ALIAS})",
        )
        parser.add_argument(
            "--target-alias",
            default=DEFAULT_TARGET_ALIAS,
            help=f"Alias odredišta iz settings.DATABASES (default: {DEFAULT_TARGET_ALIAS})",
        )
        parser.add_argument(
            "--source-object",
            default=DEFAULT_SOURCE_OBJECT,
            help=f"SQL objekat iz kojeg se čita (default: {DEFAULT_SOURCE_OBJECT}). "
                 f"Stavi 'dbo.v_servisi' ako čitaš iz view-a.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=None,
            help="Filtriraj po datumu (datum > GETDATE()-days). Ako nije dato, koristi poslednja 24h.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Bez vremenskog filtera.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ne upisuje u target; samo prebrojava/proverava.",
        )

    def handle(self, *args, **opts):
        source_alias = opts["source_alias"]
        target_alias = opts["target_alias"]
        source_object = opts["source_object"]
        days = opts["days"]
        dry_run = opts["dry_run"]
        no_time_filter = opts["all"]

        # Provera aliasa
        for alias in (source_alias, target_alias):
            if alias not in connections.databases:
                raise CommandError(f"DB alias '{alias}' nije definisan u settings.DATABASES")

        self.stdout.write(self.style.NOTICE(
            f"Izvor: {source_alias} → Odredište: {target_alias}\n"
            f"Izvorni objekat: {source_object}\n"
            f"Filter: "
            + ("(nema)" if no_time_filter else ("last 24h" if days is None else f"days={days}"))
            + f"  Dry-run: {dry_run}"
        ))

        # Redosled kolona mora da odgovara SQL objektu
        # Indeksi u kodu računaju na sledeći raspored:
        # 0:god,1:sif_par_pl,2:naz_par_pl,3:datum,4:sif_vrs,5:br_naloga,6:vez_dok,7:knt_pl,8:potrazuje,
        # 9:sif_par_npl,10:knt_npl,11:duguje,12:sif_pos,13:konto_vozila,14:kom,15:RegOzn,16:kilometraza,
        # 17:popravka_kategorija,18:nije_garaza,19:napomena
        query = f"""
            SELECT god, sif_par_pl, naz_par_pl, datum, sif_vrs, br_naloga, vez_dok, knt_pl, potrazuje,
                   sif_par_npl, knt_npl, duguje, sif_pos, konto_vozila, kom, RegOzn, kilometraza,
                   popravka_kategorija, nije_garaza, napomena
            FROM {source_object}
        """
        if not no_time_filter:
            if days is not None:
                query += f" WHERE datum > DATEADD(day, -{int(days)}, GETDATE())"
            else:
                query += " WHERE datum > DATEADD(day, -1, GETDATE())"

        # Čitanje iz izvora
        with connections[source_alias].cursor() as src_cur:
            src_cur.execute(query)
            rows = src_cur.fetchall()

        self.stdout.write(self.style.SUCCESS(f"Povučeno redova: {len(rows)}"))

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run uključen — nema upisa u draft tabelu."))
            return

        expected_columns = 20
        created = 0
        skipped_existing = 0
        bad_rows = 0

        for idx, row in enumerate(rows, start=1):
            try:
                if len(row) != expected_columns:
                    bad_rows += 1
                    self.stderr.write(
                        f"[{idx}] Neispravan broj kolona: {len(row)}/{expected_columns}. Preskačem."
                    )
                    continue

                # Ključ jedinstvenosti (isti kao u tvojoj funkciji)
                god = to_int(row[0])  
                sif_vrs = str(row[4]).strip() if row[4] is not None else None
                br_naloga = str(row[5]).strip() if row[5] is not None else None
                vez_dok = str(row[6]).strip() if row[6] is not None else None

                unique_filter = {
                    "god": god,
                    "sif_vrs": sif_vrs,
                    "br_naloga": br_naloga,
                    "vez_dok": vez_dok,
                }

                # Duplikati na TARGET-u
                if ServiceTransaction.objects.using(target_alias).filter(**unique_filter).exists():
                    skipped_existing += 1
                    continue
                if DraftServiceTransaction.objects.using(target_alias).filter(**unique_filter).exists():
                    skipped_existing += 1
                    continue

                # Konverzije
                potrazuje = float(row[8]) if row[8] not in (None, "") else None
                duguje = float(row[11]) if row[11] not in (None, "") else None
                try:
                    kilometraza = int(row[16]) if row[16] not in (None, "") else 0
                except (TypeError, ValueError):
                    kilometraza = 0

                # nije_garaza
                nije_garaza_val = False
                raw_ng = row[18]
                if isinstance(raw_ng, bool):
                    nije_garaza_val = raw_ng
                elif isinstance(raw_ng, str):
                    nije_garaza_val = (raw_ng.strip().upper() in ("DA", "1", "TRUE"))
                elif raw_ng is not None:
                    try:
                        nije_garaza_val = bool(int(raw_ng))
                    except Exception:
                        nije_garaza_val = False

                # Kategorija (ServiceType po imenu)
                service_type_instance = None
                raw_cat = row[17]
                if raw_cat not in (None, ""):
                    try:
                        service_type_instance = ServiceType.objects.using(target_alias).get(
                            name=str(raw_cat).strip()
                        )
                    except ServiceType.DoesNotExist:
                        service_type_instance = None

                # Vozilo po registraciji (RegOzn = row[15])
                vehicle_obj = None
                if row[15]:
                    # pretpostavka: Vehicle/TrafficCard su u target bazi
                    vehicle_obj = (
                        Vehicle.objects.using(target_alias)
                        .filter(traffic_cards__registration_number=row[15])
                        .first()
                    )
                datum = to_date(row[3])
                if not datum:
                    print(f"[{idx+1}] Preskačem: nevalidan datum: {row[3]}")
                    continue
                # Kreiranje draft zapisa (na TARGET-u)
                DraftServiceTransaction.objects.using(target_alias).create(
                    vehicle=vehicle_obj,
                    god=god,
                    sif_par_pl=row[1],
                    naz_par_pl=row[2],
                    datum=datum,
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
                created += 1

            except Exception as ex:
                bad_rows += 1
                self.stderr.write(f"[{idx}] Greška: {ex}")

        self.stdout.write(self.style.SUCCESS(
            f"Gotovo. Kreirano: {created}, preskočeno (postojeće): {skipped_existing}, neispravni redovi: {bad_rows}"
        ))
