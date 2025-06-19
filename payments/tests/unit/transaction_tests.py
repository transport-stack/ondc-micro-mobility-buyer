from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models.user_setup import MyUser
from custom_cities.models import City
from modules.models import TransactionStatus, TransactionType
from payments.constants import PaymentGatewayEnum, PaymentModeEnum
from payments.models.payment_gateway_setup import (
    PaymentGateway,
    PaymentGatewayMode,
    PaymentMode,
)
from payments.models.transaction_setup import Transaction

User = get_user_model()


class TransactionTestCase(TestCase):
    def setUp(self):
        self.city, _created = City.objects.get_or_create(
            code="BLR", display_name="Bangalore"
        )
        self.user = MyUser.objects.create()
        self.paytm_payment_gateway, _created = PaymentGateway.objects.get_or_create(
            name=PaymentGatewayEnum.PAYTM.value
        )
        self.upi_payment_mode, _created = PaymentMode.objects.get_or_create(
            name=PaymentModeEnum.UPI
        )
        self.gateway_mode, _created = PaymentGatewayMode.objects.get_or_create(
            gateway=self.paytm_payment_gateway, mode=self.upi_payment_mode
        )

    def create_transaction(self, amount, status, transaction_type, gateway_status):
        transaction = Transaction.objects.create(
            user=self.user,
            status=status,
            amount=amount,
            transaction_type=transaction_type,
            gateway_mode=self.gateway_mode,
            gateway_transaction_status=gateway_status,
        )
        return transaction

    def test_create_transaction(self):
        transaction = self.create_transaction(
            100,
            TransactionStatus.PENDING,
            TransactionType.DEBIT,
            TransactionStatus.PENDING,
        )
        self.assertTrue(isinstance(transaction, Transaction))
        self.assertEqual(transaction.__str__(), transaction.gateway_order_id)
        self.assertEqual(transaction.get_status(), TransactionStatus.PENDING)

    def test_handle_status_signal(self):
        transaction = self.create_transaction(
            100,
            TransactionStatus.PENDING,
            TransactionType.DEBIT,
            TransactionStatus.SUCCESS,
        )
        self.assertEqual(transaction.get_status(), TransactionStatus.SUCCESS)

    def test_create_refund_signal(self):
        transaction = self.create_transaction(
            100,
            TransactionStatus.FAILED,
            TransactionType.DEBIT,
            TransactionStatus.SUCCESS,
        )
        refund = Transaction.objects.filter(
            original_transaction=transaction, transaction_type=TransactionType.CREDIT
        ).first()
        self.assertTrue(isinstance(refund, Transaction))
        self.assertEqual(refund.amount, -transaction.amount)
        self.assertEqual(refund.status, TransactionStatus.PENDING)
        self.assertEqual(refund.user, transaction.user)
