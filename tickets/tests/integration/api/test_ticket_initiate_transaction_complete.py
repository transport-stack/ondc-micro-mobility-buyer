import responses

from modules.models import TicketStatus
from tickets.models.ticket_setup import Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketTransactionInitiationTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        
    def test_successful_ticket_transaction_sets_payment_status_to_complete(self):
        self.init_response = self.initiate_ticket()
        self.assertEqual(self.init_response.status_code, 200)

        pnr = self.init_response.data["pnr"]
        ticket_obj = Ticket.objects.get(pnr=pnr)

        assert ticket_obj

        # set ticket.status -> expired
        ticket_obj.update_status(TicketStatus.EXPIRED)
        ticket_obj.refresh_from_db()
        assert ticket_obj.status == TicketStatus.EXPIRED

        # create a transaction (via api)
        # transaction_response = self.create_transaction(pnr)

        # call ticket / pnr / confirm (use mocked gateway status)

        # assert ticket.payment_status -> completed
