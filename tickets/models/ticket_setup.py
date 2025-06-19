import datetime
import logging

import django.db.transaction as django_db_transaction
from django.apps import apps
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import serializers

from accounts.models.user_setup import MyUser
from modules.constants import GENERAL_TICKET_TYPE_ID
from modules.env_main import DEBUG
from modules.models import (
    ActiveMixin,
    DateTimeMixin,
    PaymentType,
    SourceDestinationLocationMixin,
    TicketStatus,
    TransactionType,
    TransactionStatus,
    PaymentStatus,
)
from modules.pnr_generator import generate_pnr
from modules.time_helpers import IST
from payments.constants import PaymentGatewayEnum, PaymentModeEnum
from payments.models.payment_gateway_setup import PaymentGateway, PaymentGatewayMode
from payments.models.transaction_setup import Transaction
from tickets.exceptions.main import (
    InvalidStatusUpdateError,
    MissingFareError,
    PaymentAmountMismatchError,
    TicketError,
    PostpaidTicketStatusPendingCannotCreateTransactionError, TransactionAlreadyExistsError,
)
from tickets.models.fare_setup import FareBreakup
from transit.models.transit_setup import TransitOption
from transit.views.transit_api_interface import TransitApiFactory
from ondc_buyer_backend.views.on_init import ONDCBuyerOnInitViewSet


class TicketType(models.Model):
    name = models.CharField(max_length=40, unique=True, db_index=True)
    discount_percentage = models.FloatField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_description_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.CharField(max_length=256, null=True, blank=True)

    @classmethod
    def get_default_pk(cls):
        return GENERAL_TICKET_TYPE_ID

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ticket Type"
        verbose_name_plural = "Ticket Types"


class Ticket(SourceDestinationLocationMixin, DateTimeMixin, ActiveMixin):
    # user who created it, generally the user itself
    created_by = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name="created_by_tickets",
        null=True,
        blank=True,
    )

    # user for whom it was created
    created_for = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name="created_for_tickets",
        null=True,
        blank=True,
    )

    # PNR, provided by us
    pnr = models.CharField(
        max_length=64, primary_key=True, default=generate_pnr, db_index=True
    )
    status = models.IntegerField(
        choices=TicketStatus.choices,
        help_text="Type of transit option, like bike, bus, metro etc.",
        default=TicketStatus.PENDING,
        db_index=True,
    )
    transit_option = models.ForeignKey(
        TransitOption, on_delete=models.CASCADE, null=False, blank=False
    )

    # Ticket-id/PNR given by the transit provider
    transit_pnr = models.CharField(max_length=128, null=True, blank=True)

    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.PROTECT,
        default=TicketType.get_default_pk,
    )

    passenger_count = models.IntegerField(
        default=1,
        null=True,
        blank=True,
        help_text="Number of passengers for this ticket"
    )

    # Eg: 13A
    # Eg: 3,5,11 (for multiple passengers)
    seat_no = models.CharField(max_length=16, default=None, null=True, blank=True)

    fare = models.OneToOneField(
        FareBreakup, null=True, blank=True, on_delete=models.PROTECT
    )
    amount = models.FloatField(default=0.0, null=True, blank=True)
    payment_type = models.IntegerField(
        choices=PaymentType.choices,
        help_text="Type of payment, PREPAID/POSTPAID/FREE",
        default=PaymentType.PREPAID,
        db_index=True,
        null=False,
        blank=False,
    )
    payment_status = models.IntegerField(
        choices=PaymentStatus.choices,
        help_text="1/3",
        default=PaymentStatus.NOT_COMPLETED,
        db_index=True,
        null=False,
        blank=False,
    )

    transaction = models.ManyToManyField(
        Transaction, blank=True, related_name="tickets"
    )

    valid_till = models.DateTimeField(null=True, blank=True)

    # stores detail about driver/conductor vehicle etc.
    # this will vary according to different transit_option

    # point of contact
    poc_name = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="This would be PoC for any ticket",
    )
    poc_phone = PhoneNumberField(
        null=True, blank=True, help_text="This would be PoC for any ticket"
    )
    ride_otp = models.CharField(max_length=6, null=True, blank=True)
    transaction_id = models.CharField(max_length=64, null=True, blank=True)

    # For Buses/Cabs
    driver_name = models.CharField(max_length=64, null=True, blank=True)
    driver_phone = PhoneNumberField(null=True, blank=True)
    conductor_name = models.CharField(max_length=64, null=True, blank=True)
    conductor_phone = PhoneNumberField(null=True, blank=True)

    # Cab Number/Bike Registration Plate/Flight Number/Train Number
    vehicle_number = models.CharField(max_length=32, null=True, blank=True)
    # TODO: populate this with fields from rapido
    vehicle_description = models.CharField(max_length=64, null=True, blank=True)

    # For Train
    terminal = models.CharField(max_length=10, null=True, blank=True)

    service_details = models.JSONField(null=True, blank=True)

    journey_leg_index = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        unique_together = ("transit_option", "pnr")
        # plural name for admin
        verbose_name_plural = "Tickets"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.pnr}"

    def save(self, *args, **kwargs):
        is_new_instance = self._state.adding

        if is_new_instance:
            if self.fare is None:
                raise MissingFareError()
            self.amount = self.fare.amount

        super(Ticket, self).save(*args, **kwargs)

    def is_transit_provider(self, *provider_enums):
        ticket = self
        transit_option = ticket.transit_option

        if not transit_option:
            logging.error(f"Transit option not found for ticket: {ticket}")
            return False

        transit_provider = transit_option.provider.name
        return transit_provider in provider_enums

    def update_payment_status_to_completed(self):
        if self.payment_status == PaymentStatus.NOT_COMPLETED:
            self.payment_status = PaymentStatus.COMPLETED
            self.save()

    def update_fare(self, amount):
        if self.fare:
            self.fare.basic = amount
            self.fare.save()

        # then farebreakup's post_save signal will update this ticket's amount

    def get_transit_provider(self):
        return self.transit_option.provider

    def get_poc_phone(self):
        return self.poc_phone

    def get_ticket_status(self):
        return TicketStatus(self.status)

    def get_payment_type(self):
        return self.payment_type

    def get_passenger_count(self):
        if self.passenger_count is None:
            return 1
        return self.passenger_count

    def is_payment_type_free(self):
        return self.get_payment_type() == PaymentType.FREE

    def is_payment_type_postpaid(self):
        return self.get_payment_type() == PaymentType.POSTPAID

    def is_payment_type_prepaid(self):
        return self.get_payment_type() == PaymentType.PREPAID

    def is_status_pending(self):
        return self.get_ticket_status() == TicketStatus.PENDING

    def is_status_confirmed(self):
        return self.get_ticket_status() == TicketStatus.CONFIRMED

    def is_status_cancelled(self):
        return self.get_ticket_status() == TicketStatus.CANCELLED

    def is_status_expired(self):
        return self.get_ticket_status() == TicketStatus.EXPIRED

    def validate_status(self, status):
        assert TicketStatus.is_valid(status)
        _current_status = TicketStatus(self.status)
        _new_status = status
        if _current_status == status:
            pass
        elif (
                (
                        _current_status == TicketStatus.CONFIRMED
                        and _new_status in [TicketStatus.PENDING]
                )
                or (
                        _current_status == TicketStatus.CANCELLED
                        and _new_status in [TicketStatus.CONFIRMED, TicketStatus.PENDING]
                )
                or _current_status == TicketStatus.EXPIRED
        ):
            raise InvalidStatusUpdateError(_current_status, _new_status)
        return True

    def get_successful_transactions(self):
        """
        Returns successful transactions associated with the ticket.
        """
        return self.transaction.filter(status=TransactionStatus.SUCCESS)

    def get_pending_transactions(self):
        """
        Returns pending transactions associated with the ticket.
        """
        return self.transaction.filter(status=TransactionStatus.PENDING)

    def has_successful_transaction(self):
        """
        Checks if the ticket has at least one successful transaction.
        Returns True if it does, False otherwise.
        """
        return self.get_successful_transactions().exists()

    def has_pending_transaction(self):
        """
        Checks if the ticket has at least one pending transaction.
        Returns True if it does, False otherwise.
        """
        return self.get_pending_transactions().exists()

    @staticmethod
    def has_incomplete_tickets(user):
        """
        Checks if the ticket has at least one pending transaction.
        Returns True if it does, False otherwise.
        """
        return Ticket.objects.filter(
            created_for=user, status__in=[TicketStatus.PENDING, TicketStatus.CONFIRMED]
        ).exists()

    @staticmethod
    def has_unpaid_tickets(user):
        """
        Checks if the ticket has at least one pending transaction.
        Returns True if it does, False otherwise.
        """
        return Ticket.objects.filter(
            created_by=user,
            status__in=(TicketStatus.CONFIRMED, TicketStatus.EXPIRED),
            payment_status=PaymentStatus.NOT_COMPLETED,
        ).exists()

    def validate_transaction(self):
        if not self.has_successful_transaction():
            raise Exception(f"No successful transaction found")

        # if self.transaction is None:
        #     raise MissingTransactionError()
        # if not self.transaction.is_status_success():
        #     raise TransactionNotSuccessfulError()
        return True

    def validate_amount(self):
        if self.transaction.amount != self.amount:
            raise PaymentAmountMismatchError()
        return True

    def validate_status_transition(self, new_status):
        """
        Validates the transition from the current status to a new status.
        Raises an InvalidStatusUpdateError if the transition is not allowed.
        """
        # Disallow certain transitions
        if (
                self.status == TicketStatus.CONFIRMED
                and self.payment_type == PaymentType.PREPAID
                and self.payment_status == PaymentStatus.NOT_COMPLETED
        ):
            if new_status != self.status:
                raise InvalidStatusUpdateError(self.status, new_status)

        # Add more disallowed transitions here as needed...

    def update_status(self, status, service_details=None, other_updates=None,
                      notification_title=None, notification_message=None,
                      notification=None):
        logging.debug(f"update_status for pnr: {self.pnr}, status={status}, service_details={service_details}, "
                      f"other_updates={other_updates}, notification_title={notification_title}, "
                      f"notification_message={notification_message}, notification={notification}.")
        try:
            self.validate_status(status)
            logging.debug("Status validated successfully.")

            if self.payment_type == PaymentType.PREPAID and status == TicketStatus.CONFIRMED:
                logging.debug("Payment type is PREPAID and status is CONFIRMED, validating transaction.")
                self.validate_transaction()
                # TODO: check transaction amount with ticket amount
                # logging.debug("Validating transaction amount with ticket amount.")
                # self.validate_amount()

            if other_updates is not None:
                logging.debug(f"Applying other_updates: {other_updates}")
                for member, value in other_updates.items():
                    setattr(self, member, value)
                logging.debug("Other updates applied successfully.")

            if service_details:
                logging.debug(f"Updating service_details: {service_details}")
                self.service_details = service_details

            self.status = status
            logging.debug(f"Status set to: {status}. Saving the object.")
            self.save()
            logging.debug("Object saved successfully.")

            self.refresh_from_db()
            # Check if status was updated successfully
            if self.status != status:
                logging.error(f"Failed to update status for pnr: {self.pnr}. Refreshed status: {self.status}")

            # send fcm notification
            if notification_title and notification_message:
                logging.debug(
                    f"Sending FCM notification with title: {notification_title} and message: {notification_message}.")
                self.send_user_status_notification(notification_title, notification_message, notification)
                logging.debug("FCM notification sent successfully.")

        except InvalidStatusUpdateError as e:
            logging.error(f"InvalidStatusUpdateError occurred: {e}")
        except TicketError:
            logging.debug("TicketError occurred, re-raising.")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise e
        finally:
            logging.debug("update_status method execution completed.")

    @staticmethod
    def get_all_payment_status_not_completed_tickets(sd=None, ed=None):
        tickets = Ticket.objects.filter(payment_status=PaymentStatus.NOT_COMPLETED)

        query = Q()
        if sd:
            query &= Q(created_at__gte=sd)
        if ed:
            query &= Q(created_at__lte=ed)

        tickets = tickets.filter(query)

        return tickets

    @django_db_transaction.atomic
    def create_new_transaction(self, payment_mode=None, callback_url=None):
        if self.payment_type == PaymentType.FREE:
            raise serializers.ValidationError(
                {"status": "Cannot create transaction for free ticket"}
            )

        # TODO: create SystemParameters
        # TODO: pick current active PG from SystemParameters
        payment_gateway_paytm = PaymentGateway.objects.get(
            name=PaymentGatewayEnum.PAYTM.value
        )

        if payment_mode:
            gateway_mode = PaymentGatewayMode.objects.get(
                gateway=payment_gateway_paytm, mode__name=payment_mode
            )
        else:
            gateway_mode = PaymentGatewayMode.objects.get(
                gateway=payment_gateway_paytm, mode__name=PaymentModeEnum.UNKNOWN.value
            )

        # check if ticket is postpaid and status is Pending
        if self.is_payment_type_postpaid() and self.is_status_pending():
            raise PostpaidTicketStatusPendingCannotCreateTransactionError()

        # patch for debug mode
        amount = self.amount
        if DEBUG:
            amount = 1.0

        # check if already one transaction for this ticket
        # if yes, raise error
        if self.transaction.count() > 0:
            raise TransactionAlreadyExistsError()

        ticket_type_name = self.ticket_type.name.strip()
        logging.info(f"Ticket Type Name: {ticket_type_name}")

        transaction_status = TransactionStatus.SUCCESS if ticket_type_name == 'Pink' else TransactionStatus.PENDING
        logging.info(f"Transaction Status: {transaction_status}")

        transaction = Transaction.objects.create(
            user=self.created_for,
            status=transaction_status,
            amount=amount,
            transaction_type=TransactionType.DEBIT,
            gateway_mode=gateway_mode,
        )
        self.transaction.add(transaction)
        self.save()
        if ticket_type_name == 'Pink':
            transaction_payment_gateway_payload = {
                "message": "Success",
                "description": None,
                "data": {}
            }
            return transaction_payment_gateway_payload['data']
        else:
            transaction_payment_gateway_payload = transaction.transaction_payload(callback_url=callback_url)
            return transaction_payment_gateway_payload

    def cancel_by_transit_provider(self):
        # update status in db
        # notify user
        pass

    def cancel_by_user(self, cancellation_reason):
        if self.is_status_cancelled():
            return

        # create ticket update object with this cancellation reason
        try:
            ticket_update = TicketUpdate.objects.create(
                ticket=self,
                details={
                    "status": "cancel_by_user",
                    "description": cancellation_reason,
                }
            )
        except Exception as e:
            logging.error(e)

        transit_provider = self.get_transit_provider()
        provider_name = transit_provider.name
        transit_api = TransitApiFactory(provider_name)
        transit_api.cancel(self.transit_pnr, cancellation_reason=cancellation_reason)
        # update status in db
        self.update_status(TicketStatus.CANCELLED, service_details=None)

    def cancel_by_system(self, cancellation_reason="Ticket cancelled by system, default reason"):
        if self.is_status_cancelled():
            return

        # create ticket update object with this cancellation reason
        try:
            ticket_update = TicketUpdate.objects.create(
                ticket=self,
                details={
                    "status": "cancel_by_system",
                    "description": cancellation_reason,
                }
            )
        except Exception as e:
            logging.error(e)
        transit_provider = self.get_transit_provider()
        provider_name = transit_provider.name
        transit_api = TransitApiFactory(provider_name)
        transit_api.cancel(
            self.transit_pnr,
            cancellation_reason=cancellation_reason,
        )
        self.update_status(TicketStatus.CANCELLED, service_details=None)

    def is_payment_status_completed(self):
        return self.payment_status == PaymentStatus.COMPLETED

    def check_payment_status(self):
        """update payment_status of ticket based on transaction status"""
        if self.is_payment_status_completed():
            return

        transactions = self.transaction.all()
        for transaction in transactions:
            transaction.check_gateway_transaction_status()

        if self.has_successful_transaction():
            self.update_payment_status_to_completed()

    def get_transactions(self):
        return self.transaction.all()

    def get_latest_successful_transaction(self):
        return self.transaction.filter(status=TransactionStatus.SUCCESS).last()

    def check_transit_provider_ticket_status(self):
        """update payment_status of ticket based on transaction status"""
        if self.is_status_pending():
            self.check_payment_status()
            if self.is_payment_status_completed():
                # call book ticket api
                transit_provider = self.get_transit_provider()
                provider_name = transit_provider.name
                transit_api = TransitApiFactory(provider_name)

                pnr_to_ondc_transaction_id_key = f"pnr:{self.pnr}"
                ondc_transaction_id = cache.get(pnr_to_ondc_transaction_id_key)
                response = transit_api.book(
                    user=self.created_for,
                    transit_mode=self.transit_option.transit_mode,
                    pickup_location=self.start_location_code,
                    drop_location=self.end_location_code,
                    transaction_obj=self.get_latest_successful_transaction(),
                    passenger_count=self.passenger_count,
                    ondc_transaction_id=ondc_transaction_id,
                    pnr=self.pnr,
                )
                agency = response["message"]["order"]["provider"]["descriptor"]["name"],
                logging.info(f"Agency============: {agency}")
                # transit_pnr = response.get_qr_ticket_numbers()[0]
                # convert transit pnr to comma seperated string
                # transit_pnr = ",".join(response.get_qr_ticket_numbers())
                self.transit_pnr = str(response["message"]["order"]["fulfillments"][0]["tags"][1]['list'][0]['value'])
                self.service_details['ticket_qr'] = response["message"]["order"]["fulfillments"][0]["stops"][0]["authorization"]["token"]
                self.save()

                valid_till = (self.created_at + datetime.timedelta(days=1)).astimezone(IST).replace(hour=3, minute=0,
                                                                                                    second=0,
                                                                                                    microsecond=0)

                self.update_status(
                    TicketStatus.CONFIRMED,
                    other_updates={
                        "valid_till": valid_till
                    })

        # means ticket is in final state, return
        return

    @staticmethod
    def mark_tickets_as_cancelled(start_datetime=None, end_datetime=None):
        """
        Update status of tickets to CANCELLED based on the created_at timestamp range.

        :param start_datetime: Cancel tickets created after this datetime (datetime object).
        :param end_datetime: Cancel tickets created before this datetime (datetime object).
        """
        if not start_datetime and not end_datetime:
            raise ValueError("At least one of start_datetime or end_datetime must be provided")

        filters = {'status': TicketStatus.PENDING}

        if start_datetime:
            filters['created_at__gt'] = start_datetime
        if end_datetime:
            filters['created_at__lt'] = end_datetime

        # affected_rows = Ticket.objects.filter(**filters).update(status=TicketStatus.CANCELLED)
        # Fetch the tickets that match the criteria
        tickets_to_cancel = Ticket.objects.filter(**filters)

        # Print PNR for each ticket
        for ticket in tickets_to_cancel:
            # log ticket's pnr, created_at, status, payment status
            logging.info(f"Cancelling Ticket PNR: {ticket.pnr}, "
                         f"Created At: {ticket.created_at}, "
                         f"Status: {ticket.status}, "
                         f"Transit PNR: {ticket.transit_pnr}, "
                         f"Service Details: {ticket.service_details}, "
                         f"Payment Status: {ticket.payment_status}")

            ticket.cancel_by_system(cancellation_reason="Unconfirmed ticket cancelled by system.")
            # logging.info()
            # logging.info(f"Cancelling ticket with PNR: {ticket.pnr}")

        # affected_rows = tickets_to_cancel.update(status=TicketStatus.CANCELLED)
        logging.info(f"Cancelled {tickets_to_cancel.count()} ticket(s) with criteria: {filters}")

    @staticmethod
    def mark_tickets_as_expired(start_datetime=None, end_datetime=None):
        """
        Update status of tickets to EXPIRED based on the created_at timestamp range.

        :param start_datetime: Expire tickets created after this datetime (datetime object).
        :param end_datetime: Expire tickets created before this datetime (datetime object).
        """
        if not start_datetime and not end_datetime:
            raise ValueError("At least one of start_datetime or end_datetime must be provided")

        filters = {'status': TicketStatus.CONFIRMED}

        if start_datetime:
            filters['created_at__gt'] = start_datetime
        if end_datetime:
            filters['created_at__lt'] = end_datetime

        affected_rows = Ticket.objects.filter(**filters).update(status=TicketStatus.EXPIRED)
        logging.info(f"Expired {affected_rows} ticket(s) with criteria: {filters}")

    def get_user_phone(self):
        return str(self.created_for.phone)

    def send_user_status_notification(self, title, message, notification_obj=None):
        """
        Send notification to user based on ticket status
        """
        self.created_for.send_user_notification(title, message, notification_obj)
        # extra_params = {"notification_id": 3000}
        # if notification_obj:
        #     extra_params = notification_obj.get_extra_params()
        #
        # channel_name = "DUMMY"
        # phone_number = self.get_user_phone()
        # if phone_number and len(phone_number) >= 10:
        #     channel_name = phone_number[-10:]
        #
        # async_send_fcm_notification(channel_name, title=title, body=message, extra_params=extra_params)

    @staticmethod
    def get_transit_provider_poc_phone_for_user_phone(phone, delta_seconds=600):
        """phone: +919876543210"""
        user = MyUser.objects.filter(phone=phone)
        if user.exists():
            # Calculate the datetime threshold for the last delta_seconds
            time_window_ago = datetime.datetime.now() - datetime.timedelta(seconds=delta_seconds)

            # Retrieve the latest tickets created within the last delta_seconds
            tickets = Ticket.objects.filter(
                status=TicketStatus.CONFIRMED,
                created_for=user.first(),
                created_at__gte=time_window_ago,
            )

            if tickets.exists():
                if tickets[0].poc_phone is not None:
                    return str(tickets[0].poc_phone)[-10:]
                else:
                    raise Exception("No POC phone found for the user")
            else:
                # Handle the case when no tickets are found within the specified timeframe
                logging.error(f"No tickets found within the last {delta_seconds / 60} minutes")

    @staticmethod
    def get_user_phone_for_provider_poc_phone(phone, delta_seconds=600):
        """phone: +919876543210"""
        time_window_ago = timezone.now() - datetime.timedelta(seconds=delta_seconds)
        logging.debug(f"time_window_ago: {time_window_ago}")
        ticket_obj = Ticket.objects.filter(
            status=TicketStatus.CONFIRMED,
            created_at__gte=time_window_ago,
            poc_phone=phone,
        )
        if ticket_obj.exists():
            return str(ticket_obj[0].created_for.phone)[-10:]
        else:
            # Handle the case when no tickets are found within the specified timeframe
            logging.error(f"No tickets found for poc_phone within the last {delta_seconds / 60} minutes")

    def fcm_data(self):
        return {}
        # return TicketSerializerForFCMData(self).data

    def get_journey(self):
        Journey = apps.get_model("journey", "Journey")
        return Journey.objects.filter(tickets=self).first()


class TicketUpdate(DateTimeMixin, ActiveMixin):
    trigger_signal = models.BooleanField(default=True)
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="ticket_updates",
        null=False,
        blank=False,
    )
    details = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Ticket Update"
        verbose_name_plural = "Ticket Updates"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.ticket.pnr} - {self.created_at}"

    @staticmethod
    def custom_create(details, ticket_transit_pnr, trigger_signal=True):
        logging.info(
            f"Creating TicketUpdate: details: {details}; ticket_transit_pnr: {ticket_transit_pnr}"
        )
        TicketUpdate(
            trigger_signal=trigger_signal,
            ticket=Ticket.objects.get(transit_pnr=ticket_transit_pnr),
            details=details,
        ).save()

    @staticmethod
    def build_instance(details, ticket_transit_pnr, trigger_signal=True):
        """
        Build a TicketUpdate instance without saving it.
        """
        try:
            ticket = Ticket.objects.get(transit_pnr=ticket_transit_pnr)
        except Ticket.DoesNotExist:
            return None

        ticket_update = TicketUpdate(
            trigger_signal=trigger_signal,
            ticket=ticket,
            details=details,
        )

        return ticket_update

    @classmethod
    def delete_older_ticket_updates(cls):
        """
        Delete all ticket updates older than 7 days.
        """
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        cls.objects.filter(created_at__lte=seven_days_ago).delete()
