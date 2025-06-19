import requests
import time
import os

# Configuration for the endpoints
# BASE_URL = "https://63dd-2405-201-a402-5173-b027-fb37-2d08-f0be.ngrok-free.app/api/v1/ondc/buyer"
BASE_URL = "https://3d3a-2405-201-a402-5173-b835-3bcb-f8f7-2e7f.ngrok-free.app/api/v1/ondc/buyer"
ESTIMATE_ENDPOINT = f"{BASE_URL}/buyer-estimate/"
ON_ESTIMATE_ENDPOINT = f"{BASE_URL}/buyer-on-estimate/"

def post_estimate(route_id, start_stop, end_stop):
    """Post to the /estimate endpoint and return the transaction_id."""
    data = {
        'route_id': route_id,
        'start_stop_code': start_stop,
        'end_stop_code': end_stop
    }
    headers = {'Content-Type': 'application/json'}  # Set headers to send data as JSON
    response = requests.post(ESTIMATE_ENDPOINT, json=data, headers=headers)  # Use json parameter to encode data
    if response.status_code == 200:
        return response.json().get('transaction_id')
    else:
        print("Error posting to estimate:", response.text)
        return None

def poll_on_estimate(transaction_id):
    """Poll the /on_estimate endpoint using the transaction_id."""
    params = {'txn_id': transaction_id}
    end_time = time.time() + 5 # Poll for 10 seconds
    while time.time() < end_time:
        response = requests.get(ON_ESTIMATE_ENDPOINT, params=params)
        if response.status_code == 200 and response.json().get('fare_data'):
            return response.json().get('fare_data')
        time.sleep(1)  # Sleep for 1 second between polls
    return None

def main():
    # Example data - replace with actual data as needed
    route_id = "102STLDOWN"
    start_stop = "ROHINI_SEC_22_TERMINAL"
    end_stop = "AVANTIKA_XING"

    # Step 1: Call /estimate and get transaction_id
    transaction_id = post_estimate(route_id, start_stop, end_stop)
    print("Transaction ID:", transaction_id)
    if transaction_id:
        print(f"Received transaction_id: {transaction_id}")

        # Step 2: Poll /on_estimate with the transaction_id
        fare_data = poll_on_estimate(transaction_id)
        if fare_data:
            print("Received fare data:", fare_data)
        else:
            print("No fare data received within the polling duration.")
    else:
        print("Failed to obtain a transaction_id, cannot proceed.")

if __name__ == "__main__":
    main()
