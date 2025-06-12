from fleet.utils import fetch_policy_data, fetch_service_data, fetch_requisition_data, nis_data_import, omv_putnicka_data_import, omv_teretna_data_import, kerio_login, process_vehicle_retirements
from celery import shared_task

@shared_task
def run_nis_command():
    return nis_data_import()


@shared_task
def run_omv_putnicka_command():
    return omv_putnicka_data_import()

@shared_task
def run_omv_teretna_command():
    return omv_teretna_data_import()

# Zadaci za povlačenje podataka
@shared_task
def fetch_policy_data_task():
    result = fetch_policy_data(last_24_hours=True)
    return f"Fetch Policy Data: {result}"

@shared_task
def fetch_service_data_task():
    result = fetch_service_data(last_24_hours=True)
    return f"Fetch Service Data: {result}"

@shared_task
def fetch_requisition_data_task():
    result = fetch_requisition_data(last_24_hours=True)
    return f"Fetch Requisition Data: {result}"

@shared_task
def kerio_login_task():
    return kerio_login()
			
@shared_task	
def provera_sifre_posla_task():
    from fleet.utils import update_job_codes_from_view
    return update_job_codes_from_view()	

@shared_task
def fetch_job_codes():
    from fleet.utils import sync_organizational_units_from_view
    return sync_organizational_units_from_view()

@shared_task
def proveri_otpis():
    return process_vehicle_retirements()