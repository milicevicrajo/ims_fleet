from django.shortcuts import render, redirect
from django.db import connections, IntegrityError
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import *
from .forms import *
from .filters import *
from django.db.models import OuterRef, Subquery
from django_filters.views import FilterView
from django.contrib import messages
import logging
from django.http import HttpResponseForbidden
from django.db.models import Sum, Avg
import datetime 
from datetime import date, timedelta
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .utils import calculate_average_fuel_consumption, calculate_average_fuel_consumption_ever

def dashboard(request):    
    # Count the number of objects where vehicle is None
    services_without_vehicle = ServiceTransaction.objects.filter(vehicle__isnull=True).count()
    policies_without_vehicle = Policy.objects.filter(vehicle__isnull=True).count()
    requisitions_without_vehicle = Requisition.objects.filter(vehicle__isnull=True).count()
    
    # Get today's date
    today = date.today()

    # Calculate the date 30 days from today
    thirty_days_from_now = today + timedelta(days=30)

    # Filter policies expiring within the next 30 days
    expiring_policies = Policy.objects.filter(end_date__gte=today, end_date__lte=thirty_days_from_now)
    context = {
        'services_without_vehicle': services_without_vehicle,
        'policies_without_vehicle': policies_without_vehicle,
        'requisitions_without_vehicle': requisitions_without_vehicle,
        'expiring_policies': expiring_policies,
    }
    
    return render(request, 'fleet/dashboard.html', context)



# <!-- ======================================================================= -->
#                           <!-- VEHICLE -->
# <!-- ======================================================================= -->
class VehicleListView(LoginRequiredMixin, ListView):
    model = Vehicle
    template_name = 'fleet/vehicle_list.html'
    context_object_name = 'vehicles'
    form_class = VehicleFilterForm  # Dodajemo formu za filtriranje

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Dohvati vrednosti iz GET parametara
        org_unit = self.request.GET.get('org_unit')
        fuel_in_last_6_months = self.request.GET.get('fuel_in_last_6_months')
        center_code = self.request.GET.get('center_code')

        # Subquery to get the latest org_unit for each Vehicle
        latest_org_unit_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef('pk')
        ).order_by('-assigned_date').values('organizational_unit__code')[:1]

        # Subquery to get the latest TrafficCard for each Vehicle
        latest_traffic_card_subquery = TrafficCard.objects.filter(
            vehicle_id=OuterRef('pk')
        ).order_by('-issue_date').values('registration_number')[:1]
        
        queryset = queryset.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery),
            registration_number=Subquery(latest_traffic_card_subquery),
            total_repairs=Sum('service_transactions__potrazuje')
        )


        
        # Filter za šifru posla (JobCode)
        if org_unit:
            queryset = queryset.filter(job_codes__organizational_unit=org_unit)

        # Filter za šifru centra (center_code)
        if center_code:
            queryset = queryset.filter(job_codes__organizational_unit__center=center_code)

        # Filter za gorivo u poslednjih 6 meseci
        if fuel_in_last_6_months == 'yes':
            six_months_ago = timezone.now() - timedelta(days=180)
            queryset = queryset.filter(
                fuel_consumptions__date__gte=six_months_ago
            ).distinct()  # Da ne vraća duplikate ako postoji više sipanja
        elif fuel_in_last_6_months == 'no':
            six_months_ago = timezone.now() - timedelta(days=180)
            queryset = queryset.exclude(
                fuel_consumptions__date__gte=six_months_ago
            ).distinct()  # Da ne vraća duplikate ako postoji više sipanja
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicles = context['vehicles']
        vehicle_consumption_data = {}

        for vehicle in vehicles:
            vehicle_consumption_data[vehicle.id] = calculate_average_fuel_consumption(vehicle)

        form = VehicleFilterForm(self.request.GET or None)
        context['vehicle_consumption_data'] = vehicle_consumption_data
        context['form'] = form
        context['title'] = 'Lista vozila'
        return context
    
# DETALJI VOZILA
class VehicleDetailView(LoginRequiredMixin, DetailView):
    model = Vehicle
    template_name = 'fleet/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get(self, request, *args, **kwargs):
        print("VehicleDetailView get() method called")  # This should print first
        vehicle = self.get_object()  # Get the vehicle object based on the primary key
        print(vehicle)  # This should print the vehicle object
        
        # Subquery to get the latest org_unit for each Vehicle
        latest_org_unit_subquery = JobCode.objects.filter(
            vehicle_id=OuterRef('pk')
        ).order_by('-assigned_date').values('organizational_unit__center')[:1]
        
        # Annotate the vehicle queryset with the latest org_unit code
        vehicle_with_latest_org_unit = Vehicle.objects.annotate(
            latest_org_unit=Subquery(latest_org_unit_subquery)
        ).get(pk=vehicle.pk)

        # Perform additional logic with allowed_centers or other fields if needed
        allowed_centers = request.user.allowed_centers

        if allowed_centers:
            allowed_centers_list = allowed_centers.split(',')
            if vehicle_with_latest_org_unit.latest_org_unit not in allowed_centers_list:
                return HttpResponseForbidden("Nemate dozvolu za pristup ovom vozilu.")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        vehicle = self.get_object()

        # 1. Leasing data
        lease_info = Lease.objects.filter(vehicle=vehicle).order_by('-start_date').first()

        # 2. NIS and OMV cards
        nis_card = vehicle.nis_transactions.filter().first()
        omv_card = vehicle.omv_transactions.filter().first()
        consumptions = vehicle.fuel_consumptions.all()

        # 3. Mileage (use latest FuelConsumption)
        mileage = vehicle.fuel_consumptions.order_by('-mileage').values_list('mileage', flat=True).first()
        print(mileage)

        # 4. Active Policies
        active_policies = Policy.objects.filter(vehicle=vehicle, end_date__gte=datetime.date.today())

        # 5. Book value (assuming you calculate this from external source or additional logic)
        book_value = vehicle.purchase_value  # Simplified for now

        # 6. Average Fuel Consumption
        average_consumption = vehicle.fuel_consumptions.aggregate(Avg('amount'))

        # 7. Current Job Code
        current_job_code = JobCode.objects.filter(vehicle=vehicle).order_by('-assigned_date').first()

        # 8. General status (red/green light based on repair costs)
        repair_costs = vehicle.service_transactions.aggregate(total_repairs=Sum('potrazuje'))['total_repairs'] or 0
        status_light = 'green' if repair_costs < vehicle.purchase_value else 'red'
        
        average_consumption = calculate_average_fuel_consumption(vehicle)
        average_consumption_ever = calculate_average_fuel_consumption_ever(vehicle)
        context.update({
            'lease_info': lease_info,
            'nis_card': nis_card,
            'omv_card': omv_card,
            'mileage': mileage,
            'active_policies': active_policies,
            'book_value': book_value,
            'average_consumption': average_consumption,
            'average_consumption_ever': average_consumption_ever,
            'current_job_code': current_job_code,
            'status_light': status_light,
            'repair_costs': repair_costs,
            'status_light': status_light,
            'consumptions': consumptions,
            'title':f"Detalji vozila {self.object.brand} {self.object.model}"
        })

        

        return context

# POVLACENJE PODATAKA IZ DRUGE BAZE
logger = logging.getLogger(__name__)  
def fetch_vehicle_value_view(request):
    if request.method == 'POST':
        # Povlačenje podataka iz druge baze
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT sif_osn, vrednost FROM dbo.vrednost_vozila
            """)
            rows = cursor.fetchall()

        # Broj ažuriranih vozila
        updated_vehicles_count = 0

        for row in rows:
            sif_osn = row[0].strip()  # Polje 'sif_osn' iz druge baze (odgovara 'inventory_number' u modelu Vehicle)
            vrednost = row[1]  # Polje 'vrednost' iz druge baze (odgovara polju 'value' u modelu Vehicle)

            try:
                # Pronađi vozilo po inventory_number (sif_osn)
                print(sif_osn)
                vehicle = Vehicle.objects.get(inventory_number=sif_osn)
                #print(vehicle)
                # Ažuriraj polje 'value' sa novom vrednošću
                vehicle.value = vrednost
                vehicle.save()
                updated_vehicles_count += 1

            except Vehicle.DoesNotExist:
                # Ako vozilo sa datim 'sif_osn' ne postoji, preskoči i zapiši grešku
                logger.warning(f"Vozilo sa inventory_number (sif_osn) {sif_osn} nije pronađeno.")
                continue

            except Exception as e:
                # U slučaju bilo koje druge greške
                logger.error(f"Greška prilikom ažuriranja vozila sa inventory_number {sif_osn}: {e}")
                messages.error(request, "Došlo je do greške prilikom ažuriranja podataka o vozilu.")
                return redirect('fetch_vehicle_value')

        # Poruka o uspešnom ažuriranju
        messages.success(request, f"Uspešno ažurirano {updated_vehicles_count} vozila.")

        # Preusmeravanje nakon uspešnog povlačenja podataka
        return redirect('vehicle_list')  # Postavi URL na koji želiš da preusmeriš korisnika

    return render(request, 'fleet/fetch_vehicle_value.html')


class VehicleCreateView(LoginRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('vehicle_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novo vozilo'
        context['submit_button_label'] = 'Dodaj vozilo'
        return context

class VehicleUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('vehicle_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke vozila'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class VehicleDeleteView(LoginRequiredMixin, DeleteView):
    model = Vehicle
    success_url = reverse_lazy('vehicle_list')
    template_name = 'fleet/vehicle_confirm_delete.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši vozilo'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================= -->
#                           <!-- TRAFIC CARD -->
# <!-- ======================================================================= -->
class TrafficCardListView(LoginRequiredMixin, ListView):
    model = TrafficCard
    template_name = 'fleet/trafficcard_list.html'
    context_object_name = 'traffic_cards'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista saobraćajnih dozvola'
        return context

class TrafficCardCreateView(LoginRequiredMixin, CreateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('trafficcard_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu saobraćajnu dozvolu'
        context['submit_button_label'] = 'Dodaj saobraćajnu dozvolu'
        return context

class TrafficCardUpdateView(LoginRequiredMixin, UpdateView):
    model = TrafficCard
    form_class = TrafficCardForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('trafficcard_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke saobraćajne dozvole'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class TrafficCardDetailView(LoginRequiredMixin, DetailView):
    model = TrafficCard
    template_name = 'fleet/trafficcard_detail.html'
    context_object_name = 'traffic_card'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji saobraćajne dozvole {self.object.registration_number}"
        return context

class TrafficCardDeleteView(LoginRequiredMixin, DeleteView):
    model = TrafficCard
    success_url = reverse_lazy('trafficcard_list')
    template_name = 'fleet/trafficcard_confirm_delete.html'
    context_object_name = 'traffic_card'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši saobraćajnu dozvolu'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================= -->
#                           <!-- JOB CODE -->
# <!-- ======================================================================= -->
class JobCodeListView(LoginRequiredMixin, ListView):
    model = JobCode
    template_name = 'fleet/jobcode_list.html'
    context_object_name = 'job_codes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista šifara poslova'
        return context

class JobCodeCreateView(LoginRequiredMixin, CreateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('jobcode_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu šifru posla'
        context['submit_button_label'] = 'Dodaj šifru posla'
        return context
    
class JobCodeUpdateView(LoginRequiredMixin, UpdateView):
    model = JobCode
    form_class = JobCodeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('jobcode_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni šifru posla'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class JobCodeDetailView(LoginRequiredMixin, DetailView):
    model = JobCode
    template_name = 'fleet/jobcode_detail.html'
    context_object_name = 'job_code'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji šifre posla {self.object.job_code}"
        return context

class JobCodeDeleteView(LoginRequiredMixin, DeleteView):
    model = JobCode
    success_url = reverse_lazy('jobcode_list')
    template_name = 'fleet/jobcode_confirm_delete.html'
    context_object_name = 'job_code'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši šifru posla'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================= -->
#                           <!-- LEASE -->
# <!-- ======================================================================= -->
class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = 'fleet/lease_list.html'
    context_object_name = 'leases'
    # Dodajte permission_required atribut
    permission_required = 'fleet.view_lease'
    raise_exception = True
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista zakupa vozila'
        return context

class LeaseCreateView(LoginRequiredMixin, CreateView):
    model = Lease
    form_class = LeaseForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('lease_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novi zakup'
        context['submit_button_label'] = 'Dodaj zakup'
        return context

class LeaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Lease
    form_class = LeaseForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('lease_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni zakup'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class LeaseDetailView(LoginRequiredMixin, DetailView):
    model = Lease
    template_name = 'fleet/lease_detail.html'
    context_object_name = 'lease'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji zakupa {self.object.partner_name}"
        return context

class LeaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Lease
    success_url = reverse_lazy('lease_list')
    template_name = 'fleet/lease_confirm_delete.html'
    context_object_name = 'lease'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši zakup'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
    
# LEASE KAMATE FETCH
logger = logging.getLogger(__name__)

def fetch_lease_interest_data(request):
    if request.method == 'POST':
        # Povlačenje podataka iz view-a u bazi
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT god, ugovor, iznos FROM dbo.lizing_kamate
            """)
            rows = cursor.fetchall()

        for row in rows:
            year = row[0]
            contract_number = row[1].strip()
            interest_amount = row[2]

            try:
                # Pronađi ugovor lizinga po broju ugovora
                lease = Lease.objects.get(contract_number=contract_number)

                # Proveri da li već postoji zapis za tu godinu i lizing ugovor
                lease_interest, created = LeaseInterest.objects.get_or_create(
                    lease=lease,
                    year=year,
                    defaults={'interest_amount': interest_amount}
                )

                if not created:
                    # Ako zapis već postoji, možeš ga ažurirati ako je potrebno
                    lease_interest.interest_amount = interest_amount
                    lease_interest.save()

            except Lease.DoesNotExist:
                logger.warning(f"Lizing ugovor sa brojem {contract_number} nije pronađen.")
                continue

        # Nakon uspešne obrade, preusmeravanje ili prikaz poruke
        return redirect('fetch_policies')  # Preusmeri na odgovarajući URL za prikaz lizing kamata

    return render(request, 'fleet/fetch_policies.html')

# <!-- ======================================================================= -->
#                           <!-- LEASE -->
# <!-- ======================================================================= -->
class PolicyListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'fleet/policy_list.html'
    context_object_name = 'policies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista polisa osiguranja'
        return context

class PolicyFixingListView(LoginRequiredMixin, ListView):
    model = Policy
    template_name = 'fleet/policy_list.html'
    context_object_name = 'policies'

    def get_queryset(self):
        # Filter policies where the vehicle is None
        return Policy.objects.filter(vehicle__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista polisa osiguranja koje morate dopuniti'
        return context


class PolicyCreateView(LoginRequiredMixin, CreateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('policy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novu polisu osiguranja'
        context['submit_button_label'] = 'Dodaj polisu'
        return context

class PolicyUpdateView(LoginRequiredMixin, UpdateView):
    model = Policy
    form_class = PolicyForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('policy_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni polisu osiguranja'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class PolicyDetailView(LoginRequiredMixin, DetailView):
    model = Policy
    template_name = 'fleet/policy_detail.html'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji polise {self.object.policy_number}"
        return context

class PolicyDeleteView(LoginRequiredMixin, DeleteView):
    model = Policy
    success_url = reverse_lazy('policy_list')
    template_name = 'fleet/policy_confirm_delete.html'
    context_object_name = 'policy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši polisu osiguranja'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)


def fetch_policies_view(request):
    if request.method == 'POST':
        # Povlačenje podataka iz view-a u drugoj bazi
        with connections['test_db'].cursor() as cursor:
            cursor.execute("SELECT PartnerPIB, PartnerIme, ID, BrojFakture, issuedate, VrstaOsiguranja, BrojPolise, IznosPremije FROM dbo.v_polise")
            rows = cursor.fetchall()

        for row in rows:
            # Kreiraj Policy objekte sa povučenim podacima
            try:
                policy = Policy(
                    vehicle=None,  # Ostavljaš vehicle prazno da ga korisnik kasnije doda
                    partner_pib=row[0],
                    partner_name=row[1],
                    invoice_id=row[2],  # Ovo polje je unique
                    invoice_number=row[3],
                    issue_date=row[4],
                    insurance_type=row[5],
                    policy_number=row[6],
                    premium_amount=row[7],
                )
                policy.save()
            except IntegrityError:
                # Ako postoji prekršeni unique constraint, preskoči unos
                continue
        
        # Poruka o uspehu
        messages.success(request, "Podaci su uspešno povučeni i sačuvani.")

        # Preusmeravanje posle uspešnog povlačenja podataka
        return redirect('policy_list')  # Ovde postavi URL na koji želiš da korisnika preusmeriš posle uspeha

    return render(request, 'fleet/fetch_policies.html')




# <!-- ======================================================================================== -->
#                           <!-- FUEL CONSUMPTION -->
# <!-- ======================================================================================== -->
class FuelConsumptionListView(LoginRequiredMixin, FilterView):
    model = FuelConsumption
    filterset_class = FuelFilterForm
    template_name = 'fleet/fuelconsumption_list.html'
    context_object_name = 'fuel_consumptions'


    def get_queryset(self):
        queryset = super().get_queryset()
        # Subquery to get the latest TrafficCard for each Vehicle
        latest_traffic_card_subquery = TrafficCard.objects.filter(
            vehicle_id=OuterRef('vehicle_id')
        ).order_by('-issue_date').values('registration_number')[:1]

        queryset = queryset.annotate(
            registration_number=Subquery(latest_traffic_card_subquery)
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista potrošnje goriva'

        return context

class FuelConsumptionCreateView(LoginRequiredMixin, CreateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('fuelconsumption_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj potrošnju goriva'
        context['submit_button_label'] = 'Dodaj'
        return context

class FuelConsumptionUpdateView(LoginRequiredMixin, UpdateView):
    model = FuelConsumption
    form_class = FuelConsumptionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('fuelconsumption_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni potrošnju goriva'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class FuelConsumptionDetailView(LoginRequiredMixin, DetailView):
    model = FuelConsumption
    template_name = 'fleet/fuelconsumption_detail.html'
    context_object_name = 'fuel_consumption'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji potrošnje goriva {self.object.date}"
        return context

class FuelConsumptionDeleteView(LoginRequiredMixin, DeleteView):
    model = FuelConsumption
    success_url = reverse_lazy('fuelconsumption_list')
    template_name = 'fleet/fuelconsumption_confirm_delete.html'
    context_object_name = 'fuel_consumption'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši potrošnju goriva'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)





# <!-- ======================================================================================== -->
#                           <!-- EMPLOYEES -->
# <!-- ======================================================================================== -->
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'fleet/employee_list.html'
    context_object_name = 'employees'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista zaposlenih'
        return context

class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiraj novog zaposlenog'
        context['submit_button_label'] = 'Dodaj zaposlenog'
        return context

class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni podatke zaposlenog'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    model = Employee
    template_name = 'fleet/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji zaposlenog {self.object.name}"
        return context

class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    success_url = reverse_lazy('employee_list')
    template_name = 'fleet/employee_confirm_delete.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši zaposlenog'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)




# <!-- ======================================================================================== -->
#                           <!-- FUEL CONSUMPTION -->
# <!-- ======================================================================================== -->
class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = 'fleet/incident_list.html'
    context_object_name = 'incidents'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista incidenata'
        return context

class IncidentCreateView(LoginRequiredMixin, CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('incident_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj incident'
        context['submit_button_label'] = 'Dodaj'
        return context

class IncidentUpdateView(LoginRequiredMixin, UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('incident_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni incident'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class IncidentDetailView(LoginRequiredMixin, DetailView):
    model = Incident
    template_name = 'fleet/incident_detail.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji incidenta {self.object.date}"
        return context

class IncidentDeleteView(LoginRequiredMixin, DeleteView):
    model = Incident
    success_url = reverse_lazy('incident_list')
    template_name = 'fleet/incident_confirm_delete.html'
    context_object_name = 'incident'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši incident'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)




# <!-- ======================================================================================== -->
#                           <!-- PUTNI NALOG -->
# <!-- ======================================================================================== -->
class PutniNalogListView(LoginRequiredMixin, ListView):
    model = PutniNalog
    template_name = 'fleet/putninalog_list.html'
    context_object_name = 'putni_nalozi'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista putnih naloga'
        return context

class PutniNalogCreateView(LoginRequiredMixin, CreateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('putninalog_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj putni nalog'
        context['submit_button_label'] = 'Dodaj'
        return context

class PutniNalogUpdateView(LoginRequiredMixin, UpdateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('putninalog_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni putni nalog'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class PutniNalogDetailView(LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = 'fleet/putninalog_detail.html'
    context_object_name = 'putni_nalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji putnog naloga {self.object.travel_date}"
        return context

class PutniNalogDeleteView(LoginRequiredMixin, DeleteView):
    model = PutniNalog
    success_url = reverse_lazy('putninalog_list')
    template_name = 'fleet/putninalog_confirm_delete.html'
    context_object_name = 'putni_nalog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši putni nalog'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)




# <!-- ======================================================================================== -->
#                           <!-- SERVICE TYPES -->
# <!-- ======================================================================================== -->
class ServiceTypeListView(LoginRequiredMixin, ListView):
    model = ServiceType
    template_name = 'fleet/servicetype_list.html'
    context_object_name = 'service_types'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista tipova servisa'
        return context

class ServiceTypeCreateView(LoginRequiredMixin, CreateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('servicetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj tip servisa'
        context['submit_button_label'] = 'Dodaj'
        return context

class ServiceTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceType
    form_class = ServiceTypeForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('servicetype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni tip servisa'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceTypeDetailView(LoginRequiredMixin, DetailView):
    model = ServiceType
    template_name = 'fleet/servicetype_detail.html'
    context_object_name = 'service_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji tipa servisa {self.object.name}"
        return context

class ServiceTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = ServiceType
    success_url = reverse_lazy('servicetype_list')
    template_name = 'fleet/servicetype_confirm_delete.html'
    context_object_name = 'service_type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši tip servisa'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)



# <!-- ======================================================================================== -->
#                           <!-- SERVICES -->
# <!-- ======================================================================================== -->

# POVLACENJE PODATAKA IZ DRUGE BAZE
logger = logging.getLogger(__name__)  
def fetch_service_data_view(request):
    if request.method == 'POST':
        # Povlačenje podataka iz druge baze
        with connections['test_db'].cursor() as cursor:
            cursor.execute("""
                SELECT god, sif_par_pl, naz_par_pl, datum, sif_vrs, br_naloga, vez_dok, knt_pl, potrazuje, sif_par_npl, knt_npl, duguje, sif_pos, konto_vozila FROM dbo.v_servisi
            """)
            rows = cursor.fetchall()

        for row in rows:
            try:
                # Provera jedinstvenosti na osnovu kombinacije datum, duguje, vez_dok
                if not ServiceTransaction.objects.filter(datum=row[3], duguje=row[11], vez_dok=row[6]).exists():
                    # Kreiranje novog zapisa ako ne postoji duplikat
                    service_transaction = ServiceTransaction(
                        vehicle=None,
                        god=row[0],
                        sif_par_pl=row[1],
                        naz_par_pl=row[2],
                        datum=row[3],  # Datum transakcije
                        sif_vrs=row[4],
                        br_naloga=row[5],
                        vez_dok=row[6],
                        knt_pl=row[7],
                        potrazuje=row[8],
                        sif_par_npl=row[9],
                        knt_npl=row[10],
                        duguje=row[11],
                        konto_vozila=row[13],
                        kom=None,
                        popravka_kategorija=None,  # Kategorija popravke
                        napomena=None
                    )
                    service_transaction.save()

            except IntegrityError:
                logger.warning(f"Duplikat: Datum: {row[3]}, Duguje: {row[11]}, Vezani dokument: {row[6]}")
                continue  # Preskače zapis ako postoji duplikat

            except Exception as e:
                logger.error(f"Greška: {e}")
                messages.error(request, "Došlo je do greške prilikom povlačenja podataka.")
                return redirect('fetch_policies')

        # Poruka o uspehu
        messages.success(request, "Podaci su uspešno povučeni i sačuvani, preskočeni su duplikati.")

        # Preusmeravanje posle uspešnog povlačenja podataka
        return redirect('service_fixing_list')  # Postavi URL na koji želiš da preusmeriš korisnika

    return render(request, 'fleet/fetch_policies.html')

class ServiceListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'fleet/service_list.html'
    context_object_name = 'services'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista servisa'
        return context

class ServiceFixingListView(LoginRequiredMixin, ListView):
    model = Service
    template_name = 'fleet/service_list.html'
    context_object_name = 'services'

    def get_queryset(self):
        # Filter policies where the vehicle is None
        return Service.objects.filter(vehicle__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista servisa koje morate dopuniti'
        return context


class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj servis'
        context['submit_button_label'] = 'Dodaj'
        return context

class ServiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmeni servis'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'fleet/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Detalji servisa {self.object.service_date}"
        return context

class ServiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Service
    success_url = reverse_lazy('service_list')
    template_name = 'fleet/service_confirm_delete.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Obriši servis'
        return context

    def get_object(self, queryset=None):
        return super().get_object(queryset)
    


# <!-- ======================================================================================== -->
#                           <!-- SERVICE TRANSACTIONS -->
# <!-- ======================================================================================== -->
class ServiceTransactionListView(ListView):
    model = ServiceTransaction
    template_name = 'fleet/service_transactions_list.html'
    context_object_name = 'service_transactions'

class ServiceTransactionFixingListView(LoginRequiredMixin, ListView):
    model = ServiceTransaction
    template_name = 'fleet/service_transactions_list.html'
    context_object_name = 'service_transactions'

    def get_queryset(self):
        # Filter policies where the vehicle is None
        return ServiceTransaction.objects.filter(vehicle__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Lista servisa koje morate dopuniti'
        return context

class ServiceTransactionCreateView(CreateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_transaction_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Kreiranje servisa'
        context['submit_button_label'] = 'Sačuvaj insformacije o servisu'
        return context
class ServiceTransactionUpdateView(UpdateView):
    model = ServiceTransaction
    form_class = ServiceTransactionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('service_transaction_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmena servisa'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class ServiceTransactionDeleteView(DeleteView):
    model = ServiceTransaction
    template_name = 'service_transaction_confirm_delete.html'
    success_url = reverse_lazy('service_transaction_list')



# <!-- ======================================================================================== -->
#                           <!-- REQUISTION - TREBOVANJA -->
# <!-- ======================================================================================== -->

# Povlačenje podataka iz view-a u drugoj bazi
def fetch_requisition_data_view(request):
    if request.method == 'POST':
        try:
            # Povlačenje podataka iz view-a u drugoj bazi
            with connections['test_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT sif_pred, god, oj, sif_dok, sif_vrsart, br_dok, stavka, sif_art, naz_art, kol, cena, vrednost_nab
                    FROM dbo.v_trebovanja
                """)
                rows = cursor.fetchall()

            for row in rows:
                try:
                    # Kreiranje ili ažuriranje modela `Requisition`
                    requisition = Requisition(
                        vehicle=None,
                        sif_pred=row[0],  # Šifra predmeta
                        god=row[1],  # Godina
                        br_dok=row[5],  # Broj dokumenta
                        sif_vrsart=row[4],  # Šifra vrste artikla
                        stavka=row[6],  # Stavka
                        sif_art=row[7],  # Šifra artikla
                        naz_art=row[8],  # Naziv artikla
                        kol=row[9],  # Količina
                        cena=row[10],  # Cena
                        vrednost_nab=row[11],  # Vrednost nabavke
                        mesec_unosa=None,  # Mesec unosa
                        datum_trebovanja=None,  # Datum trebovanja
                        napomena=None,  # Napomena
                    )
                    requisition.save()

                except IntegrityError as e:
                    # Ako postoji greška zbog unique constraint-a, preskoči unos
                    print(f"Greška prilikom čuvanja dokumenta {row[5]}: {e}")
                    continue

            # Poruka o uspehu
            messages.success(request, "Podaci su uspešno povučeni i sačuvani, preskočeni su duplikati.")

            # Preusmeravanje posle uspešnog povlačenja podataka
            return redirect('requisition_list')  # Postavi URL na koji želiš da preusmeriš korisnika

        except Exception as e:
            print(f"Greška prilikom povlačenja podataka: {e}")
            messages.error(request, "Došlo je do greške prilikom povlačenja podataka.")
            return redirect('error_page')

    return render(request, 'fleet\fetch_policies.html')

class RequisitionListView(ListView):
    model = Requisition
    template_name = 'fleet/requisition_list.html'
    context_object_name = 'requisitions'
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Trebovanja'
        return context
    
class RequisitionFixingListView(ListView):
    model = Requisition
    template_name = 'fleet/requisition_list.html'
    context_object_name = 'requisitions'
    
    def get_queryset(self):
        # Filter policies where the vehicle is None
        return Requisition.objects.filter(vehicle__isnull=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Trebovanja koja je potrebno dopuniti'
        return context
    
class RequisitionCreateView(CreateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Requisition successfully created."

class RequisitionUpdateView(UpdateView):
    model = Requisition
    form_class = RequisitionForm
    template_name = 'fleet/generic_form.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Trebovanje uspešno izmenjeno!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Izmena trebovanja'
        context['submit_button_label'] = 'Sačuvaj izmene'
        return context

class RequisitionDeleteView(DeleteView):
    model = Requisition
    template_name = 'requisition/requisition_confirm_delete.html'
    success_url = reverse_lazy('requisition_list')
    success_message = "Requisition successfully deleted."


# <!-- ======================================================================================== -->
#                           <!-- REQUISTION - TREBOVANJA -->
# <!-- ======================================================================================== -->

class UserListView(ListView):
    model = CustomUser
    template_name = 'fleet/user_list.html'  # Specify your template
    context_object_name = 'users'     # The name of the variable to use in the template

    # Optionally, you can override get_queryset to filter users if needed
    def get_queryset(self):
        # You can apply any filters if needed, otherwise return all users
        return CustomUser.objects.all()