from modules.models import TicketStatus, TransactionStatus, PaymentType
from payments.models.transaction_setup import Transaction
from tickets.exceptions.main import (
    PaymentAmountMismatchError,
    PostpaidTicketStatusPendingCannotCreateTransactionError,
)
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import Ticket, TicketType
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()
        self.basic_amount = 100
        self.fare_breakup = FareBreakup.objects.create(
            basic=self.basic_amount
        )  # Add required fields
        self.ticket_type = TicketType.objects.create()  # Add required fields

    def create_postpaid_ticket(self):
        return Ticket.objects.create(
            created_by=self.user,
            created_for=self.user,
            transit_option=self.transit_option,
            fare=self.fare_breakup,
            payment_type=PaymentType.POSTPAID,
        )

    def test_create_postpaid_ticket(self):
        ticket = self.create_postpaid_ticket()
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(ticket.status, TicketStatus.PENDING)
        self.assertFalse(ticket.transaction.all().exists())
        self.assertEqual(ticket.transit_option, self.transit_option)

    def test_update_postpaid_ticket_status_without_transaction_should_pass(self):
        ticket = self.create_postpaid_ticket()
        ticket.update_status(TicketStatus.CONFIRMED)
        self.assertEqual(ticket.status, TicketStatus.CONFIRMED)

    def test_no_transaction_should_be_allowed_for_pending_status(self):
        ticket = self.create_postpaid_ticket()
        with self.assertRaises(PostpaidTicketStatusPendingCannotCreateTransactionError):
            ticket.create_new_transaction()
