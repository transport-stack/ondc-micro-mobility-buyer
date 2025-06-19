import datetime
import logging
import uuid as uuid

from dateutil.utils import today

from accounts.models.user_setup import MyUser
from modules.models import ActiveMixin, DateTimeMixin, TicketStatus, JourneyStatus
from django.db import models

from tickets.models.ticket_setup import Ticket


class Journey(DateTimeMixin, ActiveMixin):
    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True
    )
    # user who created it, generally the user itself
    created_by = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name="created_by_journey",
        null=True,
        blank=True,
    )

    # user for whom it was created
    created_for = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name="created_for_journey",
        null=True,
        blank=True,
    )

    data = models.JSONField(default=dict, null=True, blank=True)

    status = models.IntegerField(
        choices=JourneyStatus.choices,
        help_text="Type of journey status like Initiated, In Progress, Completed, Cancelled",
        default=JourneyStatus.INITIATED,
        db_index=True,
    )

    tickets = models.ManyToManyField(
        Ticket, related_name="journeys", blank=True, db_index=True
    )
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        # plural name for admin
        verbose_name_plural = "Journeys"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.uuid}"

    def get_tickets(self):
        return self.tickets.all()

    def add_ticket(self, ticket_obj):
        # add ticket, don't add if ticket already exists
        self.tickets.add(ticket_obj, through_defaults={})

    def get_data(self):
        return self.data

    def set_status(self, status: JourneyStatus):
        self.status = status
        self.save()

    def is_status_initiated(self):
        return self.status == JourneyStatus.INITIATED

    def is_status_in_progress(self):
        return self.status == JourneyStatus.IN_PROGRESS

    def is_status_completed(self):
        return self.status == JourneyStatus.COMPLETED

    def is_status_cancelled(self):
        return self.status == JourneyStatus.CANCELLED

    def is_status_cancelled_or_completed(self):
        return self.is_status_cancelled() or self.is_status_completed()

    def set_status_as_completed(self):
        self.set_status(JourneyStatus.COMPLETED)

    def set_status_as_in_progress(self):
        self.set_status(JourneyStatus.IN_PROGRESS)

    @staticmethod
    def mark_journeys_as_completed():
        start_of_today = datetime.datetime.combine(
            datetime.datetime.today(), datetime.time.min
        )
        Journey.objects.filter(
            created_at__lt=start_of_today,
            status__in=[JourneyStatus.INITIATED, JourneyStatus.IN_PROGRESS],
        ).update(status=JourneyStatus.COMPLETED)

    @staticmethod
    def mark_all_previous_journeys_as_completed_for(user):
        Journey.objects.filter(
            created_for=user,
            status__in=[JourneyStatus.INITIATED, JourneyStatus.IN_PROGRESS],
        ).update(status=JourneyStatus.COMPLETED)

    def mark_as_completed(self):
        if self.is_status_completed():
            return
        self.status = JourneyStatus.COMPLETED
        self.end_datetime = datetime.datetime.now()
        self.save()

    def mark_as_cancelled(self):
        if self.is_status_cancelled():
            return
        self.status = JourneyStatus.CANCELLED
        self.end_datetime = datetime.datetime.now()
        self.save()

    def is_ticket_allowed(self):
        return True

        # future
        # return self.is_status_cancelled_or_completed()

    def check_journey_status(self):
        logging.debug("check_journey_status: Start of function")

        if self.is_status_cancelled_or_completed():
            logging.debug("check_journey_status: Status is cancelled or completed")
            # do nothing
            return
