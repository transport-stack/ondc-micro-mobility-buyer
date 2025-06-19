from modules.pg.phonepepg.api import make_refund_request
from modules.pg.phonepepg.common import PAYMENT_SUCCESS
from modules.pg.phonepepg.transaction_check_status_api import (
    make_check_status_request_phonepe_pg,
)

transaction_ids_list = ["B140620220ba7b2be34_00001", "B14062022b061a3726b_00001"]


for tid_str in transaction_ids_list:
    response_dict = make_check_status_request_phonepe_pg(tid_str).json()
    can_refund = False
    amount = 0
    if "code" in response_dict and response_dict["code"] == PAYMENT_SUCCESS:
        providerReferenceId = response_dict["data"]["providerReferenceId"]
        amount = response_dict["data"]["amount"]
        can_refund = True

    if can_refund:
        make_refund_request(
            transaction_id=tid_str,
            provider_reference_id=providerReferenceId,
            amount=amount,
            salt_key_index=1,
        )
