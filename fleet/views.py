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
from django.db.models import Sum, Exists,Count,Avg
import datetime 
from datetime import date, timedelta
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .utils import calculate_average_fuel_consumption, calculate_average_fuel_consumption_ever
from django.db.models.functions import TruncMonth, TruncYear
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import Q


# <!-- ======================================================================= -->
#                           <!-- DASHBOARD I ANALITIKA -->
# <!-- ======================================================================= -->
def dashboard(request):    
    # Count the number of objects where vehicle is None
    services_without_vehicle = ServiceTransaction.objects.filter(vehicle__isnull=True).count()
    policies_without_vehicle = Policy.objects.filter(vehicle__isnull=True).count()
    requisitions_without_vehicle = Requisition.objects.filter(vehicle__isnull=True).count()
    
    # Get today's date
    today = date.today()

    # Calculate the date 30 days from today
    thirty_days_from_now = today + timedelta(days=30)
    newest_policy = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type')
    ).order_by('-end_date').values('end_date')[:1]
    
    # Filter policies expiring within the next 30 days
    # Filter policies expiring between today and thirty days from now, but exclude older policies if a newer one exists
    expiring_policies = Policy.objects.annotate(
        latest_end_date=Subquery(newest_policy)
    ).filter(
        end_date__gte=today,
        end_date__lte=thirty_days_from_now,
        end_date=F('latest_end_date')
    )
    expiring_policies_count = expiring_policies.count()
        # Subquery to check if there is a newer policy for the same vehicle and insurance type
    newer_policy_exists = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type'),
        start_date__gt=OuterRef('start_date') 
    )

    # Filter policies that have expired but haven't been renewed
    expired_unrenewed_policies = Policy.objects.annotate(
        has_newer_policy=Exists(newer_policy_exists)
    ).filter(
        end_date__lt=today,  # Policies that have already expired
        has_newer_policy=False  # Ensure there is no newer policy
    )
    expired_unrenewed_policies_count = expired_unrenewed_policies.count()

    # Current year and last day of the previous month
    current_year = datetime.datetime.now().year
    first_day_of_current_month = date.today().replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    start_of_year = date.today().replace(month=1, day=1)

    # Number of vehicles
    total_vehicles = Vehicle.objects.count()
    passenger_vehicles = Vehicle.objects.filter(category='PUTNICKO VOZILO').count()
    transport_vehicles = Vehicle.objects.filter(category='TERETNO VOZILO').count()

    # Vehicles by center
    vehicles_by_center = Vehicle.objects.values('center_code').annotate(count=Count('id'))

    # Average vehicle age
    average_age = Vehicle.objects.aggregate(avg_age=(current_year - Avg('year_of_manufacture')))

    # Book value as of the last day of the previous month
    book_value = Vehicle.objects.filter(purchase_date__lte=last_day_of_previous_month).aggregate(total_value=Sum('value'))

    # Yearly costs
    yearly_fuel_costs = FuelConsumption.objects.filter(date__gte=start_of_year).aggregate(total_fuel_cost=Sum('cost_bruto'))
    yearly_service_costs = ServiceTransaction.objects.filter(datum__gte=start_of_year).aggregate(total_service_cost=Sum('potrazuje'))

    # Vehicles in red zone
    red_zone_vehicles = Vehicle.objects.filter(otpis=True)  # or any other criteria
    
    # Vehicle count, average vehicle age, total value, and average vehicle value per center
    center_data = Vehicle.objects.values('center_code').annotate(
        vehicle_count=Count('id', distinct=True),  # Number of vehicles per center
        avg_age=(current_year - Avg('year_of_manufacture')),  # Average age per center
        total_value=Sum('value', distinct=True),  # Total vehicle value per center
        avg_value=Avg('value'),  # Average vehicle value per center
        total_fuel_quantity=Sum('fuel_consumptions__amount'),  # Total fuel quantity per center
        total_fuel_price=Sum('fuel_consumptions__cost_bruto') 
    )


    context = {
        'services_without_vehicle': services_without_vehicle,
        'policies_without_vehicle': policies_without_vehicle,
        'requisitions_without_vehicle': requisitions_without_vehicle,
        'expiring_policies': expiring_policies,
        'expiring_policies_count': expiring_policies_count,
        'expired_unrenewed_policies': expired_unrenewed_policies,
        'expired_unrenewed_policies_count': expired_unrenewed_policies_count,
        'total_vehicles': total_vehicles,
        'passenger_vehicles': passenger_vehicles,
        'transport_vehicles': transport_vehicles,
        'vehicles_by_center': vehicles_by_center,
        'average_age': average_age['avg_age'],
        'book_value': book_value['total_value'],
        'yearly_fuel_costs': yearly_fuel_costs['total_fuel_cost'],
        'yearly_service_costs': yearly_service_costs['total_service_cost'],
        'red_zone_vehicles': red_zone_vehicles,
        'centers': center_data
    }

    return render(request, 'fleet/dashboard.html', context)

def center_statistics(request, center_code):
    # Check if the user has access to this center
    if request.user.allowed_centers:
        if center_code not in request.user.allowed_centers('code', flat=True):
            return HttpResponseForbidden("Nemati pristup ovim podacima.")

    # Fuel consumption statistics (grouped by month and year, filtered by center)
    fuel_data = FuelConsumption.objects.filter(vehicle__center_code=center_code).annotate(
        year=TruncYear('date'),
        month=TruncMonth('date')
    ).values('year', 'month').annotate(
        total_fuel_quantity=Sum('amount'),
        total_fuel_cost=Sum('cost_bruto')
    ).order_by('year', 'month')

    # Service costs statistics (grouped by service type, month, and year, filtered by center)
    service_data = ServiceTransaction.objects.filter(vehicle__center_code=center_code).annotate(
        year=TruncYear('datum'),
        month=TruncMonth('datum')
    ).values('year', 'month').annotate(
        total_cost_gume=Sum('potrazuje', filter=Q(popravka_kategorija__icontains='gume')),
        total_cost_redovan_servis=Sum('potrazuje', filter=Q(popravka_kategorija__icontains='redovan servis')),
        total_cost_tehnicki_pregled=Sum('potrazuje', filter=Q(popravka_kategorija__icontains='tehnicki pregled')),
        total_cost_registracija=Sum('potrazuje', filter=Q(popravka_kategorija__icontains='registracija'))
    ).order_by('year', 'month')
    print(service_data)
    # Registration costs statistics (grouped by month and year, filtered by center)
    insurance_data = Policy.objects.filter(vehicle__center_code=center_code).annotate(
        year=TruncYear('issue_date'),
        month=TruncMonth('issue_date')
    ).values('year', 'month').annotate(
        total_registration_cost=Sum('premium_amount')
    ).order_by('year', 'month')

    # Combine all data based on year and month
    consolidated_data = {}
    
    # Consolidating fuel data
    for fuel in fuel_data:
        year = fuel['year'].year
        month = fuel['month'].month
        consolidated_data[(year, month)] = {
            'total_fuel_quantity': fuel['total_fuel_quantity'],
            'total_fuel_cost': fuel['total_fuel_cost'],
            'total_cost_gume': 0,
            'total_cost_redovan_servis': 0,
            'total_cost_tehnicki_pregled': 0,
            'total_cost_registracija': 0,
            'total_registration_cost': 0
        }

    # Consolidating service data
    for service in service_data:
        year = service['year'].year
        month = service['month'].month
        if (year, month) not in consolidated_data:
            consolidated_data[(year, month)] = {
                'total_fuel_quantity': 0,
                'total_fuel_cost': 0,
                'total_cost_gume': service['total_cost_gume'],
                'total_cost_redovan_servis': service['total_cost_redovan_servis'],
                'total_cost_tehnicki_pregled': service['total_cost_tehnicki_pregled'],
                'total_cost_registracija': service['total_cost_registracija'],
                'total_registration_cost': 0
            }
        else:
            consolidated_data[(year, month)].update({
                'total_cost_gume': service['total_cost_gume'],
                'total_cost_redovan_servis': service['total_cost_redovan_servis'],
                'total_cost_tehnicki_pregled': service['total_cost_tehnicki_pregled'],
                'total_cost_registracija': service['total_cost_registracija']
            })

    # Consolidating insurance data
    for insurance in insurance_data:
        year = insurance['year'].year
        month = insurance['month'].month
        if (year, month) not in consolidated_data:
            consolidated_data[(year, month)] = {
                'total_fuel_quantity': 0,
                'total_fuel_cost': 0,
                'total_cost_gume': 0,
                'total_cost_redovan_servis': 0,
                'total_cost_tehnicki_pregled': 0,
                'total_cost_registracija': 0,
                'total_registration_cost': insurance['total_registration_cost']
            }
        else:
            consolidated_data[(year, month)].update({
                'total_registration_cost': insurance['total_registration_cost']
            })

    context = {
        'consolidated_data': consolidated_data,
        'center_code': center_code,
    }

    return render(request, 'fleet/dashboard_center.html', context)


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

        # 1. Aktivne polise osiguranja
        active_policies = Policy.objects.filter(vehicle=vehicle, end_date__gte=datetime.date.today())

        # 2. Job Code
        current_job_code = JobCode.objects.filter(vehicle=vehicle).order_by('-assigned_date').first()
        job_codes = JobCode.objects.filter(vehicle=vehicle).order_by('-assigned_date')

        
        # 3. Gorivo, kilometraza i kartice
        nis_card = vehicle.nis_transactions.filter().first()
        omv_card = vehicle.omv_transactions.filter().first()

        mileage = vehicle.fuel_consumptions.order_by('-mileage').values_list('mileage', flat=True).first()

        consumptions = vehicle.fuel_consumptions.all() # Za tabelu potrosnje
        average_consumption = calculate_average_fuel_consumption(vehicle) # poslednjih 10
        average_consumption_ever = calculate_average_fuel_consumption_ever(vehicle) # Sva tocenja
        
        # Grupisanje po mesecima i godinama uz dobavljača, agregiranje količine i bruto cene
        fuel_data = FuelConsumption.objects.filter(vehicle=vehicle).annotate(
            month=TruncMonth('date'),
            year=TruncYear('date')
        ).values('month', 'year', 'supplier').annotate(
            total_liters=Sum('amount'),
            total_cost_bruto=Sum('cost_bruto')
        ).order_by('year', 'month', 'supplier')

        # Razdvajanje podataka za OMV i NIS
        omv_data = fuel_data.filter(supplier='OMV')
        nis_data = fuel_data.filter(supplier='NIS')

        # 4. Leasing data
        lease_info = Lease.objects.filter(vehicle=vehicle).order_by('-start_date').first()
        lease_intrests = LeaseInterest.objects.filter(lease=lease_info).order_by('-year')

        # 5. General status (red/green light based on repair costs)
        repair_costs = vehicle.service_transactions.aggregate(total_repairs=Sum('potrazuje'))['total_repairs'] or 0
        requisition_costs = vehicle.requisitions.aggregate(total_requisitions=Sum('vrednost_nab'))['total_requisitions'] or 0

        service_list = vehicle.service_transactions.order_by('-datum')
        requisition_list = vehicle.requisitions.order_by('-datum_trebovanja')
        
        # 6. Saobracajna dozvol i istorija
        trafic_cards = TrafficCard.objects.filter(vehicle=vehicle).order_by('-issue_date')
        trafic_card = trafic_cards.first()
        status_light = 'green' if repair_costs < vehicle.purchase_value else 'red'

        
        context.update({
            'lease_info': lease_info,
            'lease_intrests':lease_intrests,
            'nis_card': nis_card,
            'omv_card': omv_card,
            'mileage': mileage,
            'active_policies': active_policies,
            'average_consumption': average_consumption,
            'average_consumption_ever': average_consumption_ever,
            'omv_data':omv_data,
            'nis_data':nis_data,
            'current_job_code': current_job_code,
            'job_codes': job_codes,
            'status_light': status_light,
            'repair_costs': repair_costs,
            'requisition_costs':requisition_costs,
            'service_list':service_list,
            'requisition_list':requisition_list,
            'consumptions': consumptions,
            'trafic_cards':trafic_cards,
            'trafic_card':trafic_card,
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
#                           <!-- POLICY -->
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

class ExpiringAndNotRenewedPolicyView(LoginRequiredMixin, ListView):
    template_name = 'fleet/policy_expiring.html'
    model = Policy

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_from_now = today + timedelta(days=30)
        
        newest_policy = Policy.objects.filter(
        vehicle=OuterRef('vehicle'),
        insurance_type=OuterRef('insurance_type')
        ).order_by('-end_date').values('end_date')[:1]

        expiring_policies = Policy.objects.annotate(
            latest_end_date=Subquery(newest_policy)
        ).filter(
            end_date__gte=today,
            end_date__lte=thirty_days_from_now,
            end_date=F('latest_end_date')
        )

        newer_policy_exists = Policy.objects.filter(
            vehicle=OuterRef('vehicle'),
            insurance_type=OuterRef('insurance_type'),
            start_date__gt=OuterRef('start_date') 
        )

        # Filter policies that have expired but haven't been renewed
        expired_unrenewed_policies = Policy.objects.annotate(
            has_newer_policy=Exists(newer_policy_exists)
        ).filter(
            end_date__lt=today,  # Policies that have already expired
            has_newer_policy=False  # Ensure there is no newer policy
        )

        context['expiring_policies'] = expiring_policies
        context['expired_unrenewed_policies'] = expired_unrenewed_policies
        context['title'] = 'Liste polisa koje ističu i koje su istekle i nisu obnovljene'
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
                # Postavi podrazumevani period na poslednjih 40 dana
        today = timezone.now().date()
        forty_days_ago = today - timedelta(days=30)

        # Ako nema GET zahteva, koristi podrazumevane datume za filtriranje
        if not self.request.GET:
            queryset = FuelConsumption.objects.filter(date__gte=forty_days_ago, date__lte=today)
        else:
            form = FuelFilterForm(self.request.GET)
            if form.is_valid():
                queryset = form.qs
            else:
                # Ako forma nije validna, prikazi podrazumevane filtrirane podatke
                queryset = FuelConsumption.objects.filter(date__gte=forty_days_ago, date__lte=today)
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