"""Pomocni filteri prikaza."""

from django import template

register = template.Library()


@register.filter
def mnozina(count, forms):
    """Srpska mnozina: `{{ n|mnozina:"posao,posla,poslova" }}`.

    Pravilo: brojevi 11–14 uvek uzimaju treci oblik; inace poslednja cifra odlucuje —
    1 prvi oblik, 2–4 drugi, ostalo treci.
    """
    try:
        number = int(count)
    except (TypeError, ValueError):
        return ""
    parts = [part.strip() for part in (forms or "").split(",")]
    if len(parts) != 3:
        return parts[-1] if parts else ""
    one, few, many = parts
    if number % 100 in (11, 12, 13, 14):
        return many
    last = number % 10
    if last == 1:
        return one
    if last in (2, 3, 4):
        return few
    return many
