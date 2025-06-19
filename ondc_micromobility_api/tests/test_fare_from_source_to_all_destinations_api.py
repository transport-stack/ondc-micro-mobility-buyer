from django.test import TestCase
import logging

from ondc_micromobility_api.ondc_wrapper.fare_from_source_to_all_destinations_api import FareFromSourceToAllDestinationsAPI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FareFromSourceToAllDestinationsAPITestCase(TestCase):

    def test_fare_from_source_to_all_destinations_api(self):
        # Assuming token generation is done internally in the API client
        STATION_ID = 17
        client = FareFromSourceToAllDestinationsAPI(stationID=STATION_ID)
        response_obj = client.post_api()

        # Assertions
        self.assertIsNotNone(response_obj)
        self.assertTrue(response_obj.is_success())  # Uncomment and modify as needed

    def test_fare_from_source_to_all_destinations_without_token_api(self):
        # This test seems to be almost the same as the above one.
        # If you're testing a scenario where token is intentionally missing,
        # you'll need to modify the client or setup accordingly.
        STATION_ID = 17
        client = FareFromSourceToAllDestinationsAPI(stationID=STATION_ID)
        response_obj = client.post_api()

        # Assertions
        self.assertIsNotNone(response_obj)
        self.assertTrue(response_obj.is_success())  # Uncomment and modify as needed
