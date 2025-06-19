import json

import requests
from retry import retry

from modules.env_main import PAYTM_BASE_URL, PAYTM_MERCHANT_ID
from modules.logger_main import logger
from modules.time_helpers import get_current_time_as_str_hhmmss


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def process_transaction_api(
    transaction_token, order_id, payment_mode="BALANCE", card_info=""
):
    """

    :param card_info:
    :param transaction_token:
    :param order_id:
    :param payment_mode:
    BALANCE (For Paytm Wallet), UPI , UPI_INTENT , CREDIT_CARD , DEBIT_CARD , NET_BANKING , EMI

    :return:
    """
    paytmParams = dict()
    paytmParams["body"] = {
        "requestType": "NATIVE",
        "mid": PAYTM_MERCHANT_ID,
        "orderId": order_id,
        "paymentMode": payment_mode,
        "authMode": "otp",
    }

    paytmParams["head"] = {"txnToken": transaction_token}

    post_data = json.dumps(paytmParams)

    url = "{}/theia/api/v1/processTransaction?mid={}&orderId={}".format(
        PAYTM_BASE_URL, PAYTM_MERCHANT_ID, order_id
    )

    response = None
    try:
        response = requests.post(
            url, data=post_data, headers={"Content-type": "application/json"}
        ).json()
    except Exception:
        logger.error("couldn't connect to paytm server in process_transaction_api")
        raise

    return response


def test_process_transaction_api_wallet():
    from modules.pg.paytm.fetch_balance_info_api import fetch_balance_info_api
    from modules.pg.paytm.initiate_transaction_api import initiate_transaction_api
    from modules.pg.paytm.sendotp_checkout_api import sendotp_checkout_api
    from modules.pg.paytm.validateotp_checkout_api import validateotp_checkout_api

    test_order_id = "BOCAL_TEST_ORDER_{}".format(get_current_time_as_str_hhmmss())
    test_amount = 1.0
    test_customer_id = "UOCAL_TEST_CUST_01"

    # initiating transaction
    test_response, payload = initiate_transaction_api(
        order_id=test_order_id,
        transaction_amount=test_amount,
        customer_id=test_customer_id,
    )
    logger.debug("initiate_transaction() called.")
    logger.debug(test_response)

    test_transaction_token = test_response["body"]["txnToken"]

    # sending otp
    test_mobile_number = "7777777777"

    # test dev phone number, Atul
    # test_mobile_number = "9625618014"

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

    # fetching balance
    fetch_balance_info_api_response = fetch_balance_info_api(
        transaction_token=test_transaction_token, order_id=test_order_id
    )
    logger.debug("fetch_balance_info_api() called.")
    logger.debug(fetch_balance_info_api_response)

    # processing transaction
    process_transaction_api_response = process_transaction_api(
        transaction_token=test_transaction_token,
        order_id=test_order_id,
        payment_mode="BALANCE",
        card_info="",
    )
    logger.debug("process_transaction_api() called.")
    logger.debug(process_transaction_api_response)


def test_process_transaction_api_upi_intent():
    from modules.pg.paytm.initiate_transaction_api import initiate_transaction_api

    test_order_id = "BOCAL_TEST_ORDER_{}".format(get_current_time_as_str_hhmmss())
    test_amount = 1.0
    test_customer_id = "UOCAL_TEST_CUST_01"

    # initiating transaction
    test_response, payload = initiate_transaction_api(
        order_id=test_order_id,
        transaction_amount=test_amount,
        customer_id=test_customer_id,
    )
    logger.debug("initiate_transaction() called.")
    logger.debug(test_response)

    test_transaction_token = test_response["body"]["txnToken"]

    # processing transaction
    payment_mode = "UPI_INTENT"

    process_transaction_api_response = process_transaction_api(
        transaction_token=test_transaction_token,
        order_id=test_order_id,
        payment_mode=payment_mode,
    )
    logger.debug("process_transaction_api() called.")
    logger.debug(process_transaction_api_response)


if __name__ == "__main__":
    # test_process_transaction_api_wallet()
    test_process_transaction_api_upi_intent()
