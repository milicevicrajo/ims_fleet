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
