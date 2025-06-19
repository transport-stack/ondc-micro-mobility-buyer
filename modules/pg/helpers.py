import json

from rest_framework import status

from modules.custom_enums import *
from modules.env_main import (
    CHARTR_WALLET_BACKEND_HOST,
    PAYTM_HOST,
    PAYTM_MERCHANT_ID,
    PHONEPE_PG_BASE_URL,
    PHONEPE_PG_MERCHANT_ID,
)
from modules.logger_main import logger
from modules.pg.paytm.helper_functions import (
    basic_fetch_payment_token as paytm_basic_fetch_payment_token,
)
from modules.pg.paytm.helper_functions import (
    process_upi_intent_request as paytm_process_upi_intent_request,
)
from modules.pg.phonepepg.api import get_debit_request_params
from modules.pg.phonepeswitch.transaction_sdk_less_initiate_api import (
    final_url as phonepe_init_url,
)
from modules.pg.phonepeswitch.transaction_sdk_less_initiate_api import (
    make_initiate_request,
)
from tickets.modules.response_codes import *


def create_transaction_request(
    gateway_order_id,
    gateway_name,
    transaction_status,
    gateway_flow,
    gateway_mode,
    fare,
    _pg_is_paytm,
    _pg_is_phonepe_pg,
    _pg_is_phonepe_switch,
    _pg_is_chartr_wallet,
    redirect_url,
    _split_to_another_vendor,
):
    response_body, response_status = "", status.HTTP_400_BAD_REQUEST

    if _pg_is_paytm:
        if gateway_flow == PaymentFlowTypes.PAYTM_CUSTOM_SDK_API:
            response_data, request_body = paytm_process_upi_intent_request(
                gateway_order_id,
                value=fare,
                _split_to_another_vendor=_split_to_another_vendor,
            )
            response_body = {
                "message": ResponseMessageEnum.SUCCESS,
                "transaction_token": None,
                "mid": PAYTM_MERCHANT_ID,
                "host": PAYTM_HOST,
                "callback_url": request_body["body"]["callbackUrl"],
                "gateway_order_id": gateway_order_id,
                "gateway_name": gateway_name,
                "data": response_data,
            }
            response_status = status.HTTP_200_OK
        else:
            if gateway_flow != PaymentFlowTypes.PAYTM_ALL_IN_ONE_SDK:
                logger.error(
                    "self.gateway_flow != PaymentFlowTypes.PAYTM_ALL_IN_ONE_SDK; transaction_id: {}".format(
                        gateway_order_id
                    )
                )
            response_body = paytm_basic_fetch_payment_token(
                gateway_order_id,
                gateway_name,
                gateway_mode,
                gateway_flow,
                fare,
                redirect_url,
                _split_to_another_vendor=_split_to_another_vendor,
            )
            response_status = status.HTTP_200_OK

    elif _pg_is_phonepe_switch:
        response, request_body = make_initiate_request(
            amount=int(fare * 100),
            transaction_id=gateway_order_id,
            redirect_url=redirect_url,
        )
        try:
            response = response.json()
        except Exception as e:
            raise Exception("response.json() + e")

        if not response["success"]:
            response_body = {"message": "Unable to initiate payment"}
            response_status = status.HTTP_400_BAD_REQUEST

        else:
            response_data = response["data"]
            response_body = {
                "message": ResponseMessageEnum.SUCCESS,
                "transaction_token": None,
                "mid": request_body["merchantId"],
                "host": phonepe_init_url,
                "callback_url": request_body["redirectUrl"],
                "gateway_order_id": gateway_order_id,
                "gateway_name": gateway_name,
                "gateway_mode": gateway_mode,
                "data": response_data,
            }
            response_status = status.HTTP_200_OK
    elif _pg_is_phonepe_pg:
        if gateway_flow == PaymentFlowTypes.PHONEPE_ANDROID_INTENT_SDK:
            base64_payload, checksum, endpoint = get_debit_request_params(
                int(fare * 100), gateway_order_id
            )
            response_data = {
                "encoded_payload": base64_payload,
                "checksum": checksum,
                "endpoint": endpoint,
            }
            response_body = {
                "message": ResponseMessageEnum.SUCCESS,
                "transaction_token": None,
                "mid": PHONEPE_PG_MERCHANT_ID,
                "host": PHONEPE_PG_BASE_URL,
                "callback_url": "",
                "gateway_order_id": gateway_order_id,
                "gateway_name": gateway_name,
                "data": response_data,
            }
            response_status = status.HTTP_200_OK
        elif gateway_flow == PaymentFlowTypes.PHONEPE_ANDROID_CUSTOM_OPEN_INTENT_SDK:
            base64_payload, checksum, endpoint = get_debit_request_params(
                int(fare * 100),
                gateway_order_id,
                PHONEPE_ANDROID_CUSTOM_OPEN_INTENT_SDK=True,
            )
            response_data = {
                "encoded_payload": base64_payload,
                "checksum": checksum,
                "endpoint": endpoint,
            }
            response_body = {
                "message": ResponseMessageEnum.SUCCESS,
                "transaction_token": None,
                "mid": PHONEPE_PG_MERCHANT_ID,
                "host": PHONEPE_PG_BASE_URL,
                "callback_url": "",
                "gateway_order_id": gateway_order_id,
                "gateway_name": gateway_name,
                "data": response_data,
            }
            response_status = status.HTTP_200_OK
    elif _pg_is_chartr_wallet:
        request_data = {}
        response_body = {
            "message": ResponseMessageEnum.SUCCESS,
            "transaction_token": None,
            "mid": None,
            "host": CHARTR_WALLET_BACKEND_HOST,
            "callback_url": None,
            "gateway_order_id": gateway_order_id,
            "gateway_name": gateway_name,
            "data": {},
        }
        response_status = status.HTTP_200_OK

    return response_body, response_status


def classify_paytm_response(paytm_api_response):
    """
    It will classify the paytm response into internal Transaction model's success, pending and failure
    There are cases where PayTM returns incorrect FAILED response but their DB takes time to propagate the actual status
    :param paytm_api_response:
    :return: (status_code, response_data)
    """
    response_code_str = paytm_api_response["RESPCODE"]
    gateway_order_id = None
    try:
        gateway_order_id = paytm_api_response["ORDERID"]
    except Exception as e:
        pass

    _transaction_status_char = TransactionStatusEnum.PENDING_CHAR
    try:
        if (
            response_code_str
            in PaytmTransactionStatusResponseCodesEnum.SUCCESS_CODES_LIST
        ):
            _transaction_status_char = TransactionStatusEnum.SUCCESS_CHAR
        elif (
            response_code_str
            in PaytmTransactionStatusResponseCodesEnum.FAILED_CODES_LIST
        ):
            _transaction_status_char = TransactionStatusEnum.FAILED_CHAR
    except Exception as e:
        logger.error(e)

    logger.debug(
        f"goi: {gateway_order_id}; RESPCODE: {response_code_str}; txn status: {_transaction_status_char}"
    )
    return _transaction_status_char


if __name__ == "__main__":
    classify_paytm_response(
        json.loads(
            '{"splitSettlementInfo":"{"splitMethod":"PERCENTAGE","splitInfo":[{"mid":"LXzykWoo992865578136","percentage":"100"}]}","TXNID":"20230512011110000863763018465412264","BANKTXNID":"","ORDERID":"B1205202397aad6927c_00001","TXNAMOUNT":"18.00","STATUS":"PENDING","TXNTYPE":"SALE","GATEWAYNAME":"PPBL","RESPCODE":"402","RESPMSG":"We are processing your transaction.","MID":"OneDel95091547366725","PAYMENTMODE":"UPI","REFUNDAMT":"0.0","TXNDATE":"2023-05-12 12:45:51.0"}'
        )
    )
