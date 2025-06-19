import json

import requests
from retry import retry

from modules.env_main import PAYTM_BASE_URL, PAYTM_MERCHANT_ID
from modules.logger_main import logger
from modules.pg.paytm.initiate_transaction_api import initiate_transaction_api
from modules.time_helpers import get_current_time_as_str_hhmmss


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def sendotp_checkout_api(transaction_token, mobile_number, order_id):
    paytmParams = dict()
    paytmParams["body"] = {"mobileNumber": mobile_number}

    paytmParams["head"] = {"txnToken": transaction_token}

    post_data = json.dumps(paytmParams)

    url = "{}/login/sendOtp?mid={}&orderId={}".format(
        PAYTM_BASE_URL, PAYTM_MERCHANT_ID, order_id
    )

    response = None
    try:
        response = requests.post(
            url, data=post_data, headers={"Content-type": "application/json"}
        ).json()
    except Exception:
        logger.error("couldn't connect to paytm server in sendotp_checkout_api")
        raise

    return response


if __name__ == "__main__":
    test_order_id = "LOCAL_TEST_ORDER_{}".format(get_current_time_as_str_hhmmss())
    test_amount = 1.0
    test_customer_id = "LOCAL_TEST_CUST_01"
    test_response = initiate_transaction_api(
        order_id=test_order_id,
        transaction_amount=test_amount,
        customer_id=test_customer_id,
    )
    logger.debug("initiate_transaction() called.")
    logger.debug(test_response)

    test_transaction_token = test_response["body"]["txnToken"]
    test_mobile_number = "7777777777"
    otd_response = sendotp_checkout_api(
        transaction_token=test_transaction_token,
        mobile_number=test_mobile_number,
        order_id=test_order_id,
    )

    logger.debug(otd_response)
