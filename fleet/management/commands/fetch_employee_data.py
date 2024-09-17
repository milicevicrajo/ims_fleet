from django.core.management.base import BaseCommand
from django.db import connections
from fleet.models import Employee
import logging
import re

logger = logging.getLogger(__name__)

def format_name(name):
    """
    Funkcija koja formatira ime i prezime:
    1. Uklanja prefikse kao što su 'dr'.
    2. Velikim slovom piše prva slova imena i prezimena.
    3. Menja 'ic' na kraju prezimena u 'ić'.
    """
    name = re.sub(r'\bdr\b', '', name, flags=re.IGNORECASE).strip()
    name_parts = name.split()
    formatted_parts = []
    for part in name_parts:
        if part.lower().endswith('ic'):
            part = part[:-2] + 'ić'
        formatted_parts.append(part.capitalize())
    return ' '.join(formatted_parts)

class Command(BaseCommand):
    help = 'Povlači i ažurira podatke o zaposlenima iz view-a'

    def handle(self, *args, **kwargs):
        # Povlačenje podataka iz view-a
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT rasif, ranaz, naz_sis, oj, sif_sis, pol, dat_rodj, dat_dolaska, mob_br FROM dbo.zaposleni
            """)
            rows = cursor.fetchall()

        for row in rows:
            employee_code = row[0]
            full_name = row[1]
            position = row[2]
            department_code = row[3]
            gender = row[5]
            date_of_birth = row[6]
            date_of_joining = row[7]
            phone_number = row[8]

            # Formatiraj ime i prezime
            name_parts = full_name.split()
            last_name = format_name(name_parts[0])
            first_name = format_name(' '.join(name_parts[1:])) if len(name_parts) > 1 else ''

            try:
                # Ažuriraj ili kreiraj novog zaposlenog
                employee, created = Employee.objects.get_or_create(
                    employee_code=employee_code,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'position': position,
                        'department_code': department_code,
                        'gender': gender,
                        'date_of_birth': date_of_birth,
                        'date_of_joining': date_of_joining,
                        'phone_number': phone_number,
                    }
                )

                if not created:
                    # Ažuriraj podatke ako zapis već postoji
                    employee.first_name = first_name
                    employee.last_name = last_name
                    employee.position = position
                    employee.department_code = department_code
                    employee.gender = gender
                    employee.date_of_birth = date_of_birth
                    employee.date_of_joining = date_of_joining
                    employee.phone_number = phone_number
                    employee.save()

            except Exception as e:
                logger.error(f"Greška prilikom obrade zaposlenog sa šifrom {employee_code}: {e}")
                continue

        self.stdout.write(self.style.SUCCESS('Uspešno povučeni i ažurirani podaci o zaposlenima'))
