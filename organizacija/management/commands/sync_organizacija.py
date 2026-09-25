from django.core.management.base import BaseCommand, CommandError

from organizacija.services import sync


class Command(BaseCommand):
    help = (
        "Nova sinhronizacija organizacije (isto sto i zakazani posao u 01:40): osvezava registar, "
        "povezuje Flotu i poredi sa starom organizacijom. Staru sinhronizaciju ne dira."
    )

    def add_arguments(self, parser):
        parser.add_argument("--firma", type=int, default=1)

    def handle(self, *args, **options):
        try:
            rezultat = sync.sinhronizuj(options["firma"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(sync.poruka(rezultat))
        kontrola = rezultat["kontrola"]
        for red in kontrola["razlika_centra"][:20]:
            self.stdout.write(f"  razlika centra  {red['sifra']:<12} staro {red['staro'] or '-':<6} registar {red['novo'] or '-'}")
        if kontrola["van_stabla"]:
            self.stdout.write("  u sifarniku, van stabla: " + ", ".join(kontrola["van_stabla"][:30]))
        if kontrola["van_sifarnika"]:
            self.stdout.write("  nema u sifarniku poslova: " + ", ".join(kontrola["van_sifarnika"][:30]))
        if kontrola["samo_u_registru"]:
            self.stdout.write(f"  samo u registru (nema OJ u staroj): {len(kontrola['samo_u_registru'])}")
