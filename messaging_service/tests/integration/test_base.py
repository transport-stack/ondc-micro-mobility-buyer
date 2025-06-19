from unittest import skip

from django.test import TestCase
from messaging_service.wrapper.base import MessagingServiceWrapper


class TestMessagingServiceWrapper(TestCase):
    def setUp(self):
        self.api = MessagingServiceWrapper()
        self.phone_number = (
            "9818711051"  # Replace with the phone number you want to test
        )

    @skip("Skipping test_send_otp")
    def test_send_otp(self):
        response = self.api.send_otp(self.phone_number).json()
        self.assertIsNotNone(response)
        # Assuming the API returns a 'message' field on success
        self.assertEqual(response.get("message"), "Success")

    @skip("Skipping test_send_otp")
    def test_wrong_verify_otp(self):
        # Note: This test assumes you have a valid OTP. Replace '1977' with an actual OTP.
        otp = "1977"
        response = self.api.verify_otp(self.phone_number, otp).json()
        self.assertIsNotNone(response)
        # Assuming the API returns a 'message' field on success
        self.assertEqual(response.get("message"), "Failed")

