# fleet/management/commands/assign_vehicle_ids.py
from __future__ import annotations

import re
from typing import Dict, Optional

from django.core.management.base import BaseCommand
from django.db import connections, transaction

from fleet.models import DraftRequisition, TrafficCard


# --- tvoja normalizacija tablice (malo prilagođena) ---
def format_license_plate(plate: str) -> str:
    plate = plate.replace("–", "-").replace("-", "").replace(" ", "").upper()
    plate = re.sub(r'[^A-Za-z0-9]', '', plate)
    m = re.match(r'^([A-Z]{2})(\d{3,4})([A-Z]{2})$', plate)
    if m:
        return f"{m.group(1)}{m.group(2)}-{m.group(3)}"
    return plate

def norm_plate_key(plate: Optional[str]) -> str:
    """Kanonik za poređenje: formatiraj, pa skini crticu → 'BG1461DX'."""
    if not plate:
        return ""
    f = format_license_plate(plate)
    return f.replace("-", "")


def norm_doc(v) -> Optional[str]:
    """
    Normalizuj broj dokumenta kao 'int' → string.
    '509' → '509', ' 000509 ' → '509', '509.0' → '509'
    Ako ne može da se pročita broj → None
    """
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
        "Dodeljuje DraftRequisition.vehicle_id za SVE redove prema mapi (br_dok → RegOzn) iz izvora, "
        "gde je br_dok normalizovan na int-string. Poređenje registarskih vrši se preko formatirane tablice."
    )

    def add_arguments(self, parser):
        parser.add_argument("--source-alias", default="test_db", help="DB alias izvora (default: test_db)")
        parser.add_argument("--target-alias", default="server_db", help="DB alias odredišta (default: server_db)")
        parser.add_argument("--source-object", default="dbo.trebovanja",
                            help="View/tabela sa kolonama br_dok, RegOzn (default: dbo.trebovanja)")
        parser.add_argument("--dry-run", action="store_true", help="Ne piše u bazu, samo izveštaj.")
        parser.add_argument("--only-missing", action="store_true",
                            help="Ažuriraj samo redove gde je vehicle NULL (default: False = svi redovi).")
        parser.add_argument("--chunk-size", type=int, default=2000, help="Veličina batch-a za bulk_update.")

    def handle(self, *args, **o):
        src = o["source_alias"]
        tgt = o["target_alias"]
        src_obj = o["source_object"]
        dry = o["dry_run"]
        only_missing = o["only_missing"]
        chunk = o["chunk_size"]

        # 0) provera konekcija
        for alias in (src, tgt):
            if alias not in connections.databases:
                self.stderr.write(self.style.ERROR(f"DB alias '{alias}' nije definisan u settings.DATABASES"))
                return

        self.stdout.write(self.style.NOTICE(
            f"Izvor: {src}  →  Odredište: {tgt}\n"
            f"Izvorni objekat: {src_obj}\n"
            f"Mode: {'ONLY-MISSING' if only_missing else 'ALL'}   Dry-run: {dry}   Chunk: {chunk}"
        ))

        # 1) reg → vehicle_id mapa sa target baze (TrafficCard)
        self.stdout.write("Učitavam registarske (TrafficCard) ...")
        reg_to_vehicle: Dict[str, int] = {}
        for tc in TrafficCard.objects.using(tgt).only("registration_number", "vehicle_id"):
            key = norm_plate_key(tc.registration_number)
            if key and key not in reg_to_vehicle:
                reg_to_vehicle[key] = tc.vehicle_id
        self.stdout.write(self.style.SUCCESS(f"Reg mapa: {len(reg_to_vehicle)} unosa"))

        # 2) DISTINCT br_dok → RegOzn iz izvora (normalizacija br_dok + tablice)
        self.stdout.write("Učitavam DISTINCT br_dok, RegOzn sa izvora ...")
        with connections[src].cursor() as cur:
            cur.execute(f"""
                SELECT DISTINCT br_dok, RegOzn
                FROM {src_obj}
                WHERE RegOzn IS NOT NULL
            """)
            rows = cur.fetchall()

        brdok_to_regkey: Dict[str, str] = {}
        collisions = 0
        for br_dok, reg in rows:
            nd = norm_doc(br_dok)
            rk = norm_plate_key(reg)
            if not nd or not rk:
                continue
            # Ako isti br_dok ima više različitih RegOzn, zadrži prvu (po potrebi izmeni logiku)
            if nd in brdok_to_regkey and brdok_to_regkey[nd] != rk:
                collisions += 1
                continue
            brdok_to_regkey.setdefault(nd, rk)

        self.stdout.write(self.style.SUCCESS(
            f"Mapa br_dok→reg: {len(brdok_to_regkey)} (detektovanih višestrukih dodela: {collisions})"
        ))

        # 3) Iteriraj SVAKI red u DraftRequisition (po zahtevu)
        qs = DraftRequisition.objects.using(tgt).only("id", "br_dok", "vehicle_id")
        if only_missing:
            qs = qs.filter(vehicle__isnull=True)

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Krećem kroz DraftRequisition redova: {total}"))

        to_update = []
        updated, no_src_map, no_plate_match = 0, 0, 0

        for dr in qs.iterator(chunk_size=5000):
            nd = norm_doc(dr.br_dok)
            if not nd:
                no_src_map += 1
                continue

            reg_key = brdok_to_regkey.get(nd)
            if not reg_key:
                no_src_map += 1
                continue

            vid = reg_to_vehicle.get(reg_key)
            if not vid:
                no_plate_match += 1
                continue

            # Postavi uvek (ALL) ili samo ako je missing (already filtered)
            if dr.vehicle_id == vid:
                continue  # već postavljeno
            dr.vehicle_id = vid
            to_update.append(dr)

            if len(to_update) >= chunk:
                if not dry:
                    with transaction.atomic(using=tgt):
                        DraftRequisition.objects.using(tgt).bulk_update(to_update, ["vehicle_id"], batch_size=chunk)
                updated += len(to_update)
                to_update.clear()

        if to_update:
            if not dry:
                with transaction.atomic(using=tgt):
                    DraftRequisition.objects.using(tgt).bulk_update(to_update, ["vehicle_id"], batch_size=chunk)
            updated += len(to_update)

        self.stdout.write(self.style.SUCCESS(
            f"Završeno. {'(dry-run) ' if dry else ''}"
            f"Ažurirano: {updated} / {total} | "
            f"Nisu našli br_dok u mapi: {no_src_map} | "
            f"Reg postoji u mapi, ali nema vozila: {no_plate_match}"
        ))
