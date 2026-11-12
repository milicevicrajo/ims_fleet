from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def attachment_response(filename, content_type, quoted=False):
    response = HttpResponse(content_type=content_type)
    disposition_filename = f'"{filename}"' if quoted else filename
    response["Content-Disposition"] = f"attachment; filename={disposition_filename}"
    return response


def csv_attachment_response(filename, charset="utf-8", quoted=True):
    content_type = "text/csv"
    if charset:
        content_type = f"{content_type}; charset={charset}"
    return attachment_response(filename, content_type, quoted=quoted)


def xlsx_attachment_response(filename, quoted=False):
    return attachment_response(filename, XLSX_CONTENT_TYPE, quoted=quoted)


def workbook_response(workbook, filename, quoted=False):
    response = xlsx_attachment_response(filename, quoted=quoted)
    workbook.save(response)
    return response


def create_xlsx_workbook(sheet_title=None):
    workbook = Workbook()
    worksheet = workbook.active
    if sheet_title:
        worksheet.title = sheet_title
    return workbook, worksheet


def style_header_row(worksheet, row_number=1):
    header_font = Font(bold=True)
    for cell in worksheet[row_number]:
        cell.font = header_font


def set_column_widths(worksheet, widths):
    for col_num, width in enumerate(widths, start=1):
        worksheet.column_dimensions[get_column_letter(col_num)].width = width


def set_uniform_column_width(worksheet, width):
    set_column_widths(worksheet, [width] * worksheet.max_column)


def autofit_columns(worksheet, min_width=10, max_width=70, padding=2):
    for col_num, column_cells in enumerate(worksheet.columns, start=1):
        max_len = max(
            (len(str(cell.value)) if cell.value is not None else 0)
            for cell in column_cells
        )
        worksheet.column_dimensions[get_column_letter(col_num)].width = min(
            max(max_len + padding, min_width),
            max_width,
        )


def rows_to_xlsx_response(
    filename,
    sheet_title,
    headers,
    rows,
    quoted=False,
    bold_header=False,
    auto_width=False,
    fixed_column_width=None,
):
    workbook, worksheet = create_xlsx_workbook(sheet_title)
    if headers:
        worksheet.append(headers)

    for row in rows:
        worksheet.append(row)

    if headers and bold_header:
        style_header_row(worksheet)

    if fixed_column_width is not None:
        set_uniform_column_width(worksheet, fixed_column_width)

    if auto_width:
        autofit_columns(worksheet)

    return workbook_response(workbook, filename, quoted=quoted)


def dataframe_xlsx_response(data, filename, sheet_name, quoted=False, engine="openpyxl"):
    import pandas as pd

    dataframe = data if hasattr(data, "to_excel") else pd.DataFrame(data)
    response = xlsx_attachment_response(filename, quoted=quoted)
    with pd.ExcelWriter(response, engine=engine) as writer:
        dataframe.to_excel(writer, index=False, sheet_name=sheet_name)
    return response


def tabela_xlsx_response(filename, sheet_title, headers, rows, *, naslov=None, podnaslov=None, iznosi=(), ukupno=None,
                         podredovi=None, quoted=True):
    """Uređena Excel tabela (od 09.11.2026.): naslov i podnaslov, podebljano zaglavlje sa bojom, zamrznuto zaglavlje,
    filter, iznosi sa dve decimale i razdvajanjem hiljada, širine kolona i podebljan red UKUPNO.

    `iznosi` su indeksi kolona (od 0) sa brojevima u formatu 1.234,56; `podredovi(red)` vraća True za red koji je
    pojašnjenje prethodnog (sivo, kurziv)."""
    from openpyxl.styles import Alignment, Border, PatternFill, Side

    plava, linija = "14395B", Side(style="thin", color="D7DCE5")
    okvir = Border(left=linija, right=linija, top=linija, bottom=linija)
    workbook, ws = create_xlsx_workbook(sheet_title)
    red = 1
    if naslov:
        ws.cell(red, 1, naslov).font = Font(bold=True, size=13, color=plava)
        red += 1
    if podnaslov:
        ws.cell(red, 1, podnaslov).font = Font(italic=True, size=9, color="475569")
        red += 1
    if red > 1:
        red += 1
    zaglavlje = red
    for k, naziv in enumerate(headers, start=1):
        c = ws.cell(red, k, naziv)
        c.font, c.fill, c.border = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor=plava), okvir
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    iznosi = set(iznosi)

    def upisi(vrednosti, stil=None):
        nonlocal red
        red += 1
        for k, v in enumerate(vrednosti, start=1):
            c = ws.cell(red, k, float(v) if k - 1 in iznosi and v is not None and not isinstance(v, str) else v)
            c.border = okvir
            if k - 1 in iznosi:
                c.number_format = "#,##0.00"
            if stil == "ukupno":
                c.font, c.fill = Font(bold=True), PatternFill("solid", fgColor="E8F0FB")
            elif stil == "pod":
                c.font = Font(italic=True, color="64748B")

    for vrednosti in rows:
        upisi(vrednosti, "pod" if podredovi and podredovi(vrednosti) else None)
    poslednji_podatak = red
    if ukupno is not None:
        upisi(ukupno, "ukupno")
    ws.freeze_panes = ws.cell(zaglavlje + 1, 1)
    if poslednji_podatak > zaglavlje:
        ws.auto_filter.ref = f"A{zaglavlje}:{get_column_letter(len(headers))}{poslednji_podatak}"
    for k, naziv in enumerate(headers, start=1):
        duzine = [len(str(naziv))] + [len(f"{c.value:,.2f}") if isinstance(c.value, float) else len(str(c.value or ""))
                                      for c in ws[get_column_letter(k)][zaglavlje:]]
        ws.column_dimensions[get_column_letter(k)].width = min(max(max(duzine) + 2, 9), 60)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    return workbook_response(workbook, filename, quoted=quoted)
