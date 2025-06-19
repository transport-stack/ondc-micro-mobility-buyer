from .base import RapidoAPIWrapper

endpoint = "cancel"


class CancelAPI(RapidoAPIWrapper):
    def cancel(self, order_id, cancel_reason):
        data = {"orderId": order_id, "cancelReason": cancel_reason}

        return self.post_data(endpoint, data)
