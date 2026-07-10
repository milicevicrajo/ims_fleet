from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError

from hr.services.attendance import (
    DEFAULT_ENTRY_BUTTONS,
    DEFAULT_EXIT_BUTTONS,
    DEFAULT_OFFICIAL_EXIT_BUTTONS,
    calculate_daily_hours_from_clock_events,
    get_clock_button_definitions,
    get_clock_event_summary,
    get_clock_events,
    get_month_daily_work_hours,
    month_period,
    resolve_attendance_db_alias,
)


class Command(BaseCommand):
    help = "Prikazuje sazetak HR prolaza i dnevnih sati iz eksternih SQL Server tabela."

    def add_arguments(self, parser):
        parser.add_argument("--employee", type=int, required=True, help="Sifra zaposlenog / rasif")
        parser.add_argument(
            "--source-worker-id",
            type=int,
            default=None,
            help="Opcioni ID iz INFORMATIKA23.ID.dbo.Radnici za proveru prolaza.",
        )
        parser.add_argument("--year", type=int, required=True, help="Godina")
        parser.add_argument("--month", type=int, required=True, help="Mesec 1-12")
        parser.add_argument("--db", default=None, help="DB alias iz settings.DATABASES")
        parser.add_argument(
            "--entry-button",
            action="append",
            default=None,
            help="Taster koji znaci ulaz. Moze vise puta. Default: 1, 3, 5, 7",
        )
        parser.add_argument(
            "--exit-button",
            action="append",
            default=None,
            help="Taster koji znaci izlaz. Moze vise puta. Default: 2",
        )
        parser.add_argument(
            "--official-exit-button",
            action="append",
            default=None,
            help="Taster koji znaci sluzbeni izlazak do 16:00. Moze vise puta. Default: 4",
        )
        parser.add_argument(
            "--show-days",
            action="store_true",
            help="Prikazi dnevne stavke i probleme, ne samo zbir.",
        )

    def handle(self, *args, **options):
        employee_code = options["employee"]
        source_worker_id = options.get("source_worker_id")
        year = options["year"]
        month = options["month"]
        using = options.get("db")
        entry_buttons = options.get("entry_button") or list(DEFAULT_ENTRY_BUTTONS)
        exit_buttons = options.get("exit_button") or list(DEFAULT_EXIT_BUTTONS)
        official_exit_buttons = options.get("official_exit_button") or list(DEFAULT_OFFICIAL_EXIT_BUTTONS)

        if month < 1 or month > 12:
            raise CommandError("Mesec mora biti izmedju 1 i 12.")

        date_from, date_to, _last_day = month_period(year, month)
        db_alias = resolve_attendance_db_alias(using)

        try:
            event_summary = get_clock_event_summary(
                date_from=date_from,
                date_to=date_to,
                employee_code=None if source_worker_id is not None else employee_code,
                source_worker_id=source_worker_id,
                using=db_alias,
            )
            clock_events = get_clock_events(
                date_from=date_from,
                date_to=date_to,
                employee_code=None if source_worker_id is not None else employee_code,
                source_worker_id=source_worker_id,
                using=db_alias,
            )
            button_definitions = get_clock_button_definitions(using=db_alias)
            daily_hours = get_month_daily_work_hours(
                employee_code=employee_code,
                year=year,
                month=month,
                using=db_alias,
            )
        except DatabaseError as exc:
            raise CommandError(
                f"Ne mogu da ucitam HR attendance podatke iz baze '{db_alias}': {exc}"
            ) from exc

        total_hours = sum((item.total_hours for item in daily_hours), Decimal("0"))
        clock_daily_hours, clock_issues = calculate_daily_hours_from_clock_events(
            clock_events,
            entry_buttons=entry_buttons,
            exit_buttons=exit_buttons,
            official_exit_buttons=official_exit_buttons,
            button_definitions=button_definitions,
        )
        clock_problem_count = len([issue for issue in clock_issues if issue.is_problem])
        clock_total_hours = sum((item.total_hours for item in clock_daily_hours), Decimal("0"))

        self.stdout.write(f"Izvor: {db_alias}")
        self.stdout.write(f"Zaposleni: {employee_code}")
        if source_worker_id is not None:
            self.stdout.write(f"ID radnika za prolaze: {source_worker_id}")
        self.stdout.write(f"Period: {date_from:%Y-%m-%d} - {date_to:%Y-%m-%d}")
        self.stdout.write(
            "Prolasci: "
            f"{event_summary.total}, "
            f"prvi: {event_summary.first_event_at or '-'}, "
            f"poslednji: {event_summary.last_event_at or '-'}"
        )
        self.stdout.write(
            "Obracun iz prolaza: "
            f"{len(clock_daily_hours)} dana, "
            f"ukupno: {clock_total_hours:.2f}, "
            f"problemi: {clock_problem_count}"
        )
        self.stdout.write(
            "Dnevni sati iz obradjene tabele: "
            f"{len(daily_hours)} dana, "
            f"ukupno: {total_hours:.2f}"
        )

        if options["show_days"]:
            self.stdout.write("")
            self.stdout.write("Dani iz prolaza:")
            for item in clock_daily_hours:
                self.stdout.write(
                    f"{item.date:%Y-%m-%d}: "
                    f"{item.hours:02d}:{item.minutes:02d} "
                    f"({item.total_hours:.2f}) "
                    f"parova={item.pair_count} "
                    f"problema={item.issue_count} "
                    f"{item.employee_name}"
                )
            if clock_issues:
                self.stdout.write("")
                self.stdout.write("Napomene i problemi u prolazima:")
                for issue in clock_issues:
                    label = "PROBLEM" if issue.is_problem else "INFO"
                    self.stdout.write(
                        f"{issue.date:%Y-%m-%d}: "
                        f"{issue.event_time} "
                        f"taster={issue.button} "
                        f"{label} "
                        f"{issue.message}"
                    )

            self.stdout.write("")
            self.stdout.write("Dani iz obradjene tabele:")
            for item in daily_hours:
                self.stdout.write(
                    f"{item.date:%Y-%m-%d}: "
                    f"{item.hours:02d}:{item.minutes:02d} "
                    f"({item.total_hours:.2f}) "
                    f"OJ={item.organizational_unit or '-'} "
                    f"{item.employee_name}"
                )
