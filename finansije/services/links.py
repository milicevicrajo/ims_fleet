from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone


def job_detail_url(code, selected_date=None):
    selected_date = selected_date or timezone.localdate()
    return reverse("finansije:job_card") + "?" + urlencode({
        "job": code, "year": selected_date.year, "month": selected_date.month,
    })
