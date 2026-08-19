import os

from django.core.management.base import BaseCommand, CommandError

from mobilni.support.mobile import sync_from_sqlserver


class Command(BaseCommand):
    help = "Povlaci mobilne pakete, dodele i potrosnju iz stare SQL Server baze."

    def add_arguments(self, parser):
        parser.add_argument("--server", default=os.environ.get("MOBILNI_SQLSERVER_HOST", "SMS-SERVER"))
        parser.add_argument("--database", default=os.environ.get("MOBILNI_SQLSERVER_DATABASE", "Mobilni"))
        parser.add_argument("--username", default=os.environ.get("MOBILNI_SQLSERVER_USER", "sa"))
        parser.add_argument("--password", default=os.environ.get("MOBILNI_SQLSERVER_PASSWORD"))
        parser.add_argument("--driver", default=os.environ.get("MOBILNI_SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server"))

    def handle(self, *args, **options):
        password = options["password"]
        if not password:
            raise CommandError("Lozinka nije prosledjena. Koristi --password ili MOBILNI_SQLSERVER_PASSWORD.")

        result = sync_from_sqlserver(
            server=options["server"],
            database=options["database"],
            username=options["username"],
            password=password,
            driver=options["driver"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "SQL Server sync zavrsen: "
                f"paketi novo {result.packages.imported}, azurirano {result.packages.updated}, "
                f"preskoceno {result.packages.skipped}; "
                f"korisnici novo {result.users.imported}, azurirano {result.users.updated}, "
                f"preskoceno {result.users.skipped}; "
                f"dodele novo {result.assignments.imported}, azurirano {result.assignments.updated}, "
                f"preskoceno {result.assignments.skipped}; "
                f"potrosnja novo {result.usages.imported}, azurirano {result.usages.updated}, "
                f"preskoceno {result.usages.skipped}; "
                f"sync zaposlenih {result.employee_links}"
            )
        )
