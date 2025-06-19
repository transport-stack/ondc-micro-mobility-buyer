import uuid as uuid

from django.db import models

from accounts.models.user_setup import MyUser
from modules.models import (
    ActiveMixin,
    DateTimeMixin,
    SourceDestinationLocationMixin,
    TransitModeMixin,
    TripStatus,
)
from transit.models.transit_setup import TransitOption


class Trip(
    SourceDestinationLocationMixin,
    DateTimeMixin,
    ActiveMixin,
    TransitModeMixin,
):
    # unique identifier for a trip
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)

    # user for whom trip was made
    user = models.ForeignKey(MyUser, on_delete=models.SET_NULL, null=True, blank=True)

    """
    # a trip can be a child of another trip
    # e.g. a trip from home to office can be a child of a trip from home to a friend's place
    # this is useful for aggregating trips
    # each trip may/may not have a parent
    # any trip can have a child, that can be accessed via trip.children
    # any trip can have more than one child
    # but a child can have only one parent
    """
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="trips",
        on_delete=models.SET_NULL,
    )

    transit_option = models.ForeignKey(
        TransitOption, on_delete=models.CASCADE, null=True, blank=True
    )

    # scheduled start and end datetime
    scheduled_start_datetime = models.DateTimeField(default=None, null=True, blank=True)
    scheduled_end_datetime = models.DateTimeField(default=None, null=True, blank=True)

    # actual start and end datetime
    actual_start_datetime = models.DateTimeField(default=None, null=True, blank=True)
    actual_end_datetime = models.DateTimeField(default=None, null=True, blank=True)

    # mode of transport, added via TransportModeMixin

    # duration of the trip in seconds, upto 1s accuracy
    duration = models.IntegerField(default=-1, null=True, blank=True)

    # distance of the trip in meters, upto 1m accuracy
    distance = models.IntegerField(default=-1, null=True, blank=True)

    # cost of the trip
    fare = models.FloatField(default=0.0, null=True, blank=True)

    class Meta:
        # plural name for admin
        verbose_name_plural = "Trips"
        ordering = ("-created_at",)

    def __str__(self):
        # return uuid + transit_mode
        return f"{self.uuid} # {self.transit_mode.__str__()}"

    # get children of a trip
    def get_children(self):
        return Trip.objects.filter(parent=self)

    # get parent of a trip
    def get_parent(self):
        return self.parent

    # get trip's status
    def get_status(self):
        if self.actual_start_datetime:
            if self.actual_end_datetime:
                return TripStatus.COMPLETED.name
            else:
                return TripStatus.ONGOING.name
        else:
            return TripStatus.SCHEDULED.name

    def get_transit_mode(self):
        return self.transit_mode
