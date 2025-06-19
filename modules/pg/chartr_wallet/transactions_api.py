import requests

from modules.env_main import CHARTR_WALLET_BACKEND_API_KEY, CHARTR_WALLET_BACKEND_HOST
from modules.logger_main import logger
from tickets.modules.response_codes import *


def check_txn_status_main(order_id):
    logger.debug(
        "TransactionComplete.checkTransactionStatus called for order_id: {OI}".format(
            OI=order_id
        )
    )

    url = "{}/transactions/{}/".format(CHARTR_WALLET_BACKEND_HOST, order_id)

    payload = ""
    headers = {"x-api-key": CHARTR_WALLET_BACKEND_API_KEY}

    try:
        response = requests.request("GET", url, headers=headers)
        response_body = response.json()

        _is_transaction_success = False
        _transaction_pk = -2
        _transaction_response_msg = None
        try:
            if (
                response_body["status"] == ResponseMessageEnum.SUCCESS
                and response_body["data"]["transact_status"] == "S"
            ):
                _is_transaction_success = True
                _transaction_pk = response_body["data"]["pk"]
                _transaction_response_msg = response_body["description"]
        except Exception as e:
            logger.debug("wallet txn status check > exception, e: {}".format(e))
            _transaction_response_msg = response_body["description"]

        logger.debug(
            str(response_body)
            + " for order_id: {}, status: {}".format(order_id, _is_transaction_success)
        )
    except Exception as e:
        logger.debug(
            "call to {url} FAILED for order_id: {OI} with error {e}".format(
                url=url, OI=order_id, e=str(e)
            )
        )
        raise

    return _is_transaction_success, _transaction_pk, _transaction_response_msg


if __name__ == "__main__":
    print(check_txn_status_main(order_id="B1203202250b8fc4349_00001"))
