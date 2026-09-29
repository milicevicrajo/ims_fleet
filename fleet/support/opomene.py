"""Opomene vozačima za nepravilno unetu kilometražu pri točenju (od 29.09.2026.).

Tok (noćni posao posle preuzimanja NIS i OMV, i dugme „Proveri sada”):
1. `otkrij()` prolazi točenja goriva (bez AdBlue-a, OMV bez duplikata i odjeka — `fleet/support/fuel.py`)
   iz poslednjih `DANA_UNAZAD` dana i za svako nepravilno pravi jednu `OpomenaGoriva`. Poredi se sa
   prethodnim ispravnim točenjem istog vozila (NIS i OMV zajedno, po vremenu). Točenje van
   rezervoara se preskače.
2. Vozač: putni nalog vozila za taj dan (nije storniran), a ako ga nema — zaduženje vozila (`vozac_tocenja`).
3. `posalji()` šalje pripremljene opomene kanalom iz `settings.OPOMENE_GORIVA["kanal"]`:
   "" = slanje isključeno (opomene se samo pripremaju i vide na ekranu), "email" = e-mail korisniku
   vezanom za vozača. Jednom vozaču ide jedna zbirna poruka po slanju.
Izvorne transakcije NIS/OMV se ne menjaju.
"""
import datetime
from collections import defaultdict

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from fleet.models import OpomenaGoriva, PutniNalog, TrafficCard, TransactionNIS, TransactionOMV, VehicleTravelOrder
from fleet.support.fuel import filter_nis_travel_order_fuel_queryset, filter_omv_travel_order_fuel_queryset
from fleet.support.garaza import NAJMANJI_DOZVOLJEN_SKOK_KM, NAJVISE_KM_DNEVNO

DANA_UNAZAD = 14
# Prethodno točenje se traži u ovom periodu pre prozora provere.
DANA_ZA_PRETHODNO = 120
NAJDUZI_NALOG_DANA = 60


def podesavanja():
    return {"kanal": "", "posiljalac": getattr(settings, "DEFAULT_FROM_EMAIL", "flota@institutims.rs"),
            **getattr(settings, "OPOMENE_GORIVA", {})}


def _dan(vreme):
    if isinstance(vreme, datetime.datetime):
        return timezone.localtime(vreme).date() if timezone.is_aware(vreme) else vreme.date()
    return vreme


def _km(vrednost):
    try:
        broj = int(vrednost or 0)
    except (TypeError, ValueError):
        return 0
    return broj if broj > 0 else 0


def tocenja(od, do):
    """Točenja goriva od-do kao rečnici, sortirana po vozilu i vremenu."""
    redovi = []
    nis = filter_nis_travel_order_fuel_queryset(TransactionNIS.objects.filter(
        vehicle__isnull=False, datum_transakcije__date__gte=od, datum_transakcije__date__lte=do))
    for t in nis.values("pk", "vehicle_id", "datum_transakcije", "kilometraza", "benzinska_stanica", "kolicina",
                        "sipanje_van_rezervoara"):
        redovi.append(dict(izvor=OpomenaGoriva.Izvor.NIS, id=t["pk"], vozilo=t["vehicle_id"], vreme=t["datum_transakcije"],
                           km=_km(t["kilometraza"]), stanica=t["benzinska_stanica"] or "", kolicina=t["kolicina"],
                           van_rezervoara=bool(t["sipanje_van_rezervoara"])))
    omv = filter_omv_travel_order_fuel_queryset(TransactionOMV.objects.filter(
        vehicle__isnull=False, transaction_date__date__gte=od, transaction_date__date__lte=do))
    for t in omv.values("pk", "vehicle_id", "transaction_date", "mileage", "corrected_mileage", "site_town", "quantity"):
        km = _km(t["corrected_mileage"]) or _km(t["mileage"])
        redovi.append(dict(izvor=OpomenaGoriva.Izvor.OMV, id=t["pk"], vozilo=t["vehicle_id"], vreme=t["transaction_date"],
                           km=km, stanica=t["site_town"] or "", kolicina=t["quantity"], van_rezervoara=False))
    redovi.sort(key=lambda r: (r["vozilo"], r["vreme"], r["id"]))
    return redovi


def nepravilnost(tocenje, prethodno):
    """Vrsta nepravilnosti ili None. `prethodno` je poslednje ranije ispravno točenje istog vozila."""
    if tocenje["van_rezervoara"]:
        return None
    if not tocenje["km"]:
        return OpomenaGoriva.Vrsta.BEZ_KM
    if prethodno is None:
        return None
    dana = max((_dan(tocenje["vreme"]) - _dan(prethodno["vreme"])).days, 1)
    if tocenje["km"] < prethodno["km"]:
        return OpomenaGoriva.Vrsta.MANJA
    if tocenje["km"] - prethodno["km"] > max(NAJMANJI_DOZVOLJEN_SKOK_KM, dana * NAJVISE_KM_DNEVNO):
        return OpomenaGoriva.Vrsta.SKOK
    if tocenje["km"] == prethodno["km"] and _dan(tocenje["vreme"]) != _dan(prethodno["vreme"]):
        return OpomenaGoriva.Vrsta.ISTA
    return None


def vozac_tocenja(vozilo_id, dan):
    """(zaposleni, odakle) — putni nalog tog dana, a ako ga nema, zaduženje vozila; inače (None, "")."""
    nalozi = (PutniNalog.objects.select_related("employee")
              .filter(vehicle_id=vozilo_id, storniran=False, employee__isnull=False, travel_date__lte=dan,
                      travel_date__gte=dan - datetime.timedelta(days=NAJDUZI_NALOG_DANA))
              .order_by("-travel_date", "-pk"))
    for n in nalozi:
        if dan < n.travel_date + datetime.timedelta(days=max(n.number_of_days or 1, 1)):
            broj = f" {n.order_number}" if n.order_number else ""
            return n.employee, f"putni nalog{broj} od {n.travel_date:%d.%m.%Y.}"
    zaduzenje = (VehicleTravelOrder.objects.select_related("employee")
                 .filter(vehicle_id=vozilo_id, employee__isnull=False, created_at__lte=dan)
                 .exclude(closed_at__lt=dan).order_by("-created_at", "-pk").first())
    if zaduzenje:
        return zaduzenje.employee, f"zaduženje vozila od {zaduzenje.created_at:%d.%m.%Y.}"
    return None, ""


def _km_tekst(vrednost):
    return f"{vrednost or 0:,}".replace(",", ".")


def tekst_opomene(o, tablica):
    vreme = timezone.localtime(o.vreme_tocenja) if timezone.is_aware(o.vreme_tocenja) else o.vreme_tocenja
    tocenje = f"točenje {vreme:%d.%m.%Y. u %H:%M}" + (f", {o.stanica}" if o.stanica else "") + f", vozilo {tablica or '—'}"
    if o.kolicina:
        tocenje += f", {o.kolicina:.2f} l".replace(".", ",")
    prethodno = f"{o.prethodni_datum:%d.%m.%Y.}" if o.prethodni_datum else ""
    if o.vrsta == OpomenaGoriva.Vrsta.BEZ_KM:
        opis = "kilometraža nije uneta"
    elif o.vrsta == OpomenaGoriva.Vrsta.MANJA:
        opis = (f"uneta kilometraža {_km_tekst(o.uneta_km)} km je manja od prethodnog točenja "
                f"({_km_tekst(o.prethodna_km)} km, {prethodno})")
    elif o.vrsta == OpomenaGoriva.Vrsta.SKOK:
        opis = (f"uneta kilometraža {_km_tekst(o.uneta_km)} km je za {_km_tekst((o.uneta_km or 0) - (o.prethodna_km or 0))} km "
                f"veća od prethodnog točenja ({prethodno}) — verovatno greška u unosu")
    else:
        opis = f"uneta je ista kilometraža kao pri prethodnom točenju ({prethodno})"
    return f"IMS Flota — {tocenje}: {opis}. Molimo da pri svakom točenju unesete tačno stanje brojila."


def otkrij(*, danas=None, dana_unazad=DANA_UNAZAD):
    """Pravi opomene za nepravilna točenja iz poslednjih `dana_unazad` dana. Vraća broj novih po vrsti."""
    danas = danas or timezone.localdate()
    od = danas - datetime.timedelta(days=dana_unazad)
    sva = tocenja(od - datetime.timedelta(days=DANA_ZA_PRETHODNO), danas)
    postojece = set(OpomenaGoriva.objects.filter(vreme_tocenja__date__gte=od - datetime.timedelta(days=1))
                    .values_list("izvor", "transakcija_id"))
    tablice = {}
    for vozilo_id, tablica in (TrafficCard.objects.order_by("vehicle_id", "-issue_date", "-pk")
                               .values_list("vehicle_id", "registration_number")):
        tablice.setdefault(vozilo_id, tablica)
    nove, brojevi, prethodno = [], defaultdict(int), {}
    for t in sva:
        prethodno_vozila = prethodno.get(t["vozilo"])
        vrsta = nepravilnost(t, prethodno_vozila)
        if vrsta and _dan(t["vreme"]) >= od and (t["izvor"], t["id"]) not in postojece:
            vozac, odakle = vozac_tocenja(t["vozilo"], _dan(t["vreme"]))
            o = OpomenaGoriva(
                izvor=t["izvor"], transakcija_id=t["id"], vehicle_id=t["vozilo"], vreme_tocenja=t["vreme"],
                stanica=t["stanica"][:255], kolicina=t["kolicina"], vrsta=vrsta, uneta_km=t["km"] or None,
                prethodna_km=prethodno_vozila["km"] if prethodno_vozila else None,
                prethodni_datum=_dan(prethodno_vozila["vreme"]) if prethodno_vozila else None,
                employee=vozac, vozac_izvor=odakle,
                status=OpomenaGoriva.Status.ZA_SLANJE if vozac else OpomenaGoriva.Status.BEZ_VOZACA,
            )
            o.poruka = tekst_opomene(o, tablice.get(t["vozilo"], ""))
            nove.append(o)
            brojevi[str(vrsta)] += 1
        # Samo ispravno točenje sa kilometražom postaje „prethodno” — pogrešno ne kvari poređenje sledećeg.
        if t["km"] and not t["van_rezervoara"] and vrsta is None:
            prethodno[t["vozilo"]] = t
    # Postojeće opomene su već isključene gore; SQL Server ne podržava ignore_conflicts, a dvostruko
    # pokretanje sprečava zaključavanje zadatka (i jedinstveni ključ izvor + točenje).
    with transaction.atomic():
        OpomenaGoriva.objects.bulk_create(nove, batch_size=500)
    return {"nove": len(nove), **brojevi}


def posalji(*, kanal=None):
    """Šalje pripremljene opomene; vraća (poslato, bez_kontakta). Isključen kanal ne šalje ništa."""
    kanal = podesavanja()["kanal"] if kanal is None else kanal
    if not kanal:
        return 0, 0
    if kanal != "email":
        raise ValueError(f"Nepoznat kanal opomena: {kanal}")
    from core.models import CustomUser

    po_vozacu = defaultdict(list)
    for o in OpomenaGoriva.objects.filter(status=OpomenaGoriva.Status.ZA_SLANJE).order_by("vreme_tocenja"):
        po_vozacu[o.employee_id].append(o)
    poslato = bez_kontakta = 0
    for vozac_id, opomene in po_vozacu.items():
        korisnik = CustomUser.objects.filter(employee_id=vozac_id, is_active=True).exclude(email="").first()
        ids = [o.pk for o in opomene]
        if korisnik is None:
            OpomenaGoriva.objects.filter(pk__in=ids).update(status=OpomenaGoriva.Status.BEZ_KONTAKTA)
            bez_kontakta += len(ids)
            continue
        try:
            send_mail("IMS Flota — kilometraža pri točenju", "\n\n".join(o.poruka for o in opomene),
                      podesavanja()["posiljalac"], [korisnik.email])
        except Exception as exc:  # greška servera pošte ne sme da zaustavi ostale vozače
            OpomenaGoriva.objects.filter(pk__in=ids).update(status=OpomenaGoriva.Status.GRESKA, kanal=kanal, greska=str(exc)[:500])
            continue
        OpomenaGoriva.objects.filter(pk__in=ids).update(status=OpomenaGoriva.Status.POSLATA, kanal=kanal, poslato=timezone.now())
        poslato += len(ids)
    return poslato, bez_kontakta


def poruka_zadatka(rezultat, poslato, bez_kontakta):
    kanal = podesavanja()["kanal"] or "isključeno"
    return (f"Opomene za gorivo: novih {rezultat['nove']} (bez km {rezultat.get('bez_km', 0)}, manja {rezultat.get('manja', 0)}, "
            f"skok {rezultat.get('skok', 0)}, ista {rezultat.get('ista', 0)}); slanje ({kanal}): poslato {poslato}, "
            f"bez kontakta {bez_kontakta}")
