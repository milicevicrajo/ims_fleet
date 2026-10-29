"""Bankarske grupe i povezana lica po spisku direktora („Banke – povezana lica”, 29.10.2026.)."""
from django.db import migrations

GRUPE = [
    ('Intesa Sanpaolo', 'Intesa Sanpaolo (Italija)'),
    ('UniCredit', 'UniCredit (Italija)'),
    ('Raiffeisen', 'Raiffeisen Bank International (Austrija)'),
    ('OTP', 'OTP Bank (Mađarska)'),
    ('NLB', 'NLB d.d. Ljubljana (Slovenija)'),
    ('Erste', 'Erste Group (Austrija)'),
    ('AIK', 'AIK / MK Group (Srbija)'),
    ('Alta', 'Alta Group (Srbija)'),
    ('Eurobank', 'Eurobank (Grčka)'),
    ('Addiko', 'Addiko Bank AG (Austrija)'),
    ('ProCredit', 'ProCredit Holding (Nemačka)'),
    ('Halkbank', 'Halkbank (Turska)'),
    ('Država Srbija', 'Republika Srbija'),
    ('API', 'AZRS Invest'),
    ('Bank of China', 'Bank of China (Kina)'),
    ('3 Banka', '—'),
    ('Mirabank', 'Arroyo Holding (UAE)'),
    ('Adriatic Bank', '—'),
    ('PPF', 'PPF (Češka)'),
]
# (grupa, vrsta, naziv, maticni broj, PIB, vlasnistvo / napomena, izvor MB, pripadnost grupi potvrdjena)
LICA = [
    ('Intesa Sanpaolo', 'Banka', 'Banca Intesa akcionarsko društvo Beograd', '07759231', '100001159', 'Intesa Holding International S.A. 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Intesa Sanpaolo', 'Lizing', 'Intesa Leasing d.o.o. Beograd', '17492713', '103023875', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Intesa Sanpaolo', 'DZU investicionih fondova', 'Intesa Invest a.d. Beograd', '21360490', '110538710', '', 'KHoV – registar DZU', 'Po nazivu (proveriti vlasnika u APR)'),
    ('UniCredit', 'Banka', 'UniCredit Bank Srbija a.d. Beograd', '17324918', '100000170', 'UniCredit SpA 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('UniCredit', 'Lizing', 'UniCredit Leasing Srbija d.o.o. Beograd', '17556797', '103374714', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('UniCredit', 'DZU investicionih fondova', 'UniCredit Invest a.d. Beograd', '22110616', '115062853', 'Fondovi onemarkets UC Invest', 'KHoV – registar DZU', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Raiffeisen', 'Banka', 'Raiffeisen banka a.d. Beograd', '17335600', '100000299', 'Raiffeisen SEE Region Holding 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Raiffeisen', 'Lizing', 'Raiffeisen Leasing d.o.o. Beograd', '17457284', '102624786', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Raiffeisen', 'DZU investicionih fondova', 'Raiffeisen Invest a.d. Beograd', '20302402', '105053883', '', 'KHoV – registar DZU', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Raiffeisen', 'DZU dobrovoljnih penzijskih fondova', 'Raiffeisen Future a.d. Beograd', '20223243', '104714052', 'Raiffeisen banka 100%', 'NBS – DZU DPF', 'Da – NBS podaci o vlasniku'),
    ('OTP', 'Banka', 'OTP banka Srbija a.d. Novi Sad', '08603537', '100584604', 'OTP Bank PLC 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('OTP', 'Lizing', 'OTP Leasing Srbija d.o.o. Beograd', '20116161', '104219657', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('OTP', 'Osiguranje (život)', 'OTP Osiguranje a.d.o. Beograd', '20561211', '106237954', 'OTP banka Srbija kvalifikovani imalac', 'NBS – registar osiguranja', 'Da – NBS podaci o vlasniku'),
    ('OTP', 'DZU investicionih fondova', 'OTP Invest a.d. Beograd', '20338407', '105191747', '', 'KHoV – registar DZU', 'Po nazivu (proveriti vlasnika u APR)'),
    ('NLB', 'Banka', 'NLB Banka AD Beograd (ranije NLB Komercijalna banka)', '07737068', '100001931', 'NLB d.d. Ljubljana 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('NLB', 'Lizing', 'NLB Lease&Go Leasing d.o.o. Beograd', '17518844', '103156991', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('NLB', 'DZU investicionih fondova', 'NLB Fondovi a.d. Beograd', '20379758', '105428701', '', 'KHoV – registar DZU', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Erste', 'Banka', 'Erste Bank a.d. Novi Sad', '08063818', '101626723', 'Erste Group Bank 74%, Steiermärkische 26%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Erste', 'Lizing', 'Erste Leasing d.o.o. Beograd', '17488104', '102941384', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('AIK', 'Banka', 'AikBank a.d. Beograd', '06876366', '100618836', 'Ranije AIK banka (promena imena 28.3.2025)', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('AIK', 'Lizing', 'AIK Leasing d.o.o. Beograd', '17352679', '100043571', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Alta', 'Banka', 'ALTA banka a.d. Beograd', '07074433', '100001829', 'ALTA GROUP DOO 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Alta', 'Lizing', 'Alta Leasing d.o.o. Beograd', '17481495', '102843789', '', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Eurobank', 'Lizing', 'ERB Leasing a.d. Beograd – u likvidaciji', '20170859', '104466014', 'Eurobank Direktna nije više na NBS spisku banaka', 'NBS – davaoci fin. lizinga', 'Po nazivu (proveriti vlasnika u APR)'),
    ('Addiko', 'Banka', 'Addiko Bank a.d. Beograd', '07726716', '100228215', 'Addiko Bank AG 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('ProCredit', 'Banka', 'ProCredit Bank a.d. Beograd', '17335677', '100000215', 'ProCredit Holding AG 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Halkbank', 'Banka', 'Halkbank a.d. Beograd', '07601093', '100895809', 'Turkish Halk Bank 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Država Srbija', 'Banka', 'Banka Poštanska štedionica a.d. Beograd', '07004893', '100002549', 'RS 78,58%, Pošta 13,27%, Telekom 7,47%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Država Srbija', 'Banka', 'Srpska banka a.d. Beograd', '07092288', '100000387', 'RS 76,69%, Jugoimport SDPR 23,31%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Država Srbija', 'Osiguranje', 'Kompanija Dunav osiguranje a.d.o. Beograd', '07046898', '100001958', 'Republika Srbija 76,70%', 'NBS – registar osiguranja', 'Da – NBS podaci o vlasniku'),
    ('Država Srbija', 'Reosiguranje', 'Dunav Re a.d.o. Beograd', '07046901', '100001327', 'Dunav osiguranje 100%', 'NBS – registar osiguranja', 'Da – NBS podaci o vlasniku'),
    ('Država Srbija', 'DZU dobrovoljnih penzijskih fondova', 'Dunav DZU DPF a.d. Beograd', '17411233', '100057074', '', 'NBS – DZU DPF', 'Po nazivu (proveriti vlasnika u APR)'),
    ('API', 'Banka', 'API Bank a.d. Beograd', '20439866', '105701111', 'AZRS INVEST d.o.o. 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Bank of China', 'Banka', 'Bank of China Srbija a.d. Beograd', '21251640', '109837136', 'Bank of China (Europe) S.A. 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('3 Banka', 'Banka', '3 Banka a.d. Novi Sad', '08761132', '101643574', 'Raspršeno vlasništvo (GLS 19,83%...)', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Mirabank', 'Banka', 'Mirabank a.d. Beograd', '21080608', '108851504', 'Arroyo Holding RSC 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('Adriatic Bank', 'Banka', 'Adriatic Bank a.d. Beograd', '07534183', '100003148', 'Alexander Shnaider 100%', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
    ('PPF', 'Banka', 'Yettel Bank a.d. Beograd', '17138669', '100000049', 'PPF Financial Holdings', 'NBS – spisak banaka', 'Da – NBS podaci o vlasniku'),
]


def upisi(apps, schema_editor):
    Grupa = apps.get_model("finansije", "BankarskaGrupa")
    Lice = apps.get_model("finansije", "PovezanoLiceBanke")
    grupe = {}
    for naziv, maticna in GRUPE:
        grupe[naziv], _ = Grupa.objects.get_or_create(naziv=naziv, defaults={"maticna_grupa": "" if maticna == "—" else maticna})
    for grupa, vrsta, naziv, mb, pib, vlasnistvo, izvor, potvrda in LICA:
        Lice.objects.get_or_create(pib=pib, defaults=dict(grupa=grupe[grupa], vrsta=vrsta, naziv=naziv, maticni_broj=mb,
                                                          vlasnistvo=vlasnistvo, izvor=izvor, potvrda=potvrda))


class Migration(migrations.Migration):
    dependencies = [("finansije", "0010_banke_nbs_grupe")]
    operations = [migrations.RunPython(upisi, migrations.RunPython.noop)]
