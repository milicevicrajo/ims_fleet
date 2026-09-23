from core.mixins import user_has_role_permission


def current_app(request):
    from potrazivanja.access import can_view, can_view_all, can_sync
    app = request.session.get("current_app", "fleet")
    sidebar_map = {
        "fleet": "sidebar_fleet.html",
        "naplata": "sidebar_naplata.html",
        "potrazivanja": "sidebar_potrazivanja.html",
        "isplate": "sidebar_isplate.html",
        "pravna": "sidebar_pravna.html",
        "kadrovi": "sidebar_kadrovi.html",
        "administracija": "sidebar_administracija.html",
        "menice": "sidebar_menice.html",
        "ugovori": "sidebar_ugovori.html",
        "nabavka": "sidebar_nabavka.html",
        "mobilni": "sidebar_mobilni.html",
        "finansije": "sidebar_finansije.html",
        "organizacija": "sidebar_organizacija.html",
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
        "potrazivanja_permissions": {"dashboard": can_view(request.user), "view_all": can_view_all(request.user), "sync_status": can_sync(request.user)},
        "finansije_permissions": {
            code: user_has_role_permission(request.user, f"finansije:{code}")
            for code in ("dashboard", "ledger", "export", "sync_status", "view_all", "bank_list", "bank_detail")
        },
        "hr_permissions": {
            code: user_has_role_permission(request.user, f"hr:{code}")
            for code in ("sick_leave_list", "sick_leave_import", "work_time_catalog", "annual_leave_list",
                         "evaluation_list", "resenje_list")
        },
        "sidebar_template": sidebar_map.get(app, "sidebar_fleet.html"),
        "organizacija_permissions": {
            code: user_has_role_permission(request.user, f"organizacija:{code}")
            for code in ("stablo",)
        },
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
