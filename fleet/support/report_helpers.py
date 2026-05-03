from django.db import connections


def get_data_from_secondary_db(query, db_alias, params=None):
    with connections[db_alias].cursor() as cursor:
        cursor.execute(query, params or [])
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _append_report_filters(query, filters):
    if filters:
        return query + " " + " ".join(filters)
    return query


def report_period_filtered_query(query, form, cast_params=False):
    filters = []
    params = []

    if form.is_valid():
        for field_name, condition in (
            ("godina", "AND godina = %s"),
            ("mesec", "AND mesec = %s"),
            ("polovina", "AND polovina = %s"),
        ):
            value = form.cleaned_data.get(field_name)
            if value:
                filters.append(condition)
                params.append(int(value) if cast_params else value)

    return _append_report_filters(query, filters), params


def date_period_filtered_query(query, form, cast_params=False):
    filters = []
    params = []

    if form.is_valid():
        godina = form.cleaned_data.get("godina")
        mesec = form.cleaned_data.get("mesec")
        polovina = form.cleaned_data.get("polovina")

        if godina:
            filters.append("AND YEAR(datum) = %s")
            params.append(int(godina) if cast_params else godina)

        if mesec:
            filters.append("AND MONTH(datum) = %s")
            params.append(int(mesec) if cast_params else mesec)

        if polovina:
            polovina_value = int(polovina)
            if polovina_value == 1:
                filters.append("AND DAY(datum) <= 15")
            elif polovina_value == 2:
                filters.append("AND DAY(datum) > 15")

    return _append_report_filters(query, filters), params
