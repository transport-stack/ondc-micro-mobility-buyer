import logging

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

from payments.constants import PaymentGatewayEnum, PaymentModeEnum
from payments.models.payment_gateway_setup import PaymentGateway, PaymentMode
from payments.models.transaction_setup import PaymentGatewayMode

logger = logging.getLogger(__name__)


def create_object(model_name, fields):
    Model = apps.get_model(model_name)
    obj, created = Model.objects.get_or_create(**fields)

    action = "created" if created else "already exists"
    logger.info(f"{model_name} {fields} {action}")


def populate_models(model_data_list):
    for model_data in model_data_list:
        create_object(model_data["model"], model_data["fields"])


def populate_payment_gateway_mode():
    # get payment gateways
    default_payment_gateway = PaymentGateway.objects.get(
        name=PaymentGatewayEnum.DEFAULT.value
    )
    paytm_payment_gateway = PaymentGateway.objects.get(
        name=PaymentGatewayEnum.PAYTM.value
    )

    # each payment mode listed above
    payment_modes = PaymentModeEnum.get_list()

    # for self gateway, add cash payment mode in payment gateway mode
    PaymentGatewayMode.objects.get_or_create(
        gateway=default_payment_gateway,
        mode=PaymentMode.objects.get(name=PaymentModeEnum.CASH.value),
    )

    # for paytm gateway, add all payment modes in payment gateway mode except cash
    for mode in payment_modes:
        if mode == PaymentModeEnum.CASH.value:
            continue
        PaymentGatewayMode.objects.get_or_create(
            gateway=paytm_payment_gateway, mode=PaymentMode.objects.get(name=mode)
        )


def setup_payment_gateways_and_modes():
    logger.info("Adding payment gateway modes")
    logger.info("Adding payment gateways")
    logger.info("Adding payment modes")

    populate_models(
        [
            {
                "model": "payments.paymentmode",
                "fields": {"name": mode},
            }
            for i, mode in enumerate(PaymentModeEnum.get_list(), start=1)
        ]
    )

    populate_models(
        [
            {
                "model": "payments.paymentgateway",
                "fields": {"name": gateway},
            }
            for i, gateway in enumerate(PaymentGatewayEnum.get_list(), start=1)
        ]
    )

    populate_payment_gateway_mode()


if __name__ == "__main__":
    setup_payment_gateways_and_modes()
