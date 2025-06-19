import json

from django.utils.deprecation import MiddlewareMixin
import logging

import settings
from modules.env_main import CAPTURE_REQUEST_RESPONSE_CONTENT

# Set up logging
logger = logging.getLogger(__name__)


class LogPostRequestsMiddleware(MiddlewareMixin):
    def should_log(self, response):
        """Determine if the request and response should be logged."""
        setting_value = CAPTURE_REQUEST_RESPONSE_CONTENT
        if setting_value == 'all':
            return True
        elif setting_value == 'error' and 400 <= response.status_code <= 500:
            return True
        return False

    def process_request(self, request):
        if CAPTURE_REQUEST_RESPONSE_CONTENT != 'off':
            if request.method == 'POST':
                try:
                    request._body = request.body
                    json_body = json.loads(request._body.decode('utf-8'))
                    request._minified_body = json.dumps(json_body, separators=(',', ':'))
                except Exception:
                    request._minified_body = request._body

    def process_response(self, request, response):
        if self.should_log(response):
            # Minify and log the request body if it exists
            req_body = getattr(request, '_minified_body', 'Unavailable').decode('utf-8') if isinstance(
                getattr(request, '_minified_body', 'Unavailable'), bytes) else getattr(request, '_minified_body',
                                                                                       'Unavailable')
            logger.debug(f"Request: {req_body}")

            # Attempt to minify and log the response body
            try:
                if 'application/json' in response.get('Content-Type', '') and response.content:
                    response_content = json.loads(response.content.decode('utf-8'))
                    minified_response = json.dumps(response_content, separators=(',', ':'))
                else:
                    minified_response = response.content.decode('utf-8')
            except Exception:
                minified_response = "Error minifying response body"

            # Log only if necessary based on CAPTURE_REQUEST_RESPONSE_CONTENT setting
            logger.debug(f"Response: {minified_response}")

        return response
