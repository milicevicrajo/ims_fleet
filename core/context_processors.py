from core.mixins import user_has_role_permission


def current_app(request):
    app = request.session.get("current_app", "fleet")
    sidebar_map = {
        "fleet": "sidebar_fleet.html",
        "naplata": "sidebar_naplata.html",
        "isplate": "sidebar_isplate.html",
        "pravna": "sidebar_pravna.html",
        "kadrovi": "sidebar_kadrovi.html",
        "administracija": "sidebar_administracija.html",
        "menice": "sidebar_menice.html",
        "ugovori": "sidebar_ugovori.html",
        "nabavka": "sidebar_nabavka.html",
        "mobilni": "sidebar_mobilni.html",
        "finansije": "sidebar_finansije.html",
    }
    nabavka_codes = [
        "dashboard",
        "case_list",
        "case_create",
        "euf_invoice_list",
        "purchase_contract_list",
        "public_procurement_list",
        "purchase_order_list",
        "reports",
        "alerts",
    ]
    naplata_codes = [
        "lista_dugovanja_po_bucketima",
        "lista_avans_klijenti",
        "lista_tuzenih",
        "lista_opomena",
        "izvestaj_po_siframa_posla",
        "neodobrene_if_izvestaj",
        "export_dugovanja_excel",
        "toggle_avans_klijent",
    ]
    return {
        "current_app": app,
        "finansije_permissions": {
            code: user_has_role_permission(request.user, f"finansije:{code}")
            for code in ("dashboard", "ledger", "export", "sync_status", "view_all")
        },
        "hr_permissions": {
            code: user_has_role_permission(request.user, f"hr:{code}")
            for code in ("sick_leave_list", "sick_leave_import", "work_time_catalog", "annual_leave_list", "evaluation_list")
        },
        "sidebar_template": sidebar_map.get(app, "sidebar_fleet.html"),
        "nabavka_permissions": {
            code: user_has_role_permission(request.user, f"nabavka:{code}")
            for code in nabavka_codes
        },
        "naplata_permissions": {
            code: user_has_role_permission(request.user, f"naplata:{code}")
            for code in naplata_codes
        },
        "must_change_password": (
            request.user.is_authenticated
            and getattr(request.user, "must_change_password", False)
        ),
    }
