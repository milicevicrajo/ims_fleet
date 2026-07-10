import calendar
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal

from django.conf import settings
from django.db import connections


@dataclass(frozen=True)
class ClockEventSummary:
    total: int
    first_event_at: object
    last_event_at: object


@dataclass(frozen=True)
class ClockEvent:
    worker_source_id: int
    employee_code: int
    last_name: str
    first_name: str
    personal_number: str
    event_id: int
    event_time: object
    button: object


@dataclass(frozen=True)
class DailyWorkHours:
    year: int
    month: int
    day: int
    employee_code: int
    organizational_unit: object
    employee_name: str
    hours: int
    minutes: int
    total_hours: Decimal

    @property
    def date(self):
        return date(self.year, self.month, self.day)


@dataclass(frozen=True)
class DailyClockHours:
    date: date
    employee_code: int
    employee_name: str
    total_minutes: int
    pair_count: int
    issue_count: int

    @property
    def hours(self):
        return self.total_minutes // 60

    @property
    def minutes(self):
        return self.total_minutes % 60

    @property
    def total_hours(self):
        return (Decimal(self.total_minutes) / Decimal("60")).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class ClockPairIssue:
    date: date
    employee_code: int
    event_time: object
    button: object
    message: str
    is_problem: bool = True


DEFAULT_CLOCK_BUTTON_DEFINITIONS = {
    "1": "Ulazak 1",
    "2": "Izlazak radnika",
    "3": "Ulazak 2",
    "4": "Sluzbeni izlazak",
    "5": "Ulazak 3",
    "7": "Ulazak u posebnu smenu",
    "11": "Ponistavanje prolaska radnika",
    "12": "Pauza",
}

DEFAULT_ENTRY_BUTTONS = ("1", "3", "5", "7")
DEFAULT_EXIT_BUTTONS = ("2",)
DEFAULT_OFFICIAL_EXIT_BUTTONS = ("4",)
DEFAULT_REVIEW_BUTTONS = ("11", "12")
DEFAULT_OFFICIAL_EXIT_END_TIME = time(16, 0)


def resolve_attendance_db_alias(using=None):
    if using:
        return using
    configured = set(getattr(settings, "DATABASES", {}).keys())
    configured_alias = getattr(settings, "HR_ATTENDANCE_DB_ALIAS", None)
    if configured_alias:
        return configured_alias
    if "default" in configured:
        return "default"
    if "server_db" in configured:
        return "server_db"
    return next(iter(configured))


def month_period(year, month):
    last_day = calendar.monthrange(year, month)[1]
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end, last_day


def _to_int(value):
    if value is None:
        return 0
    return int(value)


def _to_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _fetchone_dict(cursor):
    columns = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(zip(columns, row))


def _fetchall_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _date_param(value):
    return value.strftime("%Y%m%d") if hasattr(value, "strftime") else str(value)


def _linked_server_date_declarations(date_from, date_to):
    return (
        """
        DECLARE @date_from datetime = CONVERT(datetime, %s, 112);
        DECLARE @date_to datetime = CONVERT(datetime, %s, 112);
        """,
        [_date_param(date_from), _date_param(date_to)],
    )


def _employee_filter_sql(employee_code, source_worker_id, employee_alias="a"):
    filters = []
    if employee_code is not None:
        filters.append(f"{employee_alias}.Sifra = @employee_code")
    if source_worker_id is not None:
        filters.append(f"{employee_alias}.ID = @source_worker_id")
    return filters


def _employee_declarations(employee_code=None, source_worker_id=None):
    declarations = []
    params = []
    if employee_code is not None:
        declarations.append("DECLARE @employee_code int = %s;")
        params.append(employee_code)
    if source_worker_id is not None:
        declarations.append("DECLARE @source_worker_id int = %s;")
        params.append(source_worker_id)
    return "\n".join(declarations), params


def get_clock_event_summary(
    *,
    date_from,
    date_to,
    employee_code=None,
    source_worker_id=None,
    using=None,
):
    date_declarations, date_params = _linked_server_date_declarations(date_from, date_to)
    employee_declarations, employee_params = _employee_declarations(employee_code, source_worker_id)
    filters = _employee_filter_sql(employee_code, source_worker_id)
    where = [
        "b.Vreme >= @date_from",
        "b.Vreme < @date_to",
        *filters,
    ]
    query = f"""
        {date_declarations}
        {employee_declarations}
        SELECT
            COUNT(*) AS total,
            MIN(b.Vreme) AS first_event_at,
            MAX(b.Vreme) AS last_event_at
        FROM INFORMATIKA23.ID.dbo.Radnici AS a
        INNER JOIN INFORMATIKA23.ID.dbo.C_Prolasci_Radnika AS b
            ON a.ID = b.Radnik
        WHERE {" AND ".join(where)}
    """
    with connections[resolve_attendance_db_alias(using)].cursor() as cursor:
        cursor.execute(query, [*date_params, *employee_params])
        row = _fetchone_dict(cursor) or {}

    return ClockEventSummary(
        total=_to_int(row.get("total")),
        first_event_at=row.get("first_event_at"),
        last_event_at=row.get("last_event_at"),
    )


def get_clock_events(
    *,
    date_from,
    date_to,
    employee_code=None,
    source_worker_id=None,
    using=None,
):
    date_declarations, date_params = _linked_server_date_declarations(date_from, date_to)
    employee_declarations, employee_params = _employee_declarations(employee_code, source_worker_id)
    filters = _employee_filter_sql(employee_code, source_worker_id)
    where = [
        "b.Vreme >= @date_from",
        "b.Vreme < @date_to",
        *filters,
    ]
    query = f"""
        {date_declarations}
        {employee_declarations}
        SELECT
            a.ID AS worker_source_id,
            a.Sifra AS employee_code,
            a.Prezime AS last_name,
            a.Ime AS first_name,
            a.JMBG AS personal_number,
            b.ID AS event_id,
            b.Vreme AS event_time,
            b.Taster AS button
        FROM INFORMATIKA23.ID.dbo.Radnici AS a
        INNER JOIN INFORMATIKA23.ID.dbo.C_Prolasci_Radnika AS b
            ON a.ID = b.Radnik
        WHERE {" AND ".join(where)}
        ORDER BY b.Vreme, b.ID
    """
    with connections[resolve_attendance_db_alias(using)].cursor() as cursor:
        cursor.execute(query, [*date_params, *employee_params])
        rows = _fetchall_dicts(cursor)

    return [
        ClockEvent(
            worker_source_id=_to_int(row.get("worker_source_id")),
            employee_code=_to_int(row.get("employee_code")),
            last_name=row.get("last_name") or "",
            first_name=row.get("first_name") or "",
            personal_number=row.get("personal_number") or "",
            event_id=_to_int(row.get("event_id")),
            event_time=row.get("event_time"),
            button=row.get("button"),
        )
        for row in rows
    ]


def get_clock_button_definitions(*, using=None):
    query = """
        SELECT ID, Opis
        FROM INFORMATIKA23.ID.dbo.C_Tasteri
        WHERE Tip_Korisnika = N'Radnik'
        ORDER BY ID
    """
    with connections[resolve_attendance_db_alias(using)].cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    definitions = {}
    for button_id, description in rows:
        definitions[_button_key(button_id)] = str(description or "").strip()
    return definitions


def _event_datetime(event_time):
    if isinstance(event_time, datetime):
        return event_time
    if isinstance(event_time, str):
        normalized = event_time.strip().replace("Z", "")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None
    return None


def _button_key(button):
    if button is None:
        return ""
    return str(button).strip()


def _button_description(button, button_definitions):
    return button_definitions.get(_button_key(button)) or f"Taster {button}"


def calculate_daily_hours_from_clock_events(
    events,
    *,
    entry_buttons=DEFAULT_ENTRY_BUTTONS,
    exit_buttons=DEFAULT_EXIT_BUTTONS,
    official_exit_buttons=DEFAULT_OFFICIAL_EXIT_BUTTONS,
    review_buttons=DEFAULT_REVIEW_BUTTONS,
    official_exit_end_time=DEFAULT_OFFICIAL_EXIT_END_TIME,
    button_definitions=None,
):
    entry_buttons = {str(button).strip() for button in entry_buttons}
    exit_buttons = {str(button).strip() for button in exit_buttons}
    official_exit_buttons = {str(button).strip() for button in official_exit_buttons}
    review_buttons = {str(button).strip() for button in review_buttons}
    button_definitions = {
        **DEFAULT_CLOCK_BUTTON_DEFINITIONS,
        **(button_definitions or {}),
    }
    events_by_day = {}

    for event in events:
        event_dt = _event_datetime(event.event_time)
        if event_dt is None:
            continue
        events_by_day.setdefault(event_dt.date(), []).append((event_dt, event))

    daily_hours = []
    issues = []

    for work_date, day_events in sorted(events_by_day.items()):
        day_events.sort(key=lambda item: item[0])
        open_entry = None
        total_minutes = 0
        pair_count = 0
        employee_code = 0
        employee_name = ""
        day_issue_count = 0

        for event_dt, event in day_events:
            employee_code = event.employee_code
            employee_name = f"{event.last_name} {event.first_name}".strip()
            button = _button_key(event.button)
            button_description = _button_description(button, button_definitions)

            if button in entry_buttons:
                if open_entry is not None:
                    day_issue_count += 1
                    issues.append(
                        ClockPairIssue(
                            date=work_date,
                            employee_code=event.employee_code,
                            event_time=event.event_time,
                            button=event.button,
                            message=f"Dupli ulaz bez izlaza izmedju ({button_description}).",
                        )
                    )
                    continue
                open_entry = (event_dt, event)
                continue

            if button in exit_buttons or button in official_exit_buttons:
                is_official_exit = button in official_exit_buttons
                if open_entry is None:
                    day_issue_count += 1
                    issues.append(
                        ClockPairIssue(
                            date=work_date,
                            employee_code=event.employee_code,
                            event_time=event.event_time,
                            button=event.button,
                            message=f"{button_description} bez prethodnog ulaza.",
                        )
                    )
                    continue

                entry_dt, _entry_event = open_entry
                exit_dt = event_dt
                if is_official_exit:
                    exit_dt = datetime.combine(event_dt.date(), official_exit_end_time)

                if exit_dt <= entry_dt:
                    day_issue_count += 1
                    issues.append(
                        ClockPairIssue(
                            date=work_date,
                            employee_code=event.employee_code,
                            event_time=event.event_time,
                            button=event.button,
                            message=f"{button_description} nije posle ulaza.",
                        )
                    )
                    open_entry = None
                    continue

                total_minutes += int((exit_dt - entry_dt).total_seconds() // 60)
                pair_count += 1
                open_entry = None
                if is_official_exit:
                    issues.append(
                        ClockPairIssue(
                            date=work_date,
                            employee_code=event.employee_code,
                            event_time=event.event_time,
                            button=event.button,
                            message="Sluzbeni izlazak - racunato do 16:00.",
                            is_problem=False,
                        )
                    )
                continue

            if button in review_buttons:
                day_issue_count += 1
                issues.append(
                    ClockPairIssue(
                        date=work_date,
                        employee_code=event.employee_code,
                        event_time=event.event_time,
                        button=event.button,
                        message=f"{button_description} nije automatski ukljucen u obracun.",
                    )
                )
                continue

            day_issue_count += 1
            issues.append(
                ClockPairIssue(
                    date=work_date,
                    employee_code=event.employee_code,
                    event_time=event.event_time,
                    button=event.button,
                    message=f"Nepoznat taster: {event.button}.",
                )
            )

        if open_entry is not None:
            _entry_dt, entry_event = open_entry
            day_issue_count += 1
            issues.append(
                ClockPairIssue(
                    date=work_date,
                    employee_code=entry_event.employee_code,
                    event_time=entry_event.event_time,
                    button=entry_event.button,
                    message=f"{_button_description(entry_event.button, button_definitions)} bez izlaza.",
                )
            )

        daily_hours.append(
            DailyClockHours(
                date=work_date,
                employee_code=employee_code,
                employee_name=employee_name,
                total_minutes=total_minutes,
                pair_count=pair_count,
                issue_count=day_issue_count,
            )
        )

    return daily_hours, issues


def get_daily_work_hours(
    *,
    date_from,
    date_to,
    employee_code=None,
    using=None,
):
    date_declarations, date_params = _linked_server_date_declarations(date_from, date_to)
    employee_declarations, employee_params = _employee_declarations(employee_code=employee_code)
    employee_filter = ""
    if employee_code is not None:
        employee_filter = "AND c.Radnik = @employee_code"

    query = f"""
        {date_declarations}
        {employee_declarations}
        WITH daily AS (
            SELECT
                CONVERT(date, c.Vreme_Od) AS work_date,
                c.Radnik AS employee_code,
                r.oj AS organizational_unit,
                REPLACE(REPLACE(r.ranaz, NCHAR(262), N'C'), NCHAR(268), N'C') AS employee_name,
                SUM(
                    COALESCE(c.Trajanje_1, 0) +
                    COALESCE(c.Trajanje_2, 0) +
                    COALESCE(c.Trajanje_3, 0) +
                    COALESCE(c.Trajanje_Posebna, 0) +
                    COALESCE(c.Trajanje_Sluzbeno, 0) +
                    CASE
                        WHEN COALESCE(c.trajanje_pauza, 0) >= 0.5 THEN 0.5
                        ELSE COALESCE(c.trajanje_pauza, 0)
                    END
                ) AS total_hours
            FROM INFORMATIKA23.ID.dbo.c_parovi_radnika_detalji AS c
            INNER JOIN SERFIN.bazaldims.dbo.radnik AS r
                ON c.Radnik = r.rasif
            WHERE c.Vreme_Od >= @date_from
              AND c.Vreme_Od < @date_to
              AND (c.Trajanje_1 IS NULL OR c.Trajanje_1 < 20)
              {employee_filter}
            GROUP BY
                CONVERT(date, c.Vreme_Od),
                c.Radnik,
                r.oj,
                r.ranaz
        )
        SELECT
            YEAR(work_date) AS [year],
            MONTH(work_date) AS [month],
            DAY(work_date) AS [day],
            employee_code,
            organizational_unit,
            employee_name,
            CAST(FLOOR(total_hours) AS int) AS [hours],
            CAST(ROUND((total_hours - FLOOR(total_hours)) * 60, 0) AS int) AS [minutes],
            CAST(total_hours AS decimal(10, 2)) AS total_hours
        FROM daily
        ORDER BY work_date, employee_code, organizational_unit
    """
    with connections[resolve_attendance_db_alias(using)].cursor() as cursor:
        cursor.execute(query, [*date_params, *employee_params])
        rows = _fetchall_dicts(cursor)

    return [
        DailyWorkHours(
            year=_to_int(row.get("year")),
            month=_to_int(row.get("month")),
            day=_to_int(row.get("day")),
            employee_code=_to_int(row.get("employee_code")),
            organizational_unit=row.get("organizational_unit"),
            employee_name=row.get("employee_name") or "",
            hours=_to_int(row.get("hours")),
            minutes=_to_int(row.get("minutes")),
            total_hours=_to_decimal(row.get("total_hours")),
        )
        for row in rows
    ]


def get_month_daily_work_hours(*, employee_code, year, month, using=None):
    date_from, date_to, _last_day = month_period(year, month)
    return get_daily_work_hours(
        date_from=date_from,
        date_to=date_to,
        employee_code=employee_code,
        using=using,
    )


def daily_hours_by_day(daily_hours):
    return {item.day: item.total_hours for item in daily_hours}
