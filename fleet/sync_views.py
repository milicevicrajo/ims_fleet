import logging
import os
import tempfile

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.db import connections
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .models import Lease, LeaseInterest, Vehicle
from .utils import fetch_policy_data

logger = logging.getLogger(__name__)


@staff_member_required
def fetch_data_view(request):
    if request.method == "POST":
        command = request.POST.get("command")
        try:
            if command == "nis_command":
                call_command("nis_command")
            elif command == "omv_command_putnicka":
                call_command("omv_command_putnicka")
            elif command == "omv_command_teretna":
                call_command("omv_command_teretna")
            else:
                return JsonResponse(
                    {"status": "error", "message": "Nepoznata komanda."},
                    status=400,
                )

            return JsonResponse(
                {"status": "success", "message": f"Komanda {command} uspešno izvršena."}
            )
        except Exception as exc:
            return JsonResponse({"status": "error", "message": str(exc)}, status=500)

    return render(request, "fleet/fetch_data.html")


@staff_member_required
def import_nis_excel_view(request):
    if request.method != "POST":
        return redirect("fetch_data")

    excel_file = request.FILES.get("excel_file")
    if not excel_file:
        messages.error(request, "Nije izabran Excel fajl.")
        return redirect("fetch_data")

    extension = os.path.splitext(excel_file.name or "")[1] or ".xlsx"
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            for chunk in excel_file.chunks():
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        from .selenium_integrations import import_nis_fuel_consumption, import_nis_transactions

        import_nis_fuel_consumption(temp_file_path)
        import_nis_transactions(temp_file_path)
        messages.success(request, "NIS Excel import je uspešno završen.")
    except Exception as exc:
        logger.exception("Greška prilikom ručnog NIS Excel importa.")
        messages.error(request, f"Greška prilikom importa: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                logger.warning("Nije moguće obrisati privremeni fajl: %s", temp_file_path)

    return redirect("fetch_data")


def _handle_omv_csv_import(request, category_label):
    csv_file = request.FILES.get("omv_csv_file")
    if not csv_file:
        messages.error(request, "Nije izabran OMV CSV fajl.")
        return redirect("fetch_data")

    extension = (os.path.splitext(csv_file.name or "")[1] or ".csv").lower()
    if extension != ".csv":
        messages.error(request, "OMV ručni import podržava samo CSV fajl.")
        return redirect("fetch_data")

    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            for chunk in csv_file.chunks():
                tmp_file.write(chunk)
            temp_file_path = tmp_file.name

        from .selenium_integrations import import_omv_fuel_consumption_from_csv, import_omv_transactions_from_csv

        import_omv_fuel_consumption_from_csv(temp_file_path)
        import_omv_transactions_from_csv(temp_file_path)
        messages.success(request, f"OMV {category_label} CSV import je uspešno završen.")
    except Exception as exc:
        logger.exception("Greška prilikom ručnog OMV %s CSV importa.", category_label)
        messages.error(request, f"Greška prilikom OMV {category_label} importa: {exc}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                logger.warning("Nije moguće obrisati privremeni fajl: %s", temp_file_path)

    return redirect("fetch_data")


@staff_member_required
def import_omv_putnicka_csv_view(request):
    if request.method != "POST":
        return redirect("fetch_data")
    return _handle_omv_csv_import(request, "putnicka")


@staff_member_required
def import_omv_teretna_csv_view(request):
    if request.method != "POST":
        return redirect("fetch_data")
    return _handle_omv_csv_import(request, "teretna")


def fetch_vehicle_value_view(request):
    if request.method == "POST":
        with connections["test_db"].cursor() as cursor:
            cursor.execute(
                """
                SELECT sif_osn, vrednost FROM dbo.vrednost_vozila
            """
            )
            rows = cursor.fetchall()

        updated_vehicles_count = 0

        for row in rows:
            sif_osn = row[0].strip()
            vrednost = row[1]

            try:
                logger.info(sif_osn)
                vehicle = Vehicle.objects.get(inventory_number=sif_osn)
                vehicle.value = vrednost
                vehicle.save()
                updated_vehicles_count += 1

            except Vehicle.DoesNotExist:
                logger.warning(
                    "Vozilo sa inventory_number (sif_osn) %s nije pronađeno.",
                    sif_osn,
                )
                continue

            except Exception as exc:
                logger.error(
                    "Greška prilikom ažuriranja vozila sa inventory_number %s: %s",
                    sif_osn,
                    exc,
                )
                messages.error(
                    request,
                    "Došlo je do greške prilikom ažuriranja podataka o vozilu.",
                )
                return redirect("fetch_policies")

        messages.success(request, f"Uspešno ažurirano {updated_vehicles_count} vozila.")
        return redirect("fetch_policies")

    return render(request, "fleet/fetch_data.html")


def fetch_lease_interest_data(request):
    if request.method == "POST":
        with connections["test_db"].cursor() as cursor:
            cursor.execute(
                """
                SELECT god, ugovor, iznos FROM dbo.lizing_kamate
            """
            )
            rows = cursor.fetchall()

        for row in rows:
            year = row[0]
            contract_number = row[1].strip()
            interest_amount = row[2]

            try:
                lease = Lease.objects.get(contract_number=contract_number)
                lease_interest, created = LeaseInterest.objects.get_or_create(
                    lease=lease,
                    year=year,
                    defaults={"interest_amount": interest_amount},
                )

                if not created:
                    lease_interest.interest_amount = interest_amount
                    lease_interest.save()

            except Lease.DoesNotExist:
                logger.warning("Lizing ugovor sa brojem %s nije pronađen.", contract_number)
                continue

        return redirect("fetch_policies")

    return render(request, "fleet/fetch_data.html")


def fetch_policy_data_view(request):
    if request.method == "POST":
        days = request.POST.get("days")
        result = None

        try:
            if days:
                days = int(days)
                if days < 0:
                    raise ValueError
                result = fetch_policy_data(last_24_hours=False, days=days)
            else:
                result = fetch_policy_data()

            if result.startswith("Critical error"):
                messages.error(request, result)
            else:
                messages.success(request, result)

        except ValueError:
            messages.error(request, "Invalid number of days")

        return redirect("policy_list")

    return render(request, "fleet/fetch_policy_data.html")
