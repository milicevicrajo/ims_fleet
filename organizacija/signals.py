"""Faza 2: pri svakom cuvanju zapisa Flote veza `org_node` se ponovo izvodi iz starog polja.

Staro polje je merodavno, pa se rucno upisana vrednost `org_node` uvek prepisuje. Masovni
upisi (`update`, `bulk_create`) ne prolaze kroz ovaj signal — njih hvata ponovljivo
popunjavanje (`manage.py povezi_flotu`).
"""

from django.db.models.signals import pre_save

from organizacija.services import flota


def postavi_org_node(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw:
        return
    veza = flota.VEZE_PO_MODELU[sender.__name__]
    if update_fields is not None and veza.polje not in update_fields and veza.izvorna_kolona not in update_fields:
        return
    instance.org_node_id = flota.cvor_za_zapis(instance)


def povezi_signale():
    for veza in flota.VEZE:
        pre_save.connect(
            postavi_org_node,
            sender=veza.model_class(),
            dispatch_uid=f"organizacija.org_node.{veza.model}",
        )
