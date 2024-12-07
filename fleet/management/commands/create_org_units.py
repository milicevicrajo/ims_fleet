from django.core.management.base import BaseCommand
from fleet.models import OrganizationalUnit

class Command(BaseCommand):
    help = 'Učitavanje podataka o vozilima iz Excel fajla'
    
    def handle(self, *args, **kwargs):
        data = [
            {"name": "Geotehnicka ispitivanja i projektovanje", "code": "436111", "center": "43"},
            {"name": "Superkontrola na izgradnji gasovoda", "code": "425002", "center": "42"},
            {"name": "Gradjevinska keramika", "code": "412111", "center": "41"},
            {"name": "Laboratorijsko ispitivanje betona", "code": "413111", "center": "41"},
            {"name": "Ispitivanja opreme i konstrukcija", "code": "421114", "center": "42"},
            {"name": "Poslovi u garazi", "code": "832111", "center": "83"},
            {"name": "Pravni i kadrovski poslovi", "code": "821001", "center": "82"},
            {"name": "Organizacija i poslovanje", "code": "209001", "center": "2"},
            {"name": "Kamen i agregat", "code": "411111", "center": "41"},
            {"name": "HE Đerdap", "code": "421111", "center": "42"},
            {"name": "Veziva, hemije i malteri", "code": "414111", "center": "41"},
            {"name": "Etaloniranje", "code": "422111", "center": "42"},
            {"name": "Poslovi magacina", "code": "811002", "center": "81"},
            {"name": "Strucni nadzor", "code": "436222", "center": "43"},
            {"name": "Istrazni radovi na proj.sanac.", "code": "442112", "center": "44"},
            {"name": "Asfaltna ispitivanja", "code": "437222", "center": "43"},
            {"name": "Prednaprezanje", "code": "441111", "center": "44"},
            {"name": "Geomehanicka ispitivanja", "code": "437111", "center": "43"},
            {"name": "Stručni nadzor i ter.ispitivanja", "code": "431111", "center": "43"},
            {"name": "Projektovanje saobracajnica", "code": "439111", "center": "43"},
            {"name": "Mehan.-tehn.ispit.metala", "code": "421116", "center": "42"},
            {"name": "Ispitivanja konstrukcija", "code": "443111", "center": "44"},
            {"name": "PP zastita, zastita na radu", "code": "825003", "center": "82"},
            {"name": "Toplotna tehnika", "code": "415113", "center": "41"},
            {"name": "Drvo i sinteticki materijali", "code": "416111", "center": "41"},
            {"name": "Poslovi nabavke", "code": "811001", "center": "81"},
        ]

        for item in data:
            OrganizationalUnit.objects.update_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "center": item["center"],
                },
            )

        print("Organizational units successfully imported.")
