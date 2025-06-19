import time
import random
import logging
from functools import wraps
from requests.exceptions import SSLError
from rest_framework.response import Response


def retry_on_429_and_ssl_error(retries=5, backoff_factor=1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    response = func(*args, **kwargs)
                    if response.status_code != 429:
                        return response
                except SSLError as ssl_err:
                    logging.warning(f"SSL error encountered. Retrying: {ssl_err}")
                sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
                logging.warning(f"Rate limited or SSL error. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            return Response({'error': 'Too many requests or SSL error, please try again later.'}, status=429)
        return wrapper
    return decorator
