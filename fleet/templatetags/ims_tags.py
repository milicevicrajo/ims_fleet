from django import template
from urllib.parse import urlencode
from django import template
register = template.Library()

@register.filter
def get_verbose_name(instance, field_name):
    """
    Returns the verbose name of a model field.
    """
    return instance._meta.get_field(field_name).verbose_name

@register.filter
def get_field_value(instance, field_name):
    """
    Returns the value of a model field.
    """
    return getattr(instance, field_name)

@register.filter
def dict_get(dictionary, key):
    """Vraća vrednost iz rečnika po ključu."""
    return dictionary.get(key)