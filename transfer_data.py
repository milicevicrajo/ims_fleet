import os
import django

# Postavi Django settings modul
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ims_fleet.settings.development')
django.setup()

from fleet.models import *
# Funkcija za prebacivanje podataka između baza
def transfer_data(model):
    records = model.objects.using('default').all()
    for record in records:
        # Kreiraj novi objekat za server_db
        new_record = model()
        for field in record._meta.fields:
            setattr(new_record, field.name, getattr(record, field.name))
        new_record.save(using='server_db')

def transfer_all_data():
    # Prvo prebacujemo tabele koje nemaju zavisnosti
    models_to_transfer_first = [Vehicle, OrganizationalUnit, ServiceType, Employee]

    # Zatim prebacujemo tabele koje zavise od prethodnih
    models_to_transfer_second = [TrafficCard, JobCode, Lease, LeaseInterest, Policy, FuelConsumption, Incident, PutniNalog, Service, ServiceTransaction, Requisition, TransactionOMV, TransactionNIS]

    # Prebacivanje prvog seta modela (bez zavisnosti)
    for model in models_to_transfer_first:
        print(f"Prebacivanje podataka za model: {model.__name__}")
        transfer_data(model)

    # Prebacivanje drugog seta modela (zavisni modeli)
    for model in models_to_transfer_second:
        print(f"Prebacivanje podataka za model: {model.__name__}")
        transfer_data(model)

if __name__ == "__main__":
    transfer_all_data()
    print("Prebacivanje podataka je završeno.")
