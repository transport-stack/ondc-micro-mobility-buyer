from django.db import models

from common.constants import upper_alphanumeric_underscore_regex
from modules.models import ActiveMixin, DateTimeMixin


class PaymentGateway(ActiveMixin, DateTimeMixin):
    """
    This model represents a payment gateway, such as Stripe or Razorpay, or self for cash.
    """

    name = models.CharField(
        max_length=32,
        primary_key=True,
        validators=[upper_alphanumeric_underscore_regex],
    )

    # Here you can add more fields that describe the gateway, such as an API key.

    def __str__(self):
        return self.name


class PaymentMode(ActiveMixin, DateTimeMixin):
    """
    This model represents a payment mode, such as credit card, net banking, or cash.
    """

    name = models.CharField(
        max_length=32,
        primary_key=True,
        validators=[upper_alphanumeric_underscore_regex],
    )

    def __str__(self):
        return self.name


class PaymentGatewayMode(ActiveMixin, DateTimeMixin):
    """
    This model represents a mode available through a specific gateway.
    """

    gateway = models.ForeignKey(PaymentGateway, on_delete=models.CASCADE)
    mode = models.ForeignKey(PaymentMode, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gateway) + "-" + str(self.mode)

    class Meta:
        unique_together = ("gateway", "mode")
