from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView

from core.mixins import RolePermissionRequiredMixin

from ..forms.garaza import ProcurementItemForm, ProcurementRequestForm
from ..models import ProcurementItem, ProcurementRequest


class ProcurementRequestListView(LoginRequiredMixin, ListView):
    model = ProcurementRequest
    template_name = "fleet/gzn_list.html"
    context_object_name = "requests"
    paginate_by = 50


class ProcurementRequestCreateView(RolePermissionRequiredMixin, LoginRequiredMixin, CreateView):
    model = ProcurementRequest
    form_class = ProcurementRequestForm
    template_name = "fleet/generic_form.html"
    success_url = reverse_lazy("gzn_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Novi zahtev za nabavku"
        ctx["submit_button_label"] = "SaÄuvaj"
        return ctx

    def form_valid(self, form):
        super().form_valid(form)
        return redirect("gzn_detail", pk=self.object.pk)


class ProcurementRequestDetailView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/gzn_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.request_obj = get_object_or_404(
            ProcurementRequest.objects.select_related("job_code"), pk=kwargs.get("pk")
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action") or "add"
        item_id = request.POST.get("item_id")

        if action == "delete" and item_id:
            item = get_object_or_404(ProcurementItem, pk=item_id, request=self.request_obj)
            item.delete()
            messages.success(request, "Stavka je obrisana.")
            return redirect("gzn_detail", pk=self.request_obj.pk)

        instance = None
        if action == "update" and item_id:
            instance = get_object_or_404(ProcurementItem, pk=item_id, request=self.request_obj)

        form = ProcurementItemForm(request.POST, instance=instance)
        if form.is_valid():
            item = form.save(commit=False)
            item.request = self.request_obj
            item.save()
            messages.success(request, "Stavka je saÄuvana.")
        else:
            messages.error(request, "Proveri unete podatke.")
        return redirect("gzn_detail", pk=self.request_obj.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "gzn": self.request_obj,
                "items": list(self.request_obj.items.all()),
                "item_form": ProcurementItemForm(),
            }
        )
        return ctx


class ProcurementRequestPrintView(RolePermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    template_name = "fleet/gzn_print.html"

    def dispatch(self, request, *args, **kwargs):
        self.gzn = get_object_or_404(
            ProcurementRequest.objects.select_related("job_code"),
            pk=kwargs.get("pk"),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        max_rows = 12
        items = list(self.gzn.items.all())
        rows_pages = []
        if not items:
            rows_pages.append([None] * max_rows)
        else:
            for index in range(0, len(items), max_rows):
                chunk = items[index : index + max_rows]
                padded = chunk + [None] * max(0, max_rows - len(chunk))
                rows_pages.append(padded)

        job_code = self.gzn.job_code

        ctx.update(
            {
                "gzn": self.gzn,
                "rows_pages": rows_pages,
                "job_code": job_code,
                "center": getattr(job_code, "center", ""),
                "next_url": self.request.GET.get("next") or reverse("gzn_detail", kwargs={"pk": self.gzn.pk}),
                "auto_print": self.request.GET.get("auto") == "1",
            }
        )
        return ctx
