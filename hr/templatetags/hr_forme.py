"""Pomoćne oznake za forme u sekcijama (`hr/forms/base.html`).

    {% load hr_forme %}
    {% for section in form|sekcije:"Podaci" %}...{% endfor %}

    {% sekcija key="period" title="Period od–do" icon="mdi-calendar-range" grupa="period" %}
        ... polja ili tabela ...
    {% endsekcija %}

`telo="slobodno"` daje sekciju bez rešetke od dve kolone (za tabele i spiskove).
"""
from django import template
from django.template.base import token_kwargs
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from hr.form_layout import sekcije_forme

register = template.Library()


@register.filter
def sekcije(form, naslov='Podaci'):
    return sekcije_forme(form, naslov=naslov) if form is not None else []


class SekcijaNode(template.Node):
    def __init__(self, kwargs, nodelist):
        self.kwargs, self.nodelist = kwargs, nodelist

    def render(self, context):
        values = {key: value.resolve(context) for key, value in self.kwargs.items()}
        values['body'] = mark_safe(self.nodelist.render(context))
        return render_to_string('hr/forms/_sekcija.html', values)


@register.tag('sekcija')
def do_sekcija(parser, token):
    kwargs = token_kwargs(token.split_contents()[1:], parser)
    nodelist = parser.parse(('endsekcija',))
    parser.delete_first_token()
    return SekcijaNode(kwargs, nodelist)
