from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.viewsets import GenericViewSet

from accounts.models.user_setup import MyUser
from common.constants import NoneSerializer
from common.mixins import ViewSetPermissionByMethodMixin
from coupons.calculations import get_coupon_from_code
from coupons.serializers import CouponCodeSerializer
from ondc_micromobility_api.models import MetroStation
from journey.models.journey_setup import Journey
from modules.constants import DMRC_ENUM
from modules.models import TransitMode, PaymentType, TicketStatus
from modules.views import CustomJSONRenderer, CustomPagination
from payments.models.transaction_setup import TransactionSerializer
from tickets.filters import TicketFilter
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_recommendation_setup import TicketRecommendation
from tickets.models.ticket_setup import Ticket, TicketUpdate
from tickets.permissions import IsTicketCreator
from tickets.serializers import (
    TicketSerializer,
    TicketUpdateSerializer,
    FareBreakupSerializer, TicketCancellationSerializer, TicketRecommendationSerializer,
)
from transit.models.transit_setup import TransitProvider, TransitOption
from transit.views.transit_api_interface import TransitApiFactory
import logging
from ondc_micromobility_api.wrapper.estimate import EstimateAPI


class TicketsViewSetWebAPI(
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
    permission_classes = []
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

    @extend_schema(tags=["Tickets", "Web API"], description="Get list of tickets for this user")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        tags=["Tickets", "Web API"],
        description="Cancel this ticket",
        request=TicketCancellationSerializer,
        responses={201: NoneSerializer},
    )
    @action(detail=True, methods=["POST"])
    def cancel(self, request, pk=None):
        ticket_obj = self.get_object()
        cancellation_reason = request.data.get(
            "cancellation_reason", "ORDER_CANCELLED_BY_CUSTOMER"
        )
        ticket_obj.cancel_by_user(cancellation_reason=cancellation_reason)
        ticket_obj.refresh_from_db()
        return Response(TicketSerializer(ticket_obj).data)

    @extend_schema(
        tags=["Tickets", "Web API"],
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
    def updates(self, request, pk=None):
        return Response(
            TicketUpdateSerializer(
                TicketUpdate.objects.filter(ticket=self.get_object()), many=True
            ).data
        )

    @extend_schema(
        tags=["Tickets", "Web API"],
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
                summary="To use default PG's all-in-one SDK call with callback",
                description="",
                value={"payment_mode": "UNKNOWN", "callback": "https://example.com"},
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            ),
            OpenApiExample(
                "Example 2",
                summary="Create UPI deeplink with callback",
                description="",
                value={"payment_mode": "UPI", "callback": "https://example.com"},
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],
    )
    @action(detail=True, methods=["POST"])
    def transaction(self, request, pk=None):
        # TODO: checks if already pending transaction

        # get ticket
        ticket = self.get_object()

        # get payment mode from payload
        payment_mode = request.data.get("payment_mode", None)
        callback_url = request.data.get("callback", None)
        return Response(ticket.create_new_transaction(payment_mode=payment_mode, callback_url=callback_url))

    @extend_schema(
        tags=["Tickets", "Web API"],
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
        tags=["Tickets", "Web API"],
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
        tags=["Tickets", "Web API"],
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
        tags=["Tickets", "Web API"],
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
                    "start_location_code": "ROHINI_SEC_22_TERMINAL",
                    "end_location_code": "AVANTIKA_XING",
                    "transit_option":
                    {
                        "transit_mode": "BUS",
                        "provider":
                        {
                            "name": "ONDC"
                        }
                    },
                    "meta": {
                    "route_id": "102STLDOWN" 
                    }
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
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
            provider_name = provider_data.pop("name", None)
            provider_obj = get_object_or_404(TransitProvider, name=provider_name)
            transit_option_obj = get_object_or_404(
                TransitOption,
                provider=provider_obj,
                transit_mode=transit_mode_value,
            )

            # get source destination from request
            start_location_code = data.pop("start_location_code", None)
            end_location_code = data.pop("end_location_code", None)
            route_id=data.pop("meta", {}).get("route_id", None)


            passenger_count = data.pop("passenger_count", 1)
            transit_api = EstimateAPI()
            # Estimate API

            # order matters
            # with transaction.atomic():
            #     """cancel any last ticket if in pending state"""
            #
            #     # TODO: check if this works fine, is it cancelling all user's tickets or just this user's?
            #     # Lock the ticket row for update
            #     existing_ticket = Ticket.objects.select_for_update().filter(
            #         # created_by=user,
            #         transit_option=transit_option_obj,
            #         status__in=(TicketStatus.PENDING,),
            #     ).first()
            #
            #     if existing_ticket:
            #         # Update the status to cancelled
            #         existing_ticket.cancel_by_user("User re-initiated new ticket")

            # check transit level eligibility, don't allow within 90min as per DMRC rules
            # try:
            #     transit_api.is_eligible(transit_mode_value, pickup_location, drop_location)
            # except Exception as e:
            #     raise e

            # TODO: uncomment when testing done
            # check for unpaid tickets
            # if Ticket.has_unpaid_tickets(user):
            #     raise Exception(
            #         "User has unpaid ticket. Please pay for the ticket before initiating a new one."
            #     )
            
            try:
                # get fare estimate for single passenger
                response_obj = transit_api.estimate_wrapper(
                    route_id, start_location_code, end_location_code
                )
                logging.info("response_obj=================%s",response_obj)

                # multiply by passenger count
                fare_breakup = FareBreakup()
                fare_breakup.basic = 10
                fare_breakup.save()
            except Exception as e:
                raise Exception(f"Estimate API failed. Error: {e}")

            journey_leg_index = data.pop("journey_leg_index", 0)

            ticket_obj = Ticket.objects.create(
                # created_by=user,
                # created_for=user,
                passenger_count=passenger_count,
                fare=fare_breakup,
                start_location_code=start_location_code,
                end_location_code=end_location_code,
                transit_option=transit_option_obj,
                journey_leg_index=journey_leg_index,
                payment_type=PaymentType.PREPAID,
            )

            # get journey identifier from request, if any
            journey_uuid = data.pop("journey_uuid", None)
            if journey_uuid is not None:
                journey = get_object_or_404(Journey, uuid=journey_uuid)
                journey.add_ticket(ticket_obj)

            return Response(self.get_serializer(ticket_obj).data)

        except Exception as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)
        # if success, create ticket object with relevant information from transit provider's booking
        # if failure, return error message from transit provider
        # return ticket data

    @extend_schema(
        tags=["Tickets", "Web API"], description="Ticket confirm status (manual transaction check)"
    )
    @action(detail=True, methods=["GET"], url_path="confirm")
    def confirm(self, request, *args, **kwargs):
        ticket = self.get_object()
        ticket.check_transit_provider_ticket_status()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Tickets", "Web API"], description="Single ticket details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Tickets", "Web API"],
        description="List of recommended tickets for the user",
        parameters=[
            OpenApiParameter(
                name="x-api-key",
                description="API key",
                required=True,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
            ),
            OpenApiParameter(
                name="start_location_code",
                description="Start location code",
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
        ],
        examples=[
            OpenApiExample(
                "Example without start_location_code",
                summary="Example without start_location_code",
                request_only=True,
                value={"start_location_code": None}
            ),
            OpenApiExample(
                "Example with start_location_code",
                summary="Example with start_location_code",
                request_only=True,
                value={"start_location_code": "112"}
            )
        ]
    )
    @action(detail=False, methods=["GET"], url_path="recommendations")
    def recommendations(self, request, *args, **kwargs):
        """
        Returns a list of recommendations for the user
        """
        user = request.user
        start_location_code = request.query_params.get('start_location_code', None)

        return Response(
            TicketRecommendationSerializer(
                TicketRecommendation.get_top_recommendations(
                    user,
                    start_location_code=start_location_code
                ), many=True).data)
