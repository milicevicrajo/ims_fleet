"""Sekcije formi Kadrova, za šablon `hr/forms/base.html`.

Forma navede `SECTIONS` — (oznaka, naslov, kratak opis, polja, uputstvo, ikonica) — i šablon je
prikaže u sekcijama sa desnom karticom za kretanje, uputstvom uz svaku sekciju i prekidačima za
da/ne polja. Polje koje nije navedeno ni u jednoj sekciji ne gubi se: ide u „Ostalo“.
Forma bez `SECTIONS` prikazuje se kao jedna sekcija (`sekcije_forme`).
"""
from fleet.forms.layout import FieldsetMixin


class SekcijeMixin(FieldsetMixin):
    SECTIONS = ()

    @property
    def fieldsets(self):
        return tuple((title, description, names) for _key, title, description, names, _help, _icon in self.SECTIONS)

    @property
    def sections(self):
        groups = {group['title']: group for group in self.grouped_fields}
        sections = []
        for key, title, description, _names, help_text, icon in self.SECTIONS:
            group = groups.pop(title, None)
            if group:
                sections.append({'key': key, 'title': title, 'description': description, 'help': help_text,
                                 'icon': icon, 'fields': group['fields']})
        for group in groups.values():
            sections.append({'key': 'ostalo', 'title': group['title'], 'description': group['description'],
                             'help': '', 'icon': 'mdi-dots-horizontal', 'fields': group['fields']})
        return sections


def sekcije_forme(form, naslov='Podaci', ikona='mdi-form-select', opis=None, uputstvo=''):
    """Sekcije forme; forma bez `SECTIONS` postaje jedna sekcija sa svim vidljivim poljima."""
    if getattr(form, 'SECTIONS', None):
        return form.sections
    return [{'key': 'podaci', 'title': naslov, 'description': opis, 'help': uputstvo, 'icon': ikona,
             'fields': [field for field in form if not field.is_hidden]}]
