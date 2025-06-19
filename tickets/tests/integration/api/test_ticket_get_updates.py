import logging
from unittest.mock import patch

import responses
from django.urls import reverse

from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketInitiateTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_retrieve_ticket_updates(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]

        url = reverse("tickets:ticket-updates", kwargs={"pk": self.pnr})
        logging.info(f"URL: {url}")
        response = self.client.get(
            url,
            format="json",
        )
        self.assertEqual(response.status_code, 200)
