from unittest import skip
from unittest.mock import patch

from django.urls import reverse

from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketInitiateTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

    @skip("Skipping test_ticket_cancel_success")
    def test_ticket_cancel_success(self):
        # make initiate request
        # no such functionality in the app
        pass

