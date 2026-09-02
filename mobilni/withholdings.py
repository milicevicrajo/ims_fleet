from dataclasses import dataclass
import datetime
from decimal import Decimal

from django.db.models import Case, DecimalField, ExpressionWrapper, F, Q, Value, When

from .models import MobileParkingExemption, MobileUsage, MobileUser


REPORT_ALL = "sve"
REPORT_EMPLOYEES = "zaposleni"
REPORT_FORMER_EMPLOYEES = "bivsi-zaposleni"
REPORT_NON_EMPLOYEES = "nezaposleni"
REPORT_TYPES = {REPORT_ALL, REPORT_EMPLOYEES, REPORT_FORMER_EMPLOYEES, REPORT_NON_EMPLOYEES}

SPECIAL_PHONE_NUMBER = "381637781481"
MONEY_FIELD = DecimalField(max_digits=14, decimal_places=2)


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


def withholding_exact_usage_queryset(*, year=None, month=None, phone_number="", package_id=None):
    queryset = MobileUsage.objects.filter(
        assignment__isnull=False,
        year=F("assignment__year"),
        month=F("assignment__month"),
        phone_number=F("assignment__phone_number"),
    )
    if year:
        queryset = queryset.filter(year=year)
    if month:
        queryset = queryset.filter(month=month)
    phone_number = (phone_number or "").strip()
    if phone_number:
        queryset = queryset.filter(phone_number__icontains=phone_number)
    if package_id:
        queryset = queryset.filter(assignment__package_id=package_id)
    return queryset


def withholding_amount_expression(exempt_phone_numbers=None):
    exempt_phone_numbers = list(exempt_phone_numbers or [])
    zero = Value(Decimal("0.00"), output_field=MONEY_FIELD)
    no_amount = Value(None, output_field=MONEY_FIELD)
    parking = F("parking")
    if exempt_phone_numbers:
        parking = Case(
            When(phone_number__in=exempt_phone_numbers, then=zero),
            default=F("parking"),
            output_field=MONEY_FIELD,
        )

    special_total = ExpressionWrapper(
        F("vat_base") + parking + F("nzrd"),
        output_field=MONEY_FIELD,
    )
    standard_total = ExpressionWrapper(
        F("vat_base") - F("assignment__package__net_amount") + parking + F("nzrd"),
        output_field=MONEY_FIELD,
    )
    return Case(
        When(phone_number=SPECIAL_PHONE_NUMBER, then=special_total),
        When(assignment__package__net_amount__isnull=True, then=no_amount),
        default=standard_total,
        output_field=MONEY_FIELD,
    )


def assignment_employee_code(assignment):
    if not assignment:
        return None
    employee = assignment_linked_employee(assignment)
    if employee:
        return employee.employee_code
    if assignment.source_employee_code is not None:
        return assignment.source_employee_code
    if assignment.mobile_user_id:
        return assignment.mobile_user.employee_code
    return None


def assignment_employee_name(assignment):
    if not assignment:
        return ""
    employee = assignment_linked_employee(assignment)
    if employee:
        return str(employee).strip() or employee.original_full_name or ""
    if assignment.mobile_user_id and assignment.mobile_user.full_name:
        return assignment.mobile_user.full_name
    return assignment.source_full_name or ""


def assignment_employee_active(assignment):
    employee = assignment_linked_employee(assignment)
    return bool(employee and employee.is_active)


def assignment_linked_employee(assignment):
    if not assignment:
        return None
    if assignment.mobile_user_id:
        if assignment.mobile_user.link_status == MobileUser.LinkStatus.NON_EMPLOYEE:
            return None
        return assignment.mobile_user.employee if assignment.mobile_user.employee_id else None
    return assignment.employee if assignment.employee_id else None


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
        withholding_exact_usage_queryset(
            year=year,
            month=month,
            phone_number=phone_number,
            package_id=package_id,
        )
        .select_related(
            "assignment__package",
            "assignment__employee",
            "assignment__mobile_user",
            "assignment__mobile_user__employee",
        )
        .order_by(
            "-year",
            "-month",
            "assignment__mobile_user__full_name",
            "assignment__employee__last_name",
            "assignment__employee__first_name",
            "phone_number",
        )
    )
    employee = (employee or "").strip()
    if employee:
        employee_query = (
            Q(assignment__employee__first_name__icontains=employee)
            | Q(assignment__employee__last_name__icontains=employee)
            | Q(assignment__employee__original_full_name__icontains=employee)
            | Q(assignment__mobile_user__full_name__icontains=employee)
            | Q(assignment__source_full_name__icontains=employee)
        )
        if employee.isdigit():
            employee_query |= Q(assignment__employee__employee_code=int(employee))
            employee_query |= Q(assignment__mobile_user__employee_code=int(employee))
            employee_query |= Q(assignment__mobile_user__employee__employee_code=int(employee))
            employee_query |= Q(assignment__source_employee_code=int(employee))
        queryset = queryset.filter(employee_query)
    search = (search or "").strip()
    if search:
        query = (
            Q(phone_number__icontains=search)
            | Q(assignment__employee__first_name__icontains=search)
            | Q(assignment__employee__last_name__icontains=search)
            | Q(assignment__employee__original_full_name__icontains=search)
            | Q(assignment__mobile_user__full_name__icontains=search)
            | Q(assignment__source_full_name__icontains=search)
            | Q(assignment__package__name__icontains=search)
        )
        if search.isdigit():
            query |= Q(assignment__employee__employee_code=int(search))
            query |= Q(assignment__mobile_user__employee_code=int(search))
            query |= Q(assignment__mobile_user__employee__employee_code=int(search))
            query |= Q(assignment__source_employee_code=int(search))
        queryset = queryset.filter(query)
    return queryset


def _is_former_employee_for_period(usage):
    assignment = usage.assignment
    employee = assignment_linked_employee(assignment)
    if not employee or employee.is_active:
        return False
    mobile_user = assignment.mobile_user if assignment and assignment.mobile_user_id else None
    if not mobile_user:
        mobile_user = employee.mobile_users.order_by("-id").first()
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
        linked_employee = assignment_linked_employee(assignment)
        employee_code = assignment_employee_code(assignment)
        employee_name = assignment_employee_name(assignment)
        if report_type == REPORT_EMPLOYEES and not (linked_employee and linked_employee.is_active):
            continue
        if report_type == REPORT_FORMER_EMPLOYEES and not _is_former_employee_for_period(usage):
            continue
        if report_type == REPORT_NON_EMPLOYEES and linked_employee is not None:
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
