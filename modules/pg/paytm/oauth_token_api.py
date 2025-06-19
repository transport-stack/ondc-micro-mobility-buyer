import base64
import json

import requests
from retry import retry

from modules.env_main import (
    GATEWAY_MODE,
    PAYTM_BASE_URL,
    PAYTM_MERCHANT_ID,
    PAYTM_MERCHANT_KEY,
)
from modules.logger_main import logger
from modules.time_helpers import get_current_time_as_str_hhmmss


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def oauth_token_api():
    response = None
    paytmParams = dict()

    paytmParams["grantType"] = "authorization_code"
    paytmParams["code"] = "999e3877-97c1-XXXX-b19d-6c8787983300"
    paytmParams["deviceId"] = "Device123"

    post_data = json.dumps(paytmParams)

    auth_string = "{}:{}".format(PAYTM_MERCHANT_ID, PAYTM_MERCHANT_KEY)
    authorization_header = base64.b64encode(auth_string.encode("ascii"))
    authorization_header = authorization_header.decode("ascii")

    # for Staging
    if GATEWAY_MODE == "live":
        url = "https://accounts.paytm.com/oauth2/v3/token/sv1/"
    else:
        url = "https://accounts-uat.paytm.com/oauth2/v3/token/sv1/"

    try:
        response = requests.post(
            url,
            data=post_data,
            headers={
                "Authorization": authorization_header,
                "Content-Type": "application/json",
            },
        )

        logger.debug(response)
    except Exception:
        logger.error("couldn't connect to paytm server in fetch_payment_options_api")
        raise

    return response


if __name__ == "__main__":
    # from tickets.modules.paytm_modules.initiate_transaction_api import initiate_transaction_api
    # from tickets.modules.paytm_modules.sendotp_checkout_api import sendotp_checkout_api
    # from tickets.modules.paytm_modules.validateotp_checkout_api import validateotp_checkout_api
    #
    # test_order_id = "LOCAL_TEST_ORDER_{}".format(get_current_time_as_str_hhmmss())
    # test_amount = 1.0
    # test_customer_id = "LOCAL_TEST_CUST_01"
    #
    # # initiating transaction
    # test_response = initiate_transaction_api(
    # 	order_id=test_order_id,
    # 	transaction_amount=test_amount,
    # 	customer_id=test_customer_id
    # )
    # logger.debug("initiate_transaction() called.")
    # logger.debug(test_response)
    #
    # test_transaction_token = test_response["body"]["txnToken"]
    #
    # # sending otp
    # test_mobile_number = "7777777777"
    # sendotp_checkout_api_response = sendotp_checkout_api(
    # 	transaction_token=test_transaction_token,
    # 	mobile_number=test_mobile_number,
    # 	order_id=test_order_id
    #
    # )
    # logger.debug("sendotp_checkout_api() called.")
    # logger.debug(sendotp_checkout_api_response)
    #
    # # validating otp
    # test_otp = "489871"
    # validateotp_checkout_api_response = validateotp_checkout_api(
    # 	transaction_token=test_transaction_token,
    # 	otp=test_otp,
    # 	order_id=test_order_id
    # )
    # logger.debug("validateotp_checkout_api() called.")
    # logger.debug(validateotp_checkout_api_response)

    # getting auth token
    oauth_token_api_response = oauth_token_api()
    logger.debug("oauth_token_api() called.")
    logger.debug(oauth_token_api_response)
