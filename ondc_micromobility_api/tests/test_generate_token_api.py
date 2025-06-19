from django.test import TestCase

from ondc_micromobility_api.ondc_wrapper.base import APIClientBase


class GenerateTokenAPITestCase(TestCase):

    def test_generate_token_api(self):
        api_client_base = APIClientBase()

        # Call the get_or_generate_token method which now includes get_access_token logic.
        token = api_client_base.get_or_generate_token()

        # At minimum, check if we received access token
        print(f"Token: {token}")
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
