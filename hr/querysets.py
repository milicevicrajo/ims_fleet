from fleet.models import Employee


def employee_list_queryset(show_inactive=False):
    return Employee.objects.filter(is_active=not show_inactive).order_by("last_name", "first_name")


def employees_for_travel_orders(queryset):
    return (
        Employee.objects.filter(travel_orders__in=queryset)
        .distinct()
        .order_by("last_name", "first_name")
    )
