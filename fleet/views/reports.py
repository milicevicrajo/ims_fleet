from django.shortcuts import render

from core.exporting import dataframe_xlsx_response

from ..forms.reports import OMVPutnickaFilterForm, PutnickaFilterForm
from ..support.report_helpers import (
    date_period_filtered_query,
    get_data_from_secondary_db,
    report_period_filtered_query,
)
from ..report_exports import (
    NIS_PUTNICKA_EXPORT,
    NIS_TERETNA_EXPORT,
    OMV_PUTNICKA_EXPORT,
    OMV_TERETNA_EXPORT,
    report_xlsx_response,
)
from ..support.report_queries import (
    KASKO_RATE_SQL,
    MAGACIN_SQL,
    NIS_PUTNICKA_SQL,
    NIS_TERETNA_SQL,
    OMV_PUTNICKA_SQL,
    OMV_TERETNA_SQL,
    OTPIS_SQL,
    PO_DOBAVLJACIMA_SQL,
    POTRAZIVANJE_DDOR_SQL,
    TAHOGRAF_PARTNERI_SQL,
    TROSKOVI_SVI_SQL,
    TRO_GORIVO_MESEC_SQL,
    TRO_PARKING_SQL,
    TRO_PRACENJA_VOZILA_SQL,
    TRO_ZARADE_SQL,
    ZATVOREN_PUTNI_SQL,
)


def reports_index(request):
    """Pocetna stranica za izvestaje sa linkovima."""
    sections = {
        "Finansije": [
            {"name": "Spisak vozila po siframa posla", "url": "vehicle_list"},
            {"name": "Pregled potrosnje goriva po siframa posla - OMV putnicka", "url": "omv_putnicka"},
            {"name": "Pregled potrosnje goriva po siframa posla - OMV teretna", "url": "omv_teretna"},
            {"name": "Pregled potrosnje goriva po siframa posla - NIS putnicka", "url": "nis_putnicka"},
            {"name": "Pregled potrosnje goriva po siframa posla - NIS teretna", "url": "nis_teretna"},
        ],
        "Centri": [
            {"name": "Zatvoreni putni nalozi", "url": "zatvoreni_putni"},
        ],
        "Garaza": [
            {"name": "Trenutno stanje u magacinu", "url": "magacin"},
            {"name": "Spisak otpisanih vozila", "url": "otpis"},
        ],
        "Uprava": [
            {"name": "Promet goriva po mesecima", "url": "tro_gorivo_mesec"},
            {"name": "Pregled ukupnih troskova, pa po kontima, pa po centrima, po mesecima ", "url": "troskovi_svi"},
            {"name": "Troskovi pracenja vozila", "url": "tro_pracenja_vozila"},
            {"name": "Troskovi tahografa ", "url": "troskovi_tahograf"},
            {"name": "Troskovi parkinga", "url": "tro_parking"},
            {"name": "Pregled Potrazivanja od osiguranja", "url": "potrazivanje_ddor"},
            {"name": "Pregled Najvecih Dobavljaca Usluga", "url": "po_dobavljacima"},
        ],
    }

    return render(request, "fleet/reports_index.html", {"sections": sections})


def _secondary_report_data(query, form, filter_query, cast_params=False):
    query, params = filter_query(query, form, cast_params=cast_params)
    return get_data_from_secondary_db(query, "test_db", params=params)


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


def _render_simple_secondary_report(request, *, query, db_alias, template_name):
    data = get_data_from_secondary_db(query, db_alias)
    return render(request, template_name, {"data": data})


def omv_putnicka_view(request):
    form = OMVPutnickaFilterForm(request.GET or None)
    return _render_secondary_report(
        request,
        form=form,
        query=OMV_PUTNICKA_SQL,
        filter_query=report_period_filtered_query,
        template_name="fleet/reports/omv_putnicka.html",
        title="OMV Putnicka vozila",
        export_filename="omv_putnicka.xlsx",
        export_sheet="OMV Putnicka",
    )


def export_omv_putnicka_excel(request):
    form = PutnickaFilterForm(request.GET or None)
    return _export_secondary_report(
        form=form,
        query=OMV_PUTNICKA_SQL,
        filter_query=report_period_filtered_query,
        export_spec=OMV_PUTNICKA_EXPORT,
    )


def nis_putnicka_view(request):
    form = PutnickaFilterForm(request.GET or None)
    return _render_secondary_report(
        request,
        form=form,
        query=NIS_PUTNICKA_SQL,
        filter_query=report_period_filtered_query,
        template_name="fleet/reports/nis_putnicka.html",
        title="NIS Putnicka vozila",
        export_filename="nis_putnicka.xlsx",
        export_sheet="NIS Putnicka",
    )


def export_nis_putnicka_excel(request):
    form = PutnickaFilterForm(request.GET or None)
    return _export_secondary_report(
        form=form,
        query=NIS_PUTNICKA_SQL,
        filter_query=report_period_filtered_query,
        export_spec=NIS_PUTNICKA_EXPORT,
    )


def nis_teretna_view(request):
    form = PutnickaFilterForm(request.GET or None)
    return _render_secondary_report(
        request,
        form=form,
        query=NIS_TERETNA_SQL,
        filter_query=date_period_filtered_query,
        template_name="fleet/reports/nis_teretna.html",
        title="NIS Teretna vozila",
        export_filename="nis_teretna.xlsx",
        export_sheet="NIS Teretna",
    )


def export_nis_teretna_excel(request):
    form = PutnickaFilterForm(request.GET or None)
    return _export_secondary_report(
        form=form,
        query=NIS_TERETNA_SQL,
        filter_query=date_period_filtered_query,
        export_spec=NIS_TERETNA_EXPORT,
    )


def omv_teretna_view(request):
    form = PutnickaFilterForm(request.GET or None)
    return _render_secondary_report(
        request,
        form=form,
        query=OMV_TERETNA_SQL,
        filter_query=report_period_filtered_query,
        template_name="fleet/reports/omv_teretna.html",
        title="OMV Teretna vozila",
        export_filename="omv_teretna.xlsx",
        export_sheet="OMV Teretna",
    )


def export_omv_teretna_excel(request):
    form = PutnickaFilterForm(request.GET or None)
    return _export_secondary_report(
        form=form,
        query=OMV_TERETNA_SQL,
        filter_query=report_period_filtered_query,
        export_spec=OMV_TERETNA_EXPORT,
    )


def kasko_rate_view(request):
    return _render_simple_secondary_report(
        request,
        query=KASKO_RATE_SQL,
        db_alias="test_db",
        template_name="fleet/reports/kasko_rate.html",
    )


def zatvoren_putni_view(request):
    return _render_simple_secondary_report(
        request,
        query=ZATVOREN_PUTNI_SQL,
        db_alias="server_db",
        template_name="fleet/reports/zatvoreni_putni.html",
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
