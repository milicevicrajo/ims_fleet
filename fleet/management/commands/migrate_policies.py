from django.core.management.base import BaseCommand
from django.db import connections, transaction
from contextlib import nullcontext
from fleet.support.vehicle import format_license_plate

def norm_reg(reg: str) -> str:
    return (reg or "").strip().upper().replace(" ", "")

def nz(val, default=0):
    """Null to Zero helper"""
    return val if val is not None else default
class Command(BaseCommand):
    help = "Migrira polise iz test_db.Vozila.dbo.polise u server_db.IMS_ERP.dbo.fleet_policy i veže vehicle_id preko fleet_trafficcard."
    


    def add_arguments(self, parser):
        parser.add_argument("--src", default="test_db", help="Alias stare baze (default: test_db)")
        parser.add_argument("--dst", default="server_db", help="Alias nove baze (default: server_db)")
        parser.add_argument("--dry-run", action="store_true", help="Bez upisa u bazu (proba)")
        parser.add_argument("--upsert", action="store_true", help="Ako postoji policy_number -> UPDATE, inače INSERT")

    def handle(self, *args, **opts):
        src_alias = opts["src"]      # test_db (stara)
        dst_alias = opts["dst"]      # server_db (nova)
        dry_run   = opts["dry_run"]  # <- ovde ispravljeno
        do_upsert = opts["upsert"]   # <- i ovde

        src = connections[src_alias]
        dst = connections[dst_alias]

        # 1) REG->vehicle_id mapa iz nove baze (server_db) preko NAJNOVIJEG trafficcard-a
        reg_to_vehicle = {}
        with dst.cursor() as cur:
            cur.execute("""
                ;WITH ranked AS (
                    SELECT
                        registration_number, vehicle_id, issue_date,
                        ROW_NUMBER() OVER (
                        PARTITION BY registration_number
                        ORDER BY issue_date DESC, id DESC
                        ) AS rn
                    FROM fleet_trafficcard
                    WHERE registration_number IS NOT NULL AND registration_number <> ''
                )
                SELECT registration_number, vehicle_id
                FROM ranked
                WHERE rn = 1
            """)
            for reg, vid in cur.fetchall():
                # ključ je TAČNO kako je u trafficcard (kanonski), bez ikakvog formatiranja ovde
                reg_to_vehicle[reg] = vid

        # 2) Polise iz stare baze (test_db)
        self.stdout.write("Čitam polise iz test_db.Vozila.dbo.polise ...")
        with src.cursor() as cur_src:
            cur_src.execute("""
                SELECT
                    PartnerPIB, PartnerIme, ID, BrojFakture, issuedate,
                    VrstaOsiguranja, BrojPolise, RegistraskaOznaka,
                    PeriodOd, PeriodDo, IznosPremije, IznosPrveRate,
                    IznosOstalihRata, BrojRata
                FROM polise
            """)
            polise = cur_src.fetchall()
        self.stdout.write(f" - Nađeno polisa: {len(polise)}")

        inserted = updated = 0
        skipped_no_reg = skipped_no_vehicle = 0

        tx = nullcontext() if dry_run else transaction.atomic(using=dst_alias)
        with tx:
            with dst.cursor() as cur_dst:
                for (partner_pib, partner_name, invoice_id, invoice_number, issue_date,
                     insurance_type, policy_number, registration_number, start_date, end_date,
                     premium_amount, first_installment_amount, other_installments_amount,
                     number_of_installments) in polise:

                    if not registration_number:
                        skipped_no_reg += 1
                        self.stdout.write(self.style.WARNING(
                            f"Preskočena polisa {policy_number} (nema registraciju)"
                        ))
                        continue

                    reg_std = format_license_plate(registration_number)   # *** OVDE je ključno ***
                    vehicle_id = reg_to_vehicle.get(reg_std)              # tražiš tačan kanonski ključ

                    if not vehicle_id:
                        skipped_no_vehicle += 1
                        self.stdout.write(self.style.WARNING(
                            f"Preskočena polisa {policy_number} (registracija: {registration_number}, vozilo nije pronađeno)"
                        ))
                        continue


                    if do_upsert:
                        cur_dst.execute("SELECT id FROM fleet_policy WHERE policy_number = %s", [policy_number])
                        row = cur_dst.fetchone()
                        if row:
                            if not dry_run:
                                cur_dst.execute("""
                                    UPDATE fleet_policy
                                    SET partner_pib=%s, partner_name=%s, invoice_id=%s, invoice_number=%s,
                                        issue_date=%s, insurance_type=%s, premium_amount=%s,
                                        start_date=%s, end_date=%s, first_installment_amount=%s,
                                        other_installments_amount=%s, number_of_installments=%s,
                                        vehicle_id=%s
                                    WHERE policy_number=%s
                                """, [
                                    partner_pib, partner_name, invoice_id, invoice_number,
                                    issue_date, insurance_type, nz(premium_amount),
                                    start_date, end_date, nz(first_installment_amount),
                                    nz(other_installments_amount), nz(number_of_installments),
                                    vehicle_id, policy_number
                                ])
                            updated += 1
                        else:
                            if not dry_run:
                                cur_dst.execute("""
                                    INSERT INTO fleet_policy (
                                        partner_pib, partner_name, invoice_id, invoice_number, issue_date,
                                        insurance_type, policy_number, premium_amount,
                                        start_date, end_date, first_installment_amount,
                                        other_installments_amount, number_of_installments,
                                        vehicle_id, is_renewable
                                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                                """, [
                                    partner_pib, partner_name, invoice_id, invoice_number, issue_date,
                                    insurance_type, policy_number, nz(premium_amount),
                                    start_date, end_date, nz(first_installment_amount),
                                    nz(other_installments_amount), nz(number_of_installments),
                                    vehicle_id
                                ])
                            inserted += 1
                    else:
                        if not dry_run:
                            cur_dst.execute("""
                                INSERT INTO fleet_policy (
                                    partner_pib, partner_name, invoice_id, invoice_number, issue_date,
                                    insurance_type, policy_number, premium_amount,
                                    start_date, end_date, first_installment_amount,
                                    other_installments_amount, number_of_installments,
                                    vehicle_id, is_renewable
                                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                            """, [
                                    partner_pib, partner_name, invoice_id, invoice_number, issue_date,
                                    insurance_type, policy_number, nz(premium_amount),
                                    start_date, end_date, nz(first_installment_amount),
                                    nz(other_installments_amount), nz(number_of_installments),
                                    vehicle_id
                            ])
                        inserted += 1

        self.stdout.write(self.style.SUCCESS(
            f"Gotovo. INSERT: {inserted}, UPDATE: {updated}, "
            f"preskočeno (bez registracije): {skipped_no_reg}, "
            f"preskočeno (bez pronađenog vozila): {skipped_no_vehicle}."
        ))
