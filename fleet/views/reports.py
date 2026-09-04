from django.shortcuts import render

from core.exporting import dataframe_xlsx_response, rows_to_xlsx_response

from ..forms.reports import PutnickaFilterForm
from ..report_exports import report_xlsx_response
from ..support.fuel_reports import (
    SUPPLIER_NIS,
    SUPPLIER_OMV,
    VEHICLE_TYPE_PASSENGER,
    VEHICLE_TYPE_TRUCK,
    fuel_job_code_report,
    supplier_label,
    vehicle_type_label,
)
from ..support.report_helpers import get_data_from_secondary_db
from ..support.report_queries import (
    KASKO_RATE_SQL,
    MAGACIN_SQL,
    OTPIS_SQL,
    PO_DOBAVLJACIMA_SQL,
    POTRAZIVANJE_DDOR_SQL,
    TAHOGRAF_PARTNERI_SQL,
    TROSKOVI_SVI_SQL,
    TRO_GORIVO_MESEC_SQL,
    TRO_PARKING_SQL,
    TRO_PRACENJA_VOZILA_SQL,
    TRO_ZARADE_SQL,
)


def reports_index(request):
    sections = {
        "Finansije": [
            {"name": "Potrosnja goriva po sifri posla - OMV putnicka", "url": "fuel_job_code_omv_putnicka"},
            {"name": "Potrosnja goriva po sifri posla - OMV teretna", "url": "fuel_job_code_omv_teretna"},
            {"name": "Potrosnja goriva po sifri posla - NIS putnicka", "url": "fuel_job_code_nis_putnicka"},
            {"name": "Potrosnja goriva po sifri posla - NIS teretna", "url": "fuel_job_code_nis_teretna"},
        ],
        "Garaza": [
            {"name": "Trenutno stanje u magacinu", "url": "magacin"},
            {"name": "Spisak otpisanih vozila", "url": "otpis"},
        ],
        "Uprava": [
            {"name": "Promet goriva po mesecima", "url": "tro_gorivo_mesec"},
            {"name": "Pregled ukupnih troskova, pa po kontima, pa po centrima, po mesecima", "url": "troskovi_svi"},
            {"name": "Troskovi pracenja vozila", "url": "tro_pracenja_vozila"},
            {"name": "Troskovi tahografa", "url": "troskovi_tahograf"},
            {"name": "Troskovi parkinga", "url": "tro_parking"},
            {"name": "Pregled potrazivanja od osiguranja", "url": "potrazivanje_ddor"},
            {"name": "Pregled najvecih dobavljaca usluga", "url": "po_dobavljacima"},
        ],
    }

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
    form = PutnickaFilterForm(request.GET or None)
    selected_sifpos = (request.GET.get("sifpos") or "").strip()
    data, detail_rows = fuel_job_code_report(
        form,
        supplier=supplier,
        vehicle_type=vehicle_type,
        sifpos=selected_sifpos,
    )
    title = f"{supplier_label(supplier)} {vehicle_type_label(vehicle_type)} - potrosnja goriva po sifri posla"

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
        },
    )


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


def potrazivanje_ddor_view(request):
    return _render_simple_secondary_report(
        request,
        query=POTRAZIVANJE_DDOR_SQL,
        db_alias="server_db",
        template_name="fleet/reports/potrazivanje_ddor.html",
    )
