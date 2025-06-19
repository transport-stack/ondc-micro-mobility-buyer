from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.cache import cache
import uuid
from ondc_buyer_backend.tasks.buyer_search import buyer_search
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT

class ONDCBuyerEstimateViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def buyer_estimate(self, request):
        try:
            route_id = request.data.get('route_id')
            start_stop_code = request.data.get('start_stop_code')
            end_stop_code = request.data.get('end_stop_code')

            if not all([route_id, start_stop_code, end_stop_code]):
                return Response({"error": "Missing required fields"}, status=400)

            transaction_id = str(uuid.uuid4())
            cache_key = f"{transaction_id}:{CACHE_DELIMITER}:route_id"
            cache.set(cache_key, route_id, timeout=CACHE_TIMEOUT)

            buyer_search_result = buyer_search(transaction_id, start_stop_code, end_stop_code)
            print("buyer_search_result:", buyer_search_result)

            return Response({
                "transaction_id": transaction_id,
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

