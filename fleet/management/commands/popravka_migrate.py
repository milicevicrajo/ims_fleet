from django.core.management.base import BaseCommand
from fleet.models import (
    Requisition,
    ServiceTransaction,
    DraftRequisition,
    DraftServiceTransaction,
    ServiceType,
)

class Command(BaseCommand):
    help = "Migrira tekstualne vrednosti iz popravka_kategorija u popravka_kategorija_fk"

    def handle(self, *args, **kwargs):
        total_counts = {}

        # REQUISITION
        requisition_count = 0
        for r in Requisition.objects.exclude(popravka_kategorija__isnull=True).exclude(popravka_kategorija__exact=""):
            try:
                kategorija = ServiceType.objects.get(name=r.popravka_kategorija.strip())
                r.popravka_kategorija_fk = kategorija
                r.save()
                requisition_count += 1
            except ServiceType.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"[R] Nema kategorije za: {r.popravka_kategorija}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"[R] Greška kod ID {r.id}: {e}"))
        total_counts['Requisition'] = requisition_count

        # SERVICE TRANSACTION
        service_count = 0
        for s in ServiceTransaction.objects.exclude(popravka_kategorija__isnull=True).exclude(popravka_kategorija__exact=""):
            try:
                kategorija = ServiceType.objects.get(name=s.popravka_kategorija.strip())
                s.popravka_kategorija_fk = kategorija
                s.save()
                service_count += 1
            except ServiceType.DoesNotExist:
                pass
        total_counts['ServiceTransaction'] = service_count

        # DRAFT REQUISITION
        draft_requisition_count = 0
        for dr in DraftRequisition.objects.exclude(popravka_kategorija__isnull=True).exclude(popravka_kategorija__exact=""):
            try:
                kategorija = ServiceType.objects.get(name=dr.popravka_kategorija.strip())
                dr.popravka_kategorija_fk = kategorija
                dr.save()
                draft_requisition_count += 1
            except ServiceType.DoesNotExist:
                pass
        total_counts['DraftRequisition'] = draft_requisition_count

        # DRAFT SERVICE TRANSACTION
        draft_service_count = 0
        for ds in DraftServiceTransaction.objects.exclude(popravka_kategorija__isnull=True).exclude(popravka_kategorija__exact=""):
            try:
                kategorija = ServiceType.objects.get(name=ds.popravka_kategorija.strip())
                ds.popravka_kategorija_fk = kategorija
                ds.save()
                draft_service_count += 1
            except ServiceType.DoesNotExist:
                pass
        total_counts['DraftServiceTransaction'] = draft_service_count

        # REZULTATI
        self.stdout.write(self.style.SUCCESS("✅ Migracija završena."))
        for model, count in total_counts.items():
            self.stdout.write(self.style.SUCCESS(f"{model}: povezanih zapisa = {count}"))
