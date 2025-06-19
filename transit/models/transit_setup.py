import datetime

from django.db import models
from django.utils import timezone

from modules.models import ActiveMixin, DateTimeMixin, TransitModeMixin
from modules.utils import alphanumeric
from transit.exceptions import ServiceNotAvailableException, CalendarDateException


class TransitProvider(DateTimeMixin, ActiveMixin):
    id = models.AutoField(primary_key=True)

    # accept only alphanumeric characters and spaces
    name = models.CharField(
        max_length=255,
        help_text="Name of the transit agency or service, like Uber, MTA, Rapido, "
                  "American Airlines etc. Accepts only alphanumeric characters and spaces",
        validators=[alphanumeric],
    )
    # add website of the transit provider
    website = models.URLField(blank=True, null=True)
    # add logo url of the transit provider
    logo_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        # plural name for admin
        verbose_name_plural = "Transit Providers"


class TransitOption(TransitModeMixin, ActiveMixin):
    provider = models.ForeignKey(
        TransitProvider, related_name="transit_options", on_delete=models.CASCADE
    )

    def is_active_at_datetime(self, target_datetime: datetime = None) -> bool:
        if target_datetime is None:
            target_datetime = timezone.localtime()

        # Check for typical service availability
        service_calendar = self.service_calendar
        calendar_exception_bool = False
        service_calendar_bool = False
        is_inactive_reason = "Service Active"

        if service_calendar:
            if not service_calendar.is_typically_active(target_datetime):
                is_inactive_reason = "Outside digital ticketing hour. Resumes at 6AM tomorrow."
            else:
                service_calendar_bool = True

        # Check for exceptions
        calendar_exception = CalendarDate.objects.filter(
            active=True,
            start_datetime__lte=target_datetime,
            end_datetime__gte=target_datetime,
            exception_type__in=[1, 2, 3]
        ).first()

        if calendar_exception:
            if calendar_exception.exception_type in [1, 3]:
                calendar_exception_bool = True
            elif calendar_exception.exception_type == 2 and service_calendar_bool:
                is_inactive_reason = calendar_exception.description
                if is_inactive_reason is None or is_inactive_reason == "":
                    is_inactive_reason = "The service is not available due to a planned exception on {}.".format(
                        target_datetime.strftime("%Y-%m-%d"))
                raise ServiceNotAvailableException(is_inactive_reason)

        if calendar_exception_bool or service_calendar_bool:
            return True
        else:
            raise ServiceNotAvailableException(is_inactive_reason)

    class Meta:
        unique_together = ("provider", "transit_mode")
        verbose_name_plural = "Transit Options"

    def __str__(self):
        return f"{self.provider} - {self.get_transit_mode_display()}"

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if not ServiceCalendar.objects.filter(transit_option=self).exists():
            ServiceCalendar.objects.create(
                transit_option=self
            )


class ServiceCalendar(models.Model):
    transit_option = models.OneToOneField(
        TransitOption,
        on_delete=models.CASCADE,
        related_name='service_calendar'
    )

    monday = models.BooleanField(default=True, help_text="This service enabled on Monday")
    tuesday = models.BooleanField(default=True, help_text="This service enabled on Tuesday")
    wednesday = models.BooleanField(default=True, help_text="This service enabled on Wednesday")
    thursday = models.BooleanField(default=True, help_text="This service enabled on Thursday")
    friday = models.BooleanField(default=True, help_text="This service enabled on Friday")
    saturday = models.BooleanField(default=True, help_text="This service enabled on Saturday")
    sunday = models.BooleanField(default=True, help_text="This service enabled on Sunday")

    monday_start_time = models.TimeField(default=datetime.time(0, 0),
                                         help_text="Time when this service starts on Monday morning")
    monday_end_time = models.TimeField(default=datetime.time(23, 59),
                                       help_text="Time when this service ends on Monday night")
    tuesday_start_time = models.TimeField(default=datetime.time(0, 0),
                                          help_text="Time when this service starts on Tuesday morning")
    tuesday_end_time = models.TimeField(default=datetime.time(23, 59),
                                        help_text="Time when this service ends on Tuesday night")
    wednesday_start_time = models.TimeField(default=datetime.time(0, 0),
                                            help_text="Time when this service starts on Wednesday morning")
    wednesday_end_time = models.TimeField(default=datetime.time(23, 59),
                                          help_text="Time when this service ends on Wednesday night")
    thursday_start_time = models.TimeField(default=datetime.time(0, 0),
                                           help_text="Time when this service starts on Thursday morning")
    thursday_end_time = models.TimeField(default=datetime.time(23, 59),
                                         help_text="Time when this service ends on Thursday night")
    friday_start_time = models.TimeField(default=datetime.time(0, 0),
                                         help_text="Time when this service starts on Friday morning")
    friday_end_time = models.TimeField(default=datetime.time(23, 59),
                                       help_text="Time when this service ends on Friday night")
    saturday_start_time = models.TimeField(default=datetime.time(0, 0),
                                           help_text="Time when this service starts on Saturday morning")
    saturday_end_time = models.TimeField(default=datetime.time(23, 59),
                                         help_text="Time when this service ends on Saturday night")
    sunday_start_time = models.TimeField(default=datetime.time(0, 0),
                                         help_text="Time when this service starts on Sunday morning")
    sunday_end_time = models.TimeField(default=datetime.time(23, 59),
                                       help_text="Time when this service ends on Sunday night")

    start_date = models.DateField(default=datetime.date(2000, 1, 1), db_index=True,
                                  help_text="Start date of this service")
    end_date = models.DateField(default=datetime.date(2075, 12, 31), db_index=True,
                                help_text="End date of this service")

    def is_typically_active(self, check_datetime):
        # Make sure the check date is within the service's overall period
        if not (self.start_date <= check_datetime.date() <= self.end_date):
            return False

        # Mapping of weekday number to corresponding fields in ServiceCalendar
        weekday_field_map = {
            0: (self.monday, self.monday_start_time, self.monday_end_time),
            1: (self.tuesday, self.tuesday_start_time, self.tuesday_end_time),
            2: (self.wednesday, self.wednesday_start_time, self.wednesday_end_time),
            3: (self.thursday, self.thursday_start_time, self.thursday_end_time),
            4: (self.friday, self.friday_start_time, self.friday_end_time),
            5: (self.saturday, self.saturday_start_time, self.saturday_end_time),
            6: (self.sunday, self.sunday_start_time, self.sunday_end_time),
        }

        # Get the weekday (0=Monday, 1=Tuesday, ..., 6=Sunday)
        weekday = check_datetime.weekday()

        # Check if the service is typically active on this day of the week
        is_active_today, start_time, end_time = weekday_field_map.get(weekday)

        # Checking if the current time falls within the active hours of the service
        check_time = check_datetime.time()
        if is_active_today and start_time <= check_time <= end_time:
            return True

        return False

    class Meta:
        verbose_name_plural = "Service Calendars"

    def __str__(self):
        return f"{self.transit_option} Service Calendar"


class CalendarDate(DateTimeMixin, ActiveMixin):
    start_datetime = models.DateTimeField(db_index=True, null=True, blank=True,
                                          help_text="DateTime when the service exception starts")
    end_datetime = models.DateTimeField(db_index=True, null=True, blank=True,
                                        help_text="DateTime when the service exception ends")
    EXCEPTION_TYPE_CHOICES = [
        (1, "Service Added"),
        (2, "Service Removed"),
        (3, "Service Updated")
    ]
    exception_type = models.IntegerField(choices=EXCEPTION_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Calendar Dates"

    def __str__(self):
        type_map = {1: "Added", 2: "Removed", 3: "Updated"}
        # TODO: update this to show the start date to end date with the description, if any and type
        # TODO: update admin page
        return f"{self.start_datetime.date()} - Service {type_map.get(self.exception_type, 'Unknown')}"
