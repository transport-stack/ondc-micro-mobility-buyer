import logging
import os

from django.core.cache import cache
from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from geopy.distance import geodesic
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_206_PARTIAL_CONTENT
from rest_framework.viewsets import GenericViewSet
from modules.pnr_generator import generate_pnr
from accounts.decorators import X_API_KEY_PARAMETERS
from accounts.models import MyUser
from common.constants import NoneSerializer
from common.mixins import ViewSetPermissionByMethodMixin
from coupons.calculations import get_coupon_from_code
from coupons.serializers import CouponCodeSerializer
from journey.models.journey_setup import Journey
from modules.constants import NAMMAYATRI_ENUM
from modules.env_main import DEBUG
from modules.models import TransitMode, PaymentType, TicketStatus, JourneyStatus
from modules.views import XAPIKeyPermission, CustomJSONRenderer, CustomPagination
from ondc_buyer_backend.constants import CACHE_DELIMITER
from ondc_buyer_backend.tasks.buyer_cancel import buyer_cancel
from ondc_buyer_backend.tasks.buyer_track import buyer_track
from ondc_buyer_backend.tasks.buyer_select import buyer_select
from ondc_buyer_backend.utils.timestamp_converter import convert_to_unix_timestamp
from payments.models.transaction_setup import TransactionSerializer
from nammayatri.constants import NammayatriCancellationReasons
from scripts.driver_location_update import interpolate_coordinates
from tickets.constants import TICKET_INITIATE_TRANSACTION_TIMEOUT
from tickets.filters import TicketFilter
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import Ticket, TicketUpdate
from tickets.permissions import IsTicketCreator
from tickets.serializers import (
    TicketSerializer,
    TicketUpdateSerializer,
    FareBreakupSerializer, TicketCancellationSerializer,
)
from transit.models.transit_setup import TransitProvider, TransitOption
from transit.utils import NammayatriTransitMessages
from transit.views.transit_api_interface import TransitApiFactory


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    lookup_field = "pnr"
    model = Ticket

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get query parameters from the request
        filters = {}
        ordering = []

        valid_fields = [f.name for f in self.model._meta.get_fields()]

        for key, value in self.request.query_params.items():
            if "__" in key:
                field, lookup = key.split("__")
                if field in valid_fields and lookup in [
                    "exact",
                    "iexact",
                    "contains",
                    "icontains",
                    "gt",
                    "gte",
                    "lt",
                    "lte",
                ]:
                    filters[key] = value
            elif key == "ordering":
                ordering = [
                    o for o in value.split(",") if o.lstrip("-") in valid_fields
                ]

        # Apply filters based on query parameters
        if filters:
            queryset = queryset.filter(**filters)

        # Apply ordering if specified
        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset


@extend_schema(parameters=X_API_KEY_PARAMETERS)
class TicketsViewSet(
    ViewSetPermissionByMethodMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    model = Ticket
    filterset_class = TicketFilter
    renderer_classes = [
        CustomJSONRenderer,
    ]
    permission_classes = [
        XAPIKeyPermission,
        IsAuthenticated,
    ]
    permission_action_classes = dict(
        retrieve=(IsTicketCreator,),
        list=(IsTicketCreator,),
        cancel=(IsTicketCreator,),
        updates=(IsTicketCreator,),
        transaction=(IsTicketCreator,),
        initiate=(),
    )
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        return Ticket.objects.filter(active=True, created_for=user)

    @extend_schema(tags=["Tickets"], description="Get list of tickets for this user")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Tickets"],
        description="Cancel this ticket",
        request=TicketCancellationSerializer,
        responses={201: NoneSerializer},
    )
    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None, *args, **kwargs,):
        ticket_obj = self.get_object()
        ticket_data = super().retrieve(request, *args, **kwargs)
        cancellation_reason = request.data.get(
            "cancellation_reason", NammayatriCancellationReasons.ORDER_CANCELLED_BY_CUSTOMER
        )
        transaction_id = ticket_data.data["transaction_id"]
        on_confirm_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_confirm"
        on_confirm_data = cache.get(on_confirm_cache_key)
        if on_confirm_data:
            buyer_cancel.apply_async(args=[on_confirm_data, cancellation_reason])

        txn_canceled_key = f"{transaction_id}:{CACHE_DELIMITER}:txn_canceled"
        cache.set(txn_canceled_key, True, timeout=TICKET_INITIATE_TRANSACTION_TIMEOUT)
        ticket_obj.cancel_by_user(cancellation_reason=cancellation_reason)
        ticket_obj.refresh_from_db()
        return Response(TicketSerializer(ticket_obj).data)

    @extend_schema(
        tags=["Tickets"],
        description="Get transit operator updates about this ticket",
        responses={
            200: OpenApiResponse(
                description="Successful fetch", response=TicketUpdateSerializer
            )
        },
        request=TicketUpdateSerializer,
        examples=[],
    )
    @action(detail=True, methods=["GET"])
    def updates(self, request, pk=None, *args, **kwargs):
        ticket_data = super().retrieve(request, *args, **kwargs)
        on_confirm_cache_key = f"{ticket_data.data['transaction_id']}:{CACHE_DELIMITER}:on_confirm"
        on_confirm_data = cache.get(on_confirm_cache_key)
        if on_confirm_data:
            buyer_track.apply_async(args=[on_confirm_data])
        return Response(
            TicketUpdateSerializer(
                TicketUpdate.objects.filter(ticket=self.get_object()), many=True
            ).data
        )

    @extend_schema(
        tags=["Tickets"],
        description="Initiate transaction for this ticket",
        request=TransactionSerializer,
        responses={
            200: OpenApiResponse(
                description="Successful fetch", response=TransactionSerializer
            )
        },
        examples=[
            OpenApiExample(
                "Example 1",
                summary="To use default PG's all-in-one SDK call",
                description="",
                value={"payment_mode": "UNKNOWN"},
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            ),
            OpenApiExample(
                "Example 2",
                summary="Create UPI deeplink",
                description="",
                value={"payment_mode": "UPI"},
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            ),
        ],
    )
    @action(detail=True, methods=["POST"])
    def transaction(self, request, pk=None):
        # TODO: checks if already pending transaction

        # get ticket
        ticket = self.get_object()

        # if the mode is auto + rapido, send fcm
        transit_option = ticket.transit_option
        if ticket.transit_option.transit_mode == TransitMode.AUTO_RICKSHAW and transit_option.provider.name == NAMMAYATRI_ENUM:
            raise Exception(NammayatriTransitMessages.PAY_DIRECTLY_TO_DRIVER["message"])

        # get payment mode from payload
        payment_mode = request.data.get("payment_mode", None)
        return Response(ticket.create_new_transaction(payment_mode=payment_mode))

    @extend_schema(
        tags=["Tickets"],
        description="Check if coupon is applicable on this ticket",
        request=CouponCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="Successful created", response=serializer_class
            )
        },
    )
    @action(detail=True, methods=["POST"], url_path="check-coupon")
    def check_coupon(self, request, pk=None):
        # get ticket
        ticket = self.get_object()

        # get coupon code
        coupon_code = request.data.get("code", None)
        is_coupon_valid, coupon = get_coupon_from_code(coupon_code)
        if not is_coupon_valid:
            return Response(
                {"data": "coupon code not found."}, status=HTTP_400_BAD_REQUEST
            )

        fare = ticket.fare

        if fare.coupon is not None:
            return Response(
                {"data": "multiple coupons can not be applied."},
                status=HTTP_400_BAD_REQUEST,
            )

        fare.check_coupon(request.user, coupon)
        return Response(FareBreakupSerializer(fare, many=False).data)

    @extend_schema(
        tags=["Tickets"],
        description="Check and apply coupon applicable on this ticket",
        request=CouponCodeSerializer,
        responses={
            200: OpenApiResponse(
                description="Successful created", response=serializer_class
            )
        },
    )
    @action(detail=True, methods=["POST"], url_path="apply-coupon")
    def apply_coupon(self, request, pk=None):
        # get ticket
        ticket = self.get_object()

        # get coupon code
        coupon_code = request.data.get("code", None)
        is_coupon_valid, coupon = get_coupon_from_code(coupon_code)
        if not is_coupon_valid:
            raise Exception("Coupon code not found.")

        fare = ticket.fare
        fare.apply_coupon(request.user, coupon)
        ticket.refresh_from_db()
        return Response(self.get_serializer(ticket, many=False).data)

    @extend_schema(
        tags=["Tickets"],
        description="Remove all coupons for this ticket",
        request=None,
        responses={
            200: OpenApiResponse(description="Successful", response=serializer_class)
        },
    )
    @action(detail=True, methods=["POST"], url_path="unapply-coupon")
    def unapply_coupon(self, request, pk=None):
        # get ticket
        ticket = self.get_object()
        fare = ticket.fare
        fare.unapply_all_coupons()
        fare.save()
        ticket.refresh_from_db()
        return Response(self.get_serializer(ticket, many=False).data)

    @extend_schema(
        tags=["Tickets"],
        description="Create a new ticket",
        responses={
            200: OpenApiResponse(
                description="Successful created", response=serializer_class
            )
        },
        request=serializer_class,
        examples=[
            OpenApiExample(
                "Example 1",
                summary="With Journey",
                description="Longer description",
                value={
                    "pnr": None,
                    "transaction_id": "string",
                    "phone_number": "9777777777",
                    "start_location_name": "Connaught Place",
                    "start_location_lat": 28.7041,
                    "start_location_lng": 77.1025,
                    "end_location_lat": 28.6129,
                    "end_location_lng": 77.2295,
                    "end_location_name": "India Gate",
                    "transit_option": {
                        "transit_mode": TransitMode.AUTO_RICKSHAW.name,
                        "provider": {"name": NAMMAYATRI_ENUM},
                    },
                    "journey_uuid": "SOMETHING",
                    "journey_leg_index": 2,
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            ),
            OpenApiExample(
                "Example 2",
                summary="Without Journey",
                description="Longer description",
                value={
                    "pnr": None,
                    "transaction_id": "string",
                    "phone_number": "9777777777",
                    "start_location_name": "Connaught Place",
                    "start_location_lat": 28.5450,
                    "start_location_lng": 77.2615,
                    "end_location_lat": 28.6129,
                    "end_location_lng": 77.2295,
                    "end_location_name": "India Gate",
                    "transit_option": {
                        "transit_mode": TransitMode.AUTO_RICKSHAW.name,
                        "provider": {"name": NAMMAYATRI_ENUM},
                    },
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            ),
        ],
    )
    @action(detail=False, methods=["POST"])
    def initiate(self, request):
        # TODO: Refactor to TransitStrategyFactory method to allow for more providers
        try:
            user = get_object_or_404(MyUser, pk=request.user.pk)

            # get transit_option from request
            data = request.data
            transit_option = data.pop("transit_option")
            if "provider" not in transit_option:
                raise Exception("Transit provider not found")

            provider_data = transit_option.pop("provider", None)
            if "name" not in provider_data:
                raise Exception("Transit provider name not found")

            transit_mode = transit_option.pop("transit_mode", None)
            if transit_mode is None:
                raise Exception("Transit mode not found")

            transit_mode_value = TransitMode.get_choice_value(transit_mode)
            logging.info(f"Transit Mode value=====00000====={transit_mode_value}")
            provider_name = provider_data.pop("name", None)
            logging.info(f"Provider Name====1111====={provider_name}")
            provider_obj = get_object_or_404(TransitProvider, name=provider_name)
            logging.info(f"Provider Object====2222====={provider_obj}")
            transit_option_obj = get_object_or_404(
                TransitOption,
                provider=provider_obj,
                transit_mode=transit_mode_value,
            )
            logging.info(f"Transit Option Object====3333====={transit_option_obj}")

            # assert transit option is active
            assert transit_option_obj.is_active_at_datetime()

            # get source destination from request
            transaction_id = data.pop("transaction_id", None)
            pnr = data.pop("pnr", None)
            phone_number = data.pop("phone_number", None)
            start_location_code = data.pop("start_location_code", None)
            start_location_name = data.pop("start_location_name", None)
            start_location_lat = data.pop("start_location_lat", None)
            start_location_lng = data.pop("start_location_lng", None)

            end_location_code = data.pop("end_location_code", None)
            end_location_name = data.pop("end_location_name", None)
            end_location_lat = data.pop("end_location_lat", None)
            end_location_lng = data.pop("end_location_lng", None)

            user_phone_number = f"{transaction_id}:{CACHE_DELIMITER}:user_phone_number"
            cache.set(
                user_phone_number,
                phone_number,
                timeout=TICKET_INITIATE_TRANSACTION_TIMEOUT,
            )
            BPP_ID = os.environ.get("BPP_ID")
            on_search_cache_key = f"{transaction_id}:{BPP_ID}:{CACHE_DELIMITER}:on_search"
            estimate_cache_key = f"{transaction_id}:{BPP_ID}:{CACHE_DELIMITER}:on_estimate"
            cached_estimate_data = cache.get(estimate_cache_key)
            cached_on_search_data = cache.get(on_search_cache_key)
            quotes_array = cached_estimate_data.get("data").get("quotes")
            logging.info(f"Quotes Array=========: {quotes_array}")
            fare = ""
            for quote in quotes_array:
                logging.info(f"Service Type========={quote.get('serviceType').get('name')}")
                transit_mode_name = "AUTO_RICKSHAW" if quote.get("serviceType").get("name") in ["Auto", "Auto Ride"] else None
                logging.info(f"Transit Mode Name====1111====={transit_mode_name}")
                if transit_mode_name == transit_mode:
                    logging.info(f"Transit Mode=====2222===={transit_mode_name == transit_mode}")
                    fare = float(quote.get("totalAmount"))
                    logging.info(f"Fare====3333====={fare}")
                    break
            else:
                response_data = {
                    "message": "Failed",
                    "detail": "No Auto Rides available",
                    "data": None
                }
                return Response(response_data, status=status.HTTP_206_PARTIAL_CONTENT)

            fare_breakup = FareBreakup()

            # TODO: uncomment when testing done
            if not DEBUG:
                if Ticket.objects.filter(
                        created_by=user,
                        transit_option=transit_option_obj,
                        status__in=(TicketStatus.CONFIRMED, TicketStatus.PENDING),
                ).exists():
                    raise Exception(
                        "User already has an active ticket on this transit option"
                    )

                # TODO: uncomment when testing done
                # check for unpaid tickets
                if Ticket.has_unpaid_tickets(user):
                    raise Exception(
                        "User has unpaid ticket. Please pay for the ticket before initiating a new one."
                    )
            try:
                buyer_select.apply_async(args=[cached_on_search_data, transit_mode])  # TODO: Change to transit_mode
                fare_breakup.basic = fare
            except Exception as e:
                raise Exception(f"Estimate API failed. Error: {e}")

            # create fare breakup
            fare_breakup.save()

            # get journey identifier from request, if any
            journey_uuid = data.pop("journey_uuid", None)
            journey = None
            if journey_uuid is not None:
                journey = get_object_or_404(Journey, uuid=journey_uuid)
                if not journey.is_ticket_allowed():
                    raise Exception("Journey is not accepting tickets")

            journey_leg_index = data.pop("journey_leg_index", 0)
            ticket_obj = Ticket.objects.create(
                created_by=user,
                created_for=user,
                fare=fare_breakup,
                pnr=generate_pnr() if pnr is None else pnr,
                start_location_code=start_location_code,
                start_location_name=start_location_name,
                start_location_lat=start_location_lat,
                start_location_lng=start_location_lng,
                end_location_name=end_location_name,
                end_location_code=end_location_code,
                end_location_lat=end_location_lat,
                end_location_lng=end_location_lng,
                transit_option=transit_option_obj,
                transaction_id=transaction_id,
                # transit_pnr=transit_pnr,
                payment_type=PaymentType.POSTPAID,
                journey_leg_index=journey_leg_index,
            )
            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            logging.info(f"PNR to ONDC Transaction ID Key=====: {pnr_to_ondc_transaction_id_key}.......{ticket_obj.pnr}")
            cache.set(
                pnr_to_ondc_transaction_id_key,
                ticket_obj.pnr,
                timeout=TICKET_INITIATE_TRANSACTION_TIMEOUT,
            )

            if journey:
                journey.add_ticket(ticket_obj)

            # if the mode is auto + rapido, send fcm
            if transit_mode_value == TransitMode.AUTO_RICKSHAW and provider_name == NAMMAYATRI_ENUM:
                ticket_obj.send_user_status_notification(title=NammayatriTransitMessages.PAY_DIRECTLY_TO_DRIVER["title"],
                                                         message=NammayatriTransitMessages.PAY_DIRECTLY_TO_DRIVER[
                                                             "message"])
            return Response(self.get_serializer(ticket_obj).data)

        except Exception as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
        # if success, create ticket object with relevant information from transit provider's booking
        # if failure, return error message from transit provider
        # return ticket data

    @extend_schema(
        tags=["Tickets"], description="Ticket confirm status (manual transaction check)"
    )
    @action(detail=True, methods=["GET"], url_path="confirm")
    def confirm(self, request, *args, **kwargs):
        ticket = self.get_object()
        ticket.check_payment_status()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Tickets"], description="Single ticket details")
    def retrieve(self, request, *args, **kwargs):
        ticket_data = super().retrieve(request, *args, **kwargs)
        on_confirm_cache_key = f"{ticket_data.data['transaction_id']}:{CACHE_DELIMITER}:on_confirm"
        on_confirm_data = cache.get(on_confirm_cache_key)
        if on_confirm_data:
            buyer_track.apply_async(args=[on_confirm_data])
        return super().retrieve(request, *args, **kwargs)

    # @extend_schema(tags=["Tickets"], description="Single ticket details")
    # def retrieve(self, request, *args, **kwargs):
    #     DEFAULT_STEP_DISTANCE = 50  # Define the step distance in meters
    #     ticket_data = super().retrieve(request, *args, **kwargs)
    #     logging.info(f"Ticket Data==========={ticket_data.data}")
    #
    #     start_location_lat = float(ticket_data.data["start_location_lat"])
    #     start_location_lng = float(ticket_data.data["start_location_lng"])
    #     end_location_lat = float(ticket_data.data["end_location_lat"])
    #     end_location_lng = float(ticket_data.data["end_location_lng"])
    #
    #     # Use transaction_id or a fallback unique identifier
    #     transaction_id = ticket_data.data.get('transaction_id') or ticket_data.data['pnr']
    #     cache_key = f"{transaction_id}{CACHE_DELIMITER}step"
    #
    #     # Retrieve the current step from the cache
    #     current_step = cache.get(cache_key, 0)
    #
    #     # Calculate the total number of steps
    #     start = (start_location_lat, start_location_lng)
    #     end = (end_location_lat, end_location_lng)
    #     total_distance = geodesic(start, end).kilometers * 1000
    #     step_distance = DEFAULT_STEP_DISTANCE
    #     if total_distance < DEFAULT_STEP_DISTANCE:
    #         step_distance = max(total_distance, 2)  # Use a minimal step distance if necessary
    #
    #     logging.info(f"Total Distance==========={total_distance}")
    #     total_steps = max(1, int(total_distance / step_distance))  # Ensure at least one step
    #     logging.info(f"Total Steps==========={total_steps}")
    #
    #     # Check if we are at the end of the path
    #     if current_step > total_steps:
    #         logging.info("End of path reached")
    #         new_location = None
    #     else:
    #         # Get the new location for the current step
    #         new_location = interpolate_coordinates(
    #             start_location_lat, start_location_lng, end_location_lat, end_location_lng, current_step, total_steps
    #         )
    #         logging.info(f"New location==========={new_location}")
    #
    #         # Increment the step and update the cache
    #         cache.set(cache_key, current_step + 1)
    #
    #     # Prepare the response data
    #     ticket_update_details = {
    #         "status": "ACTIVE",
    #         "location": {
    #             "latitude": str(new_location[0] if new_location else None),
    #             "longitude": str(new_location[1] if new_location else None)
    #         },
    #         "order_id": "order_id",
    #         "timestamp": 1723134720
    #     }
    #     ticket_obj = Ticket.objects.get(pnr=ticket_data.data['pnr'])
    #     ticket_update = TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=False, details=ticket_update_details)
    #     ticket_update.save()
    #     logging.info("Ticket update saved successfully")
    #
    #     # Return a Response object
    #     return super().retrieve(request, *args, **kwargs)
