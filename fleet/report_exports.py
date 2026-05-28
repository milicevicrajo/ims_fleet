from dataclasses import dataclass, field

from core.exporting import rows_to_xlsx_response


@dataclass(frozen=True)
class ReportExportSpec:
    filename: str
    sheet_name: str
    headers: list[str]
    fields: list[str]
    formatters: dict[str, object] = field(default_factory=dict)


def report_export_rows(data, spec):
    for row in data:
        yield [
            spec.formatters[field](row[field]) if field in spec.formatters else row[field]
            for field in spec.fields
        ]


def report_xlsx_response(spec, data):
    return rows_to_xlsx_response(
        spec.filename,
        spec.sheet_name,
        spec.headers,
        report_export_rows(data, spec),
    )


OMV_PUTNICKA_EXPORT = ReportExportSpec(
    filename="omv_putnicka.xlsx",
    sheet_name="OMV Putnička",
    headers=["Šifra pos", "Godina", "Mesec", "Tip vozila", "Polovina", "Bruto", "Neto"],
    fields=["sifpos", "godina", "mesec", "tipvozila", "polovina", "bruto", "neto"],
)

NIS_PUTNICKA_EXPORT = ReportExportSpec(
    filename="nis_putnicka.xlsx",
    sheet_name="NIS Putnička",
    headers=["Tip vozila", "Šifra pos", "Godina", "Mesec", "Polovina", "Bruto", "Neto"],
    fields=["tipvozila", "sifpos", "godina", "mesec", "polovina", "bruto", "neto"],
)

NIS_TERETNA_EXPORT = ReportExportSpec(
    filename="nis_teretna.xlsx",
    sheet_name="NIS Teretna",
    headers=["Tip vozila", "Sifra pos", "Godina", "Mesec", "Polovina", "Bruto", "Neto"],
    fields=["tipvozila", "sifpos", "godina", "mesec", "polovina", "bruto", "neto"],
)

OMV_TERETNA_EXPORT = ReportExportSpec(
    filename="omv_teretna.xlsx",
    sheet_name="OMV Teretna",
    headers=["Tip vozila", "Šifra pos", "Godina", "Mesec", "Polovina", "Bruto", "Neto"],
    fields=["tipvozila", "sifpos", "godina", "mesec", "polovina", "bruto", "neto"],
)
