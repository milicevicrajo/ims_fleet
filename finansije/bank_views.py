import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from core.mixins import role_permission_required, user_has_role_permission
from menice.models import Menica
from .access import can_view_all
from .bank_forms import BankPeriodForm, BankContactForm, BankAccountRuleForm, BankBillPlacementForm
from .models import BankContact, BankAccountRule, BankBillPlacement, SyncRun
from .services import banks as service

logger = logging.getLogger(__name__)
TABS = [("basic", "Osnovni podaci"), ("contacts", "Kontakti"), ("turnover", "Promet po računima"),
        ("bills", "Menice"), ("guarantees", "Garancije"), ("deposits", "Oročena sredstva")]


def context_for(request):
    request.session["current_app"] = "finansije"
    form = BankPeriodForm(request.GET)
    context = dict(form=form, valid=form.is_valid(), restricted=not can_view_all(request.user),
                   last_success=SyncRun.objects.filter(company=service.company_id(), status="success").first())
    context["can_map"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_accounts")
    try:
        banks = service.fetch_banks(service.company_id())
    except (DatabaseError, ValueError):
        logger.exception("Bank partner source unavailable")
        context["source_error"] = "Šifarnik banaka trenutno nije dostupan. Pokušajte ponovo."
        banks = []
    context["source_banks"] = banks
    if context["valid"]:
        context["period_params"] = urlencode({key: form.cleaned_data[key].isoformat() for key in ("date_from", "date_to")})
        covered = any(run.year_from <= form.cleaned_data["date_from"].year <= run.year_to for run in
                      SyncRun.objects.filter(company=service.company_id(), status="success"))
        context["period_missing"] = not covered
    return context


def find_bank(context, bank_code):
    if context.get("source_error"):
        return None
    return next((b for b in context["source_banks"] if b["code"] == bank_code), None)


def edit_access(request):
    if not can_view_all(request.user):
        raise PermissionDenied("Održavanje bankarskih podataka zahteva pristup celoj firmi.")


def bank_redirect(bank_code, tab):
    return redirect(reverse("finansije:bank_detail", args=[bank_code]) + "?tab=" + tab)


@require_GET
@login_required
@role_permission_required()
def bank_list(request):
    context = context_for(request)
    if context["valid"] and not context.get("source_error"):
        context.update(service.report_for(request.user, context["source_banks"], context["form"].cleaned_data["date_from"], context["form"].cleaned_data["date_to"]))
    return render(request, "finansije/banks/list.html", context)


@require_GET
@login_required
@role_permission_required()
def bank_detail(request, bank_code):
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404("Partner nije banka grupe 11.")
    tab = request.GET.get("tab", "basic")
    if tab not in dict(TABS):
        raise Http404("Nepostojeća kartica.")
    context.update(bank=bank, tab=tab, tabs=[dict(code=code, label=label) for code, label in TABS])
    context["can_contact_edit"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_contact_edit")
    context["can_contact_delete"] = can_view_all(request.user) and user_has_role_permission(request.user, "finansije:bank_contact_delete")
    if tab == "contacts":
        context["contacts"] = BankContact.objects.filter(company=service.company_id(), bank_code=bank_code)
    if tab in ("turnover", "guarantees", "deposits") and context["valid"]:
        report = service.report_for(request.user, context["source_banks"], context["form"].cleaned_data["date_from"], context["form"].cleaned_data["date_to"])
        selected = next(row for row in report["banks"] if row["code"] == bank_code)
        segments = {"dinar", "foreign", "other"} if tab == "turnover" else {"guarantee"} if tab == "guarantees" else {"deposit"}
        context.update(accounts=[row for row in selected["accounts"] if row["segment"] in segments],
                       ytd_end=report["ytd_end"], unresolved_count=len(report["unmapped"]))
    if tab == "bills":
        context["can_view_bills"] = can_view_all(request.user) and user_has_role_permission(request.user, "menice:menica_list")
        context["can_view_incoming"] = can_view_all(request.user) and user_has_role_permission(request.user, "menice:ulazna_menica_list")
        context["can_bill_edit"] = (context["can_view_bills"] and context["can_view_incoming"] and
                                    user_has_role_permission(request.user, "finansije:bank_bill_edit"))
        placements = BankBillPlacement.objects.filter(company=service.company_id(), bank_code=bank_code).select_related("bill", "incoming_bill")
        if not context["can_view_bills"]:
            placements = placements.filter(bill__isnull=True)
        if not context["can_view_incoming"]:
            placements = placements.filter(incoming_bill__isnull=True)
        context["placements"] = placements
        # Registration is shown separately; it is never inferred to be physical custody.
        if context["can_view_bills"]:
            context["registered_bills"] = Menica.objects.filter(naziv_banke__iexact=bank["name"])
    return render(request, "finansije/banks/detail.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_contact_edit(request, bank_code, pk=None):
    edit_access(request)
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404
    instance = get_object_or_404(BankContact, pk=pk, company=service.company_id(), bank_code=bank_code) if pk else BankContact(company=service.company_id(), bank_code=bank_code)
    form = BankContactForm(request.POST if request.method == "POST" else None, instance=instance)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Kontakt je sačuvan.")
        return bank_redirect(bank_code, "contacts")
    context.update(bank=bank, edit_form=form, edit_title="Kontakt banke", cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=contacts")
    return render(request, "finansije/banks/form.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_contact_delete(request, bank_code, pk):
    edit_access(request)
    contact = get_object_or_404(BankContact, pk=pk, company=service.company_id(), bank_code=bank_code)
    if request.method == "POST":
        contact.delete()
        messages.success(request, "Kontakt je obrisan.")
        return bank_redirect(bank_code, "contacts")
    request.session["current_app"] = "finansije"
    return render(request, "finansije/banks/form.html", dict(edit_title="Brisanje kontakta", delete_label=f"{contact.segment} — {contact.name or contact.shared_emails}",
        cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=contacts"))


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_accounts(request):
    edit_access(request)
    context = context_for(request)
    if context.get("source_error"):
        return render(request, "finansije/banks/list.html", context, status=503)
    catalog = service.account_catalog()
    # One current label per account; historical names must not duplicate choices.
    catalog = list(dict(catalog).items())
    code = request.POST.get("account") if request.method == "POST" else request.GET.get("account")
    instance = BankAccountRule.objects.filter(company=service.company_id(), account=code).first() or BankAccountRule(company=service.company_id())
    name = dict(catalog).get(code, "")
    initial = {"account": code, "segment": service.suggested_segment(code or "", name), "bank_code": service.suggested_bank(name, context["source_banks"])} if not instance.pk else None
    form = BankAccountRuleForm(request.POST if request.method == "POST" else None, instance=instance, initial=initial, banks=context["source_banks"], accounts=catalog)
    if request.method == "POST" and form.is_valid():
        rule = form.save(commit=False)
        rule.updated_by = request.user
        rule.save()
        messages.success(request, "Veza konta je sačuvana.")
        return redirect("finansije:bank_accounts")
    saved = {r.account: r for r in BankAccountRule.objects.filter(company=service.company_id())}
    names = {b["code"]: b["name"] for b in context["source_banks"]}
    context.update(edit_form=form, catalog=[dict(code=c, name=n, rule=saved.get(c), bank=names.get(saved[c].bank_code, "—") if c in saved else "Nije potvrđeno") for c, n in catalog])
    return render(request, "finansije/banks/accounts.html", context)


@require_http_methods(["GET", "POST"])
@login_required
@role_permission_required()
def bank_bill_edit(request, bank_code, pk=None):
    edit_access(request)
    if not all(user_has_role_permission(request.user, code) for code in ("menice:menica_list", "menice:ulazna_menica_list")):
        raise PermissionDenied
    context = context_for(request)
    bank = find_bank(context, bank_code)
    if not bank:
        if context.get("source_error"):
            return render(request, "finansije/banks/list.html", context, status=503)
        raise Http404
    instance = get_object_or_404(BankBillPlacement, pk=pk, company=service.company_id(), bank_code=bank_code) if pk else BankBillPlacement(company=service.company_id(), bank_code=bank_code)
    form = BankBillPlacementForm(request.POST if request.method == "POST" else None, instance=instance, initial={"delivered_on": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(None, "Ova menica već ima evidentiranu predaju. Prvo evidentirajte vraćanje.")
        else:
            messages.success(request, "Predaja menice je sačuvana.")
            return bank_redirect(bank_code, "bills")
    context.update(bank=bank, edit_form=form, edit_title="Predaja menice banci", cancel_url=reverse("finansije:bank_detail", args=[bank_code]) + "?tab=bills")
    return render(request, "finansije/banks/form.html", context)
