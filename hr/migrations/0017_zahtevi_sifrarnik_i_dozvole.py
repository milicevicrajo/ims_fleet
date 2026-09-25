"""Obrasci zahteva, rešenje o zameni odsutnog zaposlenog i dozvole za zahteve.

Tekst zahteva prati obrazac kadrovske službe („Zahtev za izdavanje rešenja za prekovremeni
rad“ i „Imenovanje lica za zamenu“). Ime zaposlenog stoji iza dvotačke, u nominativu, da bi
tekst bio ispravan i kada se isti zahtev pravi za više zaposlenih odjednom.
"""
from django.db import migrations

UVOD = ('{zaposleni} {rod:запослен|запослена} у Институту за испитивање материјала а.д. Београд, '
        '{rod:распоређен|распоређена} у {oj}')
POUKA = ('Правна поука: Против овог решења {rod:запослени|запослена} има право да покрене спор код '
         'надлежног суда, ради заштите својих права, у року од 60 дана од дана достављања.')
DOSTAVLJENO = ('{rod:именованом|именованој}\n'
               'референту обрачуна\n'
               'Ц {centar}\n'
               'реф.за кадровске послове')

ZAMENA_RESENJE = {
    'kod': 'zamena-odsutnog', 'naziv': 'Zamena odsutnog zaposlenog', 'naslov': 'РЕШЕЊЕ',
    'podnaslov': 'О ЗАМЕНИ ОДСУТНОГ ЗАПОСЛЕНОГ', 'redosled': 80,
    'pravni_osnov': 'На основу члана 192. и 193. Закона о раду и члана 43. Статута Института ИМС а.д., доносим',
    'dispozitiv': (
        UVOD + ', {rod:одређен|одређена} је да {period} обавља послове {poslovi}.\n'
        'За време замене {rod:запослени|запослена} је {rod:дужан|дужна} да послове из тачке 1. овог решења '
        'обавља у складу са законом и општим актима Института ИМС а.д.'),
    'obrazlozenje': ('На основу захтева бр. {zahtev_broj} од {zahtev_datum}[[razlog_zahteva|, због {razlog_zahteva}]], '
                     'а ради организације рада, одлучено је као у диспозитиву.\n[[napomena|{napomena}]]'),
    'pravna_pouka': POUKA, 'dostavljeno': DOSTAVLJENO, 'trazi_period': True,
    'dodatna_polja': 'poslovi|Poslovi koje zaposleni preuzima (npr. директора Финансија)',
}

UVOD_ZAHTEVA = 'Молим Вас да[[razlog| због {razlog},]] издате решење '
ZA_ZAPOSLENOG = ' за {rod:запосленог|запослену}: {zaposleni}, {oj}.'

ZAHTEVI = [
    {
        'kod': 'prekovremeni-rad', 'naziv': 'Prekovremeni rad', 'resenje': 'prekovremeni-rad', 'redosled': 10,
        'predmet': 'Захтев за издавање решења за прековремени рад',
        'tekst': (UVOD_ZAHTEVA + 'за прековремени рад' + ZA_ZAPOSLENOG + '\n'
                  'Прековремени рад ће се обављати {period}, а доказује се потписаном радном листом.'),
        'trazi_dane': True,
    },
    {
        'kod': 'prekovremeni-i-vikend', 'naziv': 'Prekovremeni rad i rad vikendom', 'resenje': 'prekovremeni-i-vikend',
        'redosled': 20, 'predmet': 'Захтев за издавање решења за прековремени рад и рад викендом',
        'tekst': (UVOD_ZAHTEVA + 'за прековремени рад и рад викендом' + ZA_ZAPOSLENOG + '\n'
                  'Прековремени рад и рад викендом ће се обављати {period}, а доказују се потписаном радном листом.'),
        'trazi_period': True,
    },
    {
        'kod': 'nocni-rad', 'naziv': 'Noćni rad', 'resenje': 'nocni-rad', 'redosled': 30,
        'predmet': 'Захтев за издавање решења за ноћни рад',
        'tekst': UVOD_ZAHTEVA + 'за ноћни рад' + ZA_ZAPOSLENOG + '\nНоћни рад ће се обављати {period}.',
        'trazi_period': True,
    },
    {
        'kod': 'praznik', 'naziv': 'Rad na državni i verski praznik', 'resenje': 'praznik', 'redosled': 40,
        'predmet': 'Захтев за издавање решења за рад на дан државног и верског празника',
        'tekst': (UVOD_ZAHTEVA + 'за рад на дан празника' + ZA_ZAPOSLENOG + '\n'
                  'Рад ће се обављати'
                  '[[dani_drzavni| {dani_drzavni} на дан државног празника]]'
                  '[[dani_verski| и {dani_verski} на дан верског празника]]'
                  '[[dani_vikend| и {dani_vikend} за дане викенда]].'),
        'trazi_dane': True,
    },
    {
        'kod': 'vikend', 'naziv': 'Rad vikendom', 'resenje': 'vikend', 'redosled': 50,
        'predmet': 'Захтев за издавање решења за рад викендом',
        'tekst': UVOD_ZAHTEVA + 'за рад викендом' + ZA_ZAPOSLENOG + '\nРад викендом ће се обављати {dani} године.',
        'trazi_dane': True,
    },
    {
        'kod': 'prekovremeni-vikend-smene', 'naziv': 'Prekovremeni rad, rad vikendom i rad u smenama',
        'resenje': 'prekovremeni-vikend-smene', 'redosled': 60,
        'predmet': 'Захтев за издавање решења за прековремени рад, рад викендом и рад у сменама',
        'tekst': (UVOD_ZAHTEVA + 'за прековремени рад, рад викендом и рад у сменама за {rod:запосленог|запослену}: '
                  '{zaposleni}, {oj}[[radno_mesto|, на радном месту {radno_mesto}]].\n'
                  'Рад ће се обављати {period}, у поподневним и ноћним сменама.'),
        'trazi_period': True,
    },
    {
        'kod': 'placeno-odsustvo-krv', 'naziv': 'Plaćeno odsustvo — davanje krvi', 'resenje': 'placeno-odsustvo-krv',
        'redosled': 70, 'predmet': 'Захтев за плаћено одсуство ради добровољног давања крви',
        'tekst': ('Молим Вас да одобрите плаћено одсуство у трајању од {radni_dani} радна дана, ради добровољног '
                  'давања крви, за {rod:запосленог|запослену}: {zaposleni}, {oj}.\n'
                  'Одсуство ће се користити {dani} године[[datum_povratka|, а на посао ће се {rod:запослени|запослена} '
                  'јавити {datum_povratka} године]].\n'
                  'У прилогу се доставља потврда Института за трансфузију крви Србије о добровољном давању крви.'),
        'trazi_dane': True, 'trazi_radne_dane': True,
    },
    {
        'kod': 'zamena-odsutnog', 'naziv': 'Imenovanje lica za zamenu', 'resenje': 'zamena-odsutnog', 'redosled': 80,
        'predmet': 'Именовање лица за замену',
        'tekst': ('Поштовани,\n'
                  'Ради организације рада[[razlog|, због {razlog}]], предлажем да послове {poslovi} {period} '
                  'обавља {rod:запослени|запослена} {zaposleni}, {oj}.\n'
                  'Ако сте сагласни са предлогом, молим Вас да одобрите издавање решења.'),
        'trazi_period': True,
        'dodatna_polja': 'poslovi|Poslovi koje zaposleni preuzima (npr. директора Финансија)',
    },
]

DOZVOLE = [
    ('zahtev_list', 'Zahtevi — pregled liste'),
    ('zahtev_detail', 'Zahtevi — pregled pojedinačnog zahteva'),
    ('zahtev_create', 'Zahtevi — unos novog zahteva'),
    ('zahtev_edit', 'Zahtevi — izmena nacrta'),
    ('zahtev_bulk_create', 'Zahtevi — isti zahtev za više zaposlenih'),
    ('zahtev_predlog', 'Zahtevi — predlog teksta iz kadrovske evidencije'),
    ('zahtev_print', 'Zahtevi — štampa'),
    ('zahtev_bulk_print', 'Zahtevi — grupna štampa'),
    ('zahtev_podnesi', 'Zahtevi — podnošenje i zaključavanje teksta'),
    ('zahtev_storniraj', 'Zahtevi — storniranje'),
    ('zahtev_resenje_create', 'Zahtevi — rešenje iz zahteva'),
    ('zahtev_bulk_resenja', 'Zahtevi — rešenja za više zahteva'),
]
ULOGE = ('uprava', 'kadrovi', 'sekretarijat')


def napuni(apps, schema_editor):
    VrstaResenja = apps.get_model('hr', 'VrstaResenja')
    VrstaZahteva = apps.get_model('hr', 'VrstaZahteva')
    db = schema_editor.connection.alias
    podaci = dict(ZAMENA_RESENJE)
    VrstaResenja.objects.using(db).get_or_create(kod=podaci.pop('kod'), defaults=podaci)
    for stavka in ZAHTEVI:
        podaci = dict(stavka)
        kod = podaci.pop('kod')
        podaci['vrsta_resenja'] = VrstaResenja.objects.using(db).filter(kod=podaci.pop('resenje')).first()
        VrstaZahteva.objects.using(db).get_or_create(kod=kod, defaults=podaci)


def dodaj_dozvole(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    Role = apps.get_model('fleet', 'Role')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    db = schema_editor.connection.alias
    uloge = list(Role.objects.using(db).filter(slug__in=ULOGE))
    for kod, naziv in DOZVOLE:
        dozvola, _ = Permission.objects.using(db).get_or_create(code='hr:' + kod, defaults={'label': naziv})
        for uloga in uloge:
            RolePermission.objects.using(db).get_or_create(role_id=uloga.pk, permission_id=dozvola.pk)


class Migration(migrations.Migration):
    dependencies = [('hr', '0016_zahtevi')]
    operations = [migrations.RunPython(napuni, migrations.RunPython.noop),
                  migrations.RunPython(dodaj_dozvole, migrations.RunPython.noop)]
