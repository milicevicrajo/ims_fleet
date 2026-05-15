from django.core.management.base import BaseCommand

from ugovori.apr_openapi import fetch_apr_companies, normalize_maticni_broj, update_partners_from_apr
from ugovori.models import Partner


class Command(BaseCommand):
    help = "Ažurira naziv i aktivnost partnera iz APR OpenData registra po matičnom broju."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Upisuje izmene. Bez ove opcije komanda radi dry-run.",
        )
        parser.add_argument(
            "--maticni-broj",
            default=None,
            help="Ažurira samo partnera sa ovim matičnim brojem.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Ograničava broj lokalnih partnera za probu.",
        )
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Uključuje i lokalno neaktivne partnere.",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        partners = Partner.objects.filter(partner_type=Partner.LEGAL_ENTITY, residency=Partner.DOMESTIC)
        if not options["include_inactive"]:
            partners = partners.filter(is_active=True)

        requested_maticni_broj = normalize_maticni_broj(options["maticni_broj"])

        partners = partners.exclude(maticni_broj__isnull=True).exclude(maticni_broj="")
        partners = partners.order_by("id")
        if options["limit"]:
            partners = partners[: options["limit"]]
        partners = list(partners)
        if requested_maticni_broj:
            partners = [
                partner
                for partner in partners
                if normalize_maticni_broj(partner.maticni_broj) == requested_maticni_broj
            ]

        self.stdout.write("Učitavam APR OpenData registar...")
        companies = fetch_apr_companies()
        result = update_partners_from_apr(partners, companies=companies, commit=commit)

        self.stdout.write(
            self.style.SUCCESS("COMMIT: upisujem izmene.")
            if commit
            else self.style.WARNING("DRY-RUN: nema upisa.")
        )
        self.stdout.write(
            f"Provereno: {result.checked} | ažurirano: {result.updated} | "
            f"bez izmene: {result.unchanged} | bez MB: {result.missing_maticni_broj} | "
            f"nije nađeno u APR: {result.not_found}"
        )
        if not commit:
            self.stdout.write("Pokreni sa --commit kada želiš stvarni upis.")
