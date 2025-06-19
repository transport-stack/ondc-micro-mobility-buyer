from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.models import TransactionStatus, TransactionType
from payments.models.transaction_setup import Transaction


@receiver(post_save, sender=Transaction)
def create_refund(sender, instance, created, **kwargs):
    # Check if this is an update, not a creation
    if not created:
        if (
            instance.status == TransactionStatus.FAILED
            and instance.gateway_transaction_status == TransactionStatus.SUCCESS
        ):
            if not Transaction.objects.filter(
                original_transaction=instance, transaction_type=TransactionType.CREDIT
            ).exists():
                refund = Transaction(
                    user=instance.user,
                    status=TransactionStatus.PENDING,
                    amount=-instance.amount,
                    transaction_type=TransactionType.CREDIT,
                    gateway_mode=instance.gateway_mode,
                    gateway_transaction_status=TransactionStatus.PENDING,
                    original_transaction=instance,
                )
                refund.save()
