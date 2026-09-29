"""Napomena o poslednjoj očitanoj kilometraži ispod svakog polja kilometraže u Floti (od 29.09.2026.).

`oznaci_kilometrazu(polje, vozilo_polje=… | vozilo_id=…, datum_polje=…)` dodaje polju `data-km-*`
oznake; skripta `fleet/static/fleet/js/kilometraza.js` (u base.html) pita `vozilo_kilometraza` i ispod
polja ispisuje poslednju očitanu kilometražu vozila do datuma unosa, uz upozorenje kada je uneta
manja ili nerealno veća. Upozorenje ne sprečava čuvanje (prijava kvara ima strožu proveru sa potvrdom).
"""
from django.urls import reverse


def oznaci_kilometrazu(polje, *, vozilo_polje=None, vozilo_id=None, datum_polje=None):
    attrs = polje.widget.attrs
    attrs["data-km-url"] = reverse("vozilo_kilometraza")
    if vozilo_polje:
        attrs["data-km-vozilo-polje"] = f"id_{vozilo_polje}"
    if vozilo_id:
        attrs["data-km-vozilo"] = str(vozilo_id)
    if datum_polje:
        attrs["data-km-datum-polje"] = f"id_{datum_polje}"
