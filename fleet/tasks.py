from django_cron import CronJobBase, Schedule
from fleet.management.commands.nis_command import Command as NisCommand
from fleet.management.commands.omv_command_putnicka import Command as OmvPutnickaCommand
from fleet.management.commands.omv_command_teretna import Command as OmvTeretnaCommand
from fleet.utils import fetch_policy_data, fetch_service_data, fetch_requisition_data
class NisCommandCron(CronJobBase):
    RUN_AT_TIMES = ['00:00']  # Pokretanje u ponoć

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.nis_command_cron'  # Jedinstveni kod zadatka

    def do(self):
        NisCommand().handle()
        print("NIS command executed.")

class OmvPutnickaCommandCron(CronJobBase):
    RUN_AT_TIMES = ['01:00']  # Pokretanje u 01:00

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.omv_putnicka_command_cron'  # Jedinstveni kod zadatka

    def do(self):
        OmvPutnickaCommand().handle()
        print("OMV (putnička) command executed.")

class OmvTeretnaCommandCron(CronJobBase):
    RUN_AT_TIMES = ['02:00']  # Pokretanje u 02:00

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.omv_teretna_command_cron'  # Jedinstveni kod zadatka

    def do(self):
        OmvTeretnaCommand().handle()
        print("OMV (teretna) command executed.")

class FetchPolicyDataCron(CronJobBase):
    RUN_AT_TIMES = ['03:00']  # Pokreće se u 03:00

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.fetch_policy_data_cron'  # Jedinstveni kod zadatka

    def do(self):
        # Pokreće funkciju za povlačenje podataka
        result = fetch_policy_data(last_24_hours=True)
        print(f"Fetch Policy Data: {result}")


class FetchServiceDataCron(CronJobBase):
    RUN_AT_TIMES = ['03:30']  # Pokreće se u 03:30

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.fetch_service_data_cron'  # Jedinstveni kod zadatka

    def do(self):
        # Pokreće funkciju za povlačenje podataka
        result = fetch_service_data(last_24_hours=True)
        print(f"Fetch Service Data: {result}")


class FetchRequisitionDataCron(CronJobBase):
    RUN_AT_TIMES = ['04:00']  # Pokreće se u 04:00

    schedule = Schedule(run_at_times=RUN_AT_TIMES)
    code = 'fleet.fetch_requisition_data_cron'  # Jedinstveni kod zadatka

    def do(self):
        # Pokreće funkciju za povlačenje podataka
        result = fetch_requisition_data(last_24_hours=True)
        print(f"Fetch Requisition Data: {result}")