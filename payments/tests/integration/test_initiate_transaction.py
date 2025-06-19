from django.test import TestCase
from unittest import skip
from mixer.backend.django import mixer

from payments.constants import PaymentGatewayEnum, PaymentModeEnum
from payments.models.payment_gateway_setup import (
    PaymentGateway,
    PaymentGatewayMode,
    PaymentMode,
)
from payments.models.transaction_setup import Transaction, TransactionResponseSerializer


class PaymentGatewayModeTestCase(TestCase):
    def setUp(self):
        self.gateway_paytm = mixer.blend(
            PaymentGateway, name=PaymentGatewayEnum.PAYTM.value
        )
        self.gateway_default = mixer.blend(
            PaymentGateway, name=PaymentGatewayEnum.DEFAULT.value
        )
        self.mode_upi = mixer.blend(PaymentMode, name=PaymentModeEnum.UPI.value)
        self.mode_net_banking = mixer.blend(
            PaymentMode, name=PaymentModeEnum.NET_BANKING.value
        )
        self.mode_unknown = mixer.blend(PaymentMode, name=PaymentModeEnum.UNKNOWN.value)
        self.gateway_mode_upi = mixer.blend(
            PaymentGatewayMode, gateway=self.gateway_paytm, mode=self.mode_upi
        )
        self.gateway_mode_net_banking = mixer.blend(
            PaymentGatewayMode, gateway=self.gateway_paytm, mode=self.mode_net_banking
        )

        # paytm's all in one sdk where user decides mode later
        self.gateway_mode_unknown = mixer.blend(
            PaymentGatewayMode, gateway=self.gateway_paytm, mode=self.mode_unknown
        )

    @skip("Can be test with production credentials only")
    def test_transaction_payload_paytm_upi(self):
        transaction = mixer.blend(
            Transaction, amount=1, gateway_mode=self.gateway_mode_upi
        )
        result = transaction.transaction_payload()
        serializer = TransactionResponseSerializer(data=result)
        assert serializer.is_valid()

    def test_transaction_payload_paytm_net_banking(self):
        transaction = mixer.blend(
            Transaction, amount=1, gateway_mode=self.gateway_mode_net_banking
        )
        result = transaction.transaction_payload()
        serializer = TransactionResponseSerializer(data=result)
        assert serializer.is_valid()

    def test_transaction_payload_default_gateway(self):
        # for the default gateway, there is no payload generation code yet
        transaction = mixer.blend(
            Transaction, amount=1, gateway_mode=self.gateway_mode_unknown
        )
        result = transaction.transaction_payload()
        serializer = TransactionResponseSerializer(data=result)
        assert serializer.is_valid()

    def test_transaction_payload_default_gateway_incorrect_fare(self):
        # TODO: write this test
        pass
