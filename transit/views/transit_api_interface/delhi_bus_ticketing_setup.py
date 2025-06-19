from django.apps import apps
from django.utils import timezone

from ondc_micromobility_api.ondc_wrapper.utils.signature_setup import get_datetime_obj_in_api_format
from ondc_micromobility_api.wrapper.book import BookAPI
from ondc_micromobility_api.wrapper.cancel import CancelAPI
from ondc_micromobility_api.wrapper.estimate import EstimateAPI
from modules.models import TransitMode, TicketStatus
from transit.views.transit_api_interface.base import TransitAPI
import datetime


class DelhiBusTicketingAPI(TransitAPI):
    def _estimate(self, transit_mode, pickup_location, drop_location, **kwargs):
        # Rapido specific estimate logic here
        api = EstimateAPI()
        # use list of service_type in /estimate

        if transit_mode != TransitMode.BUS:
            raise ValueError("Invalid transit mode")

        source_stop_id = str(pickup_location)
        destination_stop_id = str(drop_location)
        response_obj = api.estimate(
            Src_Stn=source_stop_id,
            dest_Stn=destination_stop_id,
            Grp_Size=kwargs.get("Grp_Size", 1))
        return response_obj

    def _book(self, user, transit_mode, pickup_location, drop_location, **kwargs):
        """
        :param user: User object
        :param transit_mode: TransitMode
        :param pickup_location: int
        :param drop_location: int
        :param kwargs: transaction_obj (optional)
        """
        if transit_mode != TransitMode.BUS:
            raise ValueError("Invalid transit mode")

        api = BookAPI()

        # convert user to transit provider`s user
        user_phone_10_digit = None
        if user:
            user_phone = str(user.phone)
            user_phone_10_digit = user_phone.replace("+91", "")

        # TODO: use this later
        passenger_count = kwargs.get("passenger_count")

        # TODO: pass transaction details
        response_obj = api.book(
            ondc_transaction_id=kwargs.get("ondc_transaction_id"),
            pnr=kwargs.get("pnr"),
        )

        # self.transit_pnr = response_json["orderId"]
        # self.message = response_json["message"]
        return response_obj

    def _cancel(self, transit_pnr, cancellation_reason):
        # since it's postpaid, return 200 OK
        return
        # api = CancelAPI()
        # response = api.cancel(order_id=transit_pnr, cancel_reason=cancellation_reason)
        #
        # if response.status_code not in range(200, 300):
        #     raise Exception(f"Rapido cancellation failed: {response.json()}")
        #
        # return response.json()

    def _is_eligible(self, user, transit_mode, pickup_location, drop_location):
        DURATION_BEFORE_REPEAT_BOOKING_ALLOWED_SECONDS = 10000
        # above duration in minutes
        repeat_ticketing_cooldown_period_min = int(round(DURATION_BEFORE_REPEAT_BOOKING_ALLOWED_SECONDS / 60.0, 0))

        # Ensure you're working with the current time in the correct timezone
        now = timezone.localtime(timezone.now())

        # Calculate the earliest allowed new booking time
        earliest_allowed_new_booking_time = now - datetime.timedelta(
            seconds=DURATION_BEFORE_REPEAT_BOOKING_ALLOWED_SECONDS)

        ticket_model = apps.get_model("tickets", "Ticket")
        latest_ticket = ticket_model.objects.filter(
            created_for=user,
            status__in=[TicketStatus.EXPIRED, TicketStatus.CONFIRMED, TicketStatus.PENDING]
        ).exclude(
            created_at__lt=earliest_allowed_new_booking_time
        ).order_by('-created_at').first()

        if latest_ticket:
            # Calculate the next eligible booking time and convert it to local timezone
            next_eligible_booking_time = timezone.localtime(latest_ticket.created_at) + datetime.timedelta(
                seconds=DURATION_BEFORE_REPEAT_BOOKING_ALLOWED_SECONDS)

            if now < next_eligible_booking_time:
                # Format the datetime in a user-friendly way
                next_booking_time_str = next_eligible_booking_time.strftime("%I:%M%p")
                raise Exception(
                    f"You can book again after {next_booking_time_str}.")

        return True
