"""Izbor ugovora iz evidencije Ugovori (select2 sa pretragom) i valuta ugovora.

Obračun flote vodi iznose u dinarima. Ugovor u stranoj valuti može da se poveže, ali se iznos
naknade unosi u RSD; opcija nosi `data-currency`, pa `fleet/js/ugovor_valuta.js` ispod iznosa
prikazuje napomenu o valuti.
"""
from django import forms
from django_select2.forms import Select2Widget

from ugovori.models import Contract


class UgovorSelect(Select2Widget):
    def optgroups(self, name, value, attrs=None):
        # Valute se čitaju pri prikazu (ne pri učitavanju modula), za ugovore iz izbora.
        queryset = getattr(self.choices, 'queryset', None)
        self.valute = dict(queryset.values_list('pk', 'currency')) if queryset is not None else {}
        return super().optgroups(name, value, attrs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        valuta = getattr(self, 'valute', {}).get(getattr(value, 'value', value))
        if valuta:
            option['attrs']['data-currency'] = valuta
        return option


class UgovorField(forms.ModelChoiceField):
    def __init__(self, *args, valuta_za=None, **kwargs):
        kwargs.setdefault('queryset', Contract.objects.order_by('-contract_date', '-pk'))
        kwargs.setdefault('required', False)
        attrs = {'class': 'select2-method', 'data-placeholder': 'Pretraga po broju ili nazivu ugovora'}
        if valuta_za:
            attrs['data-ugovor-valuta'] = valuta_za  # id polja iznosa ispod kog ide napomena o valuti
        kwargs.setdefault('widget', UgovorSelect(attrs=attrs))
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        valuta = '' if (obj.currency or 'RSD') == 'RSD' else f' · {obj.currency}'
        return f'{obj}{valuta}'


def strana_valuta(ugovor):
    """Valuta ugovora ako nije RSD, inače None."""
    valuta = (getattr(ugovor, 'currency', '') or 'RSD').upper()
    return None if valuta == 'RSD' else valuta


def poruka_iznosa(valuta):
    return f'Ugovor je u {valuta}. Unesite iznos naknade u dinarima (RSD) — obračun flote vodi iznose u dinarima.'
