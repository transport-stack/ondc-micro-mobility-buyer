from typing import Tuple

from modules.logger_main import logger
from modules.pg.paytm.wrapper.base import PaytmAPIWrapper
from modules.time_helpers import get_current_time_as_str_hhmmss


class RefundApplyTransaction(PaytmAPIWrapper):
    def __init__(self):
        super().__init__()

    def run(
        self,
        original_order_id: str,
        refund_id: str,
        value: float,
        transaction_id: str
    ) -> Tuple[dict, dict]:
        paytm_body = {
            "mid": self.merchant_id,
            "txnType": "REFUND",
            "orderId": original_order_id,
            "txnId": transaction_id,
            "refId": refund_id,
            "refundAmount": f"{value}",
        }

        try:
            response = self.post_data(
                f"/refund/apply?mid={self.merchant_id}&orderId={original_order_id}",
                {"body": paytm_body},
                add_checksum=True,
            )
            logger.debug("Refund response: %s", response)
        except Exception as e:
            logger.error("Error in refund_api: %s", e)
            raise

        return response


if __name__ == "__main__":
    refund_transaction = RefundApplyTransaction()
    api_response = refund_transaction.run(
        original_order_id="2311171648532Y24MLLSD",
        refund_id="R{}".format(get_current_time_as_str_hhmmss()),
        value=10,
        transaction_id="20231117010930000932315488422554091",
    )
    logger.debug("refund_api() called.")
    logger.debug("API response: %s", api_response)
