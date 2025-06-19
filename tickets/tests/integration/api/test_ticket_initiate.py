from unittest import skip

import responses

from tickets.models.ticket_setup import TicketUpdate, Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketInitiateTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_ticket_initiate_success(self):
        self.init_response = self.initiate_ticket()
        self.assertEqual(self.init_response.status_code, 200)

        pnr = self.init_response.data["pnr"]
        ticket_obj = Ticket.objects.get(pnr=pnr)
        # Check if a TicketUpdate object has been created for the ticket
        ticket_update_exists = TicketUpdate.objects.filter(ticket=ticket_obj).exists()
        self.assertTrue(ticket_update_exists, "Expected a TicketUpdate object to be created but none found.")

        # Further, check if the details are as expected
        ticket_update = TicketUpdate.objects.get(ticket=ticket_obj)
        self.assertEqual(ticket_update.details, {"status": "created"})

    @skip("Complete this test")
    def test_ticket_re_initiate_within_90_min_should_fail(self):
        pass