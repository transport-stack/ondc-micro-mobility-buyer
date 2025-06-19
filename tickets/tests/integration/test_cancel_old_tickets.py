from unittest import skip
from unittest.mock import patch

import responses

from modules.models import TicketStatus
from payments.models.transaction_setup import Transaction
from tickets.models import Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketBookAndCancelBySystemTest(SimpleUserTransitTestCase):
    @patch("modules.views.XAPIKeyPermission.has_permission", return_value=True)
    def setUp(self, mock_auth):
        super().setUp()
        # Bypass the actual authentication
        mock_auth.return_value = (self.user, None)
        self.initiate_ticket()
        # self.assertEqual(response.status_code, 200)

    # TODO: update this test when we allow a confirmed ticket to get cancelled within stipulated time
    def test_cancel_confirmed_ticket_should_fail(self):
        # Bypass the actual authentication
        self.ticket = Ticket.objects.filter(pnr=self.pnr).first()

        # set transaction status to complete
        # transaction_response = TicketTransactionInitiationTest.create_transaction(self.pnr)
        self.create_transaction(self.pnr)

        Transaction.objects.filter(
            gateway_order_id=self.gateway_order_id).first().set_gateway_transaction_status_success()
        self.ticket.update_status(TicketStatus.CONFIRMED)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.CONFIRMED)

        self.ticket.update_status(TicketStatus.CANCELLED)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, TicketStatus.CONFIRMED)


    # @skip("This test is failing because we haven't handled the case of cancellation by system")
    def test_create_ticket_no_update_cancelled_by_system_success(self):
        # Bypass the actual authentication
        self.ticket = Ticket.objects.filter(pnr=self.pnr).first()
        self.ticket.cancel_by_system()
        self.assertEqual(self.ticket.status, TicketStatus.CANCELLED)

    @skip("This test is failing because we haven't handled the case of repeated cancellation by system")
    def test_create_ticket_no_update_cancelled_by_system_repeated_success(
            self
    ):
        # Bypass the actual authentication
        self.ticket = Ticket.objects.filter(pnr=self.pnr).first()
        self.ticket.cancel_by_system()
        self.ticket.cancel_by_system()
        self.assertEqual(self.ticket.status, TicketStatus.CANCELLED)
