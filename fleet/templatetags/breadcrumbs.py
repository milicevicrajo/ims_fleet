from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html

register = template.Library()

@register.simple_tag(takes_context=True)
def breadcrumbs(context):
    request = context['request']
    path = request.path_info.strip('/').split('/')
    full_path = ''
    breadcrumb_html = '<ol class="breadcrumb">'

    for part in path:
        full_path += f'/{part}'
        try:
            name = part.replace('-', ' ').capitalize()
            url = reverse(f'{part}')
            breadcrumb_html += f'<li class="breadcrumb-item"><a href="{url}">{name}</a></li>'
        except NoReverseMatch:
            name = part.replace('-', ' ').capitalize()
            breadcrumb_html += f'<li class="breadcrumb-item active">{name}</li>'

    breadcrumb_html += '</ol>'
    return format_html(breadcrumb_html)

