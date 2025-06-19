# Create your views here.
import logging
import uuid
from django.core.cache import cache
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.decorators import X_API_KEY_PARAMETERS
from common.constants import NoneSerializer
from ondc_micromobility_api.wrapper.estimate import EstimateAPI
from modules.views import CustomJSONRenderer
from ondc_micromobility_api.serializers import EstimateRequestSerializer
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.tasks.buyer_search import buyer_search


class EstimateView(APIView):
    serializer_class = EstimateRequestSerializer
    renderer_classes = [CustomJSONRenderer]

    # @extend_schema(
    #     tags=["Delhi_Bus_Ticketing_API"],
    #     parameters=X_API_KEY_PARAMETERS,
    #     responses={
    #         200: OpenApiResponse(
    #             description="Successful estimate", response=NoneSerializer
    #         )
    #     },
    #     request=serializer_class,
    #     examples=[
    #         OpenApiExample(
    #             "Example 1",
    #             summary="Summary",
    #             description="Longer description",
    #             value={
    #                   "transaction_id": None,
    #                   "pickupLocation": {
    #                     "lat": 28.7041,
    #                     "lng": 77.1025
    #                   },
    #                   "pickupAddress": "Connaught Place",
    #                   "dropLocation": {
    #                     "lat": 28.6129,
    #                     "lng": 77.2295
    #                   },
    #                   "dropAddress": "India Gate",
    #                   "vehicle": "AUTO_RICKSHAW"
    #                 },
    #             request_only=True,
    #             response_only=False,
    #         )
    #     ],
    # )
    def post(self, request):
        try:
            data = request.data
            pickupLocation = data.get("pickupLocation")
            formatted_pickup_location = f"{pickupLocation.get('lat')}, {pickupLocation.get('lng')}"
            pickupAddress = data.get("pickupAddress")
            dropLocation = data.get("dropLocation")
            formatted_drop_location = f"{dropLocation.get('lat')}, {dropLocation.get('lng')}"
            dropAddress = data.get("dropAddress")
            transaction_id_in_estimate = data.get("transaction_id")
            transaction_id = str(uuid.uuid4())

            logging.info(
                f"Data in API view: transaction_id={transaction_id}, pickupLocation={pickupLocation}, "
                f"pickupAddress={pickupAddress}, dropLocation={dropLocation}, "
                f"dropAddress={dropAddress}"
            )

            on_estimate_cache_key = f"{transaction_id_in_estimate}:{CACHE_DELIMITER}:on_estimate"
            fare = cache.get(on_estimate_cache_key)

            empty_fare = {
                    "requestId": transaction_id if transaction_id_in_estimate is None else transaction_id_in_estimate,
                    "rideTime": None,
                    "timeUnit": None,
                    "rideDistance": None,
                    "distanceUnit": None,
                    "quotes": None
            }

            if transaction_id_in_estimate is None and fare is None:
                logging.info(f"Calling buyer_search task with transaction_id: {transaction_id}, {transaction_id_in_estimate}, {fare}")
                buyer_search.apply_async(
                    args=[transaction_id, formatted_pickup_location, pickupAddress, formatted_drop_location, dropAddress]
                )
                return Response(empty_fare, status=status.HTTP_206_PARTIAL_CONTENT)
            elif transaction_id_in_estimate and fare is not None:
                return Response(fare['data'], status=status.HTTP_200_OK)
            else:
                logging.error("Fare not fetched.")
                return Response(empty_fare, status=status.HTTP_206_PARTIAL_CONTENT)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return Response({"description": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
