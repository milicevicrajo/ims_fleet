"""Predlog („meko popunjavanje") radne liste iz podataka koje aplikacija već ima.

Predlog se ne upisuje u bazu. Stranica radne liste njime popunjava samo prazna polja, a
zaposleni ili kadrovik ga proverava, menja i tek onda čuva. Ništa što je već uneto se ne
prepisuje.

Pravila za radni dan (ponedeljak–petak), prvo pravilo koje važi:

1. bolovanje iz uvezenih RFZO bolovanja  → 8 sati, vrsta „Bolovanje";
2. neradni praznik (državni, Božić, vaskršnji) → 8 sati, vrsta „Državni i verski praznik";
3. krsna slava zaposlenog → 8 sati, vrsta „Državni i verski praznik";
4. putni nalog (i kad tog dana ima prolaza) → 8 sati, vrsta „Redovan rad", na **šifri posla putnog naloga**
   (od 09.10.2026.: poseban red, odmah posle redovnog rada — red 2; više naloga sa različitim šiframa — red po šifri);
5. prolazi na kontroli pristupa → 8 sati (pun dan), vrsta „Redovan rad".

Terenski dodatak = broj dana u mesecu pokrivenih putnim nalogom (i vikendom).
Rad vikendom i rad na praznik se ne predlažu: za njih treba rešenje, pa se samo navode u
napomenama. Redovi osim putnih naloga dobijaju podrazumevanu šifru posla zaposlenog (njegovu OJ);
ako je nema u šifarniku, šifra ostaje prazna. Putni nalog na podrazumevanoj šifri ide u red redovnog rada.
"""
from datetime import date

from core.models import OrganizationalUnit
from hr.models import WorkTimeCategory

from .praznici import datum_slave, neradni_praznici

PUN_DAN = 8
REDOVAN, BOLOVANJE, PRAZNIK = 'redovan_rad', 'bolovanje', 'drzavni_i_verski_praznik'


def podrazumevana_sifra(employee):
    kod = str(employee.org_unit_code or employee.department_code or '').strip()
    return OrganizationalUnit.objects.filter(code=kod).first() if kod else None


def dostupne_vrste(employee):
    """Vrste koje forma radne liste nudi ovom zaposlenom, po oznaci."""
    vrste = WorkTimeCategory.objects.filter(
        is_active=True, employee_selectable=True, elements__is_active=True,
        elements__recipient_type__is_active=True,
        elements__recipient_type__code=getattr(employee, 'recipient_code', '') or '',
    ).distinct()
    return {vrsta.code: vrsta for vrsta in vrste}


def _sati_iz_prolazaka(item):
    # Dan sa prolazima se predlaže kao pun radni dan, bez obzira na stvarno trajanje.
    return PUN_DAN if item and item.pair_count else 0


def predlog(employee, godina, mesec, dana_u_mesecu, *, prolazi_po_danu, putni_nalozi_po_danu,
            bolovanja_po_danu, prolazi_ucitani=True):
    praznici = neradni_praznici(godina)
    slava, slava_iz_naziva = datum_slave(employee, godina)
    sifra = podrazumevana_sifra(employee)
    vrste = dostupne_vrste(employee)

    sati = {REDOVAN: {}, BOLOVANJE: {}, PRAZNIK: {}}
    nalozi_po_sifri = {}  # šifra posla naloga (OrganizationalUnit) → {dan: sati}
    brojaci = {'prolazi': 0, 'putni_nalog': 0, 'bolovanje': 0, 'praznik': 0, 'slava': 0}
    napomene, oznake_dana = [], {}
    teren_dana = 0

    for dan in range(1, dana_u_mesecu + 1):
        datum = date(godina, mesec, dan)
        radni_dan = datum.weekday() < 5
        item = prolazi_po_danu.get(datum)
        prolazi = _sati_iz_prolazaka(item)
        nalozi = putni_nalozi_po_danu.get(datum) or []
        if nalozi:
            teren_dana += 1
        praznik = praznici.get(datum)
        if praznik:
            oznake_dana[dan] = praznik
        if datum == slava:
            oznake_dana[dan] = f'Slava: {employee.slava}'

        if not radni_dan:
            if prolazi or (item and item.pair_count):
                napomene.append(f'{datum:%d.%m.} (vikend) ima prolaze — rad vikendom se upisuje ručno, uz rešenje.')
            continue
        if bolovanja_po_danu.get(datum):
            sati[BOLOVANJE][dan] = PUN_DAN
            brojaci['bolovanje'] += 1
            if prolazi:
                napomene.append(f'{datum:%d.%m.} ima i bolovanje i prolaze — predloženo je bolovanje.')
            continue
        if praznik:
            sati[PRAZNIK][dan] = PUN_DAN
            brojaci['praznik'] += 1
            if prolazi:
                napomene.append(f'{datum:%d.%m.} ({praznik}) ima prolaze — rad na praznik se upisuje ručno, uz rešenje.')
            continue
        if datum == slava:
            sati[PRAZNIK][dan] = PUN_DAN
            brojaci['slava'] += 1
            continue
        if nalozi:
            sifra_naloga = nalozi[0].job_code if getattr(nalozi[0], "job_code_id", None) else sifra
            if sifra_naloga is None or (sifra is not None and sifra_naloga.pk == sifra.pk):
                sati[REDOVAN][dan] = PUN_DAN
            else:
                nalozi_po_sifri.setdefault(sifra_naloga, {})[dan] = PUN_DAN
            brojaci['putni_nalog'] += 1
        elif prolazi:
            sati[REDOVAN][dan] = prolazi
            brojaci['prolazi'] += 1

    if not prolazi_ucitani:
        napomene.insert(0, 'Prolazi nisu učitani (izvor nije dostupan), pa predlog ne sadrži redovan rad iz prolazaka.')
    if slava and slava_iz_naziva and slava.month == mesec:
        napomene.append(f'Datum slave ({slava:%d.%m.}) je predložen iz naziva „{employee.slava}“ — '
                        'upišite ga kod zaposlenog ako je drugačiji.')
    elif employee.slava and not slava:
        napomene.append(f'Za slavu „{employee.slava}“ nije upisan datum, pa nije predložena.')

    redovi = []
    grupe = [(REDOVAN, 'Redovan rad', sifra, sati[REDOVAN])]
    grupe += [(REDOVAN, 'Putni nalog', s, d) for s, d in sorted(nalozi_po_sifri.items(), key=lambda x: x[0].code)]
    grupe += [(BOLOVANJE, 'Bolovanje', sifra, sati[BOLOVANJE]), (PRAZNIK, 'Državni i verski praznik', sifra, sati[PRAZNIK])]
    for kljuc, naziv, sifra_reda, dani in grupe:
        if not dani:
            continue
        vrsta = vrste.get(kljuc)
        if vrsta is None and kljuc != REDOVAN:
            # Bez ove vrste u šifarniku sati bi završili u redu bez oznake i pomešali se sa redovnim radom.
            napomene.append(f'{naziv}: vrsta nije dostupna za vrstu primaoca {employee.recipient_code or "—"}, '
                            f'pa {len(dani)} dana nije predloženo.')
            continue
        redovi.append({
            'kljuc': 'putni_nalog' if naziv == 'Putni nalog' else kljuc, 'naziv': naziv,
            'sifra_id': sifra_reda.pk if sifra_reda else None, 'sifra': sifra_reda.code.strip() if sifra_reda else '',
            'vrsta_id': vrsta.pk if vrsta else None, 'vrsta': vrsta.name if vrsta else '',
            'sati': {str(dan): vrednost for dan, vrednost in sorted(dani.items())},
            'dana': len(dani), 'ukupno': sum(dani.values()),
        })
    if sifra is None:
        napomene.append('Zaposleni nema podrazumevanu šifru posla u šifarniku (OJ '
                        f'{employee.org_unit_code or employee.department_code or "—"}), pa je šifra ostavljena prazna.')

    return {
        'redovi': redovi,
        'teren_dana': teren_dana or None,
        'brojaci': brojaci,
        'napomene': napomene,
        'oznake_dana': {str(dan): oznaka for dan, oznaka in oznake_dana.items()},
        'ima_predlog': bool(redovi or teren_dana),
    }
