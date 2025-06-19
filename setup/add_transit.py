import logging

from modules.models import TransitMode
from transit.models.transit_setup import TransitOption, TransitProvider

logger = logging.getLogger(__name__)


def create_transit_provider_and_option(transit_mode):
    transit_mode_name = transit_mode.name
    transit_mode_value = transit_mode.value

    transit_provider, provider_created = TransitProvider.objects.get_or_create(
        name=transit_mode_name
    )

    transit_option, option_created = TransitOption.objects.get_or_create(
        provider=transit_provider, transit_mode=transit_mode_value
    )

    action = "created" if provider_created else "already exists"
    logger.info(f"Transit Provider: {transit_provider.name} {action}")

    action = "created" if option_created else "already exists"
    logger.info(f"Transit Option: {transit_option} {action}")


def setup_transit_modes():
    logger.info("Adding transit providers options")

    for transit_mode in TransitMode.__members__.values():
        create_transit_provider_and_option(transit_mode)
