"""Link na detalj vozila — isti izgled svuda u Floti (od 29.09.2026.).

U sablonima: `{% load vozila %}` pa `{{ nalog.vehicle|vozilo_link }}` ili sa sopstvenim tekstom
`{{ nalog.vehicle|vozilo_link:tablica }}`; kad postoji samo sifra vozila: `{% vozilo_a vozilo_id tekst %}`.
U tabelama sa servera (JSON): `vozilo_link(vozilo)` / `vozilo_link_id(vozilo_id, tekst)`.
Stampani dokumenti (putni nalog, prijava kvara, trebovanje…) namerno nemaju linkove.
"""
from django.urls import reverse
from django.utils.html import format_html

KLASA = "fleet-table-link vozilo-link"


def vozilo_url(vozilo_id):
    return reverse("vehicle_detail", args=[vozilo_id]) if vozilo_id else ""


def vozilo_link_id(vozilo_id, tekst, klasa=KLASA):
    """Link za vozilo kada je poznata samo sifra (npr. red izvestaja); bez sifre — samo tekst."""
    if not vozilo_id:
        return format_html("{}", tekst if tekst not in (None, "") else "—")
    return format_html('<a href="{}" class="{}" title="Detalj vozila">{}</a>', vozilo_url(vozilo_id), klasa,
                       tekst if tekst not in (None, "") else "vozilo")


def vozilo_link(vozilo, tekst=None, klasa=KLASA):
    """Link na detalj vozila sa tekstom `tekst` (podrazumevano naziv vozila)."""
    if vozilo is None or not getattr(vozilo, "pk", None):
        return format_html("{}", tekst if tekst not in (None, "") else "—")
    return vozilo_link_id(vozilo.pk, str(vozilo) if tekst in (None, "") else tekst, klasa)
