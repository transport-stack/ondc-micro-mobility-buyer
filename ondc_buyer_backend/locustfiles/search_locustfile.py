# locustfiles.py
import os

import uuid
from locust import HttpUser, task, between
from celery import Celery
from ondc_buyer_backend.tasks.buyer_search import buyer_search
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
django.setup()

# Set up Celery
app = Celery('ptx_core_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


class CeleryUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def call_buyer_search(self):
        # Define the parameters for the buyer_search task
        transaction_id = str(uuid.uuid4())
        start_stop_code = 'WEST_ENCLAVE_SANSAD_VIHAR_T'
        end_stop_code = 'DEV_NAGAR'
        variant = 'AC'
        bus_reg_num = 'DL1PD5604'

        result = buyer_search.delay(transaction_id, start_stop_code, end_stop_code, variant, bus_reg_num)

        # Get the result with a timeout
        try:
            result_value = result.get(timeout=10)
            print(f'Task result: {result_value}')
        except Exception as e:
            print(f'Task failed: {e}')
