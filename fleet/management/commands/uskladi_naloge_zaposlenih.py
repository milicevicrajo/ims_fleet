from django.core.management.base import BaseCommand

from fleet.services.employee_user_profiles import uskladi_naloge_zaposlenih


class Command(BaseCommand):
    help = ("Jedan korisnicki nalog po osobi (JMBG): pravi naloge aktivnim osobama bez naloga, prebacuje nalog sa "
            "neaktivnog na aktivan broj radnika, deaktivira duple naloge i naloge bivsih zaposlenih. "
            "Bez --execute samo prikazuje plan.")

    def add_arguments(self, parser):
        parser.add_argument("--execute", action="store_true", help="Sprovodi plan (inace samo prikaz).")
        parser.add_argument("--i-van-radnog-odnosa", action="store_true", dest="van_radnog_odnosa",
                            help="Pravi naloge i osobama samo van radnog odnosa (privremeni i povremeni poslovi).")

    def handle(self, *args, **options):
        plan = uskladi_naloge_zaposlenih(execute=options["execute"], van_radnog_odnosa=options["van_radnog_odnosa"])
        w = self.stdout.write
        w(f"NALOG TREBA NAPRAVITI: {len(plan['kreirati'])}")
        for e in plan["kreirati"]:
            w(f"  {e.employee_code} | {e} | OJ {e.org_unit_code or e.department_code} | {e.get_preduzece_display()}")
        w(f"NALOG PREBACITI NA AKTIVAN BROJ: {len(plan['prebaciti'])}")
        for u, staro, novo in plan["prebaciti"]:
            w(f"  {u.username} | {staro.employee_code} -> {novo.employee_code}")
        w(f"DUPLI NALOZI ZA DEAKTIVACIJU: {len(plan['dupli'])}")
        for u in plan["dupli"]:
            w(f"  {u.username} | {u.employee.employee_code} {u.employee}")
        w(f"NALOZI BIVSIH ZAPOSLENIH ZA DEAKTIVACIJU: {len(plan['bivsi'])}")
        for u in plan["bivsi"]:
            w(f"  {u.username} | {u.employee.employee_code} {u.employee} | poslednja prijava {u.last_login or 'nikad'}")
        if not options["execute"]:
            w(self.style.WARNING("PROBA: nista nije upisano. Dodaj --execute."))
            return
        for e, u, center, reason in plan["kreirano"]:
            w(f"  NAPRAVLJEN {u.username} | {e.employee_code} {e} | centar {center or '-'} ({reason})")
        for e, razlog in plan["preskoceno"]:
            w(f"  PRESKOCEN {e.employee_code} {e}: {razlog}")
        w(self.style.SUCCESS(f"Napravljeno {len(plan['kreirano'])}, prebaceno {len(plan['prebaciti'])}, "
                             f"deaktivirano {len(plan['dupli']) + len(plan['bivsi'])}."))
