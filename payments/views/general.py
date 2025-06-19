from modules.views import BaseViewSet
from payments.models.payment_gateway_setup import PaymentGateway, PaymentMode
from payments.models.transaction_setup import (
    PaymentGatewayMode,
    PaymentGatewayModeSerializer,
    Transaction,
    TransactionSerializer,
)
from payments.serializers.payment_gateway_setup import (
    PaymentGatewaySerializer,
    PaymentModeSerializer,
)


class TransactionViewSet(BaseViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    lookup_field = "gateway_order_id"
    model = Transaction


class PaymentGatewayViewSet(BaseViewSet):
    queryset = PaymentGateway.objects.all()
    serializer_class = PaymentGatewaySerializer
    lookup_field = "id"
    model = PaymentGateway


class PaymentModeViewSet(BaseViewSet):
    queryset = PaymentMode.objects.all()
    serializer_class = PaymentModeSerializer
    lookup_field = "id"
    model = PaymentMode


class PaymentGatewayModeViewSet(BaseViewSet):
    queryset = PaymentGatewayMode.objects.all()
    serializer_class = PaymentGatewayModeSerializer
    lookup_field = "id"
    model = PaymentGatewayMode
