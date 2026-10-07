from django import template

from hr.services.rodna_ravnopravnost_izvoz import tekst

register = template.Library()


@register.filter
def rr_celija(vrednost):
    """Ćelija statistike rodne ravnopravnosti: par (broj, udeo) kao „75 (24,1%)”."""
    return tekst(vrednost)
