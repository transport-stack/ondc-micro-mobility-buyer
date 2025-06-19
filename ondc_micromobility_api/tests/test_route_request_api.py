from django.test import TestCase
import logging
from ondc_micromobility_api.ondc_wrapper.route_request_api import RouteRequestAPI

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class RouteRequestAPITestCase(TestCase):

    def test_route_request_api(self):
        client = RouteRequestAPI()
        response_obj = client.post_api()

        self.assertIsNotNone(response_obj)
        self.assertTrue(response_obj.is_success())

    def test_route_request_without_token_api(self):
        client = RouteRequestAPI()
        response_obj = client.post_api()

        self.assertIsNotNone(response_obj)
        self.assertTrue(response_obj.is_success())
