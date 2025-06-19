import logging
from time import sleep

from django.core.cache import cache

from ondc_buyer_backend.constants import CACHE_DELIMITER
from ondc_buyer_backend.tasks.buyer_confirm import buyer_confirm
from tickets.constants import TICKET_INITIATE_TRANSACTION_TIMEOUT

endpoint = "book"


class BookAPI:
    def book(
            self,
            ondc_transaction_id,
            pnr
    ):
        on_confirm_data = None

        try:
            on_init_cache_key = f"{ondc_transaction_id}:{CACHE_DELIMITER}:on_init"
            cached_on_init_data = cache.get(on_init_cache_key)

            # add <Txn>:confirm in cache to make sure we don't repeatedly call buyer_confirm
            confirm_cache_key = f"{ondc_transaction_id}:{CACHE_DELIMITER}:confirm"
            on_confirm_cache_key = f"{ondc_transaction_id}:{CACHE_DELIMITER}:on_confirm"
            # if not cache.get(confirm_cache_key):
            if not cache.get(confirm_cache_key):
                cache.set(confirm_cache_key, "confirm", timeout=TICKET_INITIATE_TRANSACTION_TIMEOUT)

            result = buyer_confirm(cached_on_init_data, pnr)
            logging.info(f"called buyer_confirm with id: {result}")

            # Put a counter for only 10 iterations
            for i in range(10):
                on_confirm_data = cache.get(on_confirm_cache_key)
                if on_confirm_data is not None:
                    break
                sleep(0.5)

            # client = FetchFareAPI(Src_Stn=start_stop_code, Dest_Stn=end_stop_code, Grp_Size=1)
            # response_obj = client.post_api()

            # return Response(response_obj)
            logging.info(f"on_confirm_data=============: {on_confirm_data}")
            return on_confirm_data
        except Exception as e:
            raise
