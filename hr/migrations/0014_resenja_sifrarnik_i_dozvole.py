"""Početni šifrarnik vrsta rešenja i dozvole za ekran rešenja.

Tekstovi su prepisani iz Word obrazaca kadrovske službe i zato stoje ćirilicom.
Rešenje koje se štampa latinicom nastaje preslovljavanjem, pa se tekst ne unosi dvaput.
"""
from django.db import migrations

POUKA = ('Правна поука: Против овог решења {rod:запослени|запослена} има право да покрене спор код '
         'надлежног суда, ради заштите својих права, у року од 60 дана од дана достављања.')
DOSTAVLJENO = ('{rod:именованом|именованој}\n'
               'референту обрачуна\n'
               'Ц {centar}\n'
               'реф.за кадровске послове')
UVOD = ('{zaposleni} {rod:запослен|запослена} у Институту за испитивање материјала а.д. Београд, '
        '{rod:распоређен|распоређена} у {oj}')

VRSTE = [
    {
        'kod': 'nocni-rad', 'naziv': 'Noćni rad', 'podnaslov': 'ЗА НОЋНИ РАД', 'redosled': 10,
        'pravni_osnov': 'На основу члана 62., 192. и 193. Закона о раду, члана 41. Правилника о раду '
                        'Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ', {rod:дужан|дужна} је да ради ноћу {period}.\n'
            'За време ноћног рада {rod:запослени|запослена} има право на увећану зараду у складу са '
            'Законом о раду и Правилником о раду Института ИМС.'),
        'obrazlozenje': (
            'Дана {zahtev_datum} поднет је захтев бр. {zahtev_broj} за издавање решења за ноћни рад, '
            'којим се тражи ангажовање {rod:запосленог|запослене}, те је на основу изнетог одлучено '
            'као у диспозитиву.\n[[napomena|{napomena}]]'),
        'trazi_period': True,
    },
    {
        'kod': 'prekovremeni-rad', 'naziv': 'Prekovremeni rad', 'podnaslov': 'О ПРЕКОВРЕМЕНОМ РАДУ', 'redosled': 20,
        'pravni_osnov': 'На основу члана 53., 192. и 193. Закона о раду, члана 14., 15. и 41. Правилника '
                        'о раду Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ', {rod:дужан|дужна} је да ради {period}, са радним временом дужим од пуног радног '
            'времена, што се доказује потписаном радном листом.\n'
            'За време рада дужег од пуног радног времена {rod:именовани|именована} има право на увећану '
            'зараду у складу са Законом о раду и Правилником о раду Института ИМС.'),
        'obrazlozenje': ('На основу захтева бр. {zahtev_broj} достављеног дана {zahtev_datum}, одлучено је '
                         'као у диспозитиву решења.\n[[napomena|{napomena}]]'),
        'trazi_dane': True,
    },
    {
        'kod': 'prekovremeni-i-vikend', 'naziv': 'Prekovremeni rad i rad vikendom',
        'podnaslov': 'ЗА ПРЕКОВРЕМЕНИ РАД И РАД ВИКЕНДОМ', 'redosled': 30,
        'pravni_osnov': 'На основу члана 53., 192. и 193. Закона о раду, као и члана 14., 15., 16. и 41. '
                        'Правилника о раду Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ', {rod:дужан|дужна} је да ради {period} са радним временом дужим од пуног радног '
            'времена и викендом.\n'
            'За време прековременог рада и рада викендом {rod:запослени|запослена} има право на увећану '
            'зараду у складу са Законом о раду и Правилником о раду Института ИМС а.д., што се доказује '
            'потписаном радном листом.'),
        'obrazlozenje': ('На основу захтева бр. {zahtev_broj} достављеног дана {zahtev_datum}, одлучено је '
                         'као у диспозитиву решења.\n[[napomena|{napomena}]]'),
        'trazi_period': True,
    },
    {
        'kod': 'praznik', 'naziv': 'Rad na državni i verski praznik',
        'podnaslov': 'ЗА РАД НА ДРЖАВНИ И ВЕРСКИ ПРАЗНИК', 'redosled': 40,
        'pravni_osnov': 'На основу члана 67., 192. и 193. Закона о раду, као и члана 16. и 41. Правилника '
                        'о раду Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ', {rod:дужан|дужна} је да ради'
            '[[dani_drzavni| {dani_drzavni} на дан државног празника]]'
            '[[dani_verski| и {dani_verski} на дан верског празника]]'
            '[[dani_vikend| и {dani_vikend} за дане викенда]].\n'
            'За рад на дан празника {rod:запослени|запослена} има право на увећану зараду у складу са '
            'Законом о раду и Правилником о раду Института ИМС а.д., што се доказује потписаном радном листом.'),
        'obrazlozenje': ('На основу захтева бр. {zahtev_broj} достављеног дана {zahtev_datum}, одлучено је '
                         'као у диспозитиву решења.\n[[napomena|{napomena}]]'),
        'trazi_dane': True,
    },
    {
        'kod': 'vikend', 'naziv': 'Rad vikendom', 'podnaslov': 'ЗА РАД ВИКЕНДОМ', 'redosled': 50,
        'pravni_osnov': 'На основу члана 67., 192. и 193. Закона о раду и члана 16. Правилника о раду '
                        'Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ', {rod:дужан|дужна} је да ради за дане викенда, {dani} године, без ноћног рада.\n'
            'За време рада викендом {rod:запослени|запослена} има право на увећану зараду у складу са '
            'Законом о раду и Правилником о раду Института ИМС а.д.'),
        'obrazlozenje': ('Због потребе посла којим се тражи ангажовање {rod:запосленог|запослене}, а на основу '
                         'захтева бр. {zahtev_broj} од {zahtev_datum}, одлучено је као у диспозитиву.\n'
                         '[[napomena|{napomena}]]'),
        'trazi_dane': True,
    },
    {
        'kod': 'prekovremeni-vikend-smene', 'naziv': 'Prekovremeni rad, rad vikendom i rad u smenama',
        'podnaslov': 'ЗА ПРЕКОВРЕМЕНИ РАД, РАД ВИКЕНДОМ И РАД У СМЕНАМА', 'redosled': 60,
        'pravni_osnov': 'На основу члана 53., 55., 192. и 193. Закона о раду, члана 14., 16. и 41. '
                        'Правилника о раду Института ИМС, доносим',
        'dispozitiv': (
            UVOD + ' на радном месту {radno_mesto}, {rod:дужан|дужна} је да ради {period}, у поподневним '
            'и ноћним сменама.\n'
            '{rod:Запослени|Запослена} је {rod:дужан|дужна} да ради у периоду наведеном у тачки 1.\n'
            'За време прековременог рада, рада викендом и рада у сменама, {rod:запослени|запослена} има '
            'право на увећану зараду у складу са Законом о раду и Правилником о раду Института ИМС а.д.'),
        'obrazlozenje': ('Дана {zahtev_datum} поднет је захтев бр. {zahtev_broj} за издавање решења за рад.\n'
                         '[[napomena|{napomena}]]\n'
                         'На основу изнетог, одлучено је као у диспозитиву.'),
        'trazi_period': True,
    },
    {
        'kod': 'placeno-odsustvo-krv', 'naziv': 'Plaćeno odsustvo — davanje krvi',
        'naslov': 'Р Е Ш Е Њ Е', 'podnaslov': 'о плаћеном одсуству запосленог (е)', 'redosled': 70,
        'pravni_osnov': 'На основу члана 192. и 193. Закона о раду, а у вези члана 77. Закона о раду, као и '
                        'члана 19. Правилника о раду Института ИМС, доносим',
        'dispozitiv': (
            '{zaposleni} {rod:запосленом|запосленој} у Институту за испитивање материјала а.д., Београд, '
            '{rod:распоређеном|распоређеној} на рад у {oj}, одобрава се ПЛАЋЕНО ОДСУСТВО у трајању од '
            '{radni_dani} радна дана.\n'
            'Плаћено одсуство {rod:запослени|запослена} ће користити {dani} године.\n'
            '{rod:Запослени|Запослена} је {rod:дужан|дужна} да се јави на посао {datum_povratka} године.'),
        'obrazlozenje': (
            '{rod:Запослени|Запослена} је дана {zahtev_datum} {rod:поднео|поднела} потврду Института за '
            'трансфузију крви Србије, да {rod:му|јој} се одобри плаћено одсуство ради добровољног давања крви.\n'
            'Чланом 77. Закона о раду {rod:запосленом|запосленој} је загарантовано право на плаћено одсуство '
            'са рада у трајању од два радна дана за случај добровољног давања крви, рачунајући и дан давања крви.\n'
            '[[napomena|{napomena}]]\n'
            'На основу напред наведеног донето је решење као у изреци.'),
        'pravna_pouka': ('Поука о правном леку: Против овог решења {rod:запослени|запослена} има право да покрене '
                         'спор код надлежног суда ради заштите својих права у року од 60 дана од дана достављања решења.'),
        'dostavljeno': ('{rod:запосленом|запосленој}\nреференту обрачуна\nЦ {centar}\nу досије запосленог'),
        'trazi_dane': True, 'trazi_radne_dane': True,
    },
]

DOZVOLE = [
    ('resenje_list', 'Rešenja — pregled liste'),
    ('resenje_detail', 'Rešenja — pregled pojedinačnog rešenja'),
    ('resenje_create', 'Rešenja — unos novog rešenja'),
    ('resenje_edit', 'Rešenja — izmena nacrta'),
    ('resenje_obrisi', 'Rešenja — brisanje nacrta'),
    ('resenje_predlog', 'Rešenja — predlog teksta iz kadrovske evidencije'),
    ('resenje_izdaj', 'Rešenja — izdavanje i zaključavanje teksta'),
    ('resenje_storniraj', 'Rešenja — storniranje izdatog rešenja'),
    ('resenje_print', 'Rešenja — štampa'),
    ('resenje_bulk_create', 'Rešenja — grupno izdavanje'),
    ('resenje_bulk_print', 'Rešenja — grupna štampa'),
    ('resenje_catalog', 'Rešenja — šifrarnik vrsta i potpisnika'),
    ('resenje_catalog_create', 'Rešenja — unos u šifrarnik'),
    ('resenje_catalog_edit', 'Rešenja — izmena šifrarnika'),
    ('resenje_view_all', 'Rešenja — pregled svih centara'),
]
SAMO_UPRAVA = {'resenje_catalog', 'resenje_catalog_create', 'resenje_catalog_edit', 'resenje_view_all'}


def napuni(apps, schema_editor):
    VrstaResenja = apps.get_model('hr', 'VrstaResenja')
    db = schema_editor.connection.alias
    for stavka in VRSTE:
        podaci = dict(stavka)
        kod = podaci.pop('kod')
        podaci.setdefault('naslov', 'РЕШЕЊЕ')
        podaci.setdefault('pravna_pouka', POUKA)
        podaci.setdefault('dostavljeno', DOSTAVLJENO)
        VrstaResenja.objects.using(db).get_or_create(kod=kod, defaults=podaci)


def dodaj_dozvole(apps, schema_editor):
    Permission = apps.get_model('fleet', 'PermissionCode')
    Role = apps.get_model('fleet', 'Role')
    RolePermission = apps.get_model('fleet', 'RolePermission')
    db = schema_editor.connection.alias
    uprava = Role.objects.using(db).filter(slug='uprava').first()
    kadrovik, _ = Role.objects.using(db).get_or_create(slug='kadrovik-resenja', defaults={
        'name': 'Kadrovik — rešenja',
        'description': 'Unos, izdavanje i štampa rešenja za zaposlene iz dozvoljenih centara.'})
    for kod, naziv in DOZVOLE:
        dozvola, _ = Permission.objects.using(db).get_or_create(code='hr:' + kod, defaults={'label': naziv})
        if uprava:
            RolePermission.objects.using(db).get_or_create(role_id=uprava.pk, permission_id=dozvola.pk)
        if kod not in SAMO_UPRAVA:
            RolePermission.objects.using(db).get_or_create(role_id=kadrovik.pk, permission_id=dozvola.pk)


class Migration(migrations.Migration):
    dependencies = [('hr', '0013_vrstaresenja_potpisnik_resenje_resenjedan_and_more'),
                    ('fleet', '0080_employee_full_name_cyrillic')]
    operations = [migrations.RunPython(napuni, migrations.RunPython.noop),
                  migrations.RunPython(dodaj_dozvole, migrations.RunPython.noop)]
