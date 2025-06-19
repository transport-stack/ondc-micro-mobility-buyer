import json

import requests
from paytmchecksum import PaytmChecksum
from retry import retry

from modules.env_main import (
    PAYTM_BASE_URL,
    PAYTM_MERCHANT_ID,
    PAYTM_MERCHANT_KEY,
    PAYTM_WEBSITENAME,
)
from modules.logger_main import logger
from modules.time_helpers import get_current_time_as_str_hhmmss


# @retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def bank_transfer_api(order_id, transaction_amount, customer_id=None):
    paytmParams = dict()
    # paytmParams = {
    # 	"beneficiaryAccount": "919899996782",
    # 	"beneficiaryIFSC": "PYTM0123456",
    # 	"orderId": order_id,
    # 	"subwalletGuid": "65c6fb00-85fa-11e9-af8f-fa163e429e83",
    # 	"amount": "1.00",
    # 	"purpose": "BONUS",
    # 	"date": "2020-02-13"
    # }

    paytmParams["subwalletGuid"] = "65c6fb00-85fa-11e9-af8f-fa163e429e83"
    paytmParams["orderId"] = order_id
    paytmParams["beneficiaryAccount"] = "919899996782"
    paytmParams["beneficiaryIFSC"] = "PYTM0123456"
    paytmParams["amount"] = "1.00"
    paytmParams["purpose"] = "BONUS"
    paytmParams["date"] = "2021-02-14"

    # for Staging
    url = "https://staging-dashboard.paytm.com/bpay/api/v1/disburse/order/bank"

    post_data = json.dumps(paytmParams)
    checksum = PaytmChecksum.generateSignature(post_data, PAYTM_MERCHANT_KEY)

    # url = PAYTM_BASE_URL + "/bpay/api/v1/disburse/order/bank"

    response = None
    try:
        response = requests.post(
            url,
            data=post_data,
            headers={
                "Content-type": "application/json",
                "x-mid": PAYTM_MERCHANT_ID,
                "x-checksum": checksum,
            },
        ).json()
    except Exception:
        logger.error("couldn't connect to paytm server in bank_transfer_api")
        raise
    return response


if __name__ == "__main__":
    test_gateway_order_id = "LOCAL_TEST_ORDER_{}".format(
        get_current_time_as_str_hhmmss()
    )
    test_amount = 1.0
    test_customer_id = "LOCAL_TEST_CUST_01"
    test_response = bank_transfer_api(
        order_id=test_gateway_order_id,
        transaction_amount=test_amount,
        customer_id=test_customer_id,
    )
    logger.debug("type of response = {}".format(type(test_response)))
    logger.debug(test_response)
