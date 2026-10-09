"""Izveštaji o gorivu u meniju Knjiženja (od 08.10.2026.): isti ekrani Flote, da knjigovodstvo ne menja modul.

Svaka stavka se vidi uz svoju dozvolu (kod = ime rute Flote; „Gorivo IMS” traži `fuel_transactions_list`, kao i sama
ruta). Uloga Knjiženje dobija sve ove kodove (`core.permissions`); obuhvat podataka je obuhvat Flote iz dodele uloge.
"""
from django.urls import reverse

from core.mixins import user_has_role_permission

# (ruta, dozvola, naziv, ikona)
IZVESTAJI = (
    ("fuel_job_code_nis_putnicka", "fuel_job_code_nis_putnicka", "NIS — putnička", "mdi-car"),
    ("fuel_job_code_nis_teretna", "fuel_job_code_nis_teretna", "NIS — teretna", "mdi-truck"),
    ("fuel_job_code_omv_putnicka", "fuel_job_code_omv_putnicka", "OMV — putnička", "mdi-car"),
    ("fuel_job_code_omv_teretna", "fuel_job_code_omv_teretna", "OMV — teretna", "mdi-truck"),
    ("fuel_invoice_control", "fuel_invoice_control", "Kontrola faktura goriva", "mdi-file-compare"),
    ("fleet_fuel_report", "fuel_transactions_list", "Gorivo IMS — meseci i šifre", "mdi-gas-station"),
    ("tro_gorivo_mesec", "tro_gorivo_mesec", "Knjiženi troškovi goriva", "mdi-book-open-variant"),
    ("fuel_transactions_list", "fuel_transactions_list", "Transakcije goriva", "mdi-format-list-bulleted"),
)
KODOVI = tuple(sorted({dozvola for _, dozvola, _, _ in IZVESTAJI}))


def meni(user):
    """Stavke menija koje korisnik sme da otvori."""
    return [{"url": reverse(ruta), "naziv": naziv, "ikona": ikona}
            for ruta, dozvola, naziv, ikona in IZVESTAJI if user_has_role_permission(user, dozvola)]
