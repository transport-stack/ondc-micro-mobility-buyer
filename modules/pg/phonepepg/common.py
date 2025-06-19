from modules.custom_enums import TransactionStatusEnum
from modules.encoders_encrypters import sha256_encrypt
from modules.env_main import (
    PHONEPE_PG_BASE_URL,
    PHONEPE_PG_KEY_1,
    PHONEPE_PG_KEY_2,
    PHONEPE_PG_MERCHANT_ID,
    PHONEPE_PG_TRANSACTION_INITIATE_URL_SUFFIX,
    PHONEPE_PG_TRANSACTION_STATUS_URL_SUFFIX,
    PHONEPE_PG_UNIQUE_ID,
)

VALIDITY_TIME_IN_MILLI = 900000


def custom_print(key, val, key_length=36):
    formatter_str = "{:<" + str(key_length) + "}: {}"
    # print(formatter_str)
    print(formatter_str.format(key, val))


def create_x_verify_hash(payload, url):
    encrypted_str = sha256_encrypt("{}{}{}".format(payload, url, PHONEPE_PG_KEY_1))
    key_num = 1  # since we used KEY_1 above
    final_x_verify_str = "{}###{}".format(encrypted_str, key_num)
    return final_x_verify_str


# https://developer.phonepe.com/v1/reference/check-transaction-status
TRANSACTION_NOT_FOUND = "TRANSACTION_NOT_FOUND"
BAD_REQUEST = "BAD_REQUEST"
AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
PAYMENT_ERROR = "PAYMENT_ERROR"
PAYMENT_PENDING = "PAYMENT_PENDING"
PAYMENT_DECLINED = "PAYMENT_DECLINED"
PAYMENT_CANCELLED = "PAYMENT_CANCELLED"
TIMED_OUT = "TIMED_OUT"


class PhonePeEnums:
    enums = {
        TRANSACTION_NOT_FOUND: "Payment not initiated inside PhonePe",
        BAD_REQUEST: "Invalid request",
        AUTHORIZATION_FAILED: "X-VERIFY header is incorrect",
        INTERNAL_SERVER_ERROR: "Something went wrong. Merchant needs to call Check Transaction Status to verify the transaction status.",
        PAYMENT_SUCCESS: "Payment is successful or In case of refund - Refund is successful.",
        PAYMENT_ERROR: "Payment failed",
        PAYMENT_PENDING: "Payment is pending. It does not indicate failed payment. Merchant needs to call Check Transaction Status to verify the transaction status.",
        PAYMENT_DECLINED: "Payment declined by user.",
        PAYMENT_CANCELLED: "Payment canceled by the merchant using Cancel API.",
        TIMED_OUT: "The payment failed due to the timeout",
    }

    @staticmethod
    def is_status_success(response_status_code_str):
        try:
            assert response_status_code_str in PhonePeEnums.enums
        except AssertionError as e:
            raise AssertionError(
                "Received status: {} not in pre-defined PhonePe status".format(
                    response_status_code_str
                )
            )
        """
		ref: https://developer.phonepe.com/reference/check-transaction-status-4#section-web-check-transaction-response-parameters
		code	
		ENUM	
		Please see the list of Transaction Status Response Codes below. 
		You should base your decision on this parameter.
		"""
        if response_status_code_str == PAYMENT_SUCCESS:
            _is_status_successful = True
        else:
            _is_status_successful = False

        _status_description = PhonePeEnums.enums[response_status_code_str]
        return _is_status_successful, _status_description

    @staticmethod
    def get_transaction_status_char(response_status_code_str):
        try:
            assert response_status_code_str in PhonePeEnums.enums
        except AssertionError as e:
            raise AssertionError(
                "Received status: {} not in pre-defined PhonePe status".format(
                    response_status_code_str
                )
            )
        """
		ref: https://developer.phonepe.com/reference/check-transaction-status-4#section-web-check-transaction-response-parameters
		code	
		ENUM	
		Please see the list of Transaction Status Response Codes below. 
		You should base your decision on this parameter.
		"""
        if response_status_code_str == PAYMENT_SUCCESS:
            _status_char = TransactionStatusEnum.SUCCESS_CHAR
        elif response_status_code_str in [
            TRANSACTION_NOT_FOUND,
            PAYMENT_ERROR,
            PAYMENT_DECLINED,
            PAYMENT_CANCELLED,
        ]:
            _status_char = TransactionStatusEnum.FAILED_CHAR
        else:
            # mainly this response_status_code_str == PAYMENT_PENDING:
            # otherwise, some issue
            _status_char = TransactionStatusEnum.PENDING_CHAR

        _status_description = PhonePeEnums.enums[response_status_code_str]
        return _status_char, _status_description


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
    print(PhonePeEnums.is_status_success("PAYMENT_ERROR"))
    print(PhonePeEnums.is_status_success("PAYMENT_SUCCESS"))
