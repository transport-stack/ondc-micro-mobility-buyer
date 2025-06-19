import json
import logging
from enum import Enum
from typing import Dict

from modules.pg.paytm.wrapper.base import PaytmAPIWrapper

SUCCESS_CODES_LIST = ["01"]
FAILED_CODES_LIST = ["227", "267", "235", "295", "401", "810", "843", "820", "841"]
PENDING_CODES_LIST = ['331', '334', '400', '402', '501']  # all other codes are pending

class ResultCode(Enum):
    TXN_SUCCESS = "01"
    BANK_DECLINED = "227"
    WALLET_INSUFFICIENT = "235"
    INVALID_UPI_ID = "295"
    NO_RECORD_FOUND = "331"
    INVALID_ORDER_ID = "334"
    INVALID_MID = "335"
    PENDING = "400"
    BANK_DECLINED_REPEAT = "401"
    PENDING_CONFIRMATION = "402"
    SERVER_DOWN = "501"
    TXN_FAILED = "810"
    DECLINED_BY_REMITTER_BANK = "841"
    BANK_DECLINED_ACCOUNT_ISSUE = "843"
    MOBILE_NUMBER_CHANGED = "820"
    BANK_GAP_NOT_MAINTAINED = "267"
    INSUFFICIENT_BALANCE = "202"


class ResultStatus(Enum):
    NO_RECORD_FOUND = "NO_RECORD_FOUND"
    TXN_FAILURE = "TXN_FAILURE"
    TXN_SUCCESS = "TXN_SUCCESS"
    PENDING = "PENDING"


class OrderStatus(PaytmAPIWrapper):
    def __init__(self):
        super().__init__()

    def run(self, order_id: str) -> Dict:
        logging.debug("Running get_transaction_status: {}".format(order_id))
        body_parameters = {
            "mid": self.merchant_id,
            "orderId": order_id,
        }

        try:
            response = self.post_data("/v3/order/status", {"body": body_parameters})
            logging.debug("Response from Paytm server: {}".format(response))
        except Exception as e:
            logging.error(
                "Couldn't connect to Paytm server in get_transaction_status. Error: %s",
                e,
            )
            raise

        self.response = None
        return response


if __name__ == "__main__":
    order_id = "2311171648532Y24MLLSD"
    response = OrderStatus().run(order_id=order_id)
    print(response)
