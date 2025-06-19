from unittest import skip
from unittest.mock import patch
import responses

from django.urls import reverse

from tickets.models import Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase, set_up_mock_responses


def determine_expected_transaction_initiate_http_result(ticket_obj):
    if ticket_obj.is_payment_type_postpaid():
        if ticket_obj.is_status_pending() or ticket_obj.is_status_cancelled():
            return 400  # Bad Request or similar failure code
        else:  # Confirmed or Expired
            return 200  # OK or success code

    elif ticket_obj.is_payment_type_prepaid():
        if ticket_obj.is_status_pending():
            return 200  # OK or success code
        else:  # Confirmed, Expired, or Cancelled
            return 400  # Bad Request or similar failure code

    return 500  # Internal Server Error or similar code for undefined cases


class TicketTransaction(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_ticket_transaction_initiate_success(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]
        # cancel the request
        ticket_obj = Ticket.objects.get(pnr=self.pnr)
        HTTP_RESULT_EXPECTED_CODE = determine_expected_transaction_initiate_http_result(ticket_obj)

        response = self.client.post(
            reverse("tickets:ticket-transaction", kwargs={"pk": self.pnr}),
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_RESULT_EXPECTED_CODE)

    def test_ticket_transaction_initiate_failed_for_repeated_call(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]

        # if pre-paid ticket, repeat transaction initiate should fail
        # if post-paid ticket, repeat transaction initiate should succeed
        ticket_obj = Ticket.objects.get(pnr=self.pnr)
        if ticket_obj.is_payment_type_prepaid():
            HTTP_RESULT_EXPECTED_CODE = 400
        elif ticket_obj.is_payment_type_postpaid():
            if ticket_obj.is_status_confirmed() or ticket_obj.is_status_expired():
                HTTP_RESULT_EXPECTED_CODE = 200
            else:
                return
        else:
            return

        response = self.client.post(
            reverse("tickets:ticket-transaction", kwargs={"pk": self.pnr}),
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("tickets:ticket-transaction", kwargs={"pk": self.pnr}),
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_RESULT_EXPECTED_CODE)

    # TODO: Write tests
    # if ticket is postpaid, status in pending or cancelled, single transaction initiate call should fail
    # if ticket is postpaid, status in confirmed or expired, single transaction initiate call should succeed
    # if ticket is prepaid, status in pending, single transaction initiate call should succeed
    # if ticket is prepaid, status in confirmed or expired or cancelled, this should fail
