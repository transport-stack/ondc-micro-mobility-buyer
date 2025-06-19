import datetime

import jwt
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.viewsets import GenericViewSet

from accounts.models.user_setup import MyUser
from common.mixins import ViewSetPermissionByMethodMixin
from ondc_micromobility_api.models import MetroStation
from journey.models.journey_setup import Journey
from modules.constants import DMRC_ENUM
from modules.models import TransitMode, PaymentType
from modules.views import CustomJSONRenderer, CustomPagination
from payments.models.transaction_setup import TransactionSerializer
from tickets.filters import TicketFilter
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import Ticket
from tickets.permissions import IsCreatedWithinSameDay, HasValidTicketToken
from tickets.serializers import (
    TicketSerializer,
)
from transit.models.transit_setup import TransitProvider, TransitOption
from transit.views.transit_api_interface import TransitApiFactory


class PerMinuteThrottle(AnonRateThrottle):
    rate = '30/min'


def create_token_for_ticket(ticket: Ticket):
    # Create a JWT token
    token_expiry_hours = 4  # Set this to desired number of hours
    expiry_time = timezone.now() + datetime.timedelta(hours=token_expiry_hours)

    ticket_data = {
        'pnr': ticket.pnr,
        'exp': expiry_time
    }

    token = jwt.encode(ticket_data, settings.SECRET_KEY, algorithm='HS256')
    return token


OpenApiParameterHeader = OpenApiParameter(
    name="X-Ticket-Token",
    description="Ticket access token",
    required=True,
    type=str,
    location=OpenApiParameter.HEADER
)


class TicketsViewSetWebV2API(
    ViewSetPermissionByMethodMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
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
        retrieve=(HasValidTicketToken, IsCreatedWithinSameDay,),
        # list=(IsTicketCreator,),
        # cancel=(IsTicketCreator,),
        # updates=(IsTicketCreator,),
        transaction=(HasValidTicketToken,),
        confirm=(HasValidTicketToken,),
        update=(HasValidTicketToken,),
        initiate=(),
    )
    pagination_class = CustomPagination
    throttle_classes = [PerMinuteThrottle]

    # def get_queryset(self):
    #     user = self.request.user
    #     return Ticket.objects.filter(active=True, created_for=user)

    @extend_schema(
        tags=["Tickets", "Web V2 API"],
        description="Initiate transaction for this ticket",
        request=TransactionSerializer,
        responses={
            200: OpenApiResponse(
                description="Successful fetch", response=TransactionSerializer
            )
        },
        parameters=[OpenApiParameterHeader],
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
        tags=["Tickets", "Web V2 API"],
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
                    "passenger_count": 3,
                    "start_location_code": "2",
                    "start_location_name": "Rohini West",
                    "end_location_code": "63",
                    "end_location_name": "Paschim Vihar (East)",
                    "transit_option": {
                        "transit_mode": TransitMode.METRO.name,
                        "provider": {"name": DMRC_ENUM},
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
        # TODO: create a ticket access token that will be used to access the ticket or update user
        try:
            if request.user.is_anonymous:
                user = None
            else:
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

            # assert transit option is active
            assert transit_option_obj.is_active_at_datetime()

            # get source destination from request
            start_location_code = data.pop("start_location_code", None)
            start_location_name = data.pop("start_location_name", None)

            try:
                start_location_metro_station = MetroStation.objects.get(station_id=int(start_location_code))
                start_location_name = start_location_metro_station.name
                start_location_metro_station_lat = start_location_metro_station.lat
                start_location_metro_station_lon = start_location_metro_station.lon
            except Exception as e:
                start_location_metro_station_lat = None
                start_location_metro_station_lon = None

            start_location_lat = data.pop("start_location_lat", start_location_metro_station_lat)
            start_location_lng = data.pop("start_location_lng", start_location_metro_station_lon)

            end_location_code = data.pop("end_location_code", None)
            end_location_name = data.pop("end_location_name", None)

            try:
                # TODO: cache these objects for faster lookup
                end_location_metro_station = MetroStation.objects.get(station_id=int(end_location_code))
                end_location_name = end_location_metro_station.name
                end_location_metro_station_lat = end_location_metro_station.lat
                end_location_metro_station_lon = end_location_metro_station.lon
            except Exception as e:
                end_location_metro_station_lat = None
                end_location_metro_station_lon = None
            end_location_lat = data.pop("end_location_lat", end_location_metro_station_lat)
            end_location_lng = data.pop("end_location_lng", end_location_metro_station_lon)

            # both will be string IDs of stops
            pickup_location = start_location_code
            drop_location = end_location_code

            passenger_count = data.pop("passenger_count", 1)

            transit_api = TransitApiFactory(provider_name)
            # Estimate API
            fare_breakup = FareBreakup()

            try:
                # get fare estimate for single passenger
                response_obj = transit_api.estimate(
                    transit_mode_value, pickup_location, drop_location
                )

                # multiply by passenger count
                fare_breakup.basic = response_obj.get_fare_inr() * passenger_count
            except Exception as e:
                raise Exception(f"Estimate API failed. Error: {e}")

            fare_breakup.save()

            journey_leg_index = data.pop("journey_leg_index", 0)
            ticket_obj = Ticket.objects.create(
                created_by=user,
                created_for=user,
                passenger_count=passenger_count,
                fare=fare_breakup,
                start_location_code=start_location_code,
                start_location_name=start_location_name,
                start_location_lat=start_location_lat,
                start_location_lng=start_location_lng,
                end_location_name=end_location_name,
                end_location_code=end_location_code,
                end_location_lat=end_location_lat,
                end_location_lng=end_location_lng,
                transit_option=transit_option_obj,
                journey_leg_index=journey_leg_index,
                payment_type=PaymentType.PREPAID,
            )

            jwt_token = create_token_for_ticket(ticket_obj)

            # get journey identifier from request, if any
            journey_uuid = data.pop("journey_uuid", None)
            if journey_uuid is not None:
                journey = get_object_or_404(Journey, uuid=journey_uuid)
                journey.add_ticket(ticket_obj)

            response_data = self.get_serializer(ticket_obj).data
            response_data["jwt_token"] = jwt_token
            return Response(response_data, status=HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Tickets", "Web V2 API"], description="Ticket confirm status (manual transaction check)",
        parameters=[OpenApiParameterHeader],
    )
    @action(detail=True, methods=["GET"], url_path="confirm")
    def confirm(self, request, *args, **kwargs):
        ticket = self.get_object()
        ticket.check_transit_provider_ticket_status()
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        tags=["Tickets", "Web V2 API"],
        description="Single ticket details",
        parameters=[OpenApiParameterHeader],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    # end point to update a user with ticket
    @extend_schema(
        tags=["Tickets", "Web V2 API"],
        description="Update ticket",
        request=None,
        parameters=[OpenApiParameterHeader],
        examples=[
            OpenApiExample(
                "Example 1",
                summary="Update User (If not already present)",
                description="Longer description",
                value={},
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],

    )
    def update(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            raise Exception("User not found")

        ticket = self.get_object()
        if ticket.created_for is None:
            ticket.created_for = user
            ticket.created_by = user
            ticket.save()
        else:
            raise Exception("Ticket already created for another user")

        return super().retrieve(request, *args, **kwargs)
