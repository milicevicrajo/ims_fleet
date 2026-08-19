from django.urls import path

from .views.mobile import (
    MobileAssignmentCreateView,
    MobileAssignmentDeleteView,
    MobileAssignmentListView,
    MobileAssignmentUpdateView,
    MobileDashboardView,
    MobilePackageCreateView,
    MobilePackageDeleteView,
    MobilePackageListView,
    MobilePackageUpdateView,
    MobileUsageCreateView,
    MobileUsageDeleteView,
    MobileUsageListView,
    MobileUsageUpdateView,
    MobileUserCreateView,
    MobileUserDeleteView,
    MobileUserListView,
    MobileUserUpdateView,
    export_assignments_xlsx,
    export_packages_xlsx,
    export_usages_xlsx,
    export_users_xlsx,
    mobile_import_view,
)


app_name = "mobilni"

urlpatterns = [
    path("", MobileDashboardView.as_view(), name="mobile_dashboard"),
    path("import/", mobile_import_view, name="mobile_import"),
    path("dodele/", MobileAssignmentListView.as_view(), name="mobile_assignment_list"),
    path("dodele/export.xlsx", export_assignments_xlsx, name="mobile_assignment_export"),
    path("dodele/novo/", MobileAssignmentCreateView.as_view(), name="mobile_assignment_create"),
    path("dodele/<int:pk>/izmena/", MobileAssignmentUpdateView.as_view(), name="mobile_assignment_update"),
    path("dodele/<int:pk>/brisanje/", MobileAssignmentDeleteView.as_view(), name="mobile_assignment_delete"),
    path("potrosnja/", MobileUsageListView.as_view(), name="mobile_usage_list"),
    path("potrosnja/export.xlsx", export_usages_xlsx, name="mobile_usage_export"),
    path("potrosnja/novo/", MobileUsageCreateView.as_view(), name="mobile_usage_create"),
    path("potrosnja/<int:pk>/izmena/", MobileUsageUpdateView.as_view(), name="mobile_usage_update"),
    path("potrosnja/<int:pk>/brisanje/", MobileUsageDeleteView.as_view(), name="mobile_usage_delete"),
    path("paketi/", MobilePackageListView.as_view(), name="mobile_package_list"),
    path("paketi/export.xlsx", export_packages_xlsx, name="mobile_package_export"),
    path("paketi/novo/", MobilePackageCreateView.as_view(), name="mobile_package_create"),
    path("paketi/<int:pk>/izmena/", MobilePackageUpdateView.as_view(), name="mobile_package_update"),
    path("paketi/<int:pk>/brisanje/", MobilePackageDeleteView.as_view(), name="mobile_package_delete"),
    path("korisnici/", MobileUserListView.as_view(), name="mobile_user_list"),
    path("korisnici/export.xlsx", export_users_xlsx, name="mobile_user_export"),
    path("korisnici/novo/", MobileUserCreateView.as_view(), name="mobile_user_create"),
    path("korisnici/<int:pk>/izmena/", MobileUserUpdateView.as_view(), name="mobile_user_update"),
    path("korisnici/<int:pk>/brisanje/", MobileUserDeleteView.as_view(), name="mobile_user_delete"),
]
