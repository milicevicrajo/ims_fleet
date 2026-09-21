"""Defaults agreed for fleet analysis; confirmed profiles always take precedence."""
import unicodedata


def estimated_purpose(vehicle, assignment=None):
    def plain(value):
        return ''.join(c for c in unicodedata.normalize('NFKD', value or '')
                       if not unicodedata.combining(c)).lower()

    unit = assignment.organizational_unit if assignment else None
    description = plain(vehicle.description)
    text = ' '.join([description, plain(unit.name if unit else '')])
    if vehicle.category == 'prikljucno':
        return 'trailer', 'Procena prema kategoriji priključnog vozila.'
    for words, purpose, reason in [
        (('busac', 'busec', 'busenj'), 'drilling', 'Opis ili šifra posla upućuje na bušenje.'),
        (('spt', 'vuca'), 'towing', 'Opis ili šifra posla upućuje na prevoz / vuču opreme.'),
        (('kontejner', 'transport masina'), 'transport', 'Opis ili šifra posla upućuje na transport.'),
        (('laborator', 'lab.', 'asfaltna ispitivanja', 'kamen i agregat', 'veziva, hemije', 'etaloniranje'), 'laboratory', 'Opis ili šifra posla upućuje na laboratorijski prevoz.'),
        (('uprava', 'direktor', 'z.sluzbe', 'zajednicke sluzbe', 'organizacija i poslovanje', 'pravni i kadrovski', 'poslovi nabavke'), 'management', 'Opis ili šifra posla upućuje na poslovnu mobilnost.'),
        (('nadzor',), 'supervision', 'Opis ili šifra posla upućuje na nadzor.'),
    ]:
        if any(word in text for word in words):
            return purpose, reason
    return 'supervision', 'Početna procena: nadzor i terenski rad; precizirati ako vozilo ima posebnu namenu.'


def holding_at(leases, day):
    active = [lease for lease in leases if lease.start_date <= day <= lease.end_date]
    if len(active) > 1:
        return 'unknown', 'Preklopljeni ugovori', None
    if not active:
        return 'owned', 'Vlasništvo IMS', None
    lease = active[0]
    return ('dugorocni' if lease.is_long_term_rental else lease.lease_type,
            lease.lease_type_label, lease)
