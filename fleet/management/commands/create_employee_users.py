import re
import unicodedata

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import OrganizationalUnit, Role
from fleet.models import Employee


def clean(value):
    return str(value or "").strip()


def ascii_slug(value):
    value = clean(value).casefold().replace("đ", "dj")
    value = "".join(
        ch for ch in unicodedata.normalize("NFD", value)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", ".", value).strip(".")


def strip_name_titles(value):
    text = clean(value)
    return re.sub(
        r"^(mr|dr|prof|dipl|ing|inž|inz)(?:\.|\s+)",
        "",
        text,
        flags=re.IGNORECASE,
    )


def username_base(employee):
    return ".".join(
        part for part in [
            ascii_slug(strip_name_titles(employee.first_name)),
            ascii_slug(employee.last_name),
        ]
        if part
    )


class Command(BaseCommand):
    help = "Kreira korisnicke naloge za aktivne zaposlene bez povezanog naloga."

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Upisuje korisnike u bazu. Bez ovoga komanda radi samo dry-run.",
        )
        parser.add_argument(
            "--role",
            default="zaposleni",
            help="Slug role koja se dodeljuje novim korisnicima. Default: zaposleni.",
        )
        parser.add_argument(
            "--default-password",
            default="",
            help="Ako je prosledjeno, svima postavlja ovu inicijalnu lozinku umesto JMBG-a.",
        )
        parser.add_argument(
            "--password-from-code",
            action="store_true",
            help="Postavlja inicijalnu lozinku u obliku ims<SIFRA_ZAPOSLENOG> umesto JMBG-a.",
        )
        parser.add_argument(
            "--center-override",
            action="append",
            default=[],
            metavar="OJ=CENTAR",
            help="Rucno mapiranje HR OJ na centar, npr. --center-override 1=11.",
        )
        parser.add_argument(
            "--include-unmapped",
            action="store_true",
            help="Kreira korisnike i bez mapiranog centra. Default je preskakanje takvih zaposlenih.",
        )

    def handle(self, *args, **options):
        if options["default_password"] and options["password_from_code"]:
            raise CommandError("Koristi ili --default-password ili --password-from-code, ne oba.")

        overrides = self.parse_overrides(options["center_override"])
        centers = sorted(
            {
                clean(center)
                for center in OrganizationalUnit.objects.values_list("center", flat=True)
                if clean(center)
            },
            key=lambda value: (len(value), value),
        )
        if not centers:
            raise CommandError("Ne postoje centri u OrganizationalUnit.")

        User = get_user_model()
        role = self.get_or_create_role(options["role"], options["execute"])
        users = User.objects.all()
        existing_usernames = {clean(username).casefold() for username in users.values_list("username", flat=True)}

        employees = (
            Employee.objects.filter(is_active=True, user_account__isnull=True)
            .order_by("employee_code")
        )
        planned = []
        skipped = []
        for employee in employees:
            center, reason = self.infer_center(employee.org_unit_code, centers, overrides)
            if not center and not options["include_unmapped"]:
                skipped.append((employee, reason))
                continue
            if not options["default_password"] and not options["password_from_code"] and not clean(employee.personal_number):
                skipped.append((employee, "nema JMBG za inicijalnu lozinku"))
                continue
            base = username_base(employee) or f"zaposleni.{employee.employee_code}"
            username = self.unique_username(base, employee.employee_code, existing_usernames)
            existing_usernames.add(username.casefold())
            planned.append((employee, username, center, reason))

        self.write(f"AKTIVNI BEZ NALOGA: {employees.count()}")
        self.write(f"ZA KREIRANJE: {len(planned)}")
        self.write(f"PRESKOCENO: {len(skipped)}")
        if skipped:
            self.write("PRESKOCENI BEZ CENTRA:")
            for employee, reason in skipped[:50]:
                self.write(
                    f"  {employee.employee_code} | {employee} | OJ={clean(employee.org_unit_code)} | {reason}"
                )
            if len(skipped) > 50:
                self.write(f"  ... jos {len(skipped) - 50}")

        self.write("PRVIH 20 ZA KREIRANJE:")
        for employee, username, center, reason in planned[:20]:
            self.write(
                f"  {employee.employee_code} | {employee} | username={username} | centar={center or '-'} | {reason}"
            )

        if not options["execute"]:
            self.write(
                self.style.WARNING(
                    "DRY-RUN: nije upisan nijedan korisnik. Dodaj --execute za upis. "
                    "Default inicijalna lozinka je JMBG i korisnik mora da je promeni."
                )
            )
            return

        created_count = 0
        with transaction.atomic():
            if role is None:
                role = self.get_or_create_role(options["role"], execute=True)
            for employee, username, center, _reason in planned:
                user = User(
                    username=username,
                    first_name=employee.first_name or "",
                    last_name=employee.last_name or "",
                    employee=employee,
                    allowed_center_codes=center or None,
                    is_active=True,
                )
                if options["default_password"]:
                    user.set_password(options["default_password"])
                elif options["password_from_code"]:
                    user.set_password(f"ims{employee.employee_code}")
                else:
                    user.set_password(clean(employee.personal_number))
                user.must_change_password = True
                user.save()
                if role is not None:
                    user.roles.add(role)
                created_count += 1

        self.write(self.style.SUCCESS(f"KREIRANO KORISNIKA: {created_count}"))

    def parse_overrides(self, raw_values):
        overrides = {}
        for raw in raw_values:
            if "=" not in raw:
                raise CommandError(f"Neispravan --center-override: {raw}. Ocekivano OJ=CENTAR.")
            org_unit, center = [clean(part) for part in raw.split("=", 1)]
            if not org_unit or not center:
                raise CommandError(f"Neispravan --center-override: {raw}.")
            overrides[org_unit] = center
        return overrides

    def infer_center(self, org_unit_code, centers, overrides):
        org_unit = clean(org_unit_code)
        if org_unit in overrides:
            return overrides[org_unit], f"override {org_unit}->{overrides[org_unit]}"
        if not org_unit:
            return "", "nema HR OJ"
        if org_unit in centers:
            return org_unit, "ista sifra centra"
        matches = [center for center in centers if org_unit.startswith(center)]
        if matches:
            max_length = max(len(center) for center in matches)
            best = sorted(center for center in matches if len(center) == max_length)
            if len(best) == 1:
                return best[0], f"prefiks {org_unit}->{best[0]}"
            return "", f"vise kandidata: {', '.join(best)}"
        return "", "nema mapiranja"

    def unique_username(self, base, employee_code, existing_usernames):
        username = base
        if username.casefold() not in existing_usernames:
            return username
        username = f"{base}.{employee_code}"
        if username.casefold() not in existing_usernames:
            return username
        suffix = 2
        while f"{username}.{suffix}".casefold() in existing_usernames:
            suffix += 1
        return f"{username}.{suffix}"

    def get_or_create_role(self, slug, execute):
        slug = clean(slug)
        if not slug:
            return None
        role = Role.objects.filter(slug=slug).first()
        if role or not execute:
            return role
        name = slug.replace("_", " ").title()
        role, _created = Role.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": "Obican zaposleni: pristup sopstvenom profilu.",
            },
        )
        return role

    def write(self, message):
        output = getattr(self.stdout, "_out", self.stdout)
        encoding = getattr(output, "encoding", None) or getattr(self.stdout, "encoding", None) or "utf-8"
        safe_message = str(message).encode(encoding, errors="replace").decode(encoding)
        self.stdout.write(safe_message)
