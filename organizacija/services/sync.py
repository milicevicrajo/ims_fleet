"""Nova sinhronizacija organizacije — radi paralelno sa starom, ne umesto nje.

Stara (`fleet.tasks.fetch_job_codes`, 01:30) i dalje puni `OrganizationalUnit` iz
`dbo.v_organizationalunit` i ostaje merodavna. Nova (01:40) iz istog izvora — tabele `posao`,
koju Finansije svakog sata preuzimaju u `FinanceJob` — osvezava registar, povezuje jedinice
Flote sa cvorovima, popunjava `org_node` i poredi staro i novo.

Nova sinhronizacija **ne pise** ni u jednu tabelu stare organizacije. Ako padne, stara radi
kao i do sada; ako se iskljuci, nista u modulima se ne menja.
"""

from datetime import timedelta

from django.utils import timezone

from organizacija.models import LegacyOrgLink, OrgNode, OrgNodeVersion
from organizacija.services import activity
from organizacija.services import classification as klas
from organizacija.services import flota
from organizacija.services.importer import DEFAULT_COMPANY, run_import
from organizacija.services.report import job_code_to_node, node_center_map

# Finansije osvezavaju sifarnik svakog sata; stariji od ovoga znaci da registar kasni za izvorom.
SVEZINA_IZVORA = timedelta(hours=26)


def sinhronizuj(company=DEFAULT_COMPANY):
    """Jedan prolaz nove sinhronizacije. Vraca recnik sa svim delovima."""
    svezina = svezina_izvora(company)
    run = run_import(company=company)
    # Sifra bez prometa u poslednjih 12 meseci je neaktivna, sa prometom aktivna (odluka 21.09.2026.);
    # nove sifre iz izvora tako ne ostaju aktivne samo zato sto ih izvor tako oznacava.
    aktivnost = activity.apply_reviews(company)
    veze = flota.povezi(company, modul="sve")
    kontrola = uporedi_jedinice(company)
    izvestaj = flota.uporedni_izvestaj(company)
    nabavka = flota.uporedni_izvestaj(company, modul="nabavka")
    finansije = flota.uporedni_izvestaj(company, modul="finansije")
    potrazivanja = flota.uporedni_izvestaj(company, modul="potrazivanja")
    return {"svezina": svezina, "run": run, "aktivnost": aktivnost, "veze": veze, "kontrola": kontrola, "izvestaj": izvestaj,
            "izvestaj_nabavke": nabavka, "izvestaj_finansija": finansije, "izvestaj_potrazivanja": potrazivanja}


def svezina_izvora(company=DEFAULT_COMPANY):
    """Kada je sifarnik poslova poslednji put uspesno preuzet iz izvora."""
    from finansije.models import SyncRun

    poslednja = (
        SyncRun.objects.filter(company=company, status="success").order_by("-finished_at")
        .values_list("finished_at", flat=True).first()
    )
    return {
        "poslednja": poslednja,
        "kasni": poslednja is None or timezone.now() - poslednja > SVEZINA_IZVORA,
    }


def uporedi_jedinice(company=DEFAULT_COMPANY, primera=10):
    """Stara organizacija naspram nove, jedinica po jedinica.

    Za svaku `OrganizationalUnit` (rezultat stare sinhronizacije): ima li cvor u registru i
    da li je centar isti. Za svaki posao u registru: postoji li i u staroj organizaciji.
    """
    from core.models import OrganizationalUnit
    from finansije.models import FinanceJob

    po_sifri = job_code_to_node(company)
    po_jedinici = dict(
        LegacyOrgLink.objects.filter(legacy_label=LegacyOrgLink.LEGACY_FLEET_UNIT).values_list("legacy_id", "node_id")
    )
    centri = node_center_map(company)
    u_sifarniku = {klas.normalize_code(code) for code in FinanceJob.objects.filter(company=company).values_list("code", flat=True)}

    rezultat = {
        "jedinica": 0, "povezano": 0, "isti_centar": 0,
        "razlika_centra": [], "van_stabla": [], "van_sifarnika": [], "samo_u_registru": [], "tehnicke": [],
    }
    stare_sifre = set()
    for pk, code, center in OrganizationalUnit.objects.order_by("code").values_list("pk", "code", "center"):
        sifra = klas.normalize_code(code)
        stare_sifre.add(sifra)
        rezultat["jedinica"] += 1
        cvor = po_jedinici.get(pk) or po_sifri.get(sifra)
        if cvor is None:
            if klas.je_tehnicka(sifra):
                rezultat["tehnicke"].append(sifra)
            else:
                (rezultat["van_stabla"] if sifra in u_sifarniku else rezultat["van_sifarnika"]).append(sifra)
            continue
        rezultat["povezano"] += 1
        stari, novi = (center or "").strip(), centri.get(cvor, "")
        if stari == novi:
            rezultat["isti_centar"] += 1
        else:
            rezultat["razlika_centra"].append({"sifra": sifra, "staro": stari, "novo": novi})

    for version in OrgNodeVersion.objects.filter(
        valid_to__isnull=True, node__company=company, node__level=OrgNode.LEVEL_JOB
    ).values_list("full_code", flat=True):
        if version not in stare_sifre:
            rezultat["samo_u_registru"].append(version)
    rezultat["primera"] = primera
    return rezultat


def poruka(rezultat):
    """Kratak izvestaj za istoriju zadataka (staje u 500 znakova)."""
    run, kontrola, izvestaj = rezultat["run"], rezultat["kontrola"], rezultat["izvestaj"]
    veze = rezultat["veze"]
    izmena = sum(z["postavljeno"] + z["promenjeno"] + z["ocisceno"] for z in veze)
    bez_para = sum(z["nerazreseno"] for z in veze)
    razlike = sum(d["razlika_zapisa"] for d in izvestaj["delovi"])
    van_stabla = sum(d["van_stabla"] for d in izvestaj["delovi"])
    delovi = [
        f"Registar: novih cvorova {run.nodes_created}, novih verzija {run.versions_created}, "
        f"za razresenje {run.unresolved}.",
        f"Aktivnost po obrtu: izmenjenih {rezultat['aktivnost']['versions_changed']}.",
        f"OJ stara/nova: {kontrola['povezano']}/{kontrola['jedinica']} povezano, "
        f"razlika centra {len(kontrola['razlika_centra'])}, van stabla {len(kontrola['van_stabla'])}.",
        f"Moduli: izmenjenih veza {izmena}, bez para {bez_para}.",
        "Uporedni izvestaj Flote: " + ("PROLAZI." if izvestaj["prolazi"] else
                                       f"NE PROLAZI ({razlike} razlika, od toga van stabla {van_stabla})."),
    ]
    for kljuc, naziv in (("izvestaj_nabavke", "Nabavke"), ("izvestaj_finansija", "Finansija"),
                         ("izvestaj_potrazivanja", "Potrazivanja")):
        deo = rezultat.get(kljuc)
        if deo is not None:
            razlike_m = sum(d["razlika_zapisa"] for d in deo["delovi"])
            delovi.append(f"{naziv}: " + ("PROLAZI." if deo["prolazi"] else f"NE PROLAZI ({razlike_m} razlika)."))
    if rezultat["svezina"]["kasni"]:
        delovi.insert(0, "UPOZORENJE: sifarnik iz Finansija nije osvezen u poslednjih 26 h.")
    return " ".join(delovi)
