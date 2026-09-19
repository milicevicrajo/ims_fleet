"""Grupisanje polja forme u celine, za `fleet/templates/fleet/generic_form.html`.

Forma navede `fieldsets` i njena polja se prikazuju u imenovanim celinama umesto
kao jedan dugačak spisak. Polje koje nije navedeno ni u jednoj celini **ne gubi
se** — prikazuje se u poslednjoj, „Ostalo“, da izmena modela ne bi tiho sakrila
novo polje.
"""


class FieldsetMixin:
    """Dodaje `grouped_fields` formi.

    `fieldsets` je niz trojki: (naslov, kratko objašnjenje ili None, nazivi polja).

        fieldsets = (
            ('Vozilo', 'Na koje vozilo se odnosi.', ('vehicle',)),
            ('Iznosi', None, ('cena', 'vrednost_nab')),
        )
    """

    fieldsets = ()

    @property
    def grouped_fields(self):
        if not self.fieldsets:
            return []

        used = []
        groups = []
        for title, description, names in self.fieldsets:
            fields = [self[name] for name in names if name in self.fields]
            if not fields:
                continue
            used.extend(field.name for field in fields)
            groups.append({'title': title, 'description': description, 'fields': fields})

        leftovers = [self[name] for name in self.fields if name not in used]
        if leftovers:
            groups.append({
                'title': 'Ostalo',
                'description': 'Polja koja nisu razvrstana u celine iznad.',
                'fields': leftovers,
            })
        return groups

    @property
    def has_required_fields(self):
        return any(field.required for field in self.fields.values())
