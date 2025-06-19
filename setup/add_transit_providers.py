import logging

from modules.constants import DIMTS_ENUM, DTC_ENUM, RAPIDO_ENUM, NAMMAYATRI_ENUM, UBER_ENUM, DMRC_ENUM, ONDC_ENUM, INTEGRATED_TICKETING_ENUM
from modules.models import TransitMode
from transit.models.transit_setup import TransitOption, TransitProvider

logger = logging.getLogger(__name__)

TRANSIT_PROVIDERS = {
    RAPIDO_ENUM: [TransitMode.BIKE.value, TransitMode.AUTO_RICKSHAW.value],
    NAMMAYATRI_ENUM: [TransitMode.AUTO_RICKSHAW.value, TransitMode.CAR.value],
    INTEGRATED_TICKETING_ENUM: [TransitMode.AUTO_RICKSHAW.value],
    UBER_ENUM: [
        TransitMode.CAR.value,
        TransitMode.BIKE.value,
        TransitMode.AUTO_RICKSHAW.value,
    ],
    DTC_ENUM: [TransitMode.BUS.value],
    DIMTS_ENUM: [TransitMode.BUS.value],
    DMRC_ENUM: [TransitMode.METRO.value],
    ONDC_ENUM: [TransitMode.BUS.value],
}


def create_transit_provider(provider_name):
    t_obj, created = TransitProvider.objects.get_or_create(name=provider_name)
    action = "created" if created else "already exists"
    logger.info(f"Transit Provider: {t_obj.name} {action}")

    return t_obj


def create_transit_option(provider, mode):
    if mode not in TransitMode.values:
        raise ValueError(f"Invalid transit mode: {mode}")

    t_opt, created = TransitOption.objects.get_or_create(
        provider=provider, transit_mode=mode
    )
    action = "created" if created else "already exists"
    logger.info(f"Transit Option for {t_opt} {action}")


def setup_transit_providers_and_options():
    logger.info("Adding transit providers options")

    for provider_name, modes in TRANSIT_PROVIDERS.items():
        provider = create_transit_provider(provider_name)

        for mode in modes:
            create_transit_option(provider, mode)
