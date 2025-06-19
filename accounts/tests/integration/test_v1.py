from unittest.mock import patch, Mock

from rest_framework import status

from accounts.models import MyUser
from django.test import TestCase

from modules.test_utils import mock_external_services, mock_login_services
from tickets.tests.integration.test_base_setup import BasicTestCase


class UserTestCase(BasicTestCase):
    def setUp(self):
        super().setUp()

        self.login_url = "/web/api/v1/accounts/login/"
        self.verify_otp_url = "/web/api/v1/accounts/verify-otp/"
        # Setup code here, if any
        self.test_username_two = "+917777777788"

    def tearDown(self):
        super().tearDown()

    def test_new_user_login_and_verify_otp(self):
        new_username = self.test_username_two

        login_response = self.client.post(
            path=self.login_url,
            data={"username": new_username},
            format="json"

        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        self.assertFalse(MyUser.objects.filter(username=new_username).exists())

        # Test verify_otp endpoint

        # note: any OTP works as we are mocking the response
        verify_otp_response = self.client.post(
            path=self.verify_otp_url,
            data={"username": new_username, "otp": "1214"},
            format="json",

        )
        self.assertEqual(verify_otp_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", verify_otp_response.data)
        self.assertIn("refresh_token", verify_otp_response.data)

        # Check if new user is created
        self.assertTrue(MyUser.objects.filter(username=new_username).exists())

    def test_repeat_user_login_and_verify_otp(self):
        self.existing_user = MyUser.objects.create(username=self.test_username_two)
        existing_username = self.existing_user.username

        login_response = self.client.post(self.login_url, {"username": existing_username},
                                          format="json", )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        verify_otp_response = self.client.post(self.verify_otp_url,
                                               {"username": existing_username, "otp": "correct_otp"},
                                               format="json", )
        self.assertEqual(verify_otp_response.status_code, status.HTTP_200_OK)

        # Check no new user is created
        self.assertEqual(MyUser.objects.filter(username=existing_username).count(), 1)

    def test_new_user_login_without_std_code_should_fail(self):
        new_username = self.test_username_two[-10:]
        login_response = self.client.post(self.login_url, {"username": new_username},
                                          format="json", )
        self.assertEqual(login_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_new_user_otp_mobile_number_without_std_code_should_fail(self):
        new_username = self.test_username_two[-10:]

        verify_otp_response = self.client.post(self.verify_otp_url,
                                               {"username": new_username, "otp": "correct_otp"},
                                               format="json", )
        self.assertEqual(verify_otp_response.status_code, status.HTTP_400_BAD_REQUEST)
