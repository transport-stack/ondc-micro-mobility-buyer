import django
django.setup()
from taskschedule.tasks import create_ticket_summary

import logging

from modules.time_utils import TimePeriod
from modules.utils import save_csv_file, convert_objects_to_csv
from datetime import datetime, timedelta

logging.info("Creating Ticket & Refund Summary for Previous Day")
start_datetime, end_datetime = TimePeriod.get_current_year()

tickets, tickets_headers = create_ticket_summary(start_datetime, end_datetime)

# Convert the data to CSV format
ticket_csv = convert_objects_to_csv(tickets, tickets_headers)

yesterday = datetime.now() - timedelta(days=1)
start_date = yesterday.strftime("%Y-%m-%d")
ticket_filename = f'ticket_summary_{start_date}.csv'
save_csv_file(ticket_filename, ticket_csv)
