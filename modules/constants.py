def round_school(x):
    i, f = divmod(x, 1)
    return int(i + ((f >= 0.5) if (x > 0) else (f > 0.5)))


GENERAL_TICKET_TYPE_ID = 1
PINK_TICKET_TYPE_ID = 2
PINK_TICKET_BASE_FARE = 10.0

# transit provider enums
RAPIDO_ENUM = "RAPIDO"
NAMMAYATRI_ENUM = "NAMMAYATRI"
INTEGRATED_TICKETING_ENUM = "INTEGRATED_TICKETING"
UBER_ENUM = "UBER"
DTC_ENUM = "DTC"
DIMTS_ENUM = "DIMTS"
DMRC_ENUM = "DMRC"
ONDC_ENUM = "ONDC"


class ResponseMessageEnum:
    SUCCESS = str("Success")
    FAILED = str("Failed")


class SchedulesEnum:
    EVERY_ONE_MINUTE_SCHEDULE_DICT = {
        "minute": "*/1",
        "hour": "*",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_FIFTEEN_MINUTES_SCHEDULE_DICT = {
        "minute": "*/15",
        "hour": "*",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_HOUR_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "*/1",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }
    EVERY_THREE_HOUR_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "*/3",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_DAY_AT_6_30_AM_SCHEDULE_DICT = {
        "minute": "30",
        "hour": "6",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_DAY_AT_23_00_SCHEDULE_DICT = {
        "minute": "30",
        "hour": "23",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_DAY_AT_23_30_SCHEDULE_DICT = {
        "minute": "30",
        "hour": "23",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MONDAY_AT_05_AM_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "12",
        "day_of_week": "1",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MONDAY_AT_12_PM_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "12",
        "day_of_week": "1",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_00_05_SCHEDULE_DICT = {
        "minute": "5",
        "hour": "0",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_WEEK_AT_03_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "3",
        "day_of_week": "1",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_00_10_SCHEDULE_DICT = {
        "minute": "10",
        "hour": "0",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_00_15_SCHEDULE_DICT = {
        "minute": "15",
        "hour": "0",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    # EVERY_DAY_AT_23_15_SCHEDULE_DICT
    EVERY_DAY_AT_23_15_SCHEDULE_DICT = {
        "minute": "15",
        "hour": "23",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_01_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "1",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }
    TEST_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "1",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_01_15_SCHEDULE_DICT = {
        "minute": "15",
        "hour": "1",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_02_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "2",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_03_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "3",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_MORNING_AT_04_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "4",
        "day_of_week": "*",
        "day_of_month": "*",
        "month_of_year": "*",
    }

    EVERY_FIRST_OF_MONTH_AT_03_00_SCHEDULE_DICT = {
        "minute": "0",
        "hour": "3",
        "day_of_week": "*",
        "day_of_month": "1",
        "month_of_year": "*",
    }


from enum import Enum


class RideStatus(Enum):
    PENDING = {
        "title": "Looking for ride",
        "message": "Looking for a ride around you."
    }

    ACCEPTED = {
        "title": "Ride accepted",
        "message_template": "{name} has accepted your ride and is en route to your location",
        "current_state": "current_state"
    }

    ARRIVED = {
        "title": "Ride arrived",
        "message_template": "{name} has arrived at your pickup location.",
        "current_state": "current_state",
        "detail": "detailResultItem"
    }

    STARTED = {
        "title": "Ride started",
        "message": "Your ride has started. Enjoy your ride.",
        "current_state": "current_state",
        "detail": "detailResultItem"
    }

    DROPPED = {
        "title": "Ride completed",
        "message": "Your ride has completed. Please make payment for your previous journey for using it again."
    }
