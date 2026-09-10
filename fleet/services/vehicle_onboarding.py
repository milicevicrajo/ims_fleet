"""Atomic vehicle creation shared by the wizard and its tests."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from core.mixins import user_has_role_permission
from ..models import Vehicle, TrafficCard, Lease, VehicleHolding, JobCode, VehicleTravelOrder
from ..forms.onboarding import IDENTITY_FIELDS, TECHNICAL_FIELDS, PURCHASE_FIELDS, CARD_FIELDS


def create_vehicle_from_steps(forms, user):
    identity, basis, technical, document, assignment = [form.cleaned_data for form in forms]
    required = ['vehicle_create']
    if basis['basis'] == 'contract':
        required.append('lease_create')
    if document.get('add_document'):
        required.append('trafficcard_create')
    if assignment.get('organizational_unit'):
        required.append('jobcode_create')
    if assignment.get('assign_employee'):
        required.append('vehicle_travel_order_create')
    for code in required:
        if not user_has_role_permission(user, code):
            raise PermissionDenied(f'Nemate dozvolu za ovaj deo unosa: {code}.')
    for key in ['assigned_date', 'created_at']:
        if assignment.get(key) and assignment[key] < basis['start_date']:
            raise ValidationError('Raspoređivanje i prvo zaduženje ne mogu biti pre početka raspolaganja vozilom.')
    if user.allowed_centers.exists():
        unit = assignment.get('organizational_unit')
        if not unit or not user.allowed_centers.filter(center=unit.center).exists():
            raise PermissionDenied('Vozilo mora biti raspoređeno u dozvoljeni centar.')

    saved_files = []
    try:
        with transaction.atomic():
            # Serialize assignment numbering with the existing fleet rows.
            # Chassis/inventory unique constraints also protect repeated final submits.
            if assignment.get('assign_employee'):
                list(Vehicle.objects.select_for_update().values_list('pk', flat=True))
            data = {key: identity[key] for key in IDENTITY_FIELDS}
            data.update({key: technical[key] for key in TECHNICAL_FIELDS if key in technical})
            if basis['basis'] == 'owned':
                data.update({key: basis.get(key) for key in PURCHASE_FIELDS})
            vehicle = Vehicle(**data)
            vehicle.full_clean()
            try:
                vehicle.save()
            finally:
                if vehicle.photo and vehicle.photo._committed:
                    saved_files.append(vehicle.photo)
            lease = None
            if basis['basis'] == 'contract':
                lease = Lease(
                    vehicle=vehicle, partner_code=basis['partner_code'], partner_name=basis['partner_name'],
                    job_code=assignment['organizational_unit'].code if assignment.get('organizational_unit') else '',
                    contract_number=basis['contract_number'], contract=basis.get('contract'),
                    lease_type=basis['lease_type'], current_payment_amount=basis['current_payment_amount'],
                    start_date=basis['start_date'], end_date=basis['end_date'], note=basis.get('note') or '',
                )
                lease.full_clean(exclude=['job_code'])
                lease.save()
            VehicleHolding.objects.create(
                vehicle=vehicle, basis=basis['basis'], start_date=basis['start_date'],
                end_date=basis.get('end_date'), lease=lease, financing=basis.get('financing') or '',
                financing_contract=basis.get('financing_contract'), evidence=basis.get('evidence') or '', note=basis.get('note') or '',
            )
            if document.get('add_document'):
                card = TrafficCard(vehicle=vehicle, **{key: document.get(key) for key in CARD_FIELDS})
                card.full_clean()
                try:
                    card.save()
                finally:
                    saved_files.extend(field for field in [card.traffic_card_pdf, card.traffic_card_front_image, card.traffic_card_back_image] if field and field._committed)
            if assignment.get('organizational_unit'):
                JobCode.objects.create(vehicle=vehicle, organizational_unit=assignment['organizational_unit'], assigned_date=assignment['assigned_date'])
            if assignment.get('assign_employee'):
                VehicleTravelOrder.objects.create(vehicle=vehicle, employee=assignment['employee'], created_at=assignment['created_at'], start_mileage=assignment['start_mileage'])
            return vehicle
    except Exception:
        for field in saved_files:
            field.storage.delete(field.name)
        raise
