from core.mixins import user_has_role_permission


def current_app(request):
    app = request.session.get("current_app", "fleet")
    sidebar_map = {
        "fleet": "sidebar_fleet.html",
        "naplata": "sidebar_naplata.html",
        "pravna": "sidebar_pravna.html",
        "kadrovi": "sidebar_kadrovi.html",
        "administracija": "sidebar_administracija.html",
        "menice": "sidebar_menice.html",
        "ugovori": "sidebar_ugovori.html",
        "nabavka": "sidebar_nabavka.html",
    }
    nabavka_codes = [
        "dashboard",
        "case_list",
        "case_create",
        "euf_invoice_list",
        "purchase_contract_list",
        "purchase_order_list",
        "reports",
        "alerts",
    ]
    return {
        "current_app": app,
        "sidebar_template": sidebar_map.get(app, "sidebar_fleet.html"),
        "nabavka_permissions": {
            code: user_has_role_permission(request.user, f"nabavka:{code}")
            for code in nabavka_codes
        },
    }
