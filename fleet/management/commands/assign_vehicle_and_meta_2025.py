# fleet/management/commands/assign_vehicle_and_meta_2025.py
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.utils.timezone import make_naive

from fleet.models import DraftRequisition, TrafficCard, ServiceType

from datetime import date, datetime

def to_date(val):
    """Pretvara SQL Server datetime/string u date ili None."""
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    # string: '2024-01-15 00:00:00.000' -> '2024-01-15'
    s = str(val).strip()
    if len(s) >= 10:
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            pass
    # probaj generički parser formata 'YYYY-MM-DD HH:MM:SS.mmm'
    try:
        return datetime.strptime(s.split('.')[0], "%Y-%m-%d %H:%M:%S").date()
    except Exception:
        return None


# ---- normalizacija tablice (tvoja funkcija, blago prilagođena) ----
def format_license_plate(plate: str) -> str:
    plate = plate.replace("–", "-").replace("-", "").replace(" ", "").upper()
    plate = re.sub(r'[^A-Za-z0-9]', '', plate)
    m = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
    if m:
        return f"{m.group(1)}{m.group(2)}-{m.group(3)}"
    return plate

def norm_plate_key(plate: Optional[str]) -> str:
    """Kanonik ključa: formatiraj pa ukloni crticu -> 'BG1461DX'."""
    if not plate:
        return ""
    f = format_license_plate(plate)
    return f.replace("-", "")

def norm_doc(v) -> Optional[str]:
    """br_dok uvek kao čist int->str (skida .0, vodeće nule, razmake)."""
    if v is None:
        return None
    s = str(v).strip()
    try:
        return str(int(float(s)))
    except ValueError:
        digits = re.sub(r"[^0-9]", "", s)
        return str(int(digits)) if digits else None


class Command(BaseCommand):
    help = (
        "Za sve DraftRequisition sa god=2025: dodeljuje vehicle_id (preko br_dok→RegOzn), "
        "i ažurira datum_trebovanja, mesec_unosa, kilometraza, popravka_kategorija (FK po identičnom nazivu)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source-alias", default="test_db", help="DB alias izvora (default: test_db)")
        parser.add_argument("--target-alias", default="server_db", help="DB alias odredišta (default: server_db)")
        parser.add_argument(
            "--source-object",
            default="dbo.trebovanja",
            help="View/tabela sa kolonama: br_dok, RegOzn, mesec_unosa, datum_trebovanja, popravka_kategorija, kilometraza",
        )
        parser.add_argument("--dry-run", action="store_true", help="Ne piše u bazu, samo izveštaj.")
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Menja samo polja koja su trenutno NULL/prazna (vehicle_id NULL, dat/mesečni/kil NULL).",
        )
        parser.add_argument("--chunk-size", type=int, default=2000, help="Veličina batch-a za bulk_update.")
        parser.add_argument(
            "--year",
            type=int,
            default=2024,
            help="Godina za filtriranje DraftRequisition (default: 2025).",
        )

    def handle(self, *args, **o):
        src = o["source_alias"]
        tgt = o["target_alias"]
        src_obj = o["source_object"]
        dry = o["dry_run"]
        only_missing = o["only_missing"]
        chunk = o["chunk_size"]
        year = o["year"]

        # provera konekcija
        for alias in (src, tgt):
            if alias not in connections.databases:
                self.stderr.write(self.style.ERROR(f"DB alias '{alias}' nije definisan u settings.DATABASES"))
                return

        self.stdout.write(self.style.NOTICE(
            f"Izvor: {src}  →  Odredište: {tgt}\n"
            f"Izvorni objekat: {src_obj}\n"
            f"Godina: {year}   Mode: {'ONLY-MISSING' if only_missing else 'ALL'}   Dry-run: {dry}   Chunk: {chunk}"
        ))

        # 1) REG → VEHICLE mapa (TrafficCard na targetu)
        self.stdout.write("Učitavam registarske (TrafficCard) ...")
        reg_to_vehicle: Dict[str, int] = {}
        for tc in TrafficCard.objects.using(tgt).only("registration_number", "vehicle_id"):
            key = norm_plate_key(tc.registration_number)
            if key and key not in reg_to_vehicle:
                reg_to_vehicle[key] = tc.vehicle_id
        self.stdout.write(self.style.SUCCESS(f"Reg mapa: {len(reg_to_vehicle)} unosa"))

        # 2) DISTINCT br_dok → (reg_key, mesec, datum, kategorija_text, km) iz izvora
        self.stdout.write("Učitavam DISTINCT br_dok, RegOzn, mesec_unosa, datum_trebovanja, popravka_kategorija, kilometraza ...")
        with connections[src].cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT
                    br_dok,
                    RegOzn,
                    mesec_unosa,
                    CAST(datum_trebovanja AS date) AS datum_trebovanja,
                    popravka_kategorija,
                    kilometraza
                FROM {src_obj}
                WHERE god = %s
            """, [year])
            rows = cur.fetchall()

        # mapiranje br_dok → podaci
        # vrednost: (reg_key, mesec:int|None, datum:date|None, kategorija_text:str|None, km:int|None)
        brdok_to_meta: Dict[str, Tuple[str, Optional[int], Optional[object], Optional[str], Optional[int]]] = {}
        collisions = 0
        for br_dok, reg, mesec, datum, kat_txt, km in rows:
            nd = norm_doc(br_dok)
            rk = norm_plate_key(reg)
            if not nd:
                continue
            # uzmi prvu viđenu kombinaciju (ako ima kolizija po br_dok, ostavi prvu)
            if nd in brdok_to_meta:
                collisions += 1
                continue
            # SQL Server vraća datetime; konvertuj na naive date
            if hasattr(datum, "date"):
                datum_val = make_naive(datum).date()
            else:
                datum_val = datum
            # mesec i km u int ako mogu
            mesec_val = int(mesec) if mesec not in (None, "") else None
            datum_val = to_date(datum)
            try:
                km_val = int(km) if km is not None else None
            except (TypeError, ValueError):
                km_val = None
            kat_val = str(kat_txt).strip() if kat_txt else None
            brdok_to_meta[nd] = (rk, mesec_val, datum_val, kat_val, km_val)

            brdok_to_meta[nd] = (rk, mesec_val, datum_val, kat_val, km_val)

        self.stdout.write(self.style.SUCCESS(
            f"Mapa br_dok→meta: {len(brdok_to_meta)} (detektovanih kolizija: {collisions})"
        ))

        # 3) Pre-učitaj ServiceType u dict {lower_name: id} radi O(1) lookup-a
        st_map: Dict[str, int] = {
            st.name.lower(): st.id
            for st in ServiceType.objects.using(tgt).only("id", "name")
        }

        # 4) Prođi sve draftove iz zadate godine
        qs = DraftRequisition.objects.using(tgt).filter(god=year).only(
            "id", "br_dok", "vehicle_id", "mesec_unosa", "datum_trebovanja",
            "popravka_kategorija_id", "kilometraza"
        )

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Krećem kroz DraftRequisition (god={year}) redova: {total}"))

        to_update = []
        updated = 0
        no_src_map = 0
        no_plate_match = 0
        st_missed = 0

        for dr in qs.iterator(chunk_size=5000):
            nd = norm_doc(dr.br_dok)
            if not nd or nd not in brdok_to_meta:
                no_src_map += 1
                continue

            reg_key, mesec_val, datum_val, kat_val, km_val = brdok_to_meta[nd]

            # vehicle
            vid = reg_to_vehicle.get(reg_key) if reg_key else None

            # service type (po istom tekstu)
            st_id = None
            if kat_val:
                st_id = st_map.get(kat_val.lower())
                if st_id is None:
                    st_missed += 1

            changed = False

            # vehicle_id
            if vid is not None:
                if (not only_missing) or (only_missing and dr.vehicle_id is None):
                    if dr.vehicle_id != vid:
                        dr.vehicle_id = vid
                        changed = True
            # mesec_unosa
            if mesec_val is not None:
                if (not only_missing) or (only_missing and (dr.mesec_unosa is None)):
                    if dr.mesec_unosa != mesec_val:
                        dr.mesec_unosa = mesec_val
                        changed = True
            # datum_trebovanja
            if datum_val is not None:
                if (not only_missing) or (only_missing and (dr.datum_trebovanja is None)):
                    if dr.datum_trebovanja != datum_val:
                        dr.datum_trebovanja = datum_val
                        changed = True
            # kilometraza
            if km_val is not None:
                if (not only_missing) or (only_missing and (dr.kilometraza is None)):
                    if dr.kilometraza != km_val:
                        dr.kilometraza = km_val
                        changed = True
            # popravka_kategorija FK (samo ako postoji isti tekst u ServiceType)
            if st_id is not None:
                if (not only_missing) or (only_missing and (dr.popravka_kategorija_id is None)):
                    if dr.popravka_kategorija_id != st_id:
                        dr.popravka_kategorija_id = st_id
                        changed = True

            if changed:
                to_update.append(dr)
                if len(to_update) >= chunk:
                    if not dry:
                        with transaction.atomic(using=tgt):
                            DraftRequisition.objects.using(tgt).bulk_update(
                                to_update,
                                ["vehicle_id", "mesec_unosa", "datum_trebovanja", "kilometraza", "popravka_kategorija_id"],
                                batch_size=chunk
                            )
                    updated += len(to_update)
                    to_update.clear()

        if to_update:
            if not dry:
                with transaction.atomic(using=tgt):
                    DraftRequisition.objects.using(tgt).bulk_update(
                        to_update,
                        ["vehicle_id", "mesec_unosa", "datum_trebovanja", "kilometraza", "popravka_kategorija_id"],
                        batch_size=chunk
                    )
            updated += len(to_update)

        self.stdout.write(self.style.SUCCESS(
            f"Završeno. {'(dry-run) ' if dry else ''}"
            f"Ažurirano: {updated} / {total} | "
            f"Nisu našli br_dok u mapi: {no_src_map} | "
            f"Reg postoji ali nema vozila: {no_plate_match} | "
            f"ServiceType promašaji (tekst ne postoji): {st_missed}"
        ))
