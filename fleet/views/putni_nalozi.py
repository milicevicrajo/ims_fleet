import textwrap

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import ExpressionWrapper, F, IntegerField, Q, Value
from django.db.models.functions import Cast, StrIndex, Substr
from django.middleware.csrf import get_token
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.html import escape
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView
from django_filters.views import FilterView

from core.mixins import RolePermissionRequiredMixin, role_permission_required, user_has_role_permission

from ..filters import PutniNalogFilter
from ..mixins import CenterMixin
from ..models import PutniNalog
from ..forms.putni_nalozi import PutniNalogForm


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
    qs = PutniNalog.objects.select_related("job_code", "employee", "vehicle").prefetch_related("vehicle__traffic_cards")
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


def _putninalog_employee_label(putni_nalog):
    return str(putni_nalog.employee) if putni_nalog.employee else (putni_nalog.other_employee_name or "")


def _putninalog_vehicle_label(putni_nalog):
    if putni_nalog.vehicle:
        traffic_card = putni_nalog.vehicle.traffic_cards.first()
        return str(getattr(traffic_card, "registration_number", "") or putni_nalog.vehicle.chassis_number or "")
    return putni_nalog.other_vehicle or ""


def _is_foreign_currency(putni_nalog):
    currency = (putni_nalog.advance_payment_currency or "").upper()
    return bool(currency and currency != "RSD")


def _putninalog_print_urls(putni_nalog, user=None):
    urls = []
    can_print = user is None or user_has_role_permission(user, "putninalog_print")
    can_print_foreign = user is None or user_has_role_permission(user, "putninalog_foreign_print")
    if can_print:
        urls.append(f"{reverse('putninalog_print', args=[putni_nalog.pk])}?auto=1")
    if _is_foreign_currency(putni_nalog) and can_print_foreign:
        urls.append(f"{reverse('putninalog_foreign_print', args=[putni_nalog.pk])}?auto=1")
    return urls


def _putninalog_actions_html(request, putni_nalog):
    user = request.user
    can_update = user_has_role_permission(user, "putninalog_update")
    can_print = user_has_role_permission(user, "putninalog_print")
    can_print_foreign = user_has_role_permission(user, "putninalog_foreign_print")
    can_create = user_has_role_permission(user, "putninalog_create")
    can_justify = user_has_role_permission(user, "putninalog_set_opravdan")
    can_storno = user_has_role_permission(user, "putninalog_storniraj")

    csrf_token = get_token(request)
    modal_id = f"stornoModal{putni_nalog.pk}"
    modal_label_id = f"stornoModalLabel{putni_nalog.pk}"
    order_number = escape(putni_nalog.order_number or "")

    update_html = ""
    print_html = ""
    copy_html = ""
    storno_html = ""

    if putni_nalog.opravdan:
        justified_html = '<span class="badge bg-success">Opravdan</span>'
        if can_update:
            update_html = (
                '<span class="btn btn-outline-secondary btn-sm disabled">'
                '<i class="mdi mdi-lock"></i> Zakljucan</span>'
            )
    else:
        if can_justify:
            justify_url = reverse("putninalog_set_opravdan", args=[putni_nalog.pk])
            justified_html = (
                f'<form method="post" action="{justify_url}">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">'
                '<button type="submit" class="btn btn-outline-success btn-sm">'
                '<i class="mdi mdi-check"></i> Opravdaj</button></form>'
            )
        else:
            justified_html = '<span class="badge bg-light text-dark">Ne</span>'
        if can_update:
            update_url = reverse("putninalog_update", args=[putni_nalog.pk])
            update_html = (
                f'<a href="{update_url}" class="btn btn-outline-primary btn-sm">'
                '<i class="mdi mdi-pencil"></i> Izmeni</a>'
            )

    if can_print:
        print_url = reverse("putninalog_print", args=[putni_nalog.pk])
        print_html += (
            f'<a href="{print_url}" class="btn btn-outline-secondary btn-sm" target="_blank">'
            '<i class="mdi mdi-printer"></i> Stampa</a>'
        )
    if _is_foreign_currency(putni_nalog) and can_print_foreign:
        foreign_print_url = reverse("putninalog_foreign_print", args=[putni_nalog.pk])
        spacer = " " if print_html else ""
        print_html += (
            f'{spacer}<a href="{foreign_print_url}" class="btn btn-outline-info btn-sm" target="_blank">'
            '<i class="mdi mdi-file-document-outline"></i> Prilog</a>'
        )

    if can_create:
        copy_url = f"{reverse('putninalog_create')}?copy={putni_nalog.pk}"
        copy_html = (
            f'<a href="{copy_url}" class="btn btn-outline-info btn-sm">'
            '<i class="mdi mdi-content-copy"></i> Ponovi</a>'
        )

    if can_storno:
        storno_url = reverse("putninalog_storniraj", args=[putni_nalog.pk])
        storno_html = f"""
            <button type="button" class="btn btn-danger btn-sm" data-bs-toggle="modal" data-bs-target="#{modal_id}">
              <i class="mdi mdi-close-circle"></i> Storniraj
            </button>
            <div class="modal fade" id="{modal_id}" tabindex="-1" aria-labelledby="{modal_label_id}" aria-hidden="true">
              <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title" id="{modal_label_id}">Potvrda storniranja</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Zatvori"></button>
                  </div>
                  <div class="modal-body text-start">
                    Da li ste sigurni da stornirate ovaj nalog <strong>{order_number}</strong>?
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-dismiss="modal">Otkazi</button>
                    <form method="post" action="{storno_url}">
                      <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                      <button type="submit" class="btn btn-danger btn-sm">
                        <i class="mdi mdi-alert-circle"></i> Da, storniraj
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
        """
    return justified_html, update_html, print_html, copy_html, storno_html


@login_required
def putninalog_datatable_data(request):
    base_qs = _putninalog_base_qs(request)
    records_total = base_qs.count()
    filterset = PutniNalogFilter(request.GET, queryset=base_qs, request=request)
    qs = filterset.qs

    search_value = request.GET.get("search[value]", "").strip()
    if search_value:
        qs = qs.filter(
            Q(order_number__icontains=search_value)
            | Q(employee__first_name__icontains=search_value)
            | Q(employee__last_name__icontains=search_value)
            | Q(other_employee_name__icontains=search_value)
            | Q(job_code__code__icontains=search_value)
            | Q(travel_location__icontains=search_value)
            | Q(contract_offer__icontains=search_value)
            | Q(vehicle__brand__icontains=search_value)
            | Q(vehicle__model__icontains=search_value)
            | Q(vehicle__chassis_number__icontains=search_value)
            | Q(vehicle__traffic_cards__registration_number__icontains=search_value)
            | Q(other_vehicle__icontains=search_value)
        ).distinct()

    records_filtered = qs.count()

    order_column = request.GET.get("order[0][column]", "0")
    order_dir = request.GET.get("order[0][dir]", "desc")
    order_map = {
        "0": "pn_sort_key",
        "1": "employee__last_name",
        "2": "job_code__code",
        "3": "travel_location",
        "4": "contract_offer",
        "5": "vehicle__brand",
        "6": "travel_date",
        "7": "number_of_days",
        "8": "advance_payment",
        "9": "isplaceno",
        "10": "is_weekly",
        "11": "opravdan",
    }
    order_field = order_map.get(order_column, "pn_sort_key")
    if order_dir == "desc":
        order_field = f"-{order_field}"
    qs = qs.order_by(order_field, "-id")

    try:
        start = max(int(request.GET.get("start", 0)), 0)
    except (TypeError, ValueError):
        start = 0
    try:
        length = int(request.GET.get("length", 50))
    except (TypeError, ValueError):
        length = 50
    if length < 0:
        length = 50
    length = min(length, 200)

    rows = []
    for putni_nalog in qs[start:start + length]:
        justified_html, update_html, print_html, copy_html, storno_html = _putninalog_actions_html(request, putni_nalog)
        rows.append({
            "DT_RowClass": "table-warning" if putni_nalog.is_weekly else "",
            "order_number": escape(putni_nalog.order_number or ""),
            "employee": escape(_putninalog_employee_label(putni_nalog)),
            "job_code": escape(getattr(putni_nalog.job_code, "code", "") or ""),
            "travel_location": escape(putni_nalog.travel_location or ""),
            "contract_offer": escape(putni_nalog.contract_offer or ""),
            "vehicle": escape(_putninalog_vehicle_label(putni_nalog)),
            "travel_date": putni_nalog.travel_date.strftime("%d.%m.%Y") if putni_nalog.travel_date else "",
            "number_of_days": putni_nalog.number_of_days or "",
            "advance_payment": str(putni_nalog.advance_payment or ""),
            "isplaceno": str(putni_nalog.isplaceno or ""),
            "is_weekly": (
                '<span class="badge bg-warning text-dark">Da</span>'
                if putni_nalog.is_weekly else '<span class="badge bg-light text-dark">Ne</span>'
            ),
            "opravdan": justified_html,
            "update": update_html,
            "print": print_html,
            "copy": copy_html,
            "storno": storno_html,
        })

    try:
        draw = int(request.GET.get("draw", 0))
    except (TypeError, ValueError):
        draw = 0

    return JsonResponse({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": rows,
    })


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
        context["can_print_putninalog_list"] = user_has_role_permission(
            self.request.user,
            "putninalog_print_list",
        )
        context["can_create_putninalog"] = user_has_role_permission(
            self.request.user,
            "putninalog_create",
        )
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

        print_urls = _putninalog_print_urls(self.object, self.request.user)
        return JsonResponse(
            {
                "redirect_url": reverse("putninalog_list"),
                "print_url": print_urls[0] if print_urls else "",
                "print_urls": print_urls,
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
        print_urls = _putninalog_print_urls(self.object, self.request.user)
        return JsonResponse(
            {
                "redirect_url": reverse("putninalog_list"),
                "print_url": print_urls[0] if print_urls else "",
                "print_urls": print_urls,
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

    def get(self, request, *args, **kwargs):
        putni_nalog = self.get_object()
        return redirect("putninalog_print", pk=putni_nalog.pk)


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


class PutniNalogForeignPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = PutniNalog
    template_name = "fleet/putni_nalog_print_foreign.html"
    context_object_name = "putni_nalog"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Prilog za put u inostranstvo {self.object.order_number}"
        context["auto_print"] = self.request.GET.get("auto") == "1"
        context["foreign_rulebook_text"] = "po pravilniku"
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
