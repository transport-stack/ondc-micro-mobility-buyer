from django.test import TestCase
from django.urls import reverse

class SearchViewTest(TestCase):

    def test_search_without_trailing_slash(self):
        # This tests the search endpoint without a trailing slash which is expected to fail
        response = self.client.post('/search', {'key': 'value'})
        # Check that the response is not 200 OK to assert the test fails as expected
        self.assertNotEqual(response.status_code, 200)

