import datetime
import time

import pytz
from pytz import timezone

INDIAN_TZ = "Asia/Kolkata"
IST = pytz.timezone("Asia/Kolkata")


def get_current_time_obj_in_IST():
    tm = datetime.datetime.now(IST)
    return tm


def get_current_datetime_tz_aware():
    tz = pytz.timezone(INDIAN_TZ)
    return datetime.datetime.now(tz)


def convert_datetime_obj_to_tz_aware(_unaware_datetime_obj):
    return _unaware_datetime_obj.replace(tzinfo=IST)


def get_current_datetime():
    return datetime.datetime.now()


def get_current_time_as_str():
    return time.strftime("%H:%M:%S", time.localtime())


def get_current_time_as_str_hhmmss():
    return time.strftime("%H%M%S", time.localtime())


def get_current_datetime_as_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# '%H:%M:%S' to datetime
def get_time_from_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%H:%M:%S")


# '%Y-%m-%d %H:%M:%S' to datetime with tzinfo as Asia/Kolkata
def get_ist_datetime_from_naive_dt_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").astimezone(
        timezone("Asia/Kolkata")
    )


def get_ist_datetime_obj_from_naive_dt_obj(dt_obj):
    return dt_obj.astimezone(timezone("Asia/Kolkata"))


# '%Y-%m-%d %H:%M:%S' to datetime
def get_datetime_from_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def get_utc_timestamp_given_datetime(datum):
    """
    :param date: local datetime
    :return: returns utc timestamp corresponding to above
    """
    tz_ist = pytz.timezone("Asia/Kolkata")
    aware_d = tz_ist.localize(datum, is_dst=False)
    utc_d = aware_d.astimezone(pytz.utc)
    return utc_d.timestamp()


def get_utc_to_ist_datetime(datetime_obj):
    _ist_datetime_obj = datetime_obj.astimezone(timezone("Asia/Kolkata"))
    _ist_datetime_obj_wo_t = datetime.datetime.strftime(
        _ist_datetime_obj, "%Y-%m-%dT%H:%M:%S"
    ).replace("T", " ")

    return _ist_datetime_obj_wo_t


def get_str_time_from_date_obj(datetime_obj):
    if not datetime_obj:
        return "NA:NA"
    return datetime.datetime.strftime(datetime_obj, "%I:%M %p")


def get_str_time_from_time_obj(time_obj):
    if not time_obj:
        return "NA:NA"
    return datetime.time.strftime(time_obj, "%I:%M %p")


def get_datetime_as_str_ist(datetime_obj):
    if not datetime_obj:
        return
    _ist_datetime_obj = datetime_obj.astimezone(timezone("Asia/Kolkata"))
    return datetime.datetime.strftime(_ist_datetime_obj, "%d/%m/%y %I:%M %p")


# x=hour of next day


def get_next_day_x_time(x=3):
    today_ist = datetime.datetime.now(IST)
    tomorrow_ist = today_ist + datetime.timedelta(days=1)
    tomorrow_ist_3am = tomorrow_ist.replace(hour=x, minute=0, second=0)
    tomorrow_ist_3am_wo_T = datetime.datetime.strftime(
        tomorrow_ist_3am, "%Y-%m-%dT%H:%M:%S"
    ).replace("T", " ")

    # print("IST in Default Format wo T: ", tomorrow_ist_3am_wo_T)
    return tomorrow_ist_3am


def get_current_time_in_milli():
    return round(time.time() * 1000)


def get_ist_time_given_epoch_time(epoch_time):
    dt = datetime.datetime.fromtimestamp(epoch_time, IST)
    return dt


if __name__ == "__main__":
    print(get_ist_time_given_epoch_time(1618420912065).isoformat())
    # print(get_next_day_x_time(3))
    # print(get_current_time_in_milli())
    # dt = get_datetime_from_str("2021-06-13 23:59:59")
    # pt = get_ist_datetime_from_naive_dt_str("2021-06-13 11:59:59")
    # validTill = datetime.datetime(pt.year, pt.month, pt.day, 23, 59, 59, tzinfo=IST)
    #
    # validTill2 = get_utc_to_ist_datetime(validTill)

    # epoch_time = int(1636987551121) / 1000.0
    # dt = get_ist_time_given_epoch_time(epoch_time)
    # print(dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
    # print(get_current_time_obj_in_IST().date())
