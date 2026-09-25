"""Organizaciona šema IMS prema aneksima A, B i C.

Ovo je opis šeme kako je dostavljena (`static/organizacija/ims-organizaciona-sema.svg`),
ne podatak iz registra organizacije: registar zna centre, jedinice i šifre posla, a šema
zna laboratorije, rukovodioce i službe. Kada se šema promeni, menjaju se crtež i ovaj
opis zajedno.
"""

LAB = 'laboratorija'
GRUPA = 'grupa'          # nadređena laboratorijska celina sa svojim laboratorijama
ODELJENJE = 'odeljenje'

U_LAB = 'Rukovodilac u laboratoriji'

UPRAVLJANJE = {
    'organi': ['Skupština', 'Nadzorni odbor', 'Izvršni odbor'],
    'direktor': 'Generalni direktor',
    'pomocnici': ['Tehnički direktor', 'Finansijski direktor'],
    'povezano': ['Sekretar', 'Naučno veće'],
}

CENTRI = [
    {
        'naziv': 'Centar za materijale', 'kratko': 'Materijali', 'rukovodilac': 'Direktor centra',
        'jedinice': [
            {'naziv': 'Centralna laboratorija za ispitivanje materijala', 'rukovodilac': 'Rukovodilac laboratorije',
             'vrsta': GRUPA, 'laboratorije': [
                 'Laboratorija za kamen i agregat',
                 'Laboratorija za građevinsku keramiku',
                 'Laboratorija za beton',
                 'Laboratorija za veziva, hemiju i maltere',
                 'Laboratorija za toplotnu tehniku i zaštitu od požara',
                 'Laboratorija za drvo i sintetičke materijale',
                 'Laboratorija za hidroizolaciju i antikorozivnu zaštitu',
                 'Laboratorija za akustiku i vibracije',
             ]},
            {'naziv': 'Metrološka laboratorija za akustiku i vibracije', 'rukovodilac': 'Rukovodilac laboratorije', 'vrsta': LAB},
            {'naziv': 'Odeljenje za zaštitu životne sredine', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
        ],
    },
    {
        'naziv': 'Centar za metale i energetiku', 'kratko': 'Metali i energetika', 'rukovodilac': 'Direktor centra',
        'jedinice': [
            {'naziv': 'Odeljenje za kontrolu opreme i MTI', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
            {'naziv': 'Laboratorija za ispitivanje metala', 'rukovodilac': 'Rukovodilac laboratorije', 'vrsta': LAB},
            {'naziv': 'Metrološka laboratorija za mehaničke veličine', 'rukovodilac': 'Rukovodilac laboratorije', 'vrsta': LAB},
        ],
    },
    {
        'naziv': 'Centar za puteve i geotehniku', 'kratko': 'Putevi i geotehnika', 'rukovodilac': 'Direktor centra',
        'jedinice': [
            {'naziv': 'Odeljenje za geotehniku i nadzor', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
            {'naziv': 'Odeljenje za projektovanje saobraćajnica', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
            {'naziv': 'Laboratorija za puteve i geotehniku', 'rukovodilac': 'Rukovodilac laboratorije',
             'vrsta': GRUPA, 'laboratorije': [
                 'Laboratorija za geomehaniku',
                 'Laboratorija za asfalt',
                 'Laboratorija za ispitivanje saobraćajne signalizacije',
                 'Laboratorija za ispitivanje geotehničkih konstrukcija',
             ]},
        ],
    },
    {
        'naziv': 'Centar za konstrukcije i prednaprezanje', 'kratko': 'Konstrukcije', 'rukovodilac': 'Direktor centra',
        'jedinice': [
            {'naziv': 'Odeljenje za prednaprezanje', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
            {'naziv': 'Odeljenje za projektovanje, nadzor i sanacije', 'rukovodilac': 'Rukovodilac odeljenja', 'vrsta': ODELJENJE},
            {'naziv': 'Laboratorija za ispitivanje konstrukcija', 'rukovodilac': 'Rukovodilac laboratorije', 'vrsta': LAB},
        ],
    },
]

OSTALE_CELINE = [
    {'naziv': 'Naučnoistraživački blok', 'rukovodilac': 'Direktor za NIR'},
    {'naziv': 'Sertifikaciono telo', 'rukovodilac': 'Rukovodilac'},
    {'naziv': 'Sertifikaciono telo za sertifikaciju osoba', 'rukovodilac': 'Rukovodilac'},
    {'naziv': 'Kontrolno telo', 'rukovodilac': 'Rukovodilac'},
    {'naziv': 'Provajder za ispitivanje osposobljenosti', 'rukovodilac': 'Rukovodilac'},
    {'naziv': 'Služba za integralne sisteme menadžmenta', 'rukovodilac': 'Predstavnik rukovodstva za integrisane sisteme'},
    {'naziv': 'Telo za tehničko ocenjivanje', 'rukovodilac': 'Rukovodilac'},
    {'naziv': 'Telo za verifikaciju', 'rukovodilac': 'Rukovodilac'},
]

ZAJEDNICKE_SLUZBE = [
    {'naziv': 'Finansijska služba', 'rukovodilac': 'Šef računovodstva', 'oblasti': [
        {'naziv': 'Računovodstvo'}, {'naziv': 'Knjigovodstvo'}, {'naziv': 'Komercijala'},
        {'naziv': 'Blagajna'}, {'naziv': 'Magacin'},
    ]},
    {'naziv': 'Služba za opšte i pomoćno tehničke poslove', 'rukovodilac': 'Direktor', 'oblasti': [
        {'naziv': 'Pravni i kadrovski poslovi'},
        {'naziv': 'Ekonomski poslovi', 'opis': 'Spoljnotrgovinski poslovi, plan i analiza'},
        {'naziv': 'Biblioteka'},
        {'naziv': 'Informatika'},
        {'naziv': 'Marketing'},
        {'naziv': 'Opšti poslovi', 'opis': 'Arhiva, pisarnica sa ekspedicijom, poslovna administracija, PPZ, BZR, '
                                           'obezbeđenje, centrala, bife i higijena'},
        {'naziv': 'Radionica, garaža, tehničko održavanje i kotlarnica'},
    ]},
]


def krajnje_laboratorije(centar):
    """Laboratorije na krajnjem nivou: nadređena laboratorijska celina se ne broji, njene laboratorije se broje."""
    ukupno = 0
    for jedinica in centar['jedinice']:
        if jedinica['vrsta'] == GRUPA:
            ukupno += len(jedinica['laboratorije'])
        elif jedinica['vrsta'] == LAB:
            ukupno += 1
    return ukupno


def sema():
    centri = [dict(centar, broj_laboratorija=krajnje_laboratorije(centar)) for centar in CENTRI]
    for centar in centri:
        centar['jedinice'] = [dict(jedinica, laboratorije=[{'naziv': naziv, 'rukovodilac': U_LAB}
                                                            for naziv in jedinica.get('laboratorije', [])])
                              for jedinica in centar['jedinice']]
    return {
        'upravljanje': UPRAVLJANJE,
        'centri': centri,
        'ostale_celine': OSTALE_CELINE,
        'sluzbe': ZAJEDNICKE_SLUZBE,
        'ukupno': {
            'centri': len(centri),
            'laboratorije': sum(centar['broj_laboratorija'] for centar in centri),
            'ostale_celine': len(OSTALE_CELINE),
            'sluzbe': len(ZAJEDNICKE_SLUZBE),
        },
        'po_centrima': ' · '.join(f"{centar['kratko']} {centar['broj_laboratorija']}" for centar in centri),
    }
