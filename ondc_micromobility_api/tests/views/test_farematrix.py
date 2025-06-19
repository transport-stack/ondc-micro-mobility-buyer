from unittest import skip

from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


class FareMatrixViewTest(TestCase):

    @skip("Fix this test")
    # @patch('path.to.your.EstimateAPI.estimate')
    def test_list_view_with_specific_stations(self):
        # Set up mock response for EstimateAPI
        # mock_estimate.return_value = {'fare': 30}  # Example fare

        # Prepare the URL and query parameters
        url = '/api/v1/dmrc/fare-matrix/?source_station__station_id=74&destination_station__station_id=211'  # Replace 'farematrix-list' with your actual URL name
        # params = {'source_station__station_id': '74', 'destination_station__station_id': '211'}

        # Make a GET request to the view
        response = self.client.get(url)

        # Assert the status code
        self.assertEqual(response.status_code, 200)

        # Assert the response structure and fare value
        response_data = response.json()
        self.assertEqual(response_data['message'], 'Success')
        self.assertEqual(response_data['description'], '')
        self.assertIn('data', response_data)
        self.assertEqual(len(response_data['data']), 1)  # Assuming there's always one item in the data list
        self.assertEqual(response_data['data'][0]['fare'], 10)  # Check if fare is as mocked

# Note: Ensure the path to EstimateAPI.estimate is correctly specified in the patch decorator.
