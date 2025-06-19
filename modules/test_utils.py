from responses import RequestsMock

SMS_BASE_URL = 'https://messages.delhitransport.in/v2'

sms_create_response = {
    "description": "OTP sent successfully",
    "expires_after": 5,
    "message": "Success"
}

sms_verify_response = {
    "description": "User verified successfully",
    "long_signature": "...",
    "message": "Success",
    "signature": "..."
}

#
# def add_mock_response(api_url=None, response_data=None, status_code=200, method="POST"):
#     """
#     Adds a mock response for a given API endpoint.
#
#     :param api_url: URL of the API endpoint.
#     :param response_data: The mock response data to return.
#     :param status_code: The HTTP status code for the mock response. Default is 200.
#     """
#     responses.add(method, api_url, json=response_data, status=status_code)
#

def mock_external_services():
    responses = RequestsMock()
    responses.start()

    # uncomment following to allow real requests to 3rd party
    responses.add_passthru(SMS_BASE_URL)

    # Mock SMS Services
    responses.add(responses.GET, f'{SMS_BASE_URL}/create/9876543211',
                  json=sms_create_response, status=200)
    responses.add(responses.POST, f'{SMS_BASE_URL}/verify/9876543211',
                  json=sms_verify_response, status=200)

    return responses


def mock_login_services():
    responses = RequestsMock()
    responses.add(responses.GET, f'{SMS_BASE_URL}/create/9876543211',
                  json=sms_create_response, status=200)
    return responses


def mock_verify_services():
    responses = RequestsMock()
    responses.add(responses.POST, f'{SMS_BASE_URL}/verify/9876543211',
                  json=sms_verify_response, status=200)
    return responses
