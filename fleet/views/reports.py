from django.shortcuts import render

from core.mixins import role_permission_required

from core.exporting import dataframe_xlsx_response, rows_to_xlsx_response

from ..forms.reports import PutnickaFilterForm
from ..report_exports import report_xlsx_response
from ..support.fuel_reports import (
    SUPPLIER_NIS,
    SUPPLIER_OMV,
    VEHICLE_TYPE_PASSENGER,
    VEHICLE_TYPE_TRUCK,
    fuel_job_code_report,
    omv_faktura_sef,
    omv_fakture,
    period_fakture,
    poslednji_fakturisani_period,
    supplier_label,
    ukupno,
    vehicle_type_label,
)
from ..support.report_helpers import get_data_from_secondary_db
from ..support.report_queries import (
    KASKO_RATE_SQL,
    MAGACIN_SQL,
    OTPIS_SQL,
    PO_DOBAVLJACIMA_SQL,
    TAHOGRAF_PARTNERI_SQL,
    TROSKOVI_SVI_SQL,
    TRO_GORIVO_MESEC_SQL,
    TRO_PARKING_SQL,
    TRO_PRACENJA_VOZILA_SQL,
    TRO_ZARADE_SQL,
)


def reports_index(request):
    sections = {
        "Vozni park": [
            {"name": "Potrošnja", "url": "fuel_transactions_list"},
            {"name": "Polise", "url": "policy_list"},
            {"name": "Popravke van IMS", "url": "service_transaction_list"},
            {"name": "Popravke u IMS", "url": "requisition_list"},
            {"name": "Lizing i najam", "url": "lease_list"},
        ],
        "Finansije": [
            {"name": "Gorivo IMS — meseci, centri i šifre posla", "url": "fleet_fuel_report", "description": "Vrsta proizvoda, period, raspored i pojedinačna točenja."},
            {"name": "Kontrola faktura goriva — SEF, transakcije i knjiženje", "url": "fuel_invoice_control", "description": "NIS i OMV fakture prema transakcijama i proknjiženom trošku po šifri posla."},
            {"name": "Potrosnja goriva po sifri posla - OMV putnicka", "url": "fuel_job_code_omv_putnicka"},
            {"name": "Potrosnja goriva po sifri posla - OMV teretna", "url": "fuel_job_code_omv_teretna"},
            {"name": "Potrosnja goriva po sifri posla - NIS putnicka", "url": "fuel_job_code_nis_putnicka"},
            {"name": "Potrosnja goriva po sifri posla - NIS teretna", "url": "fuel_job_code_nis_teretna"},
        ],
        "Osiguranje": [
            {"name": "Kasko — vozila starija od 7 godina", "url": "casco_report", "description": "Izbor po godištu, bez uslova vrednosti, sa Excel izvozom."},
            {"name": "Auto osiguranje — vlasništvo IMS", "url": "owned_insurance_report", "description": "Podaci o vozilima, dokumentima i osnovu raspolaganja."},
        ],
        "Garaža": [
            {"name": "Trenutno stanje u magacinu", "url": "magacin"},
            {"name": "Spisak otpisanih vozila", "url": "otpis"},
        ],
        "Uprava": [
            {"name": "Knjiženi troškovi goriva po mesecima", "url": "tro_gorivo_mesec", "description": "Postojeći računovodstveni pregled, odvojen od točenja."},
            {"name": "Pregled ukupnih troskova, pa po kontima, pa po centrima, po mesecima", "url": "troskovi_svi"},
            {"name": "Troskovi pracenja vozila", "url": "tro_pracenja_vozila"},
            {"name": "Troskovi tahografa", "url": "troskovi_tahograf"},
            {"name": "Troskovi parkinga", "url": "tro_parking"},
            {"name": "Pregled najvecih dobavljaca usluga", "url": "po_dobavljacima"},
        ],
        "Nabavka i delovi": [
            {"name": "Kupljeni delovi — AutoDeki / dobavljač", "url": "supplier_parts_report", "description": "Stavke faktura i robna evidencija iz Nabavke."},
        ],
    }

    icons = {
        'fuel_transactions_list': 'gas-station', 'fleet_fuel_report': 'gas-station',
        'policy_list': 'shield-check', 'service_transaction_list': 'wrench', 'requisition_list': 'tools',
        'lease_list': 'bank', 'casco_report': 'shield-car', 'owned_insurance_report': 'car',
        'supplier_parts_report': 'cart', 'magacin': 'package-variant', 'otpis': 'car-off',
        'tro_gorivo_mesec': 'calendar', 'fuel_invoice_control': 'file-compare', 'troskovi_svi': 'cash-multiple', 'tro_pracenja_vozila': 'map-marker',
        'troskovi_tahograf': 'speedometer', 'tro_parking': 'parking', 'po_dobavljacima': 'store',
    }
    for reports in sections.values():
        for report in reports:
            report['icon'] = icons.get(report['url'], 'chart-bar')
    return render(request, "fleet/reports_index.html", {"sections": sections})


def _secondary_report_data(query, form, filter_query, cast_params=False):
    query, params = filter_query(query, form, cast_params=cast_params)
    return get_data_from_secondary_db(query, "default", params=params)


def _render_secondary_report(request, *, form, query, filter_query, template_name, title, export_filename, export_sheet):
    data = _secondary_report_data(query, form, filter_query)

    if "export" in request.GET:
        return dataframe_xlsx_response(data, export_filename, export_sheet)

    return render(
        request,
        template_name,
        {
            "data": data,
            "form": form,
            "title": title,
        },
    )


def _export_secondary_report(*, form, query, filter_query, export_spec):
    data = _secondary_report_data(query, form, filter_query, cast_params=True)
    return report_xlsx_response(export_spec, data)


FUEL_JOB_CODE_EXPORT_HEADERS = [
    "Dobavljac",
    "Tip vozila",
    "Sifra posla",
    "Naziv sifre posla",
    "Godina",
    "Mesec",
    "Polovina",
    "Broj transakcija",
    "Kolicina",
    "Bruto",
    "Neto",
]


def _fuel_job_code_export_rows(rows):
    rows = list(rows)
    zbir = ukupno(rows)
    yield from _fuel_job_code_export_data(rows)
    yield ["UKUPNO", "", "", "", "", "", "", zbir["broj_transakcija"], zbir["kolicina"], zbir["bruto"], zbir["neto"]]


def _fuel_job_code_export_data(rows):
    for row in rows:
        yield [
            row["supplier"],
            row["tipvozila"],
            row["sifpos"],
            row["naziv_sifre_posla"],
            row["godina"],
            row["mesec"],
            row["polovina"],
            row["broj_transakcija"],
            row["kolicina"],
            row["bruto"],
            row["neto"],
        ]


def _render_fuel_job_code_report(request, *, supplier, vehicle_type):
    # Bez izabranih filtera: poslednji period za koji je izdata faktura (od 07.10.2026.).
    filteri = request.GET if any(request.GET.get(k) for k in ("godina", "mesec", "polovina", "faktura")) else         {**request.GET.dict(), **poslednji_fakturisani_period(supplier, vehicle_type)}
    period = None
    if supplier == SUPPLIER_OMV and (filteri.get("faktura") or "").strip():
        # Izabrana faktura: filter pokazuje njenu godinu, mesec i polovinu.
        period = period_fakture(filteri["faktura"].strip())
        if period:
            filteri = {**(filteri.dict() if hasattr(filteri, "dict") else filteri),
                       **{k: period[k] for k in ("godina", "mesec", "polovina")}}
    form = PutnickaFilterForm(filteri)
    selected_sifpos = (request.GET.get("sifpos") or "").strip()
    data, detail_rows = fuel_job_code_report(
        form,
        supplier=supplier,
        vehicle_type=vehicle_type,
        sifpos=selected_sifpos,
    )
    title = f"{supplier_label(supplier)} {vehicle_type_label(vehicle_type)} - potrosnja goriva po sifri posla"
    faktura = (filteri.get("faktura") or "").strip() if supplier == SUPPLIER_OMV else ""
    if faktura:
        title = f"OMV faktura {faktura} - raspodela po sifri posla"

    if request.GET.get("export") == "pdf":
        from core.izvoz_pdf import tabela_pdf_response
        redovi = list(_fuel_job_code_export_rows(data))
        opis = f"Faktura {faktura} · " if faktura else ""
        opis += " · ".join(f"{form.fields[k].label}: {form.data.get(k)}" for k in ("godina", "mesec", "polovina") if form.data.get(k))
        return tabela_pdf_response(f"{supplier}_{vehicle_type}_gorivo_po_sifri_posla.pdf", title, FUEL_JOB_CODE_EXPORT_HEADERS,
                                   redovi[:-1], ukupno=redovi[-1], podnaslov=opis, sekcija="Vozni park · Gorivo")
    if "export" in request.GET:
        return rows_to_xlsx_response(
            f"{supplier}_{vehicle_type}_gorivo_po_sifri_posla.xlsx",
            "Gorivo po sifri posla",
            FUEL_JOB_CODE_EXPORT_HEADERS,
            _fuel_job_code_export_rows(data),
        )

    return render(
        request,
        "fleet/reports/fuel_job_code.html",
        {
            "data": data,
            "detail_rows": detail_rows,
            "selected_sifpos": selected_sifpos,
            "form": form,
            "title": title,
            "supplier_label": supplier_label(supplier),
            "vehicle_type_label": vehicle_type_label(vehicle_type),
            "ukupno": ukupno(data),
            "detalj_ukupno": ukupno(detail_rows) if detail_rows else None,
            # OMV: izbor fakture i poređenje sa SEF-om (od 07.10.2026.).
            "omv_fakture": omv_fakture(request.GET.get("godina")) if supplier == SUPPLIER_OMV else [],
            "podrazumevani_period": not any(request.GET.get(k) for k in ("godina", "mesec", "polovina", "faktura")),
            "period_fakture": period,
            "faktura": faktura,
            "faktura_sef": omv_faktura_sef(faktura) if faktura else None,
        },
    )


@role_permission_required()  # prikazuje knjiženje iz Finansija
def fuel_invoice_control_view(request):
    """Kontrola faktura goriva: SEF ↔ transakcije ↔ knjiženje (od 07.10.2026.)."""
    from decimal import Decimal

    from django.utils import timezone

    from ..support.fuel_invoices import kontrola_faktura, sr_iznos

    from finansije.sef_models import SefFaktura

    # Bez izbora: mesec poslednje fakture goriva na SEF-u (od 07.10.2026.).
    poslednja = (SefFaktura.objects.filter(smer="ulazna", partner_pib__in=["101987198", "104052135"])
                 .exclude(datum_prometa__isnull=True).order_by("-datum_prometa").values_list("datum_prometa", flat=True).first())
    prethodni = poslednja or (timezone.localdate().replace(day=1) - timezone.timedelta(days=1))
    form = PutnickaFilterForm(request.GET or {"godina": str(prethodni.year), "mesec": str(prethodni.month)})
    godina, mesec = prethodni.year, prethodni.month
    if form.is_valid() and form.cleaned_data.get("godina") and form.cleaned_data.get("mesec"):
        godina, mesec = int(form.cleaned_data["godina"]), int(form.cleaned_data["mesec"])
    redovi = kontrola_faktura(godina, mesec)
    ukupno = {k: sum((r[k] for r in redovi), Decimal("0.00"))
              for k in ("sef_bruto", "transakcije_bruto", "razlika_transakcija", "knjizeno_trosak", "knjizeno_pdv")}
    if request.GET.get("export") in ("xlsx", "pdf"):
        zaglavlje = ["Dobavljač", "Faktura / period", "Fakture", "Kartica", "SEF bruto", "Transakcije bruto", "Razlika",
                     "Proknjiženo 51300", "PDV 27000", "Status"]
        tabela = []
        for r in redovi:
            tabela.append([r["dobavljac"], r["oznaka"], ", ".join(f.broj for f in r["fakture"]), r["kartica"], r["sef_bruto"],
                           r["transakcije_bruto"], r["razlika_transakcija"], r["knjizeno_trosak"] if r["knjizeno_stavki"] else None,
                           r["knjizeno_pdv"] if r["knjizeno_stavki"] else None, "; ".join(p for _, p in r["status"])])
            for s in r["razlike_sifara"]:
                tabela.append(["", f"   šifra {s['sifra']}", "", "", None, None, None, s["knjizeno"], None,
                               f"po transakcijama {sr_iznos(s['ocekivano'])}, razlika {sr_iznos(s['razlika'], True)}"])
        zbir = ["UKUPNO", "", "", "", ukupno["sef_bruto"], ukupno["transakcije_bruto"], ukupno["razlika_transakcija"],
                ukupno["knjizeno_trosak"], ukupno["knjizeno_pdv"], ""]
        naziv = f"kontrola_faktura_goriva_{godina}_{mesec:02d}"
        if request.GET["export"] == "pdf":
            from core.izvoz_pdf import tabela_pdf_response
            return tabela_pdf_response(f"{naziv}.pdf", f"Kontrola faktura goriva — {mesec:02d}/{godina}", zaglavlje, tabela,
                                       ukupno=zbir, podnaslov="SEF ↔ transakcije ↔ knjiženje (51300 / 27000) po šifri posla",
                                       sekcija="Vozni park · Gorivo")
        return rows_to_xlsx_response(f"{naziv}.xlsx", "Kontrola faktura", zaglavlje, tabela + [zbir])
    return render(request, "fleet/reports/fuel_invoice_control.html", {
        "form": form, "redovi": redovi, "ukupno": ukupno,
        "title": f"Kontrola faktura goriva — {mesec:02d}/{godina}",
    })


def fuel_job_code_omv_putnicka_view(request):
    return _render_fuel_job_code_report(request, supplier=SUPPLIER_OMV, vehicle_type=VEHICLE_TYPE_PASSENGER)


def fuel_job_code_omv_teretna_view(request):
    return _render_fuel_job_code_report(request, supplier=SUPPLIER_OMV, vehicle_type=VEHICLE_TYPE_TRUCK)


def fuel_job_code_nis_putnicka_view(request):
    return _render_fuel_job_code_report(request, supplier=SUPPLIER_NIS, vehicle_type=VEHICLE_TYPE_PASSENGER)


def fuel_job_code_nis_teretna_view(request):
    return _render_fuel_job_code_report(request, supplier=SUPPLIER_NIS, vehicle_type=VEHICLE_TYPE_TRUCK)


def _render_simple_secondary_report(request, *, query, db_alias, template_name):
    data = get_data_from_secondary_db(query, db_alias)
    return render(request, template_name, {"data": data})


def kasko_rate_view(request):
    return _render_simple_secondary_report(
        request,
        query=KASKO_RATE_SQL,
        db_alias="default",
        template_name="fleet/reports/kasko_rate.html",
    )


def magacin_view(request):
    return _render_simple_secondary_report(
        request,
        query=MAGACIN_SQL,
        db_alias="server_db",
        template_name="fleet/reports/magacin.html",
    )


def otpis_view(request):
    return _render_simple_secondary_report(
        request,
        query=OTPIS_SQL,
        db_alias="server_db",
        template_name="fleet/reports/otpis.html",
    )


def tro_gorivo_mesec_view(request):
    return _render_simple_secondary_report(
        request,
        query=TRO_GORIVO_MESEC_SQL,
        db_alias="server_db",
        template_name="fleet/reports/tro_gorivo_mesec.html",
    )


def troskovi_svi_view(request):
    return _render_simple_secondary_report(
        request,
        query=TROSKOVI_SVI_SQL,
        db_alias="server_db",
        template_name="fleet/reports/troskovi_svi.html",
    )


def tro_pracenja_vozila_view(request):
    return _render_simple_secondary_report(
        request,
        query=TRO_PRACENJA_VOZILA_SQL,
        db_alias="server_db",
        template_name="fleet/reports/tro_pracenja_vozila.html",
    )


def tahograf_partneri_view(request):
    return _render_simple_secondary_report(
        request,
        query=TAHOGRAF_PARTNERI_SQL,
        db_alias="server_db",
        template_name="fleet/reports/tro_tahografa.html",
    )


def tro_zarade_view(request):
    return _render_simple_secondary_report(
        request,
        query=TRO_ZARADE_SQL,
        db_alias="server_db",
        template_name="fleet/reports/tro_zarade.html",
    )


def tro_parking_view(request):
    return _render_simple_secondary_report(
        request,
        query=TRO_PARKING_SQL,
        db_alias="server_db",
        template_name="fleet/reports/tro_parking.html",
    )


def po_dobavljacima_view(request):
    return _render_simple_secondary_report(
        request,
        query=PO_DOBAVLJACIMA_SQL,
        db_alias="server_db",
        template_name="fleet/reports/po_dobavljacima.html",
    )
