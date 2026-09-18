"""Conservative, lossless conversion of legacy contact text into people and channels."""
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from potrazivanja.models import CollectionContact, ContactPoint

EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?<![\w@])(?:\+\s*\d|0)[\d\s()/.-]{5,}\d")
ROLE_WORDS = {"direktor", "dir", "knjigovodstvo", "racunovodstvo", "računovodstvo", "finansije", "office", "fax", "faks", "telefon", "tel", "mobilni", "knjig", "agencija"}


def clean_phone(value):
    value = value.strip()
    if not re.fullmatch(r"[+\d\s()/.-]+", value):
        raise ValidationError("Unesite jedan broj telefona; ime i napomena imaju posebna polja.")
    value = re.sub(r"^\+\s*381\s*\(0\)", "+381", value)
    digits = re.sub(r"\D", "", value)
    if not 7 <= len(digits) <= 15:
        raise ValidationError("Broj mora sadržati od 7 do 15 cifara.")
    return ("+" if value.startswith("+") else "") + digits


def parse_contact(raw_name, raw_email):
    emails = []
    for value in EMAIL.findall(f"{raw_email} {raw_name}"):
        value = value.strip('.').lower()
        try:
            validate_email(value)
        except ValidationError:
            continue
        if value not in emails:
            emails.append(value)
    people, general, unresolved = [], [], []
    email_remainder = EMAIL.sub('', raw_email).strip(' ,;\n\r\t')
    if email_remainder:
        unresolved.append(raw_email)
    for segment in re.split(r"[,;\n]+", raw_name):
        segment = segment.strip()
        if not segment:
            continue
        matches = list(PHONE.finditer(segment))
        phones = []
        for match in matches:
            candidate = match.group()
            try:
                value = clean_phone(candidate)
            except ValidationError:
                continue
            # Do not turn shorthand extensions, dates or adjoining numbers into one telephone.
            if re.fullmatch(r"0\d[./]\d{2}[./]\d{4}", candidate):
                continue
            if value.startswith('0') and len(value) not in (9, 10):
                continue
            phones.append(value)
        remainder = EMAIL.sub('', PHONE.sub('', segment)).strip(' -/():.')
        words = remainder.split()
        person = (len(phones) == 1 and 1 <= len(words) <= 3
                  and all(w.replace('-', '').isalpha() and w[0].isupper() for w in words)
                  and not any(w.casefold().strip('.') in ROLE_WORDS for w in words))
        if person:
            people.append({'first_name': words[0], 'last_name': ' '.join(words[1:]), 'phone': phones[0]})
        else:
            general.extend(phones)
            if remainder or not phones or len(matches) != len(phones):
                unresolved.append(segment)
    return {'emails': emails, 'people': people, 'phones': list(dict.fromkeys(general)), 'unresolved': unresolved}


def normalize_contacts():
    stats = {'source_contacts': 0, 'people_created': 0, 'points': 0, 'review': 0}
    for contact in CollectionContact.objects.filter(normalized_at__isnull=True, import_parent__isnull=True).order_by('pk'):
        raw = {'name': contact.name, 'phone': contact.phone, 'email': contact.email, 'note': contact.note,
               'legacy_partner_name': contact.legacy_partner_name}
        parsed = parse_contact(', '.join(v for v in (contact.name, contact.phone) if v), contact.email)
        contact.original_data = dict(raw, unresolved=parsed['unresolved'])
        contact.name = ''
        contact.position = 'Opšti kontakt'
        contact.phone = parsed['phones'][0] if parsed['phones'] else ''
        contact.email = parsed['emails'][0] if parsed['emails'] else ''
        contact.normalized_at = timezone.now()
        contact.needs_review = bool(parsed['unresolved'] or parsed['people'] or not contact.identity_id)
        contact.save()
        for kind, values in [('phone', parsed['phones']), ('email', parsed['emails'])]:
            for value in values:
                ContactPoint.objects.get_or_create(contact=contact, kind=kind, value=value, defaults={'label': 'Opšti kontakt'})
                stats['points'] += 1
        grouped = {}
        for person in parsed['people']:
            key = (person['first_name'], person['last_name'])
            child = grouped.get(key)
            if child is None:
                child = CollectionContact.objects.create(identity=contact.identity, first_name=key[0], last_name=key[1],
                    name=' '.join(key).strip(), phone=person['phone'], import_parent=contact, active=contact.active,
                    original_data=raw, normalized_at=timezone.now(), legacy_partner_name=contact.legacy_partner_name,
                    needs_review=not bool(contact.identity_id))
                grouped[key] = child
                stats['people_created'] += 1
            ContactPoint.objects.get_or_create(contact=child, kind='phone', value=person['phone'])
            stats['points'] += 1
        stats['source_contacts'] += 1
        stats['review'] += int(contact.needs_review)
    return stats
