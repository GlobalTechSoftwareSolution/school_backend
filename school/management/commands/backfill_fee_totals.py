from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal

from school.models import FeePayment


class Command(BaseCommand):
    help = "Backfill total_amount and remaining_amount for FeePayment records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be updated without saving.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Process payments in batches to reduce memory usage.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        batch_size = options["batch_size"]

        qs = FeePayment.objects.select_related("fee_structure", "student").order_by("pk")
        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING("No FeePayment records found."))
            return

        updated = 0
        with transaction.atomic():
            start = 0
            while True:
                batch = list(qs[start:start + batch_size])
                if not batch:
                    break
                for p in batch:
                    # Recompute fields using the model's save logic but avoid duplicate validation noise
                    # We mimic the logic here to support dry-run and avoid triggering constraints unexpectedly
                    fee_total = p.fee_structure.amount or Decimal("0")

                    # Sum of other PAID payments for same student/fee type
                    other_paid = (
                        FeePayment.objects
                        .filter(student=p.student, fee_structure=p.fee_structure, status='Paid')
                        .exclude(pk=p.pk)
                        .aggregate(total=Sum('amount_paid'))['total']
                        or Decimal('0')
                    )
                    current_paid = p.amount_paid if p.status == 'Paid' else Decimal('0')
                    remaining = fee_total - other_paid - current_paid
                    if remaining < Decimal('0'):
                        remaining = Decimal('0')

                    if (p.total_amount != fee_total) or (p.remaining_amount != remaining):
                        updated += 1
                        msg = f"Payment #{p.pk}: total {p.total_amount}→{fee_total}, remaining {p.remaining_amount}→{remaining}"
                        if dry_run:
                            self.stdout.write(self.style.WARNING(f"[DRY-RUN] {msg}"))
                        else:
                            p.total_amount = fee_total
                            p.remaining_amount = remaining
                            p.save(update_fields=["total_amount", "remaining_amount", "updated_at"])  # keep timestamps consistent
                start += batch_size

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(f"Backfill complete. Reviewed: {total}, Updated: {updated}, Dry-run: {dry_run}"))
