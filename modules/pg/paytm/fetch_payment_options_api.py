import json

import requests
from retry import retry

from modules.env_main import PAYTM_BASE_URL, PAYTM_MERCHANT_ID
from modules.logger_main import logger
from modules.time_helpers import get_current_time_as_str_hhmmss


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def fetch_payment_options_api(transaction_token, order_id):
    paytmParams = dict()
    paytmParams["head"] = {"txnToken": transaction_token}

    post_data = json.dumps(paytmParams)

    url = "{}/fetchPaymentOptions?mid={}&orderId={}".format(
        PAYTM_BASE_URL, PAYTM_MERCHANT_ID, order_id
    )

    response = None
    try:
        response = requests.post(
            url, data=post_data, headers={"Content-type": "application/json"}
        ).json()
    except Exception:
        logger.error("couldn't connect to paytm server in fetch_payment_options_api")
        raise

    return response


if __name__ == "__main__":
    from modules.pg.paytm.initiate_transaction_api import initiate_transaction_api
    from modules.pg.paytm.sendotp_checkout_api import sendotp_checkout_api
    from modules.pg.paytm.validateotp_checkout_api import validateotp_checkout_api

    test_order_id = "LOCAL_TEST_ORDER_{}".format(get_current_time_as_str_hhmmss())
    test_amount = 1.0
    test_customer_id = "LOCAL_TEST_CUST_01"

    # initiating transaction
    test_response, request_body = initiate_transaction_api(
        order_id=test_order_id,
        transaction_amount=test_amount,
        customer_id=test_customer_id,
    )
    logger.debug("initiate_transaction() called.")
    logger.debug(test_response)

    test_transaction_token = test_response["body"]["txnToken"]

    # sending otp
    test_mobile_number = "7777777777"
    sendotp_checkout_api_response = sendotp_checkout_api(
        transaction_token=test_transaction_token,
        mobile_number=test_mobile_number,
        order_id=test_order_id,
    )
    logger.debug("sendotp_checkout_api() called.")
    logger.debug(sendotp_checkout_api_response)

    # validating otp
    test_otp = "489871"
    validateotp_checkout_api_response = validateotp_checkout_api(
        transaction_token=test_transaction_token, otp=test_otp, order_id=test_order_id
    )
    logger.debug("validateotp_checkout_api() called.")
    logger.debug(validateotp_checkout_api_response)

    # fetching payment options
    fetch_payment_options_api_response = fetch_payment_options_api(
        transaction_token=test_transaction_token, order_id=test_order_id
    )
    logger.debug("fetch_payment_options_api() called.")
    logger.debug(fetch_payment_options_api_response)
