from django.db import models
from django.utils.translation import gettext_lazy as _

"""Enums"""


class TransitMode(models.IntegerChoices):
    BIKE = 1, _("Bike")
    CAR = 3, _("Car")
    BUS = 5, _("Bus")
    TRAIN = 7, _("Train")
    TRAM = 9, _("Tram")
    METRO = 11, _("Metro")
    FERRY = 13, _("Ferry")
    SCOOTER = 15, _("Scooter")
    AUTO_RICKSHAW = 17, _("Auto Rickshaw")
    MANUAL_RICKSHAW = 19, _("Manual Rickshaw")
    AIRPLANE = 21, _("Airplane")

    # get choice integer value from string
    @classmethod
    def get_choice_value(cls, choice):
        return cls[choice].value


class JourneyStatus(models.IntegerChoices):
    # The journey is being planned but not yet started.
    INITIATED = 1, _("Initiated")

    # The journey has started and it's in progress.
    IN_PROGRESS = 3, _("In Progress")

    # The journey has been completed successfully.
    COMPLETED = 5, _("Completed")

    # The journey was planned but has been cancelled before it started.
    CANCELLED = 6, _("Cancelled")

    @staticmethod
    def is_valid(choice_enum):
        return choice_enum in [choice[0] for choice in TicketStatus.choices]

    def __str__(self):
        return JourneyStatus(self).name


class TicketStatus(models.IntegerChoices):
    # The ticket has been confirmed but the journey has not yet started.
    CONFIRMED = 1, _("Confirmed")

    #  The initial state, right after a ticket has been created but not yet confirmed.
    PENDING = 3, _("Pending")

    # The ticket was confirmed but has now been cancelled.
    CANCELLED = 5, _("Cancelled")

    # The ticket was not used within its valid time period and is now no longer valid.
    # Expired ticket is a sister state of confirmed ticket.
    EXPIRED = 7, _("Expired")

    @staticmethod
    def is_valid(choice_enum):
        return choice_enum in [choice[0] for choice in TicketStatus.choices]

    def __str__(self):
        return TicketStatus(self).name


class PaymentType(models.IntegerChoices):
    PREPAID = 1, _("Prepaid")

    POSTPAID = 3, _("Postpaid")

    FREE = 5, _("Free")

    @staticmethod
    def is_valid(choice_enum):
        return choice_enum in [choice[0] for choice in PaymentType.choices]

    def __str__(self):
        return PaymentType(self).name


class TripStatus(models.IntegerChoices):
    """
    Trip status is used for tickets that are not yet confirmed or payment status still pending
    """

    COMPLETED = 1, _("Completed")
    ONGOING = 3, _("Ongoing")
    SCHEDULED = 5, _("Scheduled")


class PaymentStatus(models.IntegerChoices):
    NOT_COMPLETED = 1, _("Not Completed")
    COMPLETED = 3, _("Completed")


class TransactionStatus(models.TextChoices):
    PENDING = "P", _("Pending")
    FAILED = "F", _("Failed")
    SUCCESS = "S", _("Success")


class TransactionType(models.IntegerChoices):
    # Debit means money is deducted from user's account
    # Used in cases of ticket booking, top up etc.
    DEBIT = -1, _("Debit")

    # Credit means money is added to user's account
    # Used in cases of refunds
    CREDIT = 1, _("Credit")


"""Mixins"""


class ActiveMixin(models.Model):
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class DateTimeMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True


class TransitModeMixin(models.Model):
    transit_mode = models.IntegerField(
        choices=TransitMode.choices,
        help_text="Type of transit option, like bike, bus, metro etc.",
    )

    class Meta:
        abstract = True

    # return transit mode choice as string and not integer
    def __str__(self):
        return TransitMode(self.transit_mode).name


class SourceDestinationLocationMixin(models.Model):
    # this code can be unique identifier for the location, if any
    start_location_code = models.CharField(max_length=80, null=True, blank=True)
    start_location_name = models.CharField(max_length=255, null=True, blank=True)
    start_location_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=0.0
    )
    start_location_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=0.0
    )
    # this code can be unique identifier for the location, if any
    end_location_code = models.CharField(max_length=80, null=True, blank=True)
    end_location_name = models.CharField(max_length=255, null=True, blank=True)
    end_location_lat = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=0.0
    )
    end_location_lng = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, default=0.0
    )

    class Meta:
        abstract = True


def create_or_update(data, data_model, data_serializer, key="id"):
    serializer = data_serializer(data=data)
    if key in data:
        try:
            query = {"%s__exact" % key: data[key]}
            obj = data_model.objects.filter(**query).get()
            serializer = data_serializer(obj, data=data)
        except data_model.DoesNotExist:
            pass
    if serializer.is_valid(raise_exception=True):
        return serializer.save()
    return None


def only_create(data, data_model, data_serializer, key="id"):
    serializer = data_serializer(data=data)
    # logger.debug("API: Serializer: " + str(serializer))
    if key in data:
        try:
            query = {"%s__exact" % key: data[key]}
            # logger.debug("API: Query: " + str(query))
            obj = data_model.objects.filter(**query).get()
            return obj, True
        except data_model.DoesNotExist:
            pass
    if serializer.is_valid(raise_exception=True):
        # logger.debug("API: Only Create Saving")
        return serializer.save(), False
    return None, None
    # model_obj, if exists status


def get_model_cache_key(instance):
    app_label = instance._meta.app_label
    model_name = instance._meta.model_name
    pk = instance.pk
    return f"{app_label}_{model_name}_{pk}"
