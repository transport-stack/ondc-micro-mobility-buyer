import random
import unittest
from unittest import skip

from modules.pg.paytm.wrapper.initiate_transaction_api import InitiateTransaction
from modules.pg.paytm.wrapper.transaction_status_api import OrderStatus, ResultCode


@unittest.skip("Skipping PaytmAPIWrapper: Only to be tested with prod keys")
class TestTransactionStatusIntegration(unittest.TestCase):
    def setUp(self):
        self.initiate_transaction = InitiateTransaction()
        self.order_id = str(random.randint(100000, 999999))
        value = 100.00
        # initiate transaction
        self.initiate_transaction.run(self.order_id, value)

    def test_status_pending(self):
        response = OrderStatus().run(order_id=self.order_id)
        expected_results = [
            ResultCode.PENDING.value,
            ResultCode.PENDING_CONFIRMATION.value,
        ]
        self.assertTrue(response["body"]["resultInfo"]["resultCode"], expected_results)


if __name__ == "__main__":
    unittest.main()
