"""Flota cita sifre posla i centre iz registra organizacije (faza 2, korak 4).

Sta se cita iz registra: **spiskovi i nazivi** — koje sifre se nude za izbor (samo aktivne sifre
iz registra, uz vec upisanu vrednost), kako se zovu i kom centru pripadaju, i nazivi centara
po Pravilniku o organizaciji. Staro polje (`OrganizationalUnit` / tekstualni `job_code`) se i
dalje upisuje i ostaje kljuc za filtere, zbirove, pristup i brojeve putnih naloga: centar u
registru i `OrganizationalUnit.center` se poklapaju za sve zapise Flote (uporedni izvestaj,
`/organizacija/flota/`), pa se zbirovi ne menjaju.

Prekidac: `FLOTA_REGISTAR_ORGANIZACIJE` u postavkama (podrazumevano ukljuceno). Iskljucen
vraca stare spiskove i nazive bez ikakve druge promene. Isto vazi dok je registar prazan (pre
prvog uvoza): tada se nista ne ogranicava, da izbor sifre ne ostane prazan.
"""

from django.conf import settings


def ukljuceno():
    return getattr(settings, "FLOTA_REGISTAR_ORGANIZACIJE", True)


class Registar:
    """Snimak registra za jedan zahtev: jedinica Flote → sifra, naziv i centar iz registra."""

    def __init__(self):
        self.jedinice, self.centri = {}, {}
        if ukljuceno():
            from organizacija.services.flota import mapa_jedinica_flote

            self.jedinice, self.centri = mapa_jedinica_flote()

    @property
    def dostupan(self):
        """Ukljuceno i registar ima podatke za Flotu."""
        return bool(self.jedinice)

    def aktivne(self):
        return {pk for pk, stavka in self.jedinice.items() if stavka["aktivan"]}

    def u_registru(self):
        return set(self.jedinice)

    def oznaka(self, ou):
        """„430111 — Strucni nadzor · centar 43"; jedinica van registra zadrzava stari naziv."""
        stavka = self.jedinice.get(ou.pk)
        if stavka is None:
            if not self.dostupan:
                return str(ou)
            return f"{ou.code.strip()} — {(ou.name or '').strip()} (van registra)"
        return f"{stavka['sifra']} — {stavka['naziv'] or (ou.name or '').strip()} · centar {stavka['centar']}"

    def oznaka_centra(self, code):
        code = (code or "").strip()
        naziv = self.centri.get(code)
        return f"{code} — {naziv}" if naziv else code

    def izbor_centara(self, codes, prazno):
        codes = sorted({(c or "").strip() for c in codes if c and str(c).strip()},
                       key=lambda c: (not c.isdigit(), int(c) if c.isdigit() else 0, c))
        return [("", prazno)] + [(c, self.oznaka_centra(c)) for c in codes]


def ogranici_izbor(field, trenutni_id=None, registar=None, samo_aktivne=True):
    """Polje izbora jedinice Flote: samo sifre iz registra (aktivne), plus vec upisana vrednost.

    Iskljucen prekidac ne menja nista. Oznake stavki uzimaju se iz registra.
    """
    if not ukljuceno():
        return
    registar = registar or Registar()
    if not registar.dostupan:
        return
    dozvoljeni = registar.aktivne() if samo_aktivne else registar.u_registru()
    if trenutni_id:
        dozvoljeni = dozvoljeni | {trenutni_id}
    field.queryset = field.queryset.filter(pk__in=dozvoljeni).order_by("code")
    field.label_from_instance = registar.oznaka
