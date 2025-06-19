from unittest import skip
from unittest.mock import patch

import responses
from django.urls import reverse

from modules.models import TicketStatus
from modules.pg.paytm.wrapper.transaction_status_api import ResultCode
from modules.serializers import TicketStatusField
from payments.models import Transaction
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase, set_up_mock_responses


class TicketTransactionConfirm(SimpleUserTransitTestCase):
    def setUp(self):
        # self.responses = set_up_mock_responses()
        # self.responses.start()
        # self.responses.assert_all_requests_are_fired = False

        super().setUp()

    def tearDown(self):
        # self.responses.stop()
        # self.responses.reset()
        super().tearDown()

    def test_ticket_transaction_initiate_pg_success_ticket_confirmed(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]

        # call transaction initiate
        response = self.client.post(
            reverse("tickets:ticket-transaction", kwargs={"pk": self.pnr}),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        gateway_order_id = response.json()["data"]["gateway_order_id"]

        # mark transaction as success
        Transaction.objects.get(gateway_order_id=gateway_order_id).set_status_success()

        # call confirm
        response = self.client.get(
            reverse("tickets:ticket-confirm", kwargs={"pk": self.pnr}),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], TicketStatus.CONFIRMED.label)
        self.assertIsNotNone(response.data["service_details"])
        self.assertEqual(response.data["transit_pnr"], "9876597DUMMY4632")
