import requests

from modules.pg.phonepeswitch.common import *


def make_check_status_request(transaction_id):
    base_url = PHONEPE_BASE_URL
    url_suffix = PHONEPE_TRANSACTION_STATUS_URL_SUFFIX

    url_suffix = url_suffix.replace("MID", PHONEPE_MERCHANT_ID)
    url_suffix = url_suffix.replace("TXN_ID", transaction_id)

    final_url = "{}{}".format(base_url, url_suffix)
    # custom_print("final url", final_url)

    request_payload = ""

    X_VERIFY = create_x_verify_hash(request_payload, url_suffix)
    # custom_print("X_VERIFY", X_VERIFY)

    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": X_VERIFY,
        "X-CLIENT-ID": PHONEPE_MERCHANT_ID,
    }

    url = final_url
    response = requests.request("GET", url, headers=headers)
    # custom_print("response.status_code", response.status_code)
    # custom_print("response.json()", response.json())
    return response


if __name__ == "__main__":
    print(make_check_status_request("B17122021e5b0e5de52_00001").json())
    """
	{
		"success": true,
		"code": "PAYMENT_SUCCESS",
		"data": {
			"transactionId": "177f1c2f-ccf5-4c21-88bb-e3087c6e22c3sandip",
			"merchantId": "XXXXXXX",
			"amount": 9300,
			"providerReferenceId": "T2006161957466544984324",
			"paymentState": "COMPLETED",
			"payResponseCode": "SUCCESS"
			}
	}
	"""
