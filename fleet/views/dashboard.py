from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def fleet_other(request):
    links = [
        {
            "title": "Tipovi servisa",
            "description": "Sifarnik kategorija servisa i popravki koje se koriste u troskovima i trebovanjima.",
            "url_name": "servicetype_list",
            "icon": "mdi-format-list-bulleted-type",
        },
        {
            "title": "DDOR potrazivanja",
            "description": "Pregled DDOR potrazivanja i povezivanje naplate stete sa vozilom.",
            "url_name": "insurance_list",
            "icon": "mdi-shield-alert",
        },
        {
            "title": "Konta vozila",
            "description": "Sifarnik konta koja se koriste za prepoznavanje i klasifikaciju troskova vozila.",
            "url_name": "konta_list",
            "icon": "mdi-account-card-details",
        },
        {
            "title": "Izvestaji sa servera",
            "description": "Tehnicki i istorijski izvestaji koji se citaju direktno sa servera.",
            "url_name": "reports_index",
            "icon": "mdi-file-chart",
        },
    ]
    return render(request, "fleet/other_links.html", {"title": "Ostalo", "links": links})


@login_required
def dashboard(request):
    from ..support.fleet_snapshot import fleet_snapshot
    return render(request, 'fleet/dashboard.html', fleet_snapshot(request.user))
