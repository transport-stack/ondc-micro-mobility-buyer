import datetime

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from accounts.decorators import X_API_KEY_PARAMETERS
from common.mixins import ViewSetPermissionByMethodMixin
from journey.models.journey_setup import Journey
from journey.serializers.journey_setup import JourneySerializer, JourneySerializerMin
from modules.env_main import DEBUG
from modules.views import XAPIKeyPermission, CustomJSONRenderer
from tickets.models import Ticket


@extend_schema(parameters=X_API_KEY_PARAMETERS)
class JourneyViewSet(
    ViewSetPermissionByMethodMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Journey.objects.filter(active=True).all()
    serializer_class = JourneySerializer
    model = Journey
    lookup_field = "uuid"

    renderer_classes = [
        CustomJSONRenderer,
    ]
    permission_classes = [
        XAPIKeyPermission,
        IsAuthenticated,
    ]
    permission_action_classes = dict(
        create=(),
        retrieve=(),
        list=(),
    )

    def get_queryset(self):
        user = self.request.user
        """
        tickets_exist = Ticket.objects.filter(journeys=OuterRef('pk'))

        return Journey.objects.filter(
            active=True,
            created_for=user
        ).annotate(
            has_ticket=Exists(tickets_exist)
        ).filter(
            has_ticket=True
        )
        """
        results = Journey.objects.filter(active=True, created_for=user, tickets__isnull=False).distinct()
        return results

    @extend_schema(
        tags=["Journey"],
        description="Initiate a journey",
        responses={
            200: OpenApiResponse(
                description="Successful Initiate", response=JourneySerializerMin
            )
        },
        request=JourneySerializerMin,
        examples=[
            OpenApiExample(
                "PTx with Rapido Example",
                summary="PTx with Rapido Example",
                description="Longer description",
                value={
                    "journey_data": '{"created_at":"Wed, 12 Jul 2023 13:39:34 GMT",'
                                    '"destination_stop_name":"Botanical Garden","fare_per_person":"₹126.0 / '
                                    'person","legs":[{"availableOptions":[{"fare":106.0,"name":"bike",'
                                    '"time":5},{"fare":106.0,"name":"auto","time":5}],'
                                    '"color":"#F8CA35","current_status":"pending","description":"On '
                                    'time","distance":3741.0,"end_time":"14:19:24","fare":106.0,'
                                    '"frequency":0,"from_stop":"From My Location","idx":0,"metaInfo":{},'
                                    '"mode":"rapido","mode_info":"","name":"Book Rapido Ride",'
                                    '"otherRoutes":{"otherRoutes":[]},"polyline":"",'
                                    '"start_time":"13:44:31","stops":[{"lat":28.5438133,"lon":77.2718815,'
                                    '"name":"My Location","stop_id":0},{"lat":28.542835,"lon":77.310173,'
                                    '"name":"Kalindi Kunj","stop_id":0}],"termination_description":"",'
                                    '"termination_point":"Till Kalindi Kunj","trip_time":"40",'
                                    '"vehicle_id":"NA"},{"color":"#CC338B","description":"On time",'
                                    '"distance":3370.0,"end_time":"14:24:15","fare":20.0,"frequency":3,'
                                    '"from_stop":"From Kalindi Kunj","idx":1,"metaInfo":{'
                                    '"platform":"Platform No. 1"},"mode":"metro","mode_info":" - Botanical '
                                    'Garden","name":"Board Magenta","otherRoutes":{"otherRoutes":[]},'
                                    '"polyline":"","start_time":"14:20:15","stops":[{"lat":28.542835,'
                                    '"lon":77.310173,"name":"Kalindi Kunj","stop_id":0},{"lat":28.552816,'
                                    '"lon":77.321564,"name":"Okhla Bird Sanctuary","stop_id":0},'
                                    '{"lat":28.564198,"lon":77.334656,"name":"Botanical Garden",'
                                    '"stop_id":0}],"termination_description":"","termination_point":"Exit at '
                                    'Botanical Garden","trip_time":"4","vehicle_id":"NA"}],'
                                    '"reach_by":"14:24:15","request_time":"13:39:31",'
                                    '"source_stop_name":"My Location","total_trip_time":"44 min"}'
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        user = request.user

        # Checks
        # Check if user has any ticket in non-completed state, eg: CANCELLED, EXPIRED
        user_has_incomplete_ticket_bool = Ticket.has_incomplete_tickets(user)
        if not DEBUG:
            if user_has_incomplete_ticket_bool:
                raise Exception(
                    "User already has an active ticket on this transit option."
                )

            # check for unpaid tickets
            if Ticket.has_unpaid_tickets(user):
                raise Exception(
                    "User has unpaid ticket. Please pay for the ticket before initiating a new one."
                )

        # end all active journeys
        Journey.mark_all_previous_journeys_as_completed_for(user)

        # Checks end
        data = request.data
        journey_data = data["journey_data"]

        journey_obj = Journey.objects.create(
            created_by=user,
            created_for=user,
            data=journey_data,
            start_datetime=datetime.datetime.now(),
        )

        return Response(
            status=status.HTTP_200_OK, data=JourneySerializerMin(journey_obj).data
        )

    @extend_schema(tags=["Journey"], description="Single journey details")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(tags=["Journey"], description="Get Journeys of User")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(tags=["Journey"], description="Mark Journey as Ended")
    @action(detail=True, methods=["POST"], url_path="end")
    def end(self, request, *args, **kwargs):
        journey = self.get_object()
        journey.mark_as_completed()
        return super().retrieve(request, *args, **kwargs)
