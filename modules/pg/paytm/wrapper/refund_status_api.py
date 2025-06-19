from typing import Tuple

from modules.pg.paytm.wrapper.base import PaytmAPIWrapper
from modules.logger_main import logger


class RefundStatusTransaction(PaytmAPIWrapper):
    def __init__(self):
        super().__init__()

    def run(self, original_order_id: str, refund_id: str) -> Tuple[dict, dict]:
        paytm_body = {
            "mid": self.merchant_id,
            "orderId": original_order_id,
            "refId": refund_id,
        }

        try:
            response = self.post_data(
                "/v2/refund/status",
                {"body": paytm_body},
                add_checksum=True
            )
            logger.debug("Refund status response: %s", response)
        except Exception as e:
            logger.error("Error in refund_status_api: %s", e)
            raise

        return response


if __name__ == "__main__":
    refund_status = RefundStatusTransaction()
    api_response = refund_status.run(
        original_order_id="B22062022294dfb1bba_00001",
        refund_id="R000506"
    )
    logger.debug("refund_status_api() called.")
    logger.debug("API response: %s", api_response)
