from datetime import datetime, timedelta


class TimePeriod:
    @staticmethod
    def get_previous_n_days(n, complete_days=True):
        today = datetime.now().date()
        if complete_days:
            # End datetime is the start of today (midnight)
            end = datetime.combine(today, datetime.min.time()) - timedelta(seconds=1)
        else:
            # End datetime is the current time
            end = datetime.now()

        # Start datetime is N days before the end datetime
        start = end - timedelta(days=n)
        return start, end

    @staticmethod
    def get_previous_day():
        today = datetime.now().date()
        start = datetime.combine(today - timedelta(days=1), datetime.min.time())
        end = datetime.combine(today, datetime.min.time()) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_previous_week():
        today = datetime.now().date()
        start = datetime.combine(today - timedelta(days=today.weekday() + 7), datetime.min.time())
        end = datetime.combine(today - timedelta(days=today.weekday() + 1), datetime.min.time())
        return start, end

    @staticmethod
    def get_previous_month():
        today = datetime.now().date()
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start = datetime.combine(last_day_last_month.replace(day=1), datetime.min.time())
        end = datetime.combine(last_day_last_month + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_previous_year():
        today = datetime.now().date()
        start = datetime(today.year - 1, 1, 1)
        end = datetime(today.year, 1, 1) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_previous_hour(current_time=None, complete_hour=True):
        if not current_time:
            current_time = datetime.now()
        if complete_hour:
            start = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            end = start + timedelta(hours=1) - timedelta(seconds=1)
        else:
            start = current_time - timedelta(hours=1)
            end = current_time
        return start, end

    @staticmethod
    def get_current_month():
        today = datetime.now().date()
        start = datetime.combine(today.replace(day=1), datetime.min.time())
        end = datetime.combine(start.replace(month=start.month + 1), datetime.min.time()) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_current_day():
        today = datetime.now().date()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_current_hour():
        current_time = datetime.now()
        start = current_time.replace(minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1) - timedelta(seconds=1)
        return start, end

    @staticmethod
    def get_current_year():
        today = datetime.now().date()
        start = datetime(today.year, 1, 1)
        end = datetime(today.year + 1, 1, 1) - timedelta(seconds=1)
        return start, end


if __name__ == "__main__":
    # Get and print previous day
    start, end = TimePeriod.get_previous_day()
    print("Previous Day:", start, "to", end)

    # Get and print previous week
    start, end = TimePeriod.get_previous_week()
    print("Previous Week:", start, "to", end)

    # Get and print previous month
    start, end = TimePeriod.get_previous_month()
    print("Previous Month:", start, "to", end)

    # Get and print previous year
    start, end = TimePeriod.get_previous_year()
    print("Previous Year:", start, "to", end)

    # Get and print previous hour (last complete hour)
    start, end = TimePeriod.get_previous_hour(complete_hour=True)
    print("Previous Complete Hour:", start, "to", end)

    # Get and print previous hour (hour before current time)
    start, end = TimePeriod.get_previous_hour(complete_hour=False)
    print("Previous Hour from Now:", start, "to", end)

    # Get and print previous 7 days
    start, end = TimePeriod.get_previous_n_days(7)
    print("Previous 7 Days:", start, "to", end)

    # Get this month
    start, end = TimePeriod.get_current_month()
    print("Current Month:", start, "to", end)

    # Get current hour
    start, end = TimePeriod.get_current_hour()
    print("Current Hour:", start, "to", end)

