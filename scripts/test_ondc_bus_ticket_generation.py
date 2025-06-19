import logging
import requests
import sqlite3
import os
from dotenv import load_dotenv, find_dotenv
import concurrent.futures
import time
import random

# Load env
load_dotenv(find_dotenv("envs/.env.ondc"))
load_dotenv(find_dotenv("envs/.env.common"))

# Configuration
API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('SITE_URL')
LOGIN_URL = f"{BASE_URL}/api/v1/accounts/user/login/"
INITIATE_URL = f"{BASE_URL}/api/v1/tickets/initiate/"
ESTIMATE_URL = f"{BASE_URL}/api/v1/ondc/delhi/bus/estimate"
TRANSACTION_URL = f"{BASE_URL}/api/v1/tickets/{{}}/transaction/"
CONFIRM_URL = f"{BASE_URL}/api/v1/tickets/{{}}/confirm/"
DATABASE_PATH = 'db.sqlite3'  # Adjust this path to your SQLite database

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def login(retries=5, backoff_factor=0.3):
    """Logs in and returns the access token."""
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }
    data = {"username": os.getenv('DUMMY_USERNAME')}

    for i in range(retries):
        response = requests.post(LOGIN_URL, headers=headers, json=data)

        if response.status_code == 429:
            sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
            logging.warning(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            response.raise_for_status()  # Raise an error for other bad status codes
            response_data = response.json()

            # Debug print to see the response data
            logging.info(f"Login response data: {response_data}")

            # Check if 'access_token' is in the response
            if 'data' in response_data and 'access_token' in response_data['data']:
                return response_data['data']['access_token']
            else:
                raise ValueError("Access token not found in login response")

    raise Exception("Failed to log in after several retries")

def estimate(retries=10, backoff_factor=0.3):
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }

    data = {
        "start_stop_code": "WEST_ENCLAVE_SANSAD_VIHAR_T",
        "end_stop_code": "DEV_NAGAR",
        "route_id": "993DOWN",
        "variant": "ac",
        "bus_reg_num": "DL1PD5604",
        "category": "p"
    }

    for i in range(retries):
        response = requests.post(ESTIMATE_URL, headers=headers, json=data)

        if response.status_code == 429:
            sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
            logging.warning(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            try:
                response.raise_for_status()
                response_data = response.json()
                logging.info(f"Estimate request data: {data}")
                logging.info(f"Estimate response data: {response_data}")
                return response_data['data']['fare']['transaction_id']
            except requests.exceptions.HTTPError as e:
                logging.error(f"Estimate request data: {data}")
                logging.error(f"Estimate response data: {response.text}")
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: {response.text}")
                else:
                    raise e

    raise Exception("Failed to estimate after several retries")

def initiate(token, transaction_id, retries=10, backoff_factor=0.3):
    """Initiates a ticket purchase and returns the PNR."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY
    }
    data = {
        "transaction_id": f"{transaction_id}",
        "ticket_count": 1,
        "transit_option": {
            "transit_mode": "BUS",
            "provider": {
                "name": "ONDC"
            }
        },
        "meta": {
            "route_id": "993DOWN",
            "variant": "ac",
            "bus_reg_num": "DL1PD5604"
        }
    }

    for i in range(retries):
        response = requests.post(INITIATE_URL, headers=headers, json=data)

        if response.status_code == 429:
            sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
            logging.warning(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            try:
                response.raise_for_status()
                response_data = response.json()
                logging.info(f"Initiate request data: {data}")
                logging.info(f"Initiate response data: {response_data}")
                return response_data['data']['pnr']
            except requests.exceptions.HTTPError as e:
                logging.error(f"Initiate request data: {data}")
                logging.error(f"Initiate response data: {response.text}")
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: {response.text}")
                else:
                    raise e

    raise Exception("Failed to initiate after several retries")

def transaction(token, pnr, retries=10, backoff_factor=0.3):
    """Processes the transaction and updates the status."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY
    }
    data = {"payment_mode": "UNKNOWN"}
    url = TRANSACTION_URL.format(pnr)

    for i in range(retries):
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 429:
            sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
            logging.warning(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            try:
                response.raise_for_status()
                response_data = response.json()
                logging.info(f"Transaction request data: {data}")
                logging.info(f"Transaction response data: {response_data}")

                if 'data' in response_data and 'gateway_order_id' in response_data['data']:
                    return response_data['data']['gateway_order_id']
                else:
                    raise ValueError("Gateway order ID not found in transaction response")
            except requests.exceptions.HTTPError as e:
                logging.error(f"Transaction request data: {data}")
                logging.error(f"Transaction response data: {response.text}")
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: {response.text}")
                else:
                    raise e

    raise Exception("Failed to process transaction after several retries")

def update_transaction_status(gateway_order_id, retries=10, backoff_factor=0.3):
    """Updates the transaction status in the database."""
    conn = None
    for i in range(retries):
        try:
            conn = sqlite3.connect(DATABASE_PATH, timeout=30)
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
            cursor.execute("UPDATE payments_transaction SET status='S' WHERE gateway_order_id=?", (gateway_order_id,))
            conn.commit()
            logging.info("Transaction status updated to success for ID: %s", gateway_order_id)
            time.sleep(10)  # Adding a short sleep to give some time for the status update
            return
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
                logging.warning(f"Database is locked. Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                raise
        finally:
            if conn:
                conn.close()
    raise Exception("Failed to update transaction status after several retries")

def confirm(token, pnr, retries=10, backoff_factor=0.3):
    """Confirms the ticket purchase."""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'x-api-key': API_KEY
    }
    url = CONFIRM_URL.format(pnr)

    for i in range(retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 429:
            sleep_time = backoff_factor * (2 ** i) + random.uniform(0, 1)
            logging.warning(f"Rate limited. Retrying in {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        else:
            try:
                response.raise_for_status()
                response_data = response.json()
                logging.info(f"Confirm response data: {response_data}")

                if response_data.get('message') == 'Failed':
                    raise ValueError(f"Confirmation failed: {response_data.get('description')}")
                return response_data
            except requests.exceptions.HTTPError as e:
                logging.error(f"Confirm response data: {response.text}")
                if response.status_code == 400:
                    raise ValueError(f"Bad Request: {response.text}")
                else:
                    raise e

    raise Exception("Failed to confirm after several retries")

def generate_ticket():
    try:
        token = login()
        transaction_id = estimate()
        pnr = initiate(token, transaction_id)
        gateway_order_id = transaction(token, pnr)
        if gateway_order_id:
            update_transaction_status(gateway_order_id)
            confirmation = confirm(token, pnr)
            logging.info("Ticket confirmed successfully: %s", confirmation)
        else:
            logging.error("Transaction failed.")
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main():
    num_tickets = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_tickets) as executor:
        futures = [executor.submit(generate_ticket) for _ in range(num_tickets)]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"An error occurred during ticket generation: {e}")

if __name__ == "__main__":
    main()
