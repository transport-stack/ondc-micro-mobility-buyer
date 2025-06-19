from modules.encoders_encrypters import sha256_encrypt
from modules.env_main import (
    PHONEPE_BASE_URL,
    PHONEPE_KEY_1,
    PHONEPE_KEY_2,
    PHONEPE_MERCHANT_ID,
    PHONEPE_TRANSACTION_INITIATE_URL_SUFFIX,
    PHONEPE_TRANSACTION_STATUS_URL_SUFFIX,
    PHONEPE_UNIQUE_ID,
)

VALIDITY_TIME_IN_MILLI = 900000


def custom_print(key, val, key_length=36):
    formatter_str = "{:<" + str(key_length) + "}: {}"
    # print(formatter_str)
    print(formatter_str.format(key, val))


def create_x_verify_hash(payload, url):
    encrypted_str = sha256_encrypt("{}{}{}".format(payload, url, PHONEPE_KEY_1))
    key_num = 1  # since we used KEY_1 above
    final_x_verify_str = "{}###{}".format(encrypted_str, key_num)
    return final_x_verify_str


# https://developer.phonepe.com/v4/reference#check-status-api
TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
INVALID_TRANSACTION_ID = "INVALID_TRANSACTION_ID"
BAD_REQUEST = "BAD_REQUEST"
AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
PAYMENT_ERROR = "PAYMENT_ERROR"
PAYMENT_PENDING = "PAYMENT_PENDING"
PAYMENT_DECLINED = "PAYMENT_DECLINED"
PAYMENT_CANCELLED = "PAYMENT_CANCELLED"
API_RATE_LIMIT_REACHED = "API_RATE_LIMIT_REACHED"


class PhonePeEnums:
    enums = {
        TRANSACTION_NOT_FOUND: {"description": "Payment not initiated inside PhonePe"},
        INVALID_TRANSACTION_ID: {
            "description": "Transaction ID sent is wrong. Need to send transaction ID as sent in the initiate API"
        },
        BAD_REQUEST: {"description": "Invalid request"},
        AUTHORIZATION_FAILED: {"description": "X-VERIFY header is incorrect"},
        INTERNAL_SERVER_ERROR: {
            "description": "Something went wrong. Merchant needs to call Check Transaction Status to verify the transaction status."
        },
        PAYMENT_SUCCESS: {
            "description": "Payment is successful or In case of refund - Refund is successful."
        },
        PAYMENT_ERROR: {"description": "Payment failed"},
        PAYMENT_PENDING: {
            "description": "Payment is pending. It does not indicate failed payment. Merchant needs to call Check Transaction Status to verify the transaction status."
        },
        PAYMENT_DECLINED: {"description": "Payment declined by user"},
        PAYMENT_CANCELLED: {
            "description": "Payment cancelled by the merchant using Cancel API"
        },
        API_RATE_LIMIT_REACHED: {
            "description": "If the API call limit is breached then HTTP status code 429 would be sent"
        },
    }

    @staticmethod
    def is_status_success(response_status_success_bool, response_status_code_str):
        try:
            assert response_status_code_str in PhonePeEnums.enums
        except AssertionError as e:
            raise AssertionError(
                "Received status: {} not in pre-defined PhonePe status".format(
                    response_status_code_str
                )
            )

        if (
            response_status_code_str == PAYMENT_SUCCESS
            and response_status_success_bool is True
        ):
            _is_status_successful = True
        else:
            _is_status_successful = False

        _status_description = PhonePeEnums.enums[response_status_code_str]
        return _is_status_successful, _status_description


def calculate_mdr(fare, payment_mode):
    _fare_float = float(fare)
    if payment_mode is None:
        return _fare_float, 0.0, 0.0
    elif payment_mode == "UPI":
        return _fare_float, 0.0, 0.0
    elif payment_mode == "DC":
        gateway_fees = round(_fare_float * 0.004, 2)
        gst = round(gateway_fees * 0.18, 2)
        FARE = _fare_float - (gateway_fees + gst)
        return FARE, gateway_fees, gst
    else:
        gateway_fees = _fare_float * 0.0199
        gst = round(gateway_fees * 0.18, 2)
        _fare_float = _fare_float - (gateway_fees + gst)
        return _fare_float, gateway_fees, gst


if __name__ == "__main__":
    print(PhonePeEnums.is_status_success("TRANSACTION_NOT_FOUND"))
