from modules.env_main import PAYTM_HOST, PAYTM_MERCHANT_ID
from modules.logger_main import logger
from modules.pg.paytm.initiate_transaction_api import initiate_transaction_api
from modules.pg.paytm.process_transaction_api import process_transaction_api
from tickets.modules.response_codes import ResponseMessageEnum


def process_upi_intent_request(gateway_order_id, value, _split_to_another_vendor):
    # initiating transaction
    _response, payload = initiate_transaction_api(
        order_id=gateway_order_id,
        transaction_amount=value,
        customer_id=gateway_order_id,
        _split_to_another_vendor=_split_to_another_vendor,
    )
    logger.debug("initiate_transaction() called.")
    logger.debug(_response)

    _transaction_token = _response["body"]["txnToken"]

    # processing transaction
    payment_mode = "UPI_INTENT"

    process_transaction_api_response = process_transaction_api(
        transaction_token=_transaction_token,
        order_id=gateway_order_id,
        payment_mode=payment_mode,
    )
    logger.debug("process_transaction_api() called.")
    logger.debug(process_transaction_api_response)

    return process_transaction_api_response, payload

    # get the pg
    # if paytm, init and process txn
    # if phonepe, return 200OK
    # if upi_intent, init and process transaction and return response
    # if others, return sdk token for respective pg selected
    pass


def basic_fetch_payment_token(
    gateway_order_id,
    gateway_name,
    gateway_mode,
    gateway_flow,
    value,
    redirect_url,
    _split_to_another_vendor,
):
    fare = value
    response_body = ""

    response, request_body = initiate_transaction_api(
        order_id=gateway_order_id,
        transaction_amount=fare,
        disabled_options=None,
        _split_to_another_vendor=_split_to_another_vendor,
    )
    if response["body"]["resultInfo"]["resultStatus"] != "S":
        # response_body = {
        # 	"message": "Unable to initiate payment"
        # }
        # response_status = status.HTTP_400_BAD_REQUEST
        raise Exception("Unable to initiate payment")
    else:
        # paytm transaction END
        transaction_token = response["body"]["txnToken"]
        response_body = {
            "message": ResponseMessageEnum.SUCCESS,
            "transaction_token": transaction_token,
            "mid": PAYTM_MERCHANT_ID,
            "host": PAYTM_HOST,
            "callback_url": request_body["body"]["callbackUrl"],
            "gateway_order_id": gateway_order_id,
            "gateway_name": gateway_name,
        }
    return response_body
