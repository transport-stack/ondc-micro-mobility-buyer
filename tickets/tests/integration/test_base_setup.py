import json
import logging
import re
from pathlib import Path
from unittest.mock import patch, PropertyMock, Mock
import responses
from responses import RequestsMock
from django.test import TestCase
from django.urls import reverse
from django.test import TestCase, RequestFactory, override_settings

from accounts.models.user_setup import MyUser
from modules.constants import DMRC_ENUM
from modules.env_main import X_API_KEY, GENERIC_LOGIN_PASSWORD
from modules.models import TransitMode
from modules.utils import load_json
from setup.init import set_up_database
from transit.models.transit_setup import TransitOption

from django.test import TestCase, RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient


@override_settings(X_API_KEY="test")
class BasicTestCase(TestCase):
    def setUp(self):
        self.responses = set_up_mock_responses()
        self.responses.start()
        self.responses.assert_all_requests_are_fired = False

        # setup the mock functions
        set_up_mock_functions()

        # Patching the getpass.getpass function
        self.mocked_getpass_function = patch('getpass.getpass', return_value="your_default_password").start()

        set_up_database(testing=True)
        self.factory = RequestFactory()
        self.phone = "+917777777777"
        self.username = self.phone
        self.password = GENERIC_LOGIN_PASSWORD
        MyUser.objects.all().delete()
        self.user = MyUser.objects.create_user(
            username=self.username, phone=self.phone, password=self.password
        )
        self.token = self.get_token_for_user()

        self.client = APIClient()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.token}", HTTP_X_API_KEY=X_API_KEY
        )

    def tearDown(self):
        super().tearDown()

        # Stop the patching
        self.responses.stop()
        self.responses.reset()
        patch.stopall()
        self.mocked_getpass_function.stop()

    def get_token_for_user(self):
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)

    def test_login_view(self):
        request_data = {"username": str(self.user.phone)}
        response = self.client.post(
            reverse("accounts:user-login"), data=request_data, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_true(self):
        self.assertTrue(True)


def set_up_mock_functions():
    # Setup the mock patches
    mock_send_otp_patch = patch('messaging_service.wrapper.base.MessagingServiceWrapper.send_otp')
    mock_verify_otp_patch = patch('messaging_service.wrapper.base.MessagingServiceWrapper.verify_otp')

    # Start the patches
    mock_send_otp = mock_send_otp_patch.start()
    mock_verify_otp = mock_verify_otp_patch.start()

    # Configure the mock objects
    mock_send_otp.return_value = Mock(status_code=200, data={
        "description": "OTP sent successfully",
        "expires_after": 5,
        "message": "Success"
    })
    mock_verify_otp.return_value = Mock(status_code=200, data={
        "description": "User verified successfully",
        "long_signature": "signature",
        "message": "Success"
    })


def set_up_mock_responses():
    requests_mock_obj = RequestsMock()
    requests_mock_obj.start()
    # File paths
    file_paths = [
        Path("ondc_micromobility_api/tests/mock_responses/FareFromOneSourceToAllDestination.json"),
        Path("ondc_micromobility_api/tests/mock_responses/Fetch_Fare_Request.json"),
        Path("ondc_micromobility_api/tests/mock_responses/GenerateToken_response.json"),
        Path("ondc_micromobility_api/tests/mock_responses/Route_Request.json"),
        Path("ondc_micromobility_api/tests/mock_responses/Ticket_Request.json")
    ]

    # paytm paths
    file_paths += [
        Path("payments/tests/mock_responses/initiateTransaction.json"),
        Path("payments/tests/mock_responses/order_status_success.json"),
    ]

    # Loop through each file and set up the mock response
    for file_path in file_paths:
        mock_data = load_json(file_path)
        url = mock_data["url"]
        method = mock_data["method"]
        response = mock_data["response"]

        # Adjust this to match how you're setting up mock responses
        if method == "GET":
            requests_mock_obj.add(responses.GET, url, json=response, status=200)
        elif method == "POST":
            requests_mock_obj.add(responses.POST, url, json=response, status=200)

    # add paytm initiate transaction end point as regex
    file_path = Path("payments/tests/mock_responses/initiateTransaction.json")
    mock_data = load_json(file_path)
    # url = mock_data["url"]
    method = mock_data["method"]
    response = mock_data["response"]
    url_pattern = re.compile(
        r'https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction\?mid=[^&]+&orderId=[^&]+'
    )
    requests_mock_obj.add(
        method,
        url=url_pattern,
        json=response,
        status=200
    )

    return requests_mock_obj


class SimpleUserTransitTestCase(BasicTestCase):
    def setUp(self):
        super().setUp()
        self.transit_option = TransitOption.objects.get(
            provider__name=DMRC_ENUM, transit_mode=TransitMode.METRO
        )
        # Start patching the function
        self.mocked_fcm_function = patch('tickets.models.ticket_setup.Ticket.send_user_status_notification',
                                         return_value=None).start()

    def tearDown(self):
        responses.reset()

        # Stop the patching
        self.mocked_fcm_function.stop()

        super().tearDown()

    def initiate_ticket(self):
        request_data = {
            "start_location_code": "ROHINI_SEC_22_TERMINAL",
            "end_location_code": "AVANTIKA_XING",
            "transit_option": {
                "transit_mode": "BUS",
                "provider": {
                    "name": "ONDC"
                }
            },
            "meta": {
                "route_id": "102STLDOWN"
            }
        }
        response = self.client.post(
            reverse("tickets:ticket-initiate"), data=request_data, format="json"
        )
        self.pnr = response.data["pnr"]
        return response

    def create_transaction(self, pnr):
        request_data = {
            "payment_mode": "UNKNOWN"
        }
        response = self.client.post(
            f'/api/v1/tickets/{pnr}/transaction/',
            data=request_data,
            format="json"
        )
        self.gateway_order_id = response.data["gateway_order_id"]
        return response
