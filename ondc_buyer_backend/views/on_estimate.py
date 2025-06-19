import os
from rest_framework import viewsets,status
from rest_framework.response import Response
from django.core.cache import cache

from ondc_buyer_backend.constants import CACHE_DELIMITER


class ONDCBuyerOnEstimateViewSet(viewsets.GenericViewSet):
    def buyer_on_estimate(self,request,*args, **kwargs):
        try:
            # Extract transaction_id from the query parameters
            transaction_id = request.query_params.get("txn_id")
            if not transaction_id:
                return Response({"error": "Transaction ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            BPP_ID = os.environ.get("BPP_ID")
            # Retrieve the fare data from cache
            on_estimate_cache_key = f"{transaction_id}:{BPP_ID}:{CACHE_DELIMITER}:on_estimate"
            fare_data = cache.get(on_estimate_cache_key)

            if fare_data is None:
                return Response({"error": "No data found for the provided transaction ID"}, status=status.HTTP_404_NOT_FOUND)

            # Return the fare data found in cache
            return Response({"status": "success", "fare_data": fare_data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)