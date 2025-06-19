# Create your views here.
import logging
import os

from django.core.cache import cache
from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import serializers, status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from accounts.decorators import X_API_KEY_PARAMETERS
from accounts.models import MyUser
from journey.models import Journey
from modules.constants import NAMMAYATRI_ENUM
from modules.models import PaymentType, TransitMode
from modules.views import CustomJSONRenderer, XAPIKeyPermission
from nammayatri.serializers import BookRequestSerializer
from nammayatri.wrapper.book import BookAPI
from ondc_buyer_backend.constants import CACHE_DELIMITER
from ondc_buyer_backend.tasks.buyer_select import buyer_select
from tickets.constants import TICKET_INITIATE_TRANSACTION_TIMEOUT
from tickets.models import Ticket
from tickets.models.fare_setup import FareBreakup
from transit.models.transit_setup import TransitProvider, TransitOption


class BookView(APIView):
    serializer_class = BookRequestSerializer
    renderer_classes = [CustomJSONRenderer]
    permission_classes = [
        XAPIKeyPermission,
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["NammaYatri_API"],
        parameters=X_API_KEY_PARAMETERS,
        responses={
            200: OpenApiResponse(
                description="Successful request.", response=serializer_class
            )
        },
        request=serializer_class,
    )
    def post(self, request, format=None):
        serializer = BookRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            transaction_id = data.get("transaction_id")
            pickup_location = data.get("pickupLocation")
            drop_location = data.get("dropLocation")
            start_location_lat = pickup_location.get("lat")
            start_location_lng = pickup_location.get("lng")
            end_location_lat = drop_location.get("lat")
            end_location_lng = drop_location.get("lng")
            journey_leg_index = data.pop("journey_leg_index", 0)
            # Save users phone number in cache
            phone_number = data.get("user").get("mobile")
            vehicle = data.get("serviceType")
            phone_number_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:phone_number"
            cache.set(phone_number_cache_key, phone_number)
            BPP_ID = os.environ.get("BPP_ID")
            # fetch on_search data and vehicle from cache
            on_search_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_search"
            estimate_cache_key = f"{transaction_id}:{BPP_ID}:{CACHE_DELIMITER}:on_estimate"
            cached_estimate_data = cache.get(estimate_cache_key)
            cached_on_search_data = cache.get(on_search_cache_key)
            user = get_object_or_404(MyUser, pk=request.user.pk)
            quotes_array = cached_estimate_data.get("data").get("quotes")
            logging.info(f"Quotes Array=========: {quotes_array}")
            fare = ""
            for quote in quotes_array:
                if quote.get("serviceType").get("code") == vehicle:
                    fare = quote.get("totalAmount")
                    break
            provider_name = NAMMAYATRI_ENUM
            transit_mode_value = TransitMode.get_choice_value(vehicle)
            provider_obj = get_object_or_404(TransitProvider, name=provider_name)
            transit_option_obj = get_object_or_404(
                TransitOption,
                provider=provider_obj,
                transit_mode=transit_mode_value,
            )
            # Create a ticket for the ride
            fare_breakup = FareBreakup()
            fare_breakup.basic = float(fare)
            fare_breakup.save()

            ticket_obj = Ticket.objects.create(
                created_by=user,
                created_for=user,
                passenger_count=1,
                vehicle_number="",
                fare=fare_breakup,
                # start_location_code=start_location_code,
                # start_location_name=start_location_name,
                start_location_lat=start_location_lat,
                start_location_lng=start_location_lng,
                # end_location_name=end_location_name,
                # end_location_code=end_location_code,
                end_location_lat=end_location_lat,
                end_location_lng=end_location_lng,
                transit_option=transit_option_obj,
                journey_leg_index=journey_leg_index,
                payment_type=PaymentType.POSTPAID,
            )
            journey_uuid = data.pop("journey_uuid", None)
            if journey_uuid is not None:
                journey = get_object_or_404(Journey, uuid=journey_uuid)
                journey.add_ticket(ticket_obj)

            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            cache.set(pnr_to_ondc_transaction_id_key, ticket_obj.pnr, timeout=TICKET_INITIATE_TRANSACTION_TIMEOUT)

            # Execute the buyer_select task with the on_search and vehicle data
            buyer_select.apply_async(args=[cached_on_search_data, vehicle])

            # assuming response.json() returns a dictionary
            return Response("ACK", status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
