from decimal import Decimal, InvalidOperation

from django import template, forms
register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    attrs = value.field.widget.attrs
    existing_classes = attrs.get('class', '')
    if 'is-invalid' in existing_classes:
        css_class += ' is-invalid'
    attrs['class'] = f"{existing_classes} {css_class}".strip()
    rendered_field = str(value)
    return rendered_field

@register.filter
def get_attr(obj, attr_name):
    """Vraća vrednost atributa iz objekta."""
    return getattr(obj, attr_name, None)

@register.filter
def receipt_number(value):
    """Prikazuje broj računa kao identifikator, bez decimalnog dela."""
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        return ''
    try:
        decimal_value = Decimal(text.replace(',', '.'))
    except (InvalidOperation, ValueError):
        return text
    if decimal_value == decimal_value.to_integral_value():
        return str(decimal_value.to_integral_value())
    return text


@register.filter
def money_rs(value):
    """Formatira novcani iznos sa srpskim separatorima: 1.234.567,89."""
    if value is None:
        return ''
    text = str(value).strip()
    if not text:
        return ''
    try:
        amount = Decimal(text.replace(',', '.'))
    except (InvalidOperation, ValueError):
        return text
    formatted = f"{amount:,.2f}"
    return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
