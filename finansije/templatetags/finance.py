from django import template
from django.utils.formats import number_format
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def finance_sidebar_section(request):
    view = getattr(getattr(request, "resolver_match", None), "view_name", "")
    if view == "finansije:report":
        group = request.GET.get("group", "center")
        if group == "month":
            return "month"
        if group == "job" or request.GET.get("job"):
            return "jobs"
        return "overview"
    return {"finansije:dashboard": "overview", "finansije:job_card": "jobs",
            "finansije:ledger": "ledger", "finansije:sync_status": "sync"}.get(view, "")


@register.simple_tag
def finance_job_button(code, url):
    return format_html(
        '<a class="btn btn-outline-primary btn-sm finance-job-detail-button" href="{}" '
        'title="Otvori detalj šifre {}" aria-label="Otvori detalj šifre {}">'
        '<i class="mdi mdi-briefcase-outline" aria-hidden="true"></i><span>{}</span>'
        '<i class="mdi mdi-chevron-right" aria-hidden="true"></i></a>', url, code, code, code,
    )


@register.simple_tag
def finance_job_url(code, selected_date=None):
    from finansije.services.links import job_detail_url
    return job_detail_url(code, selected_date)


@register.filter
def amount_badge(value):
    if value is None:
        return "—"
    state, label, sign = ("positive", "Pozitivan iznos", "+") if value > 0 else ("negative", "Negativan iznos", "") if value < 0 else ("zero", "Nula", "")
    return format_html(
        '<span class="finance-amount finance-amount-{}" title="{}">{}{}</span>',
        state, label, sign, number_format(value, decimal_pos=2, use_l10n=True, force_grouping=True),
    )


@register.filter
def expense_badge(value):
    """Show the expense's effect on the result; reversals retain the opposite sign."""
    return amount_badge(-value if value is not None else None)
