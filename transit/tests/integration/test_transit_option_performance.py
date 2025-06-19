from django.test import TestCase

import time

from accounts.models import MyUser
from modules.constants import RAPIDO_ENUM
from modules.models import TransitMode
from transit.models.transit_setup import TransitOption, TransitProvider


class TransitOptionPerformanceTest(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create(username="testuser")
        # Create a transit provider for RAPIDO
        self.rapido_provider, _ = TransitProvider.objects.get_or_create(
            name=RAPIDO_ENUM
        )

        # Create transit options for RAPIDO
        self.bike_option, _ = TransitOption.objects.get_or_create(
            provider=self.rapido_provider, transit_mode=TransitMode.BIKE.value
        )
        self.auto_option, _ = TransitOption.objects.get_or_create(
            provider=self.rapido_provider, transit_mode=TransitMode.AUTO_RICKSHAW.value
        )

        self.transit_option = self.bike_option

    def test_is_active_on_response_time(self):
        total_time = 0
        number_of_runs = 1000

        for _ in range(number_of_runs):
            start_time = time.time()
            self.transit_option.is_active_at_datetime()  # You can also pass a specific datetime here
            end_time = time.time()

            total_time += (end_time - start_time)

        average_time = total_time / number_of_runs
        print(f"Average response time over {number_of_runs} runs: {average_time} seconds")
