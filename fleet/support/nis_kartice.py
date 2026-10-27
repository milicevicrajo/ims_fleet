"""Vrsta NIS kartice iz specifikacije uz fakturu (od 27.10.2026.).

NIS za svaku polovinu meseca izdaje dve fakture — „Putničko“ i „Teretno“ — i deli ih po **kartici**, ne po
kategoriji vozila u Floti (npr. BG826-VJ je u Floti putničko, a njegova kartica je na teretnoj fakturi).
Uz svaku fakturu na SEF-u je PDF „specifikacija_uz_fakturu“ sa zaglavljem `<broj fakture> Teretno` i redom
`Ukupno za karticu : <kartica> <količina> <vrednost>` za svaku karticu. Iz nje se pamti koja je kartica na
kojoj fakturi (`NisKarticaFakture`), pa se transakcije dele tačno kao na fakturama.

Septembar i 1–15. oktobar 2026: svih šest faktura se slaže sa transakcijama u dinar; podela po kategoriji
vozila je odstupala do 21.430,20 din po fakturi.
"""
import io
import logging
import re
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import NisKarticaFakture, Vehicle

logger = logging.getLogger(__name__)

NIS_PIB = "104052135"
PUTNICKA, TERETNA = NisKarticaFakture.TIP_PUTNICKA, NisKarticaFakture.TIP_TERETNA

_ZAGLAVLJE = re.compile(r"(\d{8,})\s+(Teretno|Putni\w*)")
_KARTICA = re.compile(r"Ukupno za karticu\s*:\s*(\d+)\s+[\d.,]+\s+([\d,]+\.\d{2})")


def kartica(vrednost):
    """Broj kartice kao u specifikaciji: NIS uvoz čuva „7824723064558030.0“."""
    tekst = str(vrednost or "").strip()
    if re.fullmatch(r"\d+\.0+", tekst):
        return tekst.split(".", 1)[0]
    if re.fullmatch(r"[\d.]+[eE]\+?\d+", tekst):
        return str(int(Decimal(tekst)))
    return tekst


def iz_teksta(tekst):
    """(broj fakture, vrsta, {kartica: iznos}) iz teksta specifikacije; None ako tekst nije specifikacija."""
    zaglavlje = _ZAGLAVLJE.search(tekst or "")
    if not zaglavlje:
        return None
    kartice = {}
    for broj, iznos in _KARTICA.findall(tekst):
        kartice[broj] = kartice.get(broj, Decimal("0.00")) + Decimal(iznos.replace(",", ""))
    tip = TERETNA if zaglavlje.group(2) == "Teretno" else PUTNICKA
    return zaglavlje.group(1), tip, kartice


def tekst_pdf(sadrzaj):
    from pypdf import PdfReader

    return "\n".join(strana.extract_text() or "" for strana in PdfReader(io.BytesIO(sadrzaj)).pages)


def _je_specifikacija(naziv):
    return "specifikacija" in (naziv or "").lower()


def _specifikacija(faktura):
    prilog = next((p for p in faktura.prilozi.all() if _je_specifikacija(p.naziv)), None)
    if prilog is None:
        return None
    sadrzaj = None
    if prilog.fajl:
        try:
            with prilog.fajl.open("rb") as fajl:
                sadrzaj = fajl.read()
        except OSError:
            sadrzaj = None
    if sadrzaj is None:
        # Fajl priloga je samo na serveru (media) — na drugom računaru specifikacija se čita iz UBL-a sa SEF-a
        # (samo čitanje, ništa se ne upisuje u priloge).
        from finansije.services.sef import Klijent, prilozi_iz_ubl

        sadrzaj = next((p["sadrzaj"] for p in prilozi_iz_ubl(Klijent().ubl(faktura.smer, faktura.sef_id))
                        if _je_specifikacija(p["naziv"])), None)
    return iz_teksta(tekst_pdf(sadrzaj)) if sadrzaj else None


def ucitaj_specifikacije(fakture):
    """Upisuje kartice NIS faktura koje još nisu učitane; vraća broj učitanih faktura.

    Faktura bez priloga ili sa nečitljivim prilogom se preskače i pokušava ponovo sledeći put."""
    ucitane = set(NisKarticaFakture.objects.filter(faktura__in=[f.broj for f in fakture])
                  .values_list("faktura", flat=True).distinct())
    broj = 0
    for faktura in fakture:
        if faktura.broj in ucitane or faktura.partner_pib != NIS_PIB or (faktura.vrsta and faktura.vrsta != "Invoice"):
            continue
        try:
            procitano = _specifikacija(faktura)
        except ImportError:
            logger.warning("NIS specifikacije: nije instaliran pypdf")
            return broj
        except Exception:  # fajl nedostaje ili PDF nije citljiv — ostaje podela po kategoriji vozila
            logger.exception("NIS specifikacija fakture %s nije procitana", faktura.broj)
            continue
        if not procitano or procitano[0] != faktura.broj or not procitano[2]:
            logger.warning("NIS specifikacija fakture %s nema ocekivano zaglavlje ili kartice", faktura.broj)
            continue
        _, tip, kartice = procitano
        with transaction.atomic():
            NisKarticaFakture.objects.bulk_create([
                NisKarticaFakture(faktura=faktura.broj, datum_prometa=faktura.datum_prometa, tip=tip, kartica=k, iznos=i)
                for k, i in kartice.items()])
        broj += 1
    return broj


def polovina(dan):
    """(od, do) polovine meseca u kojoj je dan: 1–15 ili 16–kraj."""
    from calendar import monthrange

    if dan.day <= 15:
        return dan.replace(day=1), dan.replace(day=15)
    return dan.replace(day=16), dan.replace(day=monthrange(dan.year, dan.month)[1])


class VrstaKartice:
    """Vrsta NIS transakcije (putnička / teretna) po fakturi njene polovine meseca.

    Redom: kartica na NIS fakturi te polovine; kartica na poslednjoj poznatoj fakturi (polovina još nije
    fakturisana); kategorija vozila u Floti (kartica se nikad nije pojavila na specifikaciji)."""

    def __init__(self):
        self._polovine = {}
        self._poslednja = None

    def _kartice_polovine(self, od, do):
        if (od, do) not in self._polovine:
            from finansije.sef_models import SefFaktura

            ucitaj_specifikacije(list(SefFaktura.objects.filter(smer="ulazna", partner_pib=NIS_PIB, vrsta="Invoice",
                                                                datum_prometa__range=(od, do)).prefetch_related("prilozi")))
            self._polovine[(od, do)] = dict(NisKarticaFakture.objects.filter(datum_prometa__range=(od, do))
                                            .values_list("kartica", "tip"))
        return self._polovine[(od, do)]

    def _poslednje(self):
        if self._poslednja is None:
            self._poslednja = {}
            for k, tip in NisKarticaFakture.objects.order_by("datum_prometa", "pk").values_list("kartica", "tip"):
                self._poslednja[k] = tip
        return self._poslednja

    def izvor(self, t):
        """(vrsta, izvor): izvor je „faktura“, „ranija faktura“ ili „vozilo“."""
        dan = timezone.localtime(t.datum_transakcije).date()
        broj = kartica(t.broj_kartice)
        tip = self._kartice_polovine(*polovina(dan)).get(broj)
        if tip:
            return tip, "faktura"
        tip = self._poslednje().get(broj)
        if tip:
            return tip, "ranija faktura"
        vozilo = t.vehicle if t.vehicle_id else None
        return (TERETNA if vozilo and vozilo.category == Vehicle.Category.CARGO else PUTNICKA), "vozilo"

    def tip(self, t):
        return self.izvor(t)[0]
