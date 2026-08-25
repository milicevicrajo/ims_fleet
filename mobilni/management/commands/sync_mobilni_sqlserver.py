import os

from django.core.management.base import BaseCommand, CommandError

from mobilni.support.mobile import sync_from_sqlserver


class Command(BaseCommand):
    help = "Povlači mobilne pakete, dodele i potrošnju iz stare SQL Server baze."

    def add_arguments(self, parser):
        parser.add_argument("--server", default=os.environ.get("MOBILNI_SQLSERVER_HOST", "SMS-SERVER"))
        parser.add_argument("--database", default=os.environ.get("MOBILNI_SQLSERVER_DATABASE", "Mobilni"))
        parser.add_argument("--username", default=os.environ.get("MOBILNI_SQLSERVER_USER", "sa"))
        parser.add_argument("--password", default=os.environ.get("MOBILNI_SQLSERVER_PASSWORD"))
        parser.add_argument("--driver", default=os.environ.get("MOBILNI_SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server"))

    def handle(self, *args, **options):
        password = options["password"]
        if not password:
            raise CommandError("Lozinka nije prosleđena. Koristi --password ili MOBILNI_SQLSERVER_PASSWORD.")

        result = sync_from_sqlserver(
            server=options["server"],
            database=options["database"],
            username=options["username"],
            password=password,
            driver=options["driver"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "SQL Server sinhronizacija završena: "
                f"paketi novo {result.packages.imported}, ažurirano {result.packages.updated}, "
                f"preskočeno {result.packages.skipped}; "
                f"korisnici novo {result.users.imported}, ažurirano {result.users.updated}, "
                f"preskočeno {result.users.skipped}; "
                f"dodele novo {result.assignments.imported}, ažurirano {result.assignments.updated}, "
                f"preskočeno {result.assignments.skipped}; "
                f"potrošnja novo {result.usages.imported}, ažurirano {result.usages.updated}, "
                f"preskočeno {result.usages.skipped}; "
                f"sinhronizacija zaposlenih {result.employee_links}"
            )
        )
