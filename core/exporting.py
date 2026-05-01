from django.http import HttpResponse


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
