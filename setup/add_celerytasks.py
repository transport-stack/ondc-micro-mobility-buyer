import logging

from modules.constants import SchedulesEnum

logger = logging.getLogger(__name__)

from django_celery_beat.models import PeriodicTask, CrontabSchedule
from pytz import timezone


def _add_crontab(schedule):
    """
    schedule={
            'minute': '*/1',
            'hour': '*',
            'day_of_week': '*',
            'day_of_month': '*',
            'month_of_year': '*',
            'timezone': 'Asia/Kolkata'
        }
    """
    # Create a new crontab schedule
    if not "timezone" in schedule:
        schedule["timezone"] = "Asia/Kolkata"

    crontab, created = CrontabSchedule.objects.get_or_create(
        minute=schedule["minute"],
        hour=schedule["hour"],
        day_of_week=schedule["day_of_week"],
        day_of_month=schedule["day_of_month"],
        month_of_year=schedule["month_of_year"],
        timezone=timezone(schedule["timezone"]),
    )


def _add_celery_task(name, task, schedule, args=None, kwargs=None):
    try:
        # Check if the task already exists in the database

        task_exists = PeriodicTask.objects.filter(name=name).exists()
        if task_exists:
            print(f"Task '{name}' already exists. Ignoring...")
            return

        # Create a new crontab schedule
        crontab = CrontabSchedule.objects.get(
            minute=schedule["minute"],
            hour=schedule["hour"],
            day_of_week=schedule["day_of_week"],
            day_of_month=schedule["day_of_month"],
            month_of_year=schedule["month_of_year"],
        )

        # Create a new periodic task
        periodic_task = PeriodicTask.objects.create(
            name=name,
            task=task,
            args=args or [],
            kwargs=kwargs or {},
            crontab=crontab,
        )

        print(f"Task '{name}' added successfully.")
    except Exception as e:
        print(f"Error adding task '{name}': {str(e)}")


def add_crontabs():
    logging.debug("Adding crontabs...")

    for schedule_name, schedule in vars(SchedulesEnum).items():
        # We only want the attributes that end with "_SCHEDULE_DICT"
        if schedule_name.endswith("_SCHEDULE_DICT"):
            _add_crontab(schedule=schedule)


def add_celery_tasks():
    add_crontabs()

    PeriodicTask.objects.all().delete()

    # Add test_one_min_task
    # _add_celery_task(
    #     name="test_one_min_task",
    #     task="test_one_min_task",
    #     schedule=SchedulesEnum.EVERY_ONE_MINUTE_SCHEDULE_DICT,  # Run every 60 seconds (1 minute)
    # )

    # Add check_transaction_status for all pending transactions
    # _add_celery_task(
    #     name="check_transaction_status",
    #     task="check_transaction_status",
    #     schedule=SchedulesEnum.EVERY_HOUR_SCHEDULE_DICT,
    # )

    # Add check_transaction_status
    # _add_celery_task(
    #     name="check_transaction_status_today",
    #     task="check_transaction_status_today",
    #     schedule=SchedulesEnum.EVERY_ONE_MINUTE_SCHEDULE_DICT,
    # )

    # Add check_transaction_status
    # _add_celery_task(
    #     name="check_transaction_status_older",
    #     task="check_transaction_status_older",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_00_05_SCHEDULE_DICT,
    # )

    # _add_celery_task(
    #     name="ticket_check_payment_status",
    #     task="ticket_check_payment_status",
    #     schedule=SchedulesEnum.EVERY_ONE_MINUTE_SCHEDULE_DICT,
    # )

    # _add_celery_task(
    #     name="check_payment_status_last_7_days",
    #     task="check_payment_status_last_7_days",
    #     schedule=SchedulesEnum.EVERY_FIFTEEN_MINUTES_SCHEDULE_DICT,
    # )

    # _add_celery_task(
    #     name="check_payment_status_all",
    #     task="check_payment_status_all",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_02_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="expire_previous_day_journeys",
    #     task="expire_previous_day_journeys",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="expire_previous_day_confirmed_tickets",
    #     task="expire_previous_day_confirmed_tickets",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )

    # _add_celery_task(
    #     name="cancel_previous_day_pending_tickets",
    #     task="cancel_previous_day_pending_tickets",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    # ONDC Search all stops of all routes
    # _add_celery_task(
    #     name="post_ondc_stops_search",
    #     task="post_ondc_stops_search",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    # # Fetch Bus fleet data
    # _add_celery_task(
    #     name="fetch_and_store_bus_fleet_data",
    #     task="fetch_and_store_bus_fleet_data",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="check_for_stops_file",
    #     task="check_for_stops_file",
    #     schedule=SchedulesEnum.EVERY_THREE_HOUR_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="check_fleet_data_cache",
    #     task="check_fleet_data_cache",
    #     schedule=SchedulesEnum.EVERY_THREE_HOUR_SCHEDULE_DICT,  # Adjust the schedule as needed
    # )

    _add_celery_task(
        name="cancel_pending_tickets_post_timeout",
        task="cancel_pending_tickets_post_timeout",
        schedule=SchedulesEnum.EVERY_ONE_MINUTE_SCHEDULE_DICT,
    )

    # refunds
    # _add_celery_task(
    #     name="create_refunds_for_current_day",
    #     task="create_refunds_for_current_day",
    #     schedule=SchedulesEnum.EVERY_DAY_AT_23_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="create_refunds_for_previous_day",
    #     task="create_refunds_for_previous_day",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_00_05_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="create_refunds_for_previous_7_days",
    #     task="create_refunds_for_previous_7_days",
    #     schedule=SchedulesEnum.EVERY_MONDAY_AT_05_AM_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="initiate_refunds_for_current_day",
    #     task="initiate_refunds_for_current_day",
    #     schedule=SchedulesEnum.EVERY_DAY_AT_23_30_SCHEDULE_DICT,
    # )

    # since payments have flown th
    # _add_celery_task(
    #     name="initiate_refunds_for_previous_day",
    #     task="initiate_refunds_for_previous_day",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )

    # _add_celery_task(
    #     name="initiate_refunds_for_previous_7_days",
    #     task="initiate_refunds_for_previous_7_days",
    #     schedule=SchedulesEnum.EVERY_DAY_AT_23_15_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="generate_recommendations",
    #     task="generate_recommendations",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="create_most_common_destination_recommendations_for_user",
    #     task="create_most_common_destination_recommendations_for_user",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_02_00_SCHEDULE_DICT,
    # )
    #
    # _add_celery_task(
    #     name="create_ticket_and_refund_summary_prev_day",
    #     task="create_ticket_and_refund_summary_prev_day",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_01_00_SCHEDULE_DICT,
    # )
    # only if required
    # _add_celery_task(
    #     name="delete_older_ticket_updates",
    #     task="delete_older_ticket_updates",
    #     schedule=SchedulesEnum.EVERY_MORNING_AT_02_00_SCHEDULE_DICT,  # Run every 1800 seconds (30 minutes)
    # )
