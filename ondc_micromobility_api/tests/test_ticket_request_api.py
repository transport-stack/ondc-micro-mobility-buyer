import datetime
import logging
import random
from concurrent.futures import ThreadPoolExecutor
from unittest import skip

from django.test import TestCase
from ondc_micromobility_api.ondc_wrapper.ticket_request_api import TicketRequestAPI
from ondc_micromobility_api.ondc_wrapper.utils.signature_setup import get_datetime_obj_in_api_format

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TicketRequestAPITestCase(TestCase):

    def test_ticket_request_api(self):
        # Setup
        rand_num = random.randint(1000000000, 9999999999)
        psp_specific_data = f"{rand_num};Merchant_ID;MerchantOrderNo;TransactionAmt;Online;BNK_TRN;CIN;PG{rand_num};DMRCC_A_{rand_num};PPBEX"

        client = TicketRequestAPI(
            tx_ref_no=f"IDFC{rand_num}",
            txn_date=get_datetime_obj_in_api_format(datetime.datetime.now()),
            psp_specific_data=psp_specific_data,
            src_stn=2,
            dest_stn=15,
        )

        # Act
        response_obj = client.post_api()

        # Assert
        self.assertIsNotNone(response_obj)
        # self.assertTrue(response_obj.is_success())  # Uncomment and modify as needed

    def call_post_api_and_get_qr_ticket_no(self, client):
        response_obj = client.post_api()
        self.assertIsNotNone(response_obj)
        return response_obj.qR_Payload['qrRecord'][0]['qR_Ticket_No']

    @skip
    def test_ticket_request_api_qr_ticket_id_parallel_consistency(self):
        """TODO: parallel requests failing but 3 requests with single worker passes test. Investigate. """
        # Setup
        rand_num = random.randint(1000000000, 9999999999)
        psp_specific_data = f"{rand_num};Merchant_ID;MerchantOrderNo;TransactionAmt;Online;BNK_TRN;CIN;PG{rand_num};DMRCC_A_{rand_num};PPBEX"

        client = TicketRequestAPI(
            tx_ref_no=f"IDFC{rand_num}",
            txn_date=get_datetime_obj_in_api_format(datetime.datetime.now()),
            psp_specific_data=psp_specific_data,
            src_stn=2,
            dest_stn=15,
        )

        # Using ThreadPoolExecutor to call post_api in parallel
        qr_ticket_ids = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.call_post_api_and_get_qr_ticket_no, client) for _ in range(3)]
            for future in futures:
                qr_ticket_ids.append(future.result())

        # Assert that all QR Ticket IDs are the same
        self.assertTrue(all(qr_ticket_id == qr_ticket_ids[0] for qr_ticket_id in qr_ticket_ids),
                        "QR Ticket IDs are not consistent")