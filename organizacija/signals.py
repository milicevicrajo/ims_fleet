"""Faza 2: pri svakom cuvanju zapisa Flote i Nabavke veza `org_node` se ponovo izvodi iz starog polja.

Staro polje je merodavno, pa se rucno upisana vrednost `org_node` uvek prepisuje. Masovni
upisi (`update`, `bulk_create`) ne prolaze kroz ovaj signal — njih hvata ponovljivo
popunjavanje (`manage.py povezi_flotu`).
"""

from django.db.models.signals import pre_save

from organizacija.services import flota


def postavi_org_node(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw:
        return
    veza = flota.veza_za(sender)
    if update_fields is not None and veza.polje not in update_fields and veza.izvorna_kolona not in update_fields:
        return
    instance.org_node_id = flota.cvor_za_zapis(instance)


def postavi_cvor_zaposlenog(sender, instance, raw=False, update_fields=None, **kwargs):
    """Zaposleni: cvor registra iz OJ kadrovske baze (organizacija/services/zaposleni.py)."""
    if raw:
        return
    if update_fields is not None and not {"org_unit_code", "department_code", "org_node"} & set(update_fields):
        return
    from organizacija.services import zaposleni

    instance.org_node_id = zaposleni.cvor_oj(zaposleni.oj_zaposlenog(instance), zaposleni.mape_registra())


def povezi_signale():
    for veza in flota.SVE_VEZE:
        pre_save.connect(
            postavi_org_node,
            sender=veza.model_class(),
            dispatch_uid=f"organizacija.org_node.{veza.oznaka_modela}",
        )
    from hr.models import Employee

    pre_save.connect(postavi_cvor_zaposlenog, sender=Employee, dispatch_uid="organizacija.org_node.zaposleni")
