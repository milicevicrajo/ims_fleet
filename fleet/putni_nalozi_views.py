import textwrap

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import ExpressionWrapper, F, IntegerField, Value
from django.db.models.functions import Cast, StrIndex, Substr
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, role_permission_required

from .filters import PutniNalogFilter
from .forms import PutniNalogForm
from .mixins import CenterMixin
from .models import PutniNalog


def _is_uprava(user):
    return user.roles.filter(slug="uprava").exists()


def _get_allowed_centers(user):
    codes = []
    raw = (user.allowed_center_codes or "").strip()
    if raw:
        parts = [part.strip() for part in raw.replace(";", ",").split(",")]
        codes.extend([part for part in parts if part])
    unit_centers = list(user.allowed_centers.values_list("center", flat=True))
    codes.extend([center for center in unit_centers if center])
    return sorted({str(code).strip() for code in codes if str(code).strip()})


def _split_putni_nalog_note_lines(note, max_lines=2, width=70):
    if not note:
        return [""] * max_lines

    wrapped_lines = []
    for raw_line in str(note).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        wrapped = textwrap.wrap(
            line,
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
        wrapped_lines.extend(wrapped or [""])

    if not wrapped_lines:
        wrapped_lines = [""]

    result = wrapped_lines[:max_lines]
    while len(result) < max_lines:
        result.append("")
    return result


def _putninalog_base_qs(request, include_stornirani=False):
    qs = PutniNalog.objects.select_related("job_code", "employee", "vehicle")
    if not include_stornirani:
        qs = qs.filter(storniran=False)
    user = request.user

    if not user.is_superuser and not _is_uprava(user):
        allowed_centers = _get_allowed_centers(user)
        if allowed_centers:
            qs = qs.filter(job_code__center__in=allowed_centers)
        else:
            return qs.none()

    qs = qs.annotate(
        _pn_dash_pos=StrIndex("order_number", Value("-")),
        _pn_slash_pos=StrIndex("order_number", Value("/")),
    ).annotate(
        _pn_year=Cast(
            Substr(
                "order_number",
                F("_pn_slash_pos") + 1,
                F("_pn_dash_pos") - F("_pn_slash_pos") - 1,
            ),
            IntegerField(),
        ),
        _pn_seq=Cast(Substr("order_number", F("_pn_dash_pos") + 1), IntegerField()),
        pn_sort_key=ExpressionWrapper(
            F("_pn_year") * Value(1000000) + F("_pn_seq"),
            output_field=IntegerField(),
        ),
    )

    return qs.order_by("-_pn_year", "-_pn_seq", "-id")


class PutniNalogListView(LoginRequiredMixin, FilterView):
    model = PutniNalog
    template_name = "fleet/putninalog_list.html"
    context_object_name = "putni_nalozi"
    filterset_class = PutniNalogFilter

    def get_queryset(self):
        return _putninalog_base_qs(self.request)

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lista putnih naloga"
        return context


@role_permission_required()
def putninalog_print_list(request):
    base_qs = _putninalog_base_qs(request)
    filterset = PutniNalogFilter(request.GET, queryset=base_qs, request=request)
    putni_nalozi = filterset.qs
    return render(
        request,
        "fleet/putninalog_list_print.html",
        {
            "title": "Štampa liste putnih naloga",
            "putni_nalozi": putni_nalozi,
        },
    )


@role_permission_required()
def putninalog_set_opravdan(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Neispravan zahtev.")

    base_qs = _putninalog_base_qs(request)
    putni_nalog = get_object_or_404(base_qs, pk=pk)
    if not putni_nalog.opravdan:
        putni_nalog.opravdan = True
        putni_nalog.save(update_fields=["opravdan"])

    return redirect(request.META.get("HTTP_REFERER", reverse("putninalog_list")))


@role_permission_required()
def putninalog_storniraj(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Neispravan zahtev.")

    base_qs = _putninalog_base_qs(request, include_stornirani=True)
    putni_nalog = get_object_or_404(base_qs, pk=pk)
    if not putni_nalog.storniran:
        putni_nalog.storniran = True
        putni_nalog.save(update_fields=["storniran"])

    return redirect(request.META.get("HTTP_REFERER", reverse("putninalog_list")))


class PutniNalogCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = "fleet/putni_nalog_form.html"
    success_url = reverse_lazy("putninalog_list")

    def get_initial(self):
        initial = super().get_initial()
        copy_pk = self.request.GET.get("copy")
        if copy_pk:
            base_qs = _putninalog_base_qs(self.request)
            source = base_qs.filter(pk=copy_pk).first()
            if source:
                initial.update(
                    {
                        "employee": source.employee,
                        "other_employee_name": source.other_employee_name,
                        "job_code": source.job_code,
                        "travel_location": source.travel_location,
                        "task": source.task,
                        "napomena": source.napomena,
                        "contract_offer": source.contract_offer,
                        "vehicle": source.vehicle,
                        "other_vehicle": source.other_vehicle,
                        "number_of_days": source.number_of_days,
                        "advance_payment": source.advance_payment,
                        "advance_payment_currency": source.advance_payment_currency,
                        "daily_allowance": source.daily_allowance,
                        "is_weekly": source.is_weekly,
                    }
                )
                if source.vehicle:
                    initial["transport_type"] = "ims"
                elif source.other_vehicle:
                    initial["transport_type"] = "other"
                if source.employee:
                    initial["employee_type"] = "ims"
                elif source.other_employee_name:
                    initial["employee_type"] = "other"
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dodaj putni nalog"
        context["submit_button_label"] = "Dodaj"
        return context

    def form_valid(self, form):
        try:
            self.object = form.save()
        except ValueError as exc:
            form.add_error("start_sequence", str(exc))
            return self.form_invalid(form)

        return JsonResponse(
            {
                "redirect_url": reverse("putninalog_list"),
                "print_url": f"{reverse('putninalog_print', args=[self.object.pk])}?auto=1",
            }
        )


class PutniNalogUpdateView(CenterMixin, RolePermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    model = PutniNalog
    form_class = PutniNalogForm
    template_name = "fleet/putni_nalog_form.html"
    success_url = reverse_lazy("putninalog_list")
    org_unit_field = "job_code"
    allow_if_no_scope = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Izmeni putni nalog"
        context["submit_button_label"] = "Sačuvaj izmene"
        return context

    def form_valid(self, form):
        self.object = form.save()
        return JsonResponse(
            {
                "redirect_url": reverse("putninalog_list"),
                "print_url": f"{reverse('putninalog_print', args=[self.object.pk])}?auto=1",
            }
        )

    def get_queryset(self):
        return PutniNalog.objects.all()

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.storniran:
            raise PermissionDenied("Nalog je storniran i zakljucan za izmene.")
        user = self.request.user
        if user.is_superuser:
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        center_code = getattr(obj.job_code, "center", None)
        if not center_code:
            raise PermissionDenied("Ne možete menjati naloge iz ovog centra.")

        center_code = str(center_code).strip()
        allowed_center_codes = set(self.get_user_allowed_center_codes())
        if allowed_center_codes and center_code in allowed_center_codes:
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        allowed_units = self.get_user_allowed_units()
        if allowed_units.filter(center=center_code).exists():
            if obj.opravdan:
                raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
            return obj

        raise PermissionDenied("Ne možete menjati naloge iz ovog centra.")


class PutniNalogDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = "fleet/putninalog_detail.html"
    context_object_name = "putni_nalog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Detalji putnog naloga {self.object.travel_date}"
        return context


class PutniNalogPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = "fleet/putni_nalog_print.html"
    context_object_name = "putni_nalog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Štampa putnog naloga {self.object.order_number}"
        context["auto_print"] = self.request.GET.get("auto") == "1"
        context["napomena_lines"] = _split_putni_nalog_note_lines(self.object.napomena)
        return context


class PutniNalogDeleteView(RolePermissionRequiredMixin, LoginRequiredMixin, DeleteView):
    model = PutniNalog
    success_url = reverse_lazy("putninalog_list")
    template_name = "fleet/putninalog_confirm_delete.html"
    context_object_name = "putni_nalog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Obriši putni nalog"
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.storniran:
            raise PermissionDenied("Nalog je storniran i zakljucan za izmene.")
        if obj.opravdan:
            raise PermissionDenied("Nalog je opravdan i zakljucan za izmene.")
        return obj
