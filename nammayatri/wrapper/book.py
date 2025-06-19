from ..constants import SERVICE_TYPE_AUTO_STR
from .base import RapidoAPIWrapper

endpoint = "book"


class BookAPI(RapidoAPIWrapper):
    def book(
        self,
        user,
        pickup_location,
        drop_location,
        pin: str,
        service_type=SERVICE_TYPE_AUTO_STR,
        # payment_mode=PAYMENT_MODE,
        metadata={},
    ):
        data = {
            "user": user,
            "pickupLocation": pickup_location,
            "dropLocation": drop_location,
            "serviceType": service_type,
            # "paymentMode": payment_mode,
            "metadata": metadata,
            "pickupOtp": pin,
        }
        return self.post_data(endpoint, data)
