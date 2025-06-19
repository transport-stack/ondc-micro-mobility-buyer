import json

import requests
from paytmchecksum import PaytmChecksum
from retry import retry

from modules.env_main import PAYTM_BASE_URL, PAYTM_MERCHANT_ID, PAYTM_MERCHANT_KEY
from modules.logger_main import logger
from modules.time_helpers import get_current_time_as_str_hhmmss


@retry(Exception, tries=3, delay=2, backoff=2, max_delay=10, logger=logger)
def refund_api(original_order_id, refund_id, value, transaction_id):
    paytmParams = dict()
    # TODO: if transaction_id is None, get it from status API

    paytmParams["body"] = {
        "mid": PAYTM_MERCHANT_ID,
        "txnType": "REFUND",
        "orderId": original_order_id,
        "txnId": transaction_id,
        "refId": refund_id,
        "refundAmount": "{}".format(value),
    }

    # Generate checksum by parameters we have in body
    # Find your Merchant Key in your Paytm Dashboard at https://dashboard.paytm.com/next/apikeys
    checksum = PaytmChecksum.generateSignature(
        json.dumps(paytmParams["body"]), PAYTM_MERCHANT_KEY
    )

    paytmParams["head"] = {"signature": checksum}

    post_data = json.dumps(paytmParams)
    url = "{}/refund/apply".format(PAYTM_BASE_URL)

    response = None
    logger.debug("post_data: {}".format(post_data))

    try:
        response = requests.post(
            url, data=post_data, headers={"Content-type": "application/json"}
        ).json()
    except Exception:
        logger.error("couldn't connect to paytm server in refund_api")
        raise
    print(response)
    return response


if __name__ == "__main__":
    api_response = refund_api(
        original_order_id="B22062022294dfb1bba_00001",
        refund_id="R{}".format(get_current_time_as_str_hhmmss()),
        value=4.5,
        transaction_id="20220622111212800110168871561292217",
    )
    logger.debug("refund_api() called.")
    logger.debug(api_response)
