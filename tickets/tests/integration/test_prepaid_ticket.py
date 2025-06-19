from modules.models import TicketStatus, TransactionStatus, PaymentType
from payments.models.transaction_setup import Transaction
from tickets.exceptions.main import PaymentAmountMismatchError
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import Ticket, TicketType
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()
        self.ticket_type = TicketType.objects.create()  # Add required fields
        self.basic_amount = 100

    def create_prepaid_ticket(self, transaction=None):
        self.fare_breakup = FareBreakup.objects.create(
            basic=self.basic_amount
        )  # Add required fields
        ticket = Ticket.objects.create(
            created_by=self.user,
            created_for=self.user,
            transit_option=self.transit_option,
            fare=self.fare_breakup,
            payment_type=PaymentType.PREPAID,
        )
        ticket.transaction.add(transaction)
        return ticket

    def create_postpaid_ticket(self, transaction=None):
        ticket = Ticket.objects.create(
            created_by=self.user,
            created_for=self.user,
            transit_option=self.transit_option,
            fare=self.fare_breakup,
            transaction=transaction,
            payment_type=PaymentType.PREPAID,
        )

        ticket.transaction.add(transaction)
        return ticket

    def test_create_prepaid_ticket(self):
        ticket = self.create_prepaid_ticket()
        self.assertEqual(Ticket.objects.count(), 1)
        self.assertEqual(ticket.status, TicketStatus.PENDING)
        self.assertEqual(ticket.transit_option, self.transit_option)

    def test_update_prepaid_ticket_status_without_transaction_should_fail(self):
        ticket = self.create_prepaid_ticket()
        with self.assertRaises(Exception):
            ticket.update_status(TicketStatus.CONFIRMED)

    def test_update_prepaid_ticket_status_with_transaction_should_pass(self):
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=self.basic_amount,
            status=TransactionStatus.SUCCESS,
        )
        ticket = self.create_prepaid_ticket(self.transaction)
        ticket.update_status(TicketStatus.CONFIRMED)
        self.assertEqual(ticket.status, TicketStatus.CONFIRMED)

    def test_update_prepaid_ticket_status_with_failed_transaction_should_fail(self):
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=self.basic_amount,
            status=TransactionStatus.FAILED,
        )

        ticket = self.create_prepaid_ticket(self.transaction)
        with self.assertRaises(Exception):
            ticket.update_status(TicketStatus.CONFIRMED)

    def test_update_prepaid_ticket_status_with_pending_transaction_should_fail(self):
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=self.basic_amount,
            status=TransactionStatus.PENDING,
        )

        ticket = self.create_prepaid_ticket(self.transaction)
        with self.assertRaises(Exception):
            ticket.update_status(TicketStatus.CONFIRMED)

    # add test with successful transaction with different amount that should fail
    # TODO: add transaction amount mismatch test
    # def test_update_prepaid_ticket_status_with_successful_transaction_with_different_amount_should_fail(
    #         self,
    # ):
    #     self.transaction = Transaction.objects.create(
    #         user=self.user,
    #         amount=self.basic_amount - 10,
    #         status=TransactionStatus.SUCCESS,
    #     )
    #
    #     ticket = self.create_prepaid_ticket(self.transaction)
    #     with self.assertRaises(PaymentAmountMismatchError):
    #         ticket.update_status(TicketStatus.CONFIRMED)
