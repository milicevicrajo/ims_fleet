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