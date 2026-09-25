from collections import Counter

from django.core.management.base import BaseCommand

from organizacija.services import prava


class Command(BaseCommand):
    help = (
        "Plan prelaska na registar, 3.2: prevodi stara prava u nacrt dodela sa obuhvatom i poredi, "
        "za svakog korisnika, sta danas vidi u Finansijama, Potrazivanjima i putnim nalozima, a sta bi "
        "video po nacrtu. Nacrt ne odlucuje ni o cemu; stara prava se ne diraju."
    )

    def add_arguments(self, parser):
        parser.add_argument("--bez-prevoda", action="store_true", help="Ne prevodi ponovo, samo poredi postojeci nacrt.")
        parser.add_argument("--svi", action="store_true", help="Prikazi i korisnike bez razlike.")

    def handle(self, *args, bez_prevoda=False, svi=False, **options):
        if not bez_prevoda:
            z = prava.prevedi()
            self.stdout.write(
                f"Prevod: korisnika sa ulogom {z['korisnika']}, dodela u nacrtu {z['dodela']}, bez uloge {z['bez_uloge']}, "
                f"vec odobrenih (ne dira se) {z['odobreni']}")
            if z["nepoznate_oznake"]:
                self.stdout.write(f"  oznake centra bez cvora: {dict(z['nepoznate_oznake'])}")
            if z["oj_van_registra"]:
                self.stdout.write(f"  OJ van registra: {dict(z['oj_van_registra'])}")
        redovi = prava.senka()
        po_modulu = Counter()
        for red in redovi:
            for modul, m in red["moduli"].items():
                if m["manje"]:
                    po_modulu[(modul, "manje")] += 1
                if m["vise"]:
                    po_modulu[(modul, "vise")] += 1
        self.stdout.write(f"Senka: korisnika {len(redovi)}, sa razlikom {sum(1 for r in redovi if r['razlika'])}")
        for (modul, smer), broj in sorted(po_modulu.items()):
            self.stdout.write(f"  {modul}: {broj} korisnika bi video {'MANJE' if smer == 'manje' else 'VISE'}")
        for red in redovi:
            if not (red["razlika"] or svi):
                continue
            delovi = []
            for modul, m in red["moduli"].items():
                if m["manje"] or m["vise"] or svi:
                    delovi.append(f"{modul} {m['staro']}→{m['novo']}"
                                  + (f" (-{len(m['manje'])} sifara: {', '.join(m['manje'][:5])})" if m["manje"] else "")
                                  + (f" (+{len(m['vise'])}: {', '.join(m['vise'][:5])})" if m["vise"] else ""))
            self.stdout.write(f"  {red['korisnik'].username:<24} " + "; ".join(delovi))
