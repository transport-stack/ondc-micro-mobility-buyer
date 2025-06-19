import random
import unittest

from modules.pg.paytm.wrapper.initiate_transaction_api import (
    InitiateTransaction,
    ResultCode,
)
from modules.pg.paytm.wrapper.process_transaction_api import (
    PayTMPaymentMode,
    ProcessTransaction,
)


@unittest.skip("Skipping PaytmAPIWrapper: Only to be tested with prod keys")
class TestInitiateTransactionUPIIntentIntegration(unittest.TestCase):
    def setUp(self):
        self.initiate_transaction = InitiateTransaction()

    def test_run_success(self):
        order_id = str(random.randint(100000, 999999))
        value = 100.00

        response = self.initiate_transaction.run(order_id, value)
        transaction_token = response["body"]["txnToken"]
        response = ProcessTransaction().run(
            order_id=order_id,
            payment_mode=PayTMPaymentMode.UPI_INTENT,
            transaction_token=transaction_token,
            callback_url=self.initiate_transaction.callback_url
        )

        # Check that the response is a success
        # The actual condition should be replaced with the actual success condition
        self.assertEqual(
            response["body"]["resultInfo"]["resultCode"], ResultCode.SUCCESS.value
        )

    # def test_run_failure(self):
    #     # Here we use an invalid order_id, value, and customer_id
    #     # You should replace these with your own testing values
    #     order_id = "invalid_order"
    #     value = -100.00  # Invalid value
    #
    #     # Please ensure that these transactions do not create actual financial implications
    #     # Ideally, these should be tested against a sandbox or testing environment
    #     response = self.initiate_transaction.run(order_id, value)
    #
    #     # Check that the response indicates a failure
    #     # The actual condition should be replaced with the actual failure condition
    #     self.assertEqual(response["body"]["resultInfo"]["resultCode"], ResultCode.INVALID_TXN_AMOUNT.value)


if __name__ == "__main__":
    unittest.main()
