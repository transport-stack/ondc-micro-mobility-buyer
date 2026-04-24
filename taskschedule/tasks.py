import datetime
import logging
from collections import Counter
from email.mime.text import MIMEText

import uuid
from django.apps import apps
from django.core.cache import cache
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDate, Abs
from django.utils import timezone

from ondc_micromobility_api.models import SystemParameters as dmrc_ticketing_api_SystemParameters
from modules.firebase_cloud_messaging import send_fcm_silent_notification
from modules.models import TransactionType, TransactionStatus, TicketStatus
from modules.smtp_utils.core import SMTPUtils
from modules.time_utils import TimePeriod
from modules.utils import convert_objects_to_csv
import requests
import os
from modules.ondc_signature_generator.cryptic_utils import create_authorisation_header,verify_authorisation_header
import json
from datetime import datetime, time
from ondc_buyer_backend.constants import location
import datetime as dt

try:
    from celery import shared_task
except ImportError as exc:
    raise ImportError(
        "Please set up Redis and Celery for background tasks. See: "
        "https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/ "
        "and https://docs.celeryq.dev/en/stable/getting-started/introduction.html"
    ) from exc


@shared_task(name="test_one_min_task")
def test_one_min_task():
    logging.info("This is a test task that runs every minute")


@shared_task(name="check_transaction_status")
def check_transaction_status():
    Transaction = apps.get_model("payments", "Transaction")
    logging.info("check_transaction_status")
    for transaction in Transaction.get_all_gateway_transaction_status_pending_transactions():
        transaction.check_gateway_transaction_status()


@shared_task(name="check_transaction_status_today")
def check_transaction_status_today():
    Transaction = apps.get_model("payments", "Transaction")
    today_start_datetime = datetime.combine(datetime.today(), time.min)
    today_end_datetime = datetime.combine(datetime.today(), time.max)

    logging.info("check_transaction_status_today")
    for transaction in Transaction.get_all_gateway_transaction_status_pending_transactions(
        sd=today_start_datetime, ed=today_end_datetime
    ):
        transaction.check_gateway_transaction_status()


@shared_task(name="check_transaction_status_older")
def check_transaction_status_older():
    Transaction = apps.get_model("payments", "Transaction")
    logging.info("check_transaction_status_older")
    seven_days_ago_datetime = timezone.now() - datetime.timedelta(days=7)
    today_start_datetime = datetime.combine(datetime.today(), time.min)
    for transaction in Transaction.get_all_gateway_transaction_status_pending_transactions(
        sd=seven_days_ago_datetime, ed=today_start_datetime
    ):
        transaction.check_gateway_transaction_status()


@shared_task(name="ticket_check_payment_status")
def ticket_check_payment_status():
    """
    Checks for all tickets that are not completed and checks their payment status
    for last 30 days
    """
    logging.info("ticket_check_payment_status")
    thirty_days_ago_datetime = timezone.now() - datetime.timedelta(days=30)
    today_end_datetime = datetime.combine(datetime.today(), time.max)

    Ticket = apps.get_model("tickets", "Ticket")
    for ticket in Ticket.get_all_payment_status_not_completed_tickets(
        thirty_days_ago_datetime, today_end_datetime
    ):
        ticket.check_payment_status()


@shared_task(name="expire_previous_day_journeys")
def expire_previous_day_journeys():
    logging.info("expire_previous_day_journeys")
    Journey = apps.get_model("journey", "Journey")
    Journey.mark_journeys_as_completed()


@shared_task(name="check_payment_status_last_7_days")
def check_payment_status_last_7_days():
    logging.info("Checking payment status for the last 7 days' transactions")
    start_datetime = datetime.combine(datetime.today() - datetime.timedelta(days=7), time.min)
    end_datetime = timezone.now()

    Ticket = apps.get_model("tickets", "Ticket")
    for ticket in Ticket.get_all_payment_status_not_completed_tickets(start_datetime, end_datetime):
        ticket.check_payment_status()


@shared_task(name="check_payment_status_all")
def check_payment_status_all():
    logging.info("Checking payment status for all transactions")

    Ticket = apps.get_model("tickets", "Ticket")
    for ticket in Ticket.get_all_payment_status_not_completed_tickets(None, None):
        ticket.check_payment_status()


@shared_task(name="expire_previous_day_journeys")
def expire_previous_day_journeys():
    logging.info("expire_previous_day_journeys")
    Journey = apps.get_model("journey", "Journey")
    Journey.mark_journeys_as_completed()


@shared_task(name="expire_previous_day_confirmed_tickets")
def expire_previous_day_confirmed_tickets():
    logging.info("expire_previous_day_confirmed_tickets")
    end_of_yesterday = datetime.combine(datetime.today(), time.min)
    Ticket = apps.get_model("tickets", "Ticket")
    Ticket.mark_tickets_as_expired(end_datetime=end_of_yesterday)


@shared_task(name="cancel_previous_day_pending_tickets")
def cancel_previous_day_pending_tickets():
    logging.info("cancel_previous_day_pending_tickets")
    start_of_today = datetime.combine(datetime.today(), time.min)
    start_of_today = timezone.make_aware(start_of_today, timezone.get_current_timezone())
    Ticket = apps.get_model("tickets", "Ticket")
    Ticket.mark_tickets_as_cancelled(end_datetime=start_of_today)


@shared_task(name="cancel_pending_tickets_post_timeout")
def cancel_pending_tickets_post_timeout():
    SystemParameters = apps.get_model("ondc_micromobility_api", "SystemParameters")
    logging.info("cancel_pending_tickets_post_timeout")
    current_time = timezone.now()
    start_of_today = timezone.make_aware(dt.datetime.combine(current_time.date(), dt.time.min),
                                         timezone.get_current_timezone())

    # Get the timeout value
    timeout_seconds = SystemParameters.objects.get().ticket_confirmation_timeout
    timeout_time = current_time - dt.timedelta(seconds=timeout_seconds)
    Ticket = apps.get_model("tickets", "Ticket")
    Ticket.mark_tickets_as_cancelled(start_datetime=start_of_today, end_datetime=timeout_time)


@shared_task(name="delete_older_ticket_updates")
def delete_older_ticket_updates():
    """Run this every night"""
    logging.info("delete_older_ticket_updates")
    TicketUpdate = apps.get_model("tickets", "TicketUpdate")
    TicketUpdate.delete_older_ticket_updates()


@shared_task(name="create_refunds")
def create_refunds(start_datetime, end_datetime):
    logging.info("Creating Refunds for transactions between {} and {}".format(start_datetime, end_datetime))

    # Condition 1: Transaction status is FAILED, gateway transaction status is SUCCESS
    Transaction = apps.get_model("payments", "Transaction")
    transactions_for_refund_1 = Transaction.objects.filter(
        status=TransactionStatus.FAILED,
        gateway_transaction_status=TransactionStatus.SUCCESS,
        created_at__range=(start_datetime, end_datetime)
    )

    # Condition 2: Associated ticket is cancelled and gateway transaction status is SUCCESS
    # Exclude transactions already selected in transactions_for_refund_1
    Transaction = apps.get_model("payments", "Transaction")
    transactions_for_refund_2 = Transaction.objects.filter(
        tickets__status=TicketStatus.CANCELLED,
        gateway_transaction_status=TransactionStatus.SUCCESS,
        created_at__range=(start_datetime, end_datetime)
    ).exclude(
        gateway_order_id__in=transactions_for_refund_1.values('gateway_order_id')
    )

    # Combine both querysets
    refundable_transactions = transactions_for_refund_1 | transactions_for_refund_2

    for transaction in refundable_transactions:
        # Create and call refund API to refund transaction
        transaction.create_refund_transaction()


@shared_task(name="create_refunds_for_current_day")
def create_refunds_for_current_day():
    start_datetime, end_datetime = TimePeriod.get_current_day()
    create_refunds(start_datetime, end_datetime)


@shared_task(name="create_refunds_for_previous_day")
def create_refunds_for_previous_day():
    start_datetime, end_datetime = TimePeriod.get_previous_day()
    create_refunds(start_datetime, end_datetime)


@shared_task(name="create_refunds_for_previous_7_days")
def create_refunds_for_previous_7_days():
    start_datetime, end_datetime = TimePeriod.get_previous_n_days(7)
    create_refunds(start_datetime, end_datetime)


@shared_task(name="check_refund_status")
def check_refund_status():
    logging.info("Checking Refund Status")

    # Assuming you want to check the refunds initiated in the last 30 minutes
    thirty_minutes_ago = timezone.localtime() - datetime.timedelta(minutes=30)
    Transaction = apps.get_model("payments", "Transaction")
    refund_transactions = Transaction.objects.filter(
        transaction_type=TransactionType.CREDIT,
        status=TransactionStatus.PENDING,
        created_at__gte=thirty_minutes_ago,
    )

    for refund_transaction in refund_transactions:
        refund_transaction.check_gateway_transaction_status()


"""
create a task to initiate a refund for a transaction 
"""


@shared_task(name="initiate_refunds")
def initiate_refunds(start_datetime, end_datetime):
    # initiate refunds whose original transactions were created in above range
    logging.info("Initiate Refunds for transactions between {} and {}".format(start_datetime, end_datetime))

    # Condition 1: Transaction status is FAILED, gateway transaction status is SUCCESS
    Transaction = apps.get_model("payments", "Transaction")

    refundable_transactions = Transaction.objects.filter(
        status=TransactionStatus.PENDING,
        transaction_type=TransactionType.CREDIT,
        original_transaction__created_at__range=(start_datetime, end_datetime)
    )

    for transaction in refundable_transactions:
        # Create and call refund API to refund transaction
        transaction.initiate_refund_transaction()


@shared_task(name="initiate_refunds_for_current_day")
def initiate_refunds_for_current_day():
    start_datetime, end_datetime = TimePeriod.get_current_day()
    initiate_refunds(start_datetime, end_datetime)


@shared_task(name="initiate_refunds_for_previous_day")
def initiate_refunds_for_previous_day():
    start_datetime, end_datetime = TimePeriod.get_previous_day()
    initiate_refunds(start_datetime, end_datetime)


@shared_task(name="initiate_refunds_for_previous_7_days")
def initiate_refunds_for_previous_7_days():
    start_datetime, end_datetime = TimePeriod.get_previous_n_days(7)
    initiate_refunds(start_datetime, end_datetime)


@shared_task(name="send_user_silent_notification_shared_task")
def send_user_silent_notification_shared_task(channel_name, extra_params):
    logging.debug("send_user_silent_notification_shared_task")
    send_fcm_silent_notification(channel_name, extra_params=extra_params)


@shared_task(name="generate_recommendations")
def generate_recommendations():
    print("Generating Recommendations")

    # Replace 'accounts', 'tickets', and model names with your actual app and model names
    MyUser = apps.get_model("accounts", "MyUser")
    TicketRecommendation = apps.get_model("tickets", "TicketRecommendation")
    Ticket = apps.get_model("tickets", "Ticket")

    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)

    all_tickets_recently = Ticket.objects.filter(
        Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
        created_at__gte=thirty_days_ago,
        created_for__isnull=False
    )

    # Get distinct user IDs who created these tickets
    distinct_user_ids = all_tickets_recently.values_list('created_for', flat=True).distinct()

    for user_id in distinct_user_ids:
        user = MyUser.objects.get(id=user_id)
        print("Checking recommendations for user {}".format(user.id))
        # Find the latest TicketRecommendation object for the user
        latest_recommendation = TicketRecommendation.objects.filter(
            created_for=user
        ).order_by('-created_at').first()

        # handle the case when latest_recommendation isn't found
        if latest_recommendation:
            print("Previous recommendations found for user {}".format(user.id))

            # check if there's a need to generate a new recommendation
            new_tickets_since_last_recommendation = Ticket.objects.filter(
                Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
                created_for=user,
                created_at__gte=latest_recommendation.created_at
            ).exists()

            if not new_tickets_since_last_recommendation:
                print("No new tickets since last recommendation for user {}".format(user.id))
                continue

        # Fetch tickets from the last 30 days for the user
        # TODO: since tickets fetched above are already fetched from DB,
        #  we can reuse that data instead of querying db again
        recent_tickets = Ticket.objects.filter(
            Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
            created_for=user,
            created_at__gte=thirty_days_ago
        )

        if not recent_tickets.exists():
            continue  # Skip if no tickets in the last 30 days

        # Make existing recommendations inactive
        TicketRecommendation.objects.filter(
            created_for=user,
            start_location_code__isnull=False,
        ).delete()

        # Count occurrences of source-destination pairs
        # TODO: add coordinates of the src and dst
        src_dst_counter = Counter(
            (
                ticket.start_location_code,
                ticket.end_location_code,
                ticket.start_location_name,
                ticket.end_location_name,
                ticket.transit_option,
            ) for ticket in recent_tickets
        )

        total_trips = sum(src_dst_counter.values())

        # Create recommendations based on the most frequent trips
        print("Creating recommendations for user {}".format(user.id))
        for (start_location_code, end_location_code, start_location_name,
             end_location_name, transit_option), count in src_dst_counter.most_common(4):
            print(
                "Creating recommendation for user {} with start_location_code {} and end_location_code {}".format(
                    user.id, start_location_code, end_location_code
                ))
            weight = round(count / total_trips, 2)
            TicketRecommendation.objects.create(
                created_for=user,
                start_location_code=start_location_code,
                end_location_code=end_location_code,
                start_location_name=start_location_name,
                end_location_name=end_location_name,
                transit_option=transit_option,
                weight=weight,
            )

            print("Recommendations generated")


@shared_task(name="create_most_common_destination_recommendations_for_user")
def create_most_common_destination_recommendations_for_user():
    print("Generating Most Common Destination Recommendations")

    # Replace 'accounts', 'tickets', and model names with your actual app and model names
    MyUser = apps.get_model("accounts", "MyUser")
    TicketRecommendation = apps.get_model("tickets", "TicketRecommendation")
    Ticket = apps.get_model("tickets", "Ticket")

    thirty_days_ago = timezone.now() - datetime.timedelta(days=30)

    all_tickets_recently = Ticket.objects.filter(
        Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
        created_at__gte=thirty_days_ago,
        created_for__isnull=False
    )

    # Get distinct user IDs who created these tickets
    distinct_user_ids = all_tickets_recently.values_list('created_for', flat=True).distinct()

    for user_id in distinct_user_ids:
        user = MyUser.objects.get(id=user_id)
        print(f"Creating destination recommendations for user {user.id}")

        latest_destination_recommendation = TicketRecommendation.objects.filter(
            created_for=user, start_location_code=None
        ).order_by('-created_at').first()

        if latest_destination_recommendation:
            print(f"Previous destination recommendations found for user {user.id}")
            new_tickets_since_last_recommendation = Ticket.objects.filter(
                Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
                created_for=user,
                created_at__gte=latest_destination_recommendation.created_at
            ).exists()

            if not new_tickets_since_last_recommendation:
                print(f"No new tickets since last destination recommendation for user {user.id}")
                continue

        # Fetch tickets from the last 30 days for the user
        # TODO: since tickets fetched above are already fetched from DB,
        #  we can reuse that data instead of querying db again
        recent_tickets = Ticket.objects.filter(
            Q(status=TicketStatus.EXPIRED) | Q(status=TicketStatus.CONFIRMED),
            created_for=user,
            created_at__gte=thirty_days_ago
        )

        if not recent_tickets.exists():
            continue  # Skip if no tickets in the last 30 days

        # Make existing destination-only recommendations inactive
        TicketRecommendation.objects.filter(created_for=user, start_location_code=None).delete()

        # Count occurrences of each destination for this user
        # TODO: add coordinates of the dst
        destination_counter = Counter(
            (
                ticket.end_location_name,
                ticket.end_location_code,
                ticket.transit_option
            ) for ticket in recent_tickets
        )

        total_tickets = recent_tickets.count()

        # Create recommendations based on the most frequent destinations
        for (end_location_name, end_location_code, transit_option), count in destination_counter.most_common():
            print(
                "Creating destination recommendation for user {} with end_location_code {}".format(
                    user.id, end_location_code,
                ))
            weight = round(count / total_tickets, 2)
            TicketRecommendation.objects.create(
                created_for=user,
                end_location_name=end_location_name,
                end_location_code=end_location_code,
                transit_option=transit_option,
                weight=weight,
            )

        print(f"Destination recommendations generated for user {user.id}")


@shared_task(name="create_ticket_summary")
def create_ticket_summary(start_datetime, end_datetime):
    # initiate refunds whose original transactions were created in above range
    logging.info("create_ticket_summary between {} and {}".format(start_datetime, end_datetime))

    # Condition 1: Transaction status is FAILED, gateway transaction status is SUCCESS
    Ticket = apps.get_model("tickets", "Ticket")

    # Get all confirmed/expired tickets in the given time period
    # TODO: tickets not coming
    valid_tickets = Ticket.objects.filter(
        Q(status=TicketStatus.CONFIRMED) | Q(status=TicketStatus.EXPIRED),
        created_at__range=(start_datetime, end_datetime)
    )
    # created_at	start_location_name	end_location_name	pnr	passenger_count	amount	transaction
    columns_to_select = [
        'created_at',
        'start_location_name',
        'end_location_name',
        'pnr',
        'passenger_count',
        'amount',
        'transaction',
    ]
    valid_tickets = valid_tickets.values(*columns_to_select)

    # return csv with columns
    return valid_tickets, columns_to_select


def create_ticket_summary_day_wise_aggregated(start_datetime, end_datetime):
    logging.info("create_ticket_summary_day_wise_aggregated between {} and {}".format(start_datetime, end_datetime))

    Ticket = apps.get_model("tickets", "Ticket")

    # Aggregate the tickets by date, summing up passenger_count and amount
    aggregated_tickets = Ticket.objects.filter(
        (Q(status=TicketStatus.CONFIRMED) | Q(status=TicketStatus.EXPIRED)),
        created_at__range=(start_datetime, end_datetime)
    ).annotate(
        date=TruncDate('created_at')
    ).values(
        'date'
    ).annotate(
        total_passenger_count=Sum('passenger_count'),
        total_settled_amount=Sum('amount')
    ).order_by('date')

    # Define the columns to return - in this case, we'll generate them dynamically
    # since the aggregated query alters the structure of our returned data.
    columns_to_return = ['date', 'total_passenger_count', 'total_settled_amount']

    return aggregated_tickets, columns_to_return

@shared_task(name="create_refund_summary")
def create_refund_summary(start_datetime, end_datetime):
    # initiate refunds whose original transactions were created in above range
    logging.info("create_refund_summary between {} and {}".format(start_datetime, end_datetime))

    # Condition 1: Transaction status is FAILED, gateway transaction status is SUCCESS
    Transaction = apps.get_model("payments", "Transaction")

    # Get all confirmed/expired tickets in the given time period
    refund_transactions = Transaction.objects.filter(
        transaction_type=TransactionType.CREDIT,
        created_at__range=(start_datetime, end_datetime)
    )
    # created_at	original_transaction	amount	gateway_order_id	gateway_transaction_id
    columns_to_select = [
        'created_at',
        'original_transaction',
        'amount',
        'gateway_order_id',
        'gateway_transaction_id',
    ]
    refund_transactions = refund_transactions.values(*columns_to_select)

    # return csv with columns
    return refund_transactions, columns_to_select


def create_refund_summary_day_wise_aggregated(start_datetime, end_datetime):
    logging.info("create_refund_summary_day_wise_aggregated between {} and {}".format(start_datetime, end_datetime))

    Transaction = apps.get_model("payments", "Transaction")

    # Aggregate refund transactions by date, summing up the amount
    aggregated_refunds = Transaction.objects.filter(
        transaction_type=TransactionType.CREDIT,
        created_at__range=(start_datetime, end_datetime)
    ).annotate(
        date=TruncDate('created_at')  # Extract date from datetime for grouping
    ).values(
        'date'  # Group by date
    ).annotate(
        total_amount=Sum(Abs(F('amount'))),  # Sum amount for each group
        refund_count=Count('pk')  # Count refunds for each group
    ).order_by('date')

    # Define columns to return. Here, we're interested in the date, total refunded amount,
    # and count of refunds processed on each date.
    columns_to_return = ['date', 'total_amount', 'refund_count']

    return aggregated_refunds, columns_to_return

@shared_task(name="create_ticket_and_refund_summary_prev_day")
def create_ticket_and_refund_summary_prev_day():
    logging.info("Creating Ticket & Refund Summary for Previous Day")
    start_datetime, end_datetime = TimePeriod.get_previous_day()
    # get date as YYYY-MM-DD format
    start_date = start_datetime.strftime("%Y-%m-%d")
    tickets, tickets_headers = create_ticket_summary(start_datetime, end_datetime)
    refunds, refunds_headers = create_refund_summary(start_datetime, end_datetime)

    # Convert the data to CSV format
    ticket_csv = convert_objects_to_csv(tickets, tickets_headers)
    refund_csv = convert_objects_to_csv(refunds, refunds_headers)

    # Prepare attachments
    attachments = {}

    filename = f'ticket_summary_{start_date}.csv'
    attachment = MIMEText(ticket_csv, 'plain')
    attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    attachments[filename] = attachment

    filename = f'refund_summary_{start_date}.csv'
    attachment = MIMEText(refund_csv, 'plain')
    attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
    attachments[filename] = attachment

    try:
        system_parameter_object = dmrc_ticketing_api_SystemParameters.objects.get()
        receiver_address_to, receiver_address_cc = system_parameter_object.get_report_to(), system_parameter_object.get_report_cc()
        subject = f'DMRC Ticketing Summary for One Delhi App - {start_date}'
        body = f'Attached are the ticket and refund summaries for the {start_date}'

        smtp_utils = SMTPUtils()
        smtp_utils.send_email_with_attachments(receiver_address_to=receiver_address_to,
                                               subject=subject,
                                               body=body,
                                               attachments=attachments,
                                               receiver_address_cc=receiver_address_cc
                                               )
    except dmrc_ticketing_api_SystemParameters.DoesNotExist:
        logging.error('SystemParameters matching query does not exist.')
        return {"message": "SystemParameters matching query does not exist."}


# @shared_task(name="post_ondc_stops_search")
# def post_ondc_stops_search():
#     ONDC_SEARCH_URL = os.environ.get("ONDC_SEARCH_URL")
#     current_utc_datetime = datetime.now(timezone.utc)
#     formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
#     search_payload = {
#         "context": {
#             "location": location,
#             "domain": "ONDC:TRV11",
#             "timestamp": formatted_current_utc,
#             "bap_id": os.environ.get("BAP_ID"),
#             "transaction_id": str(uuid.uuid4()),
#             "message_id": str(uuid.uuid4()),
#             "version": "2.0.0",
#             "action": "search",
#             "bap_uri": os.environ.get("BAP_URI"),
#             "ttl": "PT30S"
#         },
#         "message": {
#             "intent": {
#                 "fulfillment": {"vehicle": {"category": "BUS"}},
#                 "payment": {
#                     "tags": [
#                       {
#                         "descriptor": {
#                           "code": "BUYER_FINDER_FEES"
#                         },
#                         "display": False,
#                         "list": [
#                           {
#                             "descriptor": {
#                               "code": "BUYER_FINDER_FEES_PERCENTAGE"
#                             },
#                             "value": "1"
#                           },
#                           {
#                             "descriptor": {
#                               "code": "BUYER_FINDER_FEES_TYPE"
#                             },
#                             "value": "percent-annualized"
#                           }
#                         ]
#                       },
#                       {
#                         "descriptor": {
#                           "code": "SETTLEMENT_TERMS"
#                         },
#                         "display": False,
#                         "list": [
#                           {
#                             "descriptor": {
#                               "code": "DELAY_INTEREST"
#                             },
#                             "value": "2.5"
#                           },
#                           {
#                             "descriptor": {
#                               "code": "STATIC_TERMS"
#                             },
#                             "value": "https://api.example-bap.com/booking/terms"
#                           }
#                         ]
#                       }
#                     ]
#                 }
#             }
#         }
#     }
#     request_body_raw_text = json.dumps(search_payload)
#     signature = create_authorisation_header(request_body=request_body_raw_text, created=None, expires=None)
#     signature = signature[1:-1]
#     verified = verify_authorisation_header(f'{signature}',request_body_str=request_body_raw_text,public_key=os.environ.get("PUBLIC_KEY"))
#
#     headers = {
#         'Authorization': signature,
#         'Content-Type': 'application/json'
#     }
#     post_result = requests.post(ONDC_SEARCH_URL, headers=headers, json=search_payload)
#
#     return post_result.json()
#
#
# @shared_task(name="fetch_and_store_bus_fleet_data")
# def fetch_and_store_bus_fleet_data():
#     FLEET_DATA_URL = os.environ.get("FLEET_DATA_URL")
#     fleet_data_response = requests.get(FLEET_DATA_URL)
#
#     if fleet_data_response.json():
#         fleet_data_cache_key = "fleet_data"
#
#         cache.set(fleet_data_cache_key, fleet_data_response.json(), timeout=60 * 60 * 24)
#
#         cached_fleet_data = cache.get(fleet_data_cache_key)
#
#         logging.info(f"Fleet data cached==========")
#         return {"message": "Fleet data fetched and cached successfully."}
#     else:
#         return {"message": "Fleet data fetching failed."}
#
#
# @shared_task(name="check_for_stops_file")
# def check_for_stops_file():
#     file_path = 'data/static_stops_data/routes_and_stops.7z'
#     logging.info(f"Checking for the file: {file_path}")
#     if not os.path.exists(file_path):
#         logging.info(f"File not found: {file_path}. Triggering post_ondc_stops_search task.")
#         post_ondc_stops_search.apply_async()
#     else:
#         file_size = os.path.getsize(file_path)
#         logging.info(f"File exists: {file_path}. Size of the file: {file_size} bytes.")
#
#         if file_size > 1 * 1024 * 1024:  # 1MB in bytes
#             logging.info(f"File size exceeds 1MB. Triggering post_ondc_stops_search task.")
#             post_ondc_stops_search.apply_async()
#         else:
#             logging.info(f"File size is within the limit.")
#
#
# @shared_task(name="check_fleet_data_cache")
# def check_fleet_data_cache():
#     fleet_data_cache_key = "fleet_data"
#     logging.info(f"Checking for cached data with key: {fleet_data_cache_key}")
#     cached_fleet_data = cache.get(fleet_data_cache_key)
#     if cached_fleet_data is None:
#         logging.info(f"Cache miss for key: {fleet_data_cache_key}. Triggering fetch_and_store_bus_fleet_data task.")
#         fetch_and_store_bus_fleet_data.apply_async()
#     else:
#         logging.info(f"Cache exist for key: {fleet_data_cache_key}")
