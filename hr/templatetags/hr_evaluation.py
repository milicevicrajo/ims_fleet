from decimal import Decimal, InvalidOperation

from django import template

from hr.services.evaluations import latin

register = template.Library()


@register.filter
def coefficient(value):
    if value is None or value == '':
        return '-'
    try:
        return f'{Decimal(str(value)):.5f}'.replace('.', ',')
    except (InvalidOperation, ValueError):
        return '-'


@register.filter
def latin_text(value):
    return latin(value)
