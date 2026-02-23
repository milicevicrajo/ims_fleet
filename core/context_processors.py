def current_app(request):
    app = request.session.get("current_app", "fleet")
    sidebar_map = {
        "fleet": "sidebar_fleet.html",
        "naplata": "sidebar_naplata.html",
        "pravna": "sidebar_pravna.html",
        "kadrovi": "sidebar_kadrovi.html",
        "administracija": "sidebar_administracija.html",
    }
    return {
        "current_app": app,
        "sidebar_template": sidebar_map.get(app, "sidebar_fleet.html"),
    }
