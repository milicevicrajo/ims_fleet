# fleet/management/commands/sync_employees.py

from django.core.management.base import BaseCommand
from fleet.models import Employee
import requests

class Command(BaseCommand):
    help = 'Sync employee data from external source'

    def handle(self, *args, **kwargs):
        # Replace with the actual URL of your external employee data API or data source
        response = requests.get('http://external-source.com/api/employees')
        
        if response.status_code == 200:
            employees_data = response.json()
            self.sync_employees(employees_data)
        else:
            self.stdout.write(self.style.ERROR('Failed to fetch employee data'))

    def sync_employees(self, employees_data):
        for data in employees_data:
            Employee.objects.update_or_create(
                employee_code=data['employee_code'],
                defaults={
                    'name': data['name'],
                    'position': data['position'],
                    'department_code': data['department_code'],
                    'gender': data['gender'],
                    'date_of_birth': data['date_of_birth'],
                    'date_of_joining': data['date_of_joining'],
                    'phone_number': data['phone_number'],
                }
            )
        self.stdout.write(self.style.SUCCESS('Successfully synced employee data'))



# Scheduling the Command
# To schedule the command to run monthly, you can use a cron job. Here’s how to set it up:
# Open the Crontab Editor:

# crontab -e

# Add the Cron Job:
# Add the following line to schedule the command to run on the 1st of every month at midnight:
# 0 0 1 * * /path/to/your/venv/bin/python /path/to/your/project/manage.py sync_employees

# Make sure to replace /path/to/your/venv with the path to your virtual environment and /path/to/your/project with the path to your Django project.