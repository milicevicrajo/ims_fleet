from fleet.utils import fetch_policy_data, fetch_service_data, fetch_requisition_data, nis_data_import, omv_putnicka_data_import, omv_teretna_data_import, kerio_login
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
			
			
