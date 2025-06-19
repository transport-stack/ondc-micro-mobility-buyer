from transit.views.transit_api_interface.base import TransitAPI
from transit.views.transit_api_interface.delhi_bus_ticketing_setup import DelhiBusTicketingAPI


def TransitApiFactory(provider_name: str) -> TransitAPI:
    if provider_name.lower() == "nammayatri" or "integrated_ticketing":
        return DelhiBusTicketingAPI()
        # return True
    # elif provider_name.lower() == 'anotherprovider':
    #    return AnotherProviderAPI()
    else:
        raise ValueError("Unsupported provider")
