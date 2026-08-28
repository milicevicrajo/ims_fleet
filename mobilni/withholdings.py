from dataclasses import dataclass
import datetime
from decimal import Decimal

from django.db.models import F, Q

from .models import MobileParkingExemption, MobileUsage


REPORT_ALL = "sve"
REPORT_EMPLOYEES = "zaposleni"
REPORT_FORMER_EMPLOYEES = "bivsi-zaposleni"
REPORT_TYPES = {REPORT_ALL, REPORT_EMPLOYEES, REPORT_FORMER_EMPLOYEES}

SPECIAL_PHONE_NUMBER = "381637781481"


@dataclass(frozen=True)
class WithholdingRow:
    usage: MobileUsage
    employee_code: int | None
    employee_name: str
    package_name: str
    package_net_amount: Decimal | None
    withholding: Decimal | None
    parking_exempt: bool

    @property
    def year(self):
        return self.usage.year

    @property
    def month(self):
        return self.usage.month

    @property
    def phone_number(self):
        return self.usage.phone_number


def normalize_phone_number(value):
    value = str(value or "").strip()
    if value.endswith(".0"):
        value = value[:-2]
    return "".join(ch for ch in value if ch.isdigit()) or value


def parking_exempt_phone_numbers(year=None, month=None):
    return {normalize_phone_number(item.phone_number) for item in MobileParkingExemption.objects.all()}


def assignment_employee_code(assignment):
    return assignment.employee.employee_code if assignment and assignment.employee_id else None


def assignment_employee_name(assignment):
    if not assignment or not assignment.employee_id:
        return ""
    return str(assignment.employee).strip() or assignment.employee.original_full_name or ""


def assignment_employee_active(assignment):
    return bool(assignment and assignment.employee_id and assignment.employee.is_active)


def assignment_package_name(assignment):
    return assignment.package.name if assignment and assignment.package_id else ""


def assignment_package_amount(assignment):
    return assignment.package.net_amount if assignment and assignment.package_id else None


def is_parking_exempt(usage, exempt_phone_numbers=None):
    if exempt_phone_numbers is None:
        exempt_phone_numbers = parking_exempt_phone_numbers(usage.year, usage.month)
    return normalize_phone_number(usage.phone_number) in exempt_phone_numbers


def calculate_withholding(usage, exempt_phone_numbers=None):
    assignment = usage.assignment
    if assignment is None:
        return None

    phone_number = normalize_phone_number(usage.phone_number)
    package_amount = assignment_package_amount(assignment)
    if phone_number == SPECIAL_PHONE_NUMBER:
        package_deduction = Decimal("0")
    elif package_amount is None:
        return None
    else:
        package_deduction = package_amount

    parking = Decimal("0") if is_parking_exempt(usage, exempt_phone_numbers) else usage.parking
    return usage.vat_base - package_deduction + parking + usage.nzrd


def withholding_usage_queryset(
    *,
    year=None,
    month=None,
    search="",
    phone_number="",
    employee="",
    package_id=None,
):
    queryset = (
        MobileUsage.objects.filter(
            assignment__isnull=False,
            year=F("assignment__year"),
            month=F("assignment__month"),
            phone_number=F("assignment__phone_number"),
        )
        .select_related("assignment__package", "assignment__employee")
        .order_by("-year", "-month", "assignment__employee__last_name", "assignment__employee__first_name", "phone_number")
    )
    if year:
        queryset = queryset.filter(year=year)
    if month:
        queryset = queryset.filter(month=month)
    phone_number = (phone_number or "").strip()
    if phone_number:
        queryset = queryset.filter(phone_number__icontains=phone_number)
    employee = (employee or "").strip()
    if employee:
        employee_query = (
            Q(assignment__employee__first_name__icontains=employee)
            | Q(assignment__employee__last_name__icontains=employee)
            | Q(assignment__employee__original_full_name__icontains=employee)
        )
        if employee.isdigit():
            employee_query |= Q(assignment__employee__employee_code=int(employee))
        queryset = queryset.filter(employee_query)
    if package_id:
        queryset = queryset.filter(assignment__package_id=package_id)
    search = (search or "").strip()
    if search:
        query = (
            Q(phone_number__icontains=search)
            | Q(assignment__employee__first_name__icontains=search)
            | Q(assignment__employee__last_name__icontains=search)
            | Q(assignment__employee__original_full_name__icontains=search)
            | Q(assignment__package__name__icontains=search)
        )
        if search.isdigit():
            query |= Q(assignment__employee__employee_code=int(search))
        queryset = queryset.filter(query)
    return queryset


def _is_former_employee_for_period(usage):
    assignment = usage.assignment
    if not assignment or not assignment.employee_id or assignment.employee.is_active:
        return False
    mobile_user = assignment.employee.mobile_users.order_by("-id").first()
    if mobile_user and mobile_user.departure_date:
        period_start = datetime.date(usage.year, usage.month, 1)
        return mobile_user.departure_date < period_start
    return True


def get_withholding_rows(
    report_type,
    *,
    year=None,
    month=None,
    search="",
    phone_number="",
    employee="",
    package_id=None,
):
    if report_type not in REPORT_TYPES:
        raise ValueError(f"Nepoznat izveštaj obustava: {report_type}")

    usages = withholding_usage_queryset(
        year=year,
        month=month,
        search=search,
        phone_number=phone_number,
        employee=employee,
        package_id=package_id,
    )
    exempt_phone_numbers = parking_exempt_phone_numbers(year, month)
    rows = []
    for usage in usages:
        assignment = usage.assignment
        employee_code = assignment_employee_code(assignment)
        employee_name = assignment_employee_name(assignment)
        if report_type == REPORT_EMPLOYEES and (
            not assignment_employee_active(assignment) or employee_code is None
        ):
            continue
        if report_type == REPORT_FORMER_EMPLOYEES and not _is_former_employee_for_period(usage):
            continue

        parking_exempt = is_parking_exempt(usage, exempt_phone_numbers)
        rows.append(
            WithholdingRow(
                usage=usage,
                employee_code=employee_code,
                employee_name=employee_name,
                package_name=assignment_package_name(assignment),
                package_net_amount=assignment_package_amount(assignment),
                withholding=calculate_withholding(usage, exempt_phone_numbers),
                parking_exempt=parking_exempt,
            )
        )
    return rows
