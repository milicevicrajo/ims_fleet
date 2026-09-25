from django.core.management.base import BaseCommand, CommandError

from organizacija.services import flota


class Command(BaseCommand):
    help = (
        "Faza 2 registra: popunjava vezu org_node na modelima Flote iz postojecih polja, "
        "u ponovljivim paketima. Staro polje ostaje merodavno i nista se u Floti ne cita iz veze."
    )

    def add_arguments(self, parser):
        parser.add_argument("--firma", type=int, default=flota.DEFAULT_COMPANY)
        parser.add_argument("--paket", type=int, default=flota.BATCH_SIZE, help="Broj redova po paketu.")
        parser.add_argument(
            "--model",
            action="append",
            choices=[veza.kljuc for veza in flota.SVE_VEZE],
            help="Samo navedeni model; moze vise puta. Bez ovoga — svi.",
        )
        parser.add_argument("--proba", action="store_true", help="Samo prikazi sta bi se promenilo, bez upisa.")
        parser.add_argument(
            "--izvestaj",
            action="store_true",
            help="Posle popunjavanja prikazi uporedni izvestaj (stari put naspram registra).",
        )
        parser.add_argument("--godina", type=int, help="Uporedni izvestaj samo za jednu godinu.")
        parser.add_argument("--modul", choices=["flota", "nabavka", "finansije", "potrazivanja", "sve"], default="flota",
                            help="Koji modul se povezuje (podrazumevano flota).")

    def handle(self, *args, **options):
        if options["paket"] < 1:
            raise CommandError("--paket mora biti bar 1.")
        zbirovi = flota.povezi(
            company=options["firma"],
            proba=options["proba"],
            batch_size=options["paket"],
            modeli=options["model"],
            modul=options["modul"],
        )
        for zbir in zbirovi:
            self._zbir(zbir)
        if options["proba"]:
            self.stdout.write(self.style.WARNING("PROBA — nista nije upisano."))
        else:
            izmena = sum(z["postavljeno"] + z["promenjeno"] + z["ocisceno"] for z in zbirovi)
            self.stdout.write(self.style.SUCCESS(f"Izmenjenih veza: {izmena}"))

        if options["izvestaj"]:
            moduli = list(flota.MODULI) if options["modul"] == "sve" else [options["modul"]]
            for modul in moduli:
                self._izvestaj(flota.uporedni_izvestaj(options["firma"], options["godina"], modul=modul))

    def _zbir(self, z):
        self.stdout.write(f"{z['naziv']} ({z['kljuc']})")
        self.stdout.write(
            f"  ukupno {z['ukupno']}; vec povezano {z['vec_povezano']}; "
            f"postavljeno {z['postavljeno']}; promenjeno {z['promenjeno']}; ocisceno {z['ocisceno']}"
        )
        linija = f"  bez sifre {z['bez_sifre']}; bez para u registru {z['nerazreseno']}"
        self.stdout.write(self.style.WARNING(linija) if z["nerazreseno"] else linija)
        for sifra, broj in z["nerazresene_sifre"][:10]:
            self.stdout.write(f"    {sifra:<12} {broj}")
        if len(z["nerazresene_sifre"]) > 10:
            self.stdout.write(f"    ... jos {len(z['nerazresene_sifre']) - 10} sifara")

    def _izvestaj(self, izvestaj):
        self.stdout.write("")
        naslov = "Uporedni izvestaj" + (f" za {izvestaj['godina']}." if izvestaj["godina"] else "")
        self.stdout.write(naslov)
        for deo in izvestaj["delovi"]:
            oznaka = self.style.SUCCESS("PROLAZI") if deo["prolazi"] else self.style.ERROR("NE PROLAZI")
            self.stdout.write(
                f"  {oznaka}  {deo['naziv']}: {deo['ukupno']} zapisa, razlika {deo['razlika_zapisa']}, "
                f"dopuna iz registra {deo['dopuna']}"
            )
            for red in deo["redovi"]:
                if red["poklapa"]:
                    continue
                self.stdout.write(
                    f"      {red['centar']:<12} staro {red['staro_broj']:>6} {red['staro_iznos']:>16}"
                    f"   registar {red['novo_broj']:>6} {red['novo_iznos']:>16}"
                )
            for primer in deo["primeri"][:5]:
                self.stdout.write(
                    f"      #{primer['pk']} {primer['sifra'] or '-'}: {primer['staro']} → {primer['novo']}"
                )
        ukupno = self.style.SUCCESS("PROLAZI") if izvestaj["prolazi"] else self.style.ERROR("NE PROLAZI")
        self.stdout.write(f"Ukupno: {ukupno}")
