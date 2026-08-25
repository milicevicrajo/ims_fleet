import calendar
import datetime
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import F, Q

from .models import MobileUsage


REPORT_ALL = "sve"
REPORT_EMPLOYEES = "zaposleni"
REPORT_FORMER_EMPLOYEES = "bivsi-zaposleni"
REPORT_TYPES = {REPORT_ALL, REPORT_EMPLOYEES, REPORT_FORMER_EMPLOYEES}

SPECIAL_PHONE_NUMBER = "381637781481"
PARKING_EXEMPT_EMPLOYEE_CODES = {141, 647}


@dataclass(frozen=True)
class WithholdingRow:
    usage: MobileUsage
    employee_code: int | None
    employee_name: str
    package_name: str
    package_net_amount: Decimal | None
    withholding: Decimal | None

    @property
    def year(self):
        return self.usage.year

    @property
    def month(self):
        return self.usage.month

    @property
    def phone_number(self):
        return self.usage.phone_number


def _normalized_phone_number(value):
    value = str(value or "").strip()
    if value.endswith(".0"):
        value = value[:-2]
    return value


def calculate_withholding(usage):
    assignment = usage.assignment
    if assignment is None:
        return None

    phone_number = _normalized_phone_number(usage.phone_number)
    package_amount = assignment.package.net_amount if assignment.package_id else None
    if phone_number == SPECIAL_PHONE_NUMBER:
        package_deduction = Decimal("0")
    elif package_amount is None:
        return None
    else:
        package_deduction = package_amount

    parking = (
        Decimal("0")
        if assignment.employee_code in PARKING_EXEMPT_EMPLOYEE_CODES
        else usage.parking
    )
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
        .select_related("assignment__package", "assignment__mobile_user")
        .order_by("-year", "-month", "assignment__employee_name", "phone_number")
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
        employee_query = Q(assignment__employee_name__icontains=employee)
        if employee.isdigit():
            employee_query |= Q(assignment__employee_code=int(employee))
        queryset = queryset.filter(employee_query)
    if package_id:
        queryset = queryset.filter(assignment__package_id=package_id)
    search = (search or "").strip()
    if search:
        query = Q(phone_number__icontains=search) | Q(assignment__employee_name__icontains=search)
        if search.isdigit():
            query |= Q(assignment__employee_code=int(search))
        queryset = queryset.filter(query)
    return queryset


def _is_former_employee_for_period(usage):
    assignment = usage.assignment
    if assignment.employee_active or not assignment.mobile_user_id:
        return False
    departure_date = assignment.mobile_user.departure_date
    if departure_date is None:
        return False
    month_end = datetime.date(
        usage.year,
        usage.month,
        calendar.monthrange(usage.year, usage.month)[1],
    )
    return departure_date < month_end


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
    rows = []
    for usage in usages:
        assignment = usage.assignment
        if report_type == REPORT_EMPLOYEES and (
            not assignment.employee_active or assignment.employee_code is None
        ):
            continue
        if report_type == REPORT_FORMER_EMPLOYEES and not _is_former_employee_for_period(usage):
            continue

        package_amount = assignment.package.net_amount if assignment.package_id else None
        rows.append(
            WithholdingRow(
                usage=usage,
                employee_code=assignment.employee_code,
                employee_name=assignment.employee_name,
                package_name=assignment.package_name,
                package_net_amount=package_amount,
                withholding=calculate_withholding(usage),
            )
        )
    return rows
