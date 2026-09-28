from celery import shared_task
from finansije.services.sync import SyncBusy
from .services.sync import sync_collections


def poruka(run):
    """Kratak izvestaj za istoriju zadataka: stanje i kontrole naspram izvora."""
    ukupno = (run.control_totals or {}).get("totals", {})
    razlike = sum(k.get("differences", 0) for k in (run.control_totals or {}).values()
                  if isinstance(k, dict) and "differences" in k)
    return (f"Potrazivanja: pozicija {ukupno.get('positions', 0)}, partnera {ukupno.get('partners', 0)}, "
            f"saldo {ukupno.get('balance', '0')}; kontrole: " + ("bez razlika." if not razlike else f"{razlike} RAZLIKA."))


@shared_task(bind=True, name="potrazivanja.tasks.sync_collections_task")
def sync_collections_task(self):
    """Puna sinhronizacija Potrazivanja; nocu u 03:00 (od 28.09.2026.), a moze i rucno sa ekrana.

    Nocu se izvor retko menja, pa izostaje greska „izvor se promenio tokom citanja” kakva se 22.09.2026.
    javila pri rucnom pokretanju. Neuspeh podize izuzetak, pa ga istorija zadataka belezi kao pad.
    """
    try:
        run = sync_collections(trigger="celery", task_id=self.request.id or "")
    except SyncBusy:
        return "SKIP: sinhronizacija Potrazivanja je vec aktivna."
    return poruka(run)
