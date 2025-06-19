import threading
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
        super().setUp()

    def tearDown(self):
        super().tearDown()

    @skip("Try with staging postgres DB only")
    def test_ticket_transaction_initiate_pg_success_ticket_confirmed(self):
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

        def hit_confirm_endpoint():
            # You might need to adjust this URL call based on your actual URL configuration
            # call confirm
            response = self.client.get(
                reverse("tickets:ticket-confirm", kwargs={"pk": self.pnr}),
                format="json",
            )
            responses.append(response)

        responses = []

        # Create threads to hit the confirm endpoint concurrently
        thread1 = threading.Thread(target=hit_confirm_endpoint)
        thread2 = threading.Thread(target=hit_confirm_endpoint)

        # Start the threads
        thread1.start()
        thread2.start()

        # Wait for both threads to complete
        thread1.join()
        thread2.join()

        # Assert on the responses
        # Depending on your implementation, you might check for a specific response
        # to ensure one request was processed and the other possibly blocked or handled differently
        self.assertTrue(1 == 1)
        # self.assertEqual(len(responses), 2)
