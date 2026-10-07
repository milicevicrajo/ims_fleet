from django.core.management.base import BaseCommand

from hr.services.osobe import pregled_identiteta


def _maska(vrednost, pun):
    return vrednost if pun or len(vrednost) < 5 else vrednost[:4] + "*" * (len(vrednost) - 4)


class Command(BaseCommand):
    help = "Pregled pre razdvajanja osobe (JMBG) od broja radnika. Samo cita izvor i tabelu zaposlenih."

    def add_arguments(self, parser):
        parser.add_argument("--db", dest="db", default="server_db", help="Naziv baze iz settings.DATABASES")
        parser.add_argument("--puni-jmbg", action="store_true", help="Ispisi ceo JMBG (podrazumevano je skracen)")

    def handle(self, *args, **options):
        pun = options["puni_jmbg"]
        p = pregled_identiteta(using=options["db"])
        w = self.stdout.write

        def red(r):
            lok = r["lokalni"]
            kod_nas = (f"kod nas: {'aktivan' if lok.is_active else 'neaktivan'} (id {lok.pk})" if lok
                       else "kod nas: nema")
            return (f"    pred. {r['preduzece']} · broj {r['broj']:>5} · {r['ime']:<32} · "
                    f"{'aktivan' if r['aktivan'] else 'neaktivan':<9} · prijem {r['prijem'] or '—'} · {kod_nas}")

        w(f"Izvor: {p['izvor_redova']} brojeva radnika, {p['izvor_osoba']} osoba sa JMBG-om.")
        w(f"Pogled dbo.hr_employee: {p['pogled_redova']} redova za {p['pogled_brojeva']} brojeva "
          f"({'duplirani redovi' if p['pogled_redova'] > p['pogled_brojeva'] else 'bez duplikata'}).")

        w(self.style.MIGRATE_HEADING(f"\nOsobe sa vise brojeva radnika: {len(p['vise_brojeva'])}"))
        for broj_jmbg, redovi in sorted(p["vise_brojeva"].items(), key=lambda x: x[1][0]["ime"]):
            w(f"  JMBG {_maska(broj_jmbg, pun)}")
            for r in redovi:
                w(red(r))

        w(self.style.MIGRATE_HEADING(f"\nIsti broj radnika u oba preduzeca: {len(p['sukobi_broja'])}"))
        for broj, redovi in sorted(p["sukobi_broja"].items()):
            for r in redovi:
                w(red(r) + f" · JMBG {_maska(r['jmbg'], pun) or '—'}")

        w(self.style.MIGRATE_HEADING(f"\nIzvor bez JMBG-a: {len(p['izvor_bez_jmbg'])}"))
        for r in p["izvor_bez_jmbg"]:
            w(red(r))

        w(self.style.MIGRATE_HEADING(f"\nKod nas: isti JMBG na vise zaposlenih: {len(p['lokalno_duplikati'])}"))
        for broj_jmbg, zaposleni in p["lokalno_duplikati"].items():
            w(f"  JMBG {_maska(broj_jmbg, pun)}: " + "; ".join(
                f"{e.employee_code} {e} ({'aktivan' if e.is_active else 'neaktivan'})" for e in zaposleni))

        w(self.style.MIGRATE_HEADING(f"\nKod nas bez JMBG-a: {len(p['lokalno_bez_jmbg'])}"))
        for e in p["lokalno_bez_jmbg"]:
            w(f"  {e.employee_code} {e} ({'aktivan' if e.is_active else 'neaktivan'})")

        w(self.style.MIGRATE_HEADING(f"\nKod nas, a nema u izvoru: {len(p['lokalno_nema_u_izvoru'])}"))
        for e in p["lokalno_nema_u_izvoru"]:
            w(f"  {e.employee_code} {e} ({'aktivan' if e.is_active else 'neaktivan'})")
