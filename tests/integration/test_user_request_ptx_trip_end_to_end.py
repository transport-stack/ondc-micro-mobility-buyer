from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import MyUser
from django.test import Client


class JSONClient(Client):
    def post(self, path, data=None, content_type="application/json", **extra):
        return super().post(path, data, content_type=content_type, **extra)


@patch("modules.views.XAPIKeyPermission.has_permission")
class MyUserViewSetTestCase(TestCase):
    accounts_user_login_url = reverse("accounts:user-login")
    tickets_ticket_initiate_url = reverse("tickets:ticket-initiate")

    def setUp(self):
        self.username = "abc@gmail.com"
        self.client = JSONClient()  # Use the custom client

        # first time user login, note: password automatically gets generated
        self.client.post(
            self.accounts_user_login_url,
            {
                "username": self.username,
            },
        )

    def test_login_successful(self, mock_authenticate):  # Add the mock argument here
        # You can configure the mock here if needed
        # mock_authenticate.return_value = (self.user, None)

        response = self.client.post(
            self.accounts_user_login_url,
            {
                "username": self.username,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

        # You can add more assertions here to check the content of the response
