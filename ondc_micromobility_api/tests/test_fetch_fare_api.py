import logging

from ondc_micromobility_api.ondc_wrapper.fetch_fare_api import FetchFareAPI
from django.test import TestCase

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FetchFareAPITestCase(TestCase):  # Inherit from TestCase

    def test_fetch_fare_api(self):  # Define your test as a method inside this class
        # Arrange
        client = FetchFareAPI(Src_Stn=18, Dest_Stn=19)

        # Act
        response_obj = client.post_api()

        # Assert
        self.assertIsNotNone(response_obj)  # Using TestCase's assert methods
        self.assertTrue(response_obj.is_success())
