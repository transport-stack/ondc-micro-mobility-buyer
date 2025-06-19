from enum import Enum

"""
these values are only for easier management for string values to be used across the project 
"""


class PaymentGatewayEnum(Enum):
    PAYTM = "PAYTM"
    DEFAULT = "DEFAULT"

    @classmethod
    def get_list(cls):
        return [member.value for member in cls]


class PaymentModeEnum(Enum):
    CASH = "CASH"
    NET_BANKING = "NET_BANKING"
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    WALLET = "WALLET"
    NCMC = "NCMC"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def get_list(cls):
        return [member.value for member in cls]
