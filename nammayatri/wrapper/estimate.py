from ..constants import SERVICE_TYPE_LIST
from .base import RapidoAPIWrapper

endpoint = "estimate"


class EstimateAPI(RapidoAPIWrapper):
    def estimate(
        self,
        pickup_location,
        drop_location,
        service_type=None,
    ):
        if service_type is None:
            service_type = [SERVICE_TYPE_LIST[0]]
        data = {
            "pickupLocation": pickup_location,
            "dropLocation": drop_location,
            "serviceType": service_type,
        }
        # Get the response from post_data method
        response = self.post_data(endpoint, data)
        response_json = response.json()
        # Check if the necessary keys exist in the response
        if (
            "status" not in response_json
            or "data" not in response_json
            or "quotes" not in response_json["data"]
        ):
            raise Exception("The response does not contain necessary fields.")

        return response
