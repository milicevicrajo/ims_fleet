"""Partner detail projections of the existing, published collection snapshot."""
from collections import defaultdict
from decimal import Decimal

from .sync import bucket


INVOICE_BUCKETS = (
    ('181', 'Baket 6 — preko 180 dana'),
    ('180', 'Baket 5 — 91–180 dana'),
    ('90', 'Baket 4 — 61–90 dana'),
    ('60', 'Baket 3 — 46–60 dana'),
)
BUCKET_LABELS = {
    '0.1': 'Nedospelo / bez datuma', '30': '1–30 dana', '45': '31–45 dana',
    '60': '46–60 dana', '90': '61–90 dana', '180': '91–180 dana', '181': 'Preko 180 dana',
}


def invoice_groups(positions, as_of_date, bucket_code):
    """Same partner/reference/job sums as Naplata, after permission filtering."""
    groups = {}
    for position in positions:
        if bucket(position.due_date, as_of_date) != bucket_code:
            continue
        key = (position.identity_id, position.reference, position.job_code)
        group = groups.setdefault(key, {
            'identity': position.identity, 'reference': position.reference,
            'job_code': position.job_code, 'amounts': defaultdict(Decimal),
        })
        for field in ('debit', 'credit', 'balance'):
            group['amounts'][field] += getattr(position, field)
    return groups.values()


def basic_fields(identity, raw):
    fields = (
        ('Šifra partnera', 'sif_par', identity.partner_code),
        ('Naziv', 'naz_par', identity.source_name),
        ('Ulica', 'ulica_par', identity.source_address),
        ('Poštanski broj', 'p_b_par', ''), ('Mesto', 'mesto_par', identity.source_city),
        ('Žiro račun', 'zr', ''), ('Matični broj', 'mb', identity.source_registration_number),
        ('Telefon', 'telefon', ''), ('Fax', 'fax', ''), ('Email', 'email', ''),
        ('Kontakt osoba', 'lice', ''), ('Web', 'web', ''), ('Procenat rabata', 'proc_rabata', ''),
        ('Broj dana plaćanja', 'br_dana', ''), ('Vlasnik', 'vlasnik', ''),
        ('PIB', 'pib', identity.source_tax_id), ('Zemlja', 'zemlja', identity.source_country),
        ('PDV obveznik', 'pdv_obveznik', ''),
    )
    return [(label, raw.get(key, fallback)) for label, key, fallback in fields]
