from rest_framework import serializers

from payments.models.payment_gateway_setup import PaymentGateway, PaymentMode


class PaymentGatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGateway
        fields = ("name",)


class PaymentModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMode
        fields = ("name",)
