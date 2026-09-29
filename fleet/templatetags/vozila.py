"""Link na detalj vozila u sablonima Flote (`fleet/support/vehicle_links.py`)."""
from django import template

from fleet.support.vehicle_links import vozilo_link as _vozilo_link, vozilo_link_id

register = template.Library()


@register.filter
def vozilo_link(vozilo, tekst=None):
    """`{{ x.vehicle|vozilo_link }}` ili `{{ x.vehicle|vozilo_link:"BG123-AA" }}`."""
    return _vozilo_link(vozilo, tekst)


@register.simple_tag
def vozilo_a(vozilo_id, tekst=""):
    """`{% vozilo_a red.vehicle_id red.tablica %}` — kad postoji samo sifra vozila."""
    return vozilo_link_id(vozilo_id, tekst)
