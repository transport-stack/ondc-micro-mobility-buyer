import os
import unittest
from datetime import timedelta
from unittest import skip
from unittest.mock import patch

import django
from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from modules.models import TicketStatus
from taskschedule.tasks import (
    test_one_min_task,
    check_transaction_status,
    check_transaction_status_older,
    ticket_check_payment_status,
    expire_previous_day_journeys,
    expire_previous_day_confirmed_tickets,
    cancel_previous_day_pending_tickets,
    check_transaction_status_today, 
    # cancel_pending_tickets_post_timeout
)

django.setup()


# TODO: Add integration test for each

class IntegrationTaskTestCases(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        # Cleanup: Remove any data you added during setUp
        pass

    @skip("Not implemented")
    def test_test_one_min_task(self):
        test_one_min_task()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_check_transaction_status_today(self):
        check_transaction_status_today()

    @skip("Not implemented")
    def test_check_transaction_status(self):
        check_transaction_status()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_check_transaction_status_older(self):
        check_transaction_status_older()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_ticket_check_payment_status(self):
        ticket_check_payment_status()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_expire_previous_day_journeys(self):
        expire_previous_day_journeys()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_expire_previous_day_confirmed_tickets(self):
        expire_previous_day_confirmed_tickets()
        # Use assertions to verify expected results in the test database

    @skip("Not implemented")
    def test_cancel_previous_day_pending_tickets(self):
        cancel_previous_day_pending_tickets()
        # Use assertions to verify expected results in the test database

    # @skip("Not implemented")
    # @patch("ondc_micromobility_api.models.SystemParameters.objects.get")
    # def test_cancel_pending_tickets_post_timeout(self, mock_get):
    #     mock_system_parameters = mock_get.return_value

    #     mock_system_parameters.ticket_confirmation_timeout = 120
    #     # cancel_pending_tickets_post_timeout()

if __name__ == "__main__":
    unittest.main()
