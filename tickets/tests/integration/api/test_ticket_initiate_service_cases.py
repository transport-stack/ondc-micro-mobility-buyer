import logging

import responses

from tickets.models.ticket_setup import TicketUpdate, Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase
from unittest.mock import patch
from django.utils import timezone
import datetime


class TicketInitiateTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()

        # modifying calendar for this test case
        service_calendar = self.transit_option.service_calendar
        service_calendar.monday_start_time = datetime.time(6, 0)
        service_calendar.monday_end_time = datetime.time(21, 0)
        service_calendar.tuesday_start_time = datetime.time(6, 0)
        service_calendar.tuesday_end_time = datetime.time(21, 0)
        service_calendar.wednesday_start_time = datetime.time(6, 0)
        service_calendar.wednesday_end_time = datetime.time(21, 0)
        service_calendar.thursday_start_time = datetime.time(6, 0)
        service_calendar.thursday_end_time = datetime.time(21, 0)
        service_calendar.friday_start_time = datetime.time(6, 0)
        service_calendar.friday_end_time = datetime.time(21, 0)
        service_calendar.saturday_start_time = datetime.time(6, 0)
        service_calendar.saturday_end_time = datetime.time(21, 0)
        service_calendar.sunday_start_time = datetime.time(8, 0)
        service_calendar.sunday_end_time = datetime.time(21, 0)

        service_calendar.save()

    def tearDown(self):
        super().tearDown()

    def test_ticket_initiate_just_after_service_starts(self):
        """Test initiating a ticket shortly after the transit service begins operations for the day."""

        # Get the current date before mocking
        current_date = timezone.now().date()

        # Set the current time to just after the service starts
        # Assuming service starts at 6:00 AM, we'll test at 6:05 AM
        with patch('django.utils.timezone.now') as mock_now:
            mock_service_start_time = timezone.make_aware(datetime.datetime.combine(
                current_date,
                datetime.datetime.strptime("08:05", "%H:%M").time()
            ))
            mock_now.return_value = mock_service_start_time

            # Initiate ticket
            response = self.initiate_ticket()

            logging.info("Response: {}".format(response.data))
            # Assert ticket initiation is successful
            self.assertEqual(response.status_code, 200,
                             "Ticket initiation should be successful just after service starts")
            self.assertIn("pnr", response.data, "Response should contain a PNR number")

    def test_ticket_initiate_on_inactive_service_day(self):
        """Test initiating a ticket on a day when the transit service is marked as inactive."""

    def test_ticket_initiate_on_holiday(self):
        """Test initiating a ticket on a day that is a holiday for the transit service."""

    def test_ticket_initiate_on_limited_hours_day(self):
        """Test initiating a ticket on a day when the transit service operates for limited hours, outside which
        the service is inactive."""

    def test_ticket_initiate_during_active_hours(self):
        """Test initiating a ticket during the hours when the transit service is active."""

    def test_ticket_initiate_just_before_service_ends(self):
        """Test initiating a ticket shortly before the transit service schedule ends for the day."""
