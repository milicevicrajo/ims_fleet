"""Faza 2 registra za Flotu: veza `org_node` pored postojecih polja.

Pravila (dokumentacija/plan-registra-sifara-posla.md, poglavlje 3):

- staro polje ostaje **merodavno**; `org_node` se iz njega izvodi i nista ga ne cita u obracunu;
- veza se popunjava u ponovljivim paketima; red bez para ostaje prazan i ide u izvestaj;
- uporedni izvestaj poredi centar i iznose starim putem (`OrganizationalUnit.center`) i
  kroz registar — po centru moraju biti identicni.

Razresavanje je bez pogadjanja: jedinica Flote ide preko `LegacyOrgLink` (po primarnom
kljucu), a ako veze jos nema — preko tacne sifre iz sifarnika poslova. Tekstualna sifra
(gorivo, lizing) ide samo preko tacne sifre. Prefiks sifre se nikad ne koristi. Naucne
sifre su od 25.09.2026. poslovi u bloku 3, pa se razresavaju isto kao i ostale.
"""

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from organizacija.models import ExternalOrgMapping, LegacyOrgLink
from organizacija.services import classification as klas
from organizacija.services.report import job_code_to_node, node_center_map

DEFAULT_COMPANY = 1
BATCH_SIZE = 500
NEPOVEZANO = "nepovezano"
VAN_STABLA = "van stabla"
TEHNICKA = klas.TEHNICKA
BEZ_CENTRA = "bez centra"


@dataclass(frozen=True)
class Veza:
    """Jedan model modula: odakle se izvodi cvor i kako se model zove u izvestaju."""

    kljuc: str
    naziv: str
    model: str
    polje: str
    tekst: bool = False
    iznos: str = ""
    app: str = "fleet"
    # Stari centar je polje na samom zapisu (Finansije: `LedgerEntry.center`), a ne jedinica Flote.
    centar_polje: str = ""
    firma_polje: str = ""
    aktivni_polje: str = ""
    # Poredi se samo poslednji objavljeni snimak (Potrazivanja: pozicije su snimci stanja).
    poslednji_snimak: bool = False

    def model_class(self):
        from django.apps import apps

        return apps.get_model(self.app, self.model)

    @property
    def oznaka_modela(self):
        return f"{self.app}.{self.model}"

    @property
    def izvorna_kolona(self):
        return self.polje if self.tekst else f"{self.polje}_id"


VEZE = (
    Veza("dodele", "Dodele vozila šiframa posla", "JobCode", "organizational_unit"),
    Veza("putni_nalozi", "Putni nalozi", "PutniNalog", "job_code"),
    Veza("nalozi_vozila", "Nalozi za korišćenje vozila", "VehicleTravelOrder", "job_code"),
    Veza("zahtevi_nabavke", "Zahtevi za nabavku (GZN)", "ProcurementRequest", "job_code"),
    Veza("gorivo", "Gorivo (šifra sa kartice)", "FuelConsumption", "job_code", tekst=True, iznos="cost_bruto"),
    Veza("lizing", "Lizing", "Lease", "job_code", tekst=True, iznos="current_payment_amount"),
)
# Nabavka (faza 2, drugi modul po planu): ista vrsta veze kao Flota — FK na `OrganizationalUnit`.
# Broj predmeta (`ProcurementCase.get_center_code`) i dalje se pravi iz starog polja.
NABAVKA = (
    Veza("predmeti", "Predmeti nabavke", "ProcurementCase", "job_code", app="nabavka"),
    Veza("fakture", "Fakture — glavna šifra posla", "ProcurementInvoice", "job_code", iznos="amount", app="nabavka"),
    Veza("veze_faktura", "Veze faktura sa šiframa posla", "ProcurementInvoiceJobCodeLink", "job_code", app="nabavka"),
)
# Finansije (faza 2, treci modul): tekstualna sifra posla na knjizenju; stari centar je
# `LedgerEntry.center` (prepisan iz `posao.blok`), po kome Finansije grupisu i ogranicavaju pristup.
FINANSIJE = (
    Veza("knjizenja", "Knjiženja (duguje)", "LedgerEntry", "job_code", tekst=True, iznos="debit", app="finansije",
         centar_polje="center", firma_polje="company", aktivni_polje="active"),
)
# Potrazivanja (faza 2, cetvrti modul): tekstualna sifra i `center_code` prepisan iz `posao.blok`,
# po kojima se ogranicava pristup. Pozicije su objavljeni snimci stanja — poredi se poslednji.
POTRAZIVANJA = (
    Veza("stavke", "Knjiženja potraživanja (duguje)", "ReceivablePosting", "job_code", tekst=True, iznos="debit",
         app="potrazivanja", centar_polje="center_code", firma_polje="company", aktivni_polje="active"),
    Veza("pozicije", "Otvorene pozicije — poslednji snimak (saldo)", "ReceivablePosition", "job_code", tekst=True,
         iznos="balance", app="potrazivanja", centar_polje="center_code", poslednji_snimak=True),
)
MODULI = {"flota": VEZE, "nabavka": NABAVKA, "finansije": FINANSIJE, "potrazivanja": POTRAZIVANJA}
NAZIVI_MODULA = {"flota": "Flota", "nabavka": "Nabavka", "finansije": "Finansije", "potrazivanja": "Potraživanja"}
SVE_VEZE = VEZE + NABAVKA + FINANSIJE + POTRAZIVANJA
VEZE_PO_MODELU = {veza.oznaka_modela: veza for veza in SVE_VEZE}


def veza_za(model_ili_zapis):
    meta = model_ili_zapis._meta
    return VEZE_PO_MODELU.get(f"{meta.app_label}.{meta.object_name}")


def veze_modula(modul):
    return SVE_VEZE if modul == "sve" else MODULI[modul]


class Razresavac:
    """Staro polje → cvor registra. Sve se ucitava jednom, pa je paket bez upita po redu."""

    def __init__(self, company=DEFAULT_COMPANY):
        from core.models import OrganizationalUnit

        self.company = company
        self.po_sifri = job_code_to_node(company)
        self.po_jedinici = dict(
            LegacyOrgLink.objects.filter(legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT).values_list(
                "legacy_id", "node_id"
            )
        )
        from finansije.models import FinanceJob

        self.jedinice = {
            unit_id: (code, (center or "").strip())
            for unit_id, code, center in OrganizationalUnit.objects.values_list("pk", "code", "center")
        }
        # Sifre koje postoje u sifarniku, ali ih registar ne vodi (lista za razresenje); tehnicke
        # sifre nisu ovde — one su odlukom bez centra i vode se posebno.
        self.van_stabla = {
            klas.normalize_code(c) for c in FinanceJob.objects.filter(company=company).values_list("code", flat=True)
        } - set(self.po_sifri) - set(klas.TEHNICKE_SIFRE)
        # Stari put za tekstualnu sifru: jedinica Flote sa istom sifrom i njen centar.
        self.centar_po_sifri = {
            klas.normalize_code(code): center for code, center in self.jedinice.values()
        }

    def za_jedinicu(self, unit_id):
        if unit_id is None:
            return None
        node_id = self.po_jedinici.get(unit_id)
        if node_id is not None:
            return node_id
        return self.za_sifru(self.jedinice.get(unit_id, ("", ""))[0])

    def za_sifru(self, sifra):
        sifra = klas.normalize_code(sifra)
        return self.po_sifri.get(sifra) if sifra else None

    def cvor(self, veza, vrednost):
        return self.za_sifru(vrednost) if veza.tekst else self.za_jedinicu(vrednost)

    def stari_centar(self, veza, vrednost):
        """Centar kako ga Flota danas vidi: `OrganizationalUnit.center`."""
        if veza.tekst:
            return self.centar_po_sifri.get(klas.normalize_code(vrednost)) or None
        if vrednost is None:
            return None
        return self.jedinice.get(vrednost, ("", ""))[1] or None

    def sirova(self, veza, vrednost):
        if veza.tekst:
            return klas.normalize_code(vrednost)
        return (self.jedinice.get(vrednost, ("", ""))[0] or "").strip()


def cvor_za_zapis(instance, company=DEFAULT_COMPANY):
    """Cvor za jedan zapis — za signal pri cuvanju. Dva mala upita, bez ucitavanja svega."""
    veza = veza_za(instance)
    if veza is None:
        return None
    vrednost = getattr(instance, veza.izvorna_kolona)
    if veza.tekst:
        return _cvor_sifre(vrednost, company)
    if vrednost is None:
        return None
    node_id = (
        LegacyOrgLink.objects.filter(legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT, legacy_id=vrednost)
        .values_list("node_id", flat=True)
        .first()
    )
    if node_id is not None:
        return node_id
    from core.models import OrganizationalUnit

    code = OrganizationalUnit.objects.filter(pk=vrednost).values_list("code", flat=True).first()
    return _cvor_sifre(code, company)


def _cvor_sifre(sifra, company):
    sifra = klas.normalize_code(sifra)
    return _mapiranje(sifra, company) if sifra else None


def _mapiranje(sifra, company):
    return (
        ExternalOrgMapping.objects.filter(
            source=ExternalOrgMapping.SOURCE_FINANCE_JOB,
            company=company,
            source_key=sifra,
            valid_to__isnull=True,
        )
        .values_list("node_id", flat=True)
        .first()
    )


# --------------------------------------------------------------------------- popunjavanje


def mapa_jedinica_flote(company=DEFAULT_COMPANY):
    """Za citanje u Floti: `OrganizationalUnit.pk` → sifra, naziv, aktivnost, jedinica i centar iz
    registra, i oznaka centra → naziv. Jedinica bez cvora u registru nije u mapi."""
    from organizacija.models import OrgNode, OrgNodeVersion

    razresavac = Razresavac(company)
    verzije = {
        v.node_id: v
        for v in OrgNodeVersion.objects.filter(valid_to__isnull=True, node__company=company).select_related("node")
    }
    centri = {v.full_code: v.name for v in verzije.values() if v.node.level == OrgNode.LEVEL_CENTER}
    mapa = {}
    for pk in razresavac.jedinice:
        posao = verzije.get(razresavac.za_jedinicu(pk))
        if posao is None or posao.node.level != OrgNode.LEVEL_JOB:
            continue
        jedinica = verzije.get(posao.parent_id)
        centar = verzije.get(jedinica.parent_id) if jedinica else None
        mapa[pk] = {
            "sifra": posao.full_code,
            "naziv": posao.name,
            "aktivan": posao.is_active,
            "jedinica": jedinica.full_code if jedinica else "",
            "naziv_jedinice": jedinica.name if jedinica else "",
            "centar": centar.full_code if centar else "",
            "naziv_centra": centar.name if centar else "",
        }
    return mapa, centri


def povezi(company=DEFAULT_COMPANY, proba=False, batch_size=BATCH_SIZE, modeli=None, modul="flota"):
    """Popunjava `org_node` na modelima modula (`flota`, `nabavka` ili `sve`). Ponovljivo: menja
    samo ono sto odstupa. Vraca po jedan zbir po modelu. `proba=True` ne upisuje nista.
    """
    razresavac = Razresavac(company)
    return [
        _povezi_model(veza, razresavac, proba, batch_size)
        for veza in veze_modula(modul)
        if modeli is None or veza.kljuc in modeli
    ]


def _povezi_model(veza, razresavac, proba, batch_size):
    model = veza.model_class()
    redovi_modela = model.objects.all()
    if veza.firma_polje:
        redovi_modela = redovi_modela.filter(**{veza.firma_polje: razresavac.company})
    zbir = {
        "kljuc": veza.kljuc,
        "naziv": veza.naziv,
        "ukupno": 0,
        "vec_povezano": 0,
        "postavljeno": 0,
        "promenjeno": 0,
        "ocisceno": 0,
        "bez_sifre": 0,
        "nerazreseno": 0,
        "nerazresene_sifre": defaultdict(int),
    }
    # Redovi se citaju unapred (tri kolone, par desetina hiljada redova): upis paketa ne sme
    # da se preplete sa otvorenim kursorom citanja na SQL Serveru.
    redovi = list(redovi_modela.order_by("pk").values_list("pk", veza.izvorna_kolona, "org_node_id"))
    for pocetak in range(0, len(redovi), batch_size):
        _obradi_paket(model, veza, razresavac, redovi[pocetak:pocetak + batch_size], zbir, proba)

    zbir["nerazresene_sifre"] = sorted(
        zbir["nerazresene_sifre"].items(), key=lambda item: (-item[1], item[0])
    )
    return zbir


def _obradi_paket(model, veza, razresavac, paket, zbir, proba):
    izmene = defaultdict(list)
    for pk, vrednost, trenutni in paket:
        zbir["ukupno"] += 1
        cilj = razresavac.cvor(veza, vrednost)
        prazno = vrednost is None or (veza.tekst and not klas.normalize_code(vrednost))
        if prazno:
            zbir["bez_sifre"] += 1
        elif cilj is None:
            zbir["nerazreseno"] += 1
            zbir["nerazresene_sifre"][razresavac.sirova(veza, vrednost) or f"#{vrednost}"] += 1
        if cilj == trenutni:
            if cilj is not None:
                zbir["vec_povezano"] += 1
            continue
        if trenutni is None:
            zbir["postavljeno"] += 1
        elif cilj is None:
            zbir["ocisceno"] += 1
        else:
            zbir["promenjeno"] += 1
        izmene[cilj].append(pk)

    if proba or not izmene:
        return
    # `update` namerno: ne pokrece save(), pa ne dira nijedno drugo polje ni datum izmene.
    with transaction.atomic():
        for cilj, pks in izmene.items():
            model.objects.filter(pk__in=pks).update(org_node_id=cilj)


# --------------------------------------------------------------------------- uporedni izvestaj


def godine_goriva():
    """Godine za koje postoji gorivo, najnovija prva — izbor perioda u izvestaju."""
    from fleet.models import FuelConsumption

    return sorted({d.year for d in FuelConsumption.objects.dates("date", "year")}, reverse=True)


def uporedni_izvestaj(company=DEFAULT_COMPANY, godina=None, primera=15, modul="flota"):
    """Stari put naspram registra, po centru. Nista ne upisuje.

    Za svaki model: broj (i iznos, gde postoji) po centru starim putem i kroz upisanu vezu
    `org_node`. Gorivo se poredi i putem kojim ga Flota stvarno rasporedjuje — preko dodele
    vozila vazece na dan tocenja. Izvestaj prolazi kada se sve kolone poklapaju do dinara.
    """
    razresavac = Razresavac(company)
    centri = node_center_map(company)
    delovi = [_uporedi_model(veza, razresavac, centri, godina, primera) for veza in veze_modula(modul)]
    if modul == "flota":
        delovi.append(_uporedi_gorivo_po_vozilu(razresavac, centri, _dodele_po_vozilu(), godina, primera))
    return {
        "modul": modul,
        "godina": godina,
        "delovi": delovi,
        "prolazi": all(deo["prolazi"] for deo in delovi),
        "napravljen": timezone.now(),
    }


def _uporedi_model(veza, razresavac, centri, godina, primera):
    model = veza.model_class()
    redovi = model.objects.all()
    if veza.firma_polje:
        redovi = redovi.filter(**{veza.firma_polje: razresavac.company})
    if veza.aktivni_polje:
        redovi = redovi.filter(**{veza.aktivni_polje: True})
    if veza.poslednji_snimak:
        from potrazivanja.models import BalanceSnapshot

        snimak = (BalanceSnapshot.objects.filter(status=BalanceSnapshot.Status.PUBLISHED)
                  .order_by("-published_at", "-pk").values_list("pk", flat=True).first())
        redovi = redovi.filter(snapshot_id=snimak)
    datum = _polje_datuma(veza)
    if godina and datum:
        redovi = redovi.filter(**{f"{datum}__year": godina})
    kolone = ["pk", veza.izvorna_kolona, "org_node_id", veza.iznos or "pk", veza.centar_polje or "pk"]

    def stari(red):
        if veza.centar_polje:
            # Prazan centar u izvoru kod potvrdjenih sifara (110002, 430001) je potvrdjena dopuna.
            return ((red[4] or "").strip()
                    or klas.POTVRDJENI_CENTRI_SIFARA.get(klas.normalize_code(red[1]))
                    or None)
        return razresavac.stari_centar(veza, red[1])

    tok = (
        (red[0], stari(red), red[2], red[3] if veza.iznos else None, razresavac.sirova(veza, red[1]))
        for red in redovi.values_list(*kolone).iterator(chunk_size=5000)
    )
    osnova = f"{veza.model}.{veza.polje}" + (f", centar iz {veza.model}.{veza.centar_polje}" if veza.centar_polje else "")
    return _uporedi(veza.kljuc, veza.naziv, tok, centri, bool(veza.iznos), primera,
                    osnova=osnova, stari_put=bool(veza.centar_polje) or not veza.tekst,
                    van_stabla=razresavac.van_stabla)


def _polje_datuma(veza):
    return {
        "PutniNalog": "order_date",
        "VehicleTravelOrder": "created_at",
        "ProcurementRequest": "created_at",
        "FuelConsumption": "date",
        "JobCode": "assigned_date",
        "Lease": "start_date",
        "ProcurementCase": "created_at",
        "ProcurementInvoice": "invoice_date",
        "ProcurementInvoiceJobCodeLink": "invoice__invoice_date",
        "LedgerEntry": "booking_date",
        "ReceivablePosting": "booking_date",
    }.get(veza.model)


def _dodele_po_vozilu():
    from fleet.models import JobCode

    dodele = defaultdict(list)
    for vozilo, datum, pk, jedinica, cvor in JobCode.objects.order_by("assigned_date", "pk").values_list(
        "vehicle_id", "assigned_date", "pk", "organizational_unit_id", "org_node_id"
    ):
        dodele[vozilo].append((datum, jedinica, cvor))
    return {vozilo: ([d[0] for d in niz], niz) for vozilo, niz in dodele.items()}


def _dodela_na_dan(dodele, vozilo, dan):
    if vozilo not in dodele:
        return None
    datumi, niz = dodele[vozilo]
    mesto = bisect_right(datumi, dan)
    return niz[mesto - 1] if mesto else None


def _uporedi_gorivo_po_vozilu(razresavac, centri, dodele, godina, primera):
    from fleet.models import FuelConsumption

    veza_dodele = VEZE_PO_MODELU["fleet.JobCode"]
    redovi = FuelConsumption.objects.all()
    if godina:
        redovi = redovi.filter(date__year=godina)

    def tok():
        for pk, vozilo, kada, iznos in redovi.values_list("pk", "vehicle_id", "date", "cost_bruto").iterator(
            chunk_size=2000
        ):
            dan = timezone.localtime(kada).date() if timezone.is_aware(kada) else kada.date()
            dodela = _dodela_na_dan(dodele, vozilo, dan)
            if dodela is None:
                yield pk, None, None, iznos, ""
                continue
            _, jedinica, cvor = dodela
            yield (pk, razresavac.stari_centar(veza_dodele, jedinica), cvor, iznos,
                   razresavac.sirova(veza_dodele, jedinica))

    return _uporedi(
        "gorivo_po_vozilu",
        "Gorivo po dodeli vozila (put izveštaja Flote)",
        tok(),
        centri,
        True,
        primera,
        osnova="dodela vozila važeća na dan točenja",
        stari_put=True,
        van_stabla=razresavac.van_stabla,
    )


def _uporedi(kljuc, naziv, tok, centri, sa_iznosom, primera, osnova, stari_put, van_stabla=frozenset()):
    """Zbir po centru za oba puta.

    `stari_put=False` znaci da Flota danas ne rasporedjuje po ovom polju (tekstualna sifra
    goriva i lizinga): tada zapis koji centar dobija **samo** iz registra nije razlika nego
    dopuna, i ne obara izvestaj. Kod polja po kojima Flota rasporedjuje i dopuna je razlika.

    Zapis bez cvora cija sifra postoji u sifarniku, ali je na listi za razresenje, vodi se
    kao `van stabla`, odvojeno od nepovezanog. I dalje je razlika: po prelasku na registar
    takav zapis ne bi imao centar, pa mora biti resen pre koraka 4.
    """
    staro = defaultdict(lambda: [0, Decimal("0")])
    novo = defaultdict(lambda: [0, Decimal("0")])
    razlike = []
    sifre_van_stabla = van_stabla
    ukupno = razlika_broj = dopuna = van_stabla = tehnickih = 0
    for pk, stari, cvor, iznos, sirova in tok:
        ukupno += 1
        iznos = iznos or Decimal("0")
        stari = stari or BEZ_CENTRA
        if sirova in klas.TEHNICKE_SIFRE:
            # Odluka 25.09.2026.: tehnicka sifra nema centar ni starim putem ni u registru.
            stari = novi = TEHNICKA
            tehnickih += 1
        elif cvor is not None:
            novi = centri.get(cvor, BEZ_CENTRA)
        elif stari == BEZ_CENTRA:
            novi = BEZ_CENTRA
        else:
            novi = VAN_STABLA if sirova in sifre_van_stabla else NEPOVEZANO
        if novi == VAN_STABLA:
            van_stabla += 1
        staro[stari][0] += 1
        staro[stari][1] += iznos
        novo[novi][0] += 1
        novo[novi][1] += iznos
        if stari != novi:
            if stari == BEZ_CENTRA and novi not in (NEPOVEZANO, BEZ_CENTRA):
                dopuna += 1
            if stari == BEZ_CENTRA and not stari_put:
                continue
            razlika_broj += 1
            if len(razlike) < primera:
                razlike.append({"pk": pk, "sifra": sirova, "staro": stari, "novo": novi, "iznos": iznos})

    redovi = []
    for centar in sorted(set(staro) | set(novo), key=_redosled_centra):
        s, n = staro.get(centar, [0, Decimal("0")]), novo.get(centar, [0, Decimal("0")])
        redovi.append({
            "centar": centar,
            "staro_broj": s[0],
            "novo_broj": n[0],
            "staro_iznos": s[1],
            "novo_iznos": n[1],
            "razlika_broj": n[0] - s[0],
            "razlika_iznos": n[1] - s[1],
            "poklapa": s[0] == n[0] and s[1] == n[1],
        })
    return {
        "kljuc": kljuc,
        "naziv": naziv,
        "osnova": osnova,
        "sa_iznosom": sa_iznosom,
        "ukupno": ukupno,
        "redovi": redovi,
        "stari_put": stari_put,
        "razlika_zapisa": razlika_broj,
        "dopuna": dopuna,
        "van_stabla": van_stabla,
        "tehnickih": tehnickih,
        "primeri": razlike,
        "prolazi": razlika_broj == 0,
    }


def _redosled_centra(centar):
    posebni = {BEZ_CENTRA: 4, TEHNICKA: 3, NEPOVEZANO: 2, VAN_STABLA: 1}
    return (posebni.get(centar, 0), len(centar), centar)
