import json
import time
import os
import base64
import datetime
import json
from django.views.decorators.csrf import csrf_exempt
from nacl.bindings import crypto_sign_ed25519_sk_to_seed
import nacl.hash
from nacl.signing import SigningKey
from cryptography.hazmat.primitives import serialization
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from django.http import JsonResponse
from django.shortcuts import render
import requests
import uuid
import threading
import pytz

bapBaseUrl = "https://pre-prod-mm-ondc-api.delhitransport.in/"
registry_url = "https://preprod.registry.ondc.org/ondc/subscribe"
subscribers = None
subscribers_uniquekey_store = {}

bapSubscribeBody = {
    "context": {
        "operation": {
            "ops_no": 1
        },
    },
    "message": {
        "request_id": "",
        "timestamp": "",
        "entity": {
            "gst": {
                "legal_entity_name": "Anamar Technologies Private Limited",
                "business_address": "3rd Floor,D- BLOCK, D-303, Krishvi Dhavala, Doddakannelli Kadubeesanahalli Road, "
                                    "Bengaluru, Bengaluru Urban, Karnataka, 560102",
                "city_code": [
                    "std:080"
                ],
                "gst_no": "29AARCA5379C1Z9"
            },
            "pan": {
                "name_as_per_pan": "Anamar Technologies Private Limited",
                "pan_no": "AARCA5379C",
                "date_of_incorporation": "02/11/2018"
            },
            "name_of_authorised_signatory": "Pravesh Biyani",
            "email_id": "contact@chartr.in",
            "mobile_no": 9818711051,
            "country": "IND",
            "subscriber_id": "pre-prod-mm-ondc-api.delhitransport.in",
            "unique_key_id": "",
            "callback_url": "/",
            "key_pair": {
                "signing_public_key": "4rUM7XreO5qEotuk3chFEI2ymQAOfIgHNb8i8RN9lpg=",
                "encryption_public_key": "MCowBQYDK2VuAyEA04HqOtg21vXDxACBPBspcbJN7TThLZXNKqFhcQjvjRc=",
                "valid_from": "",
                "valid_until": "2030-06-19T11:57:54.101Z"
            }
        },
        "network_participant": [
            {
                "subscriber_url": "/",
                "domain": "ONDC:TRV10",
                "type": "buyerApp",
                "msn": False,
                "city_code": []
            }
        ]
    }
}


def sign(signing_key, private_key):
    try:
        private_key64 = base64.b64decode(private_key)
        seed = crypto_sign_ed25519_sk_to_seed(private_key64)
        signer = SigningKey(seed)
        signed = signer.sign(bytes(signing_key, encoding='utf8'))
        signature = base64.b64encode(signed.signature).decode()
        return signature
    except Exception as e:
        print(f"Error in signing: {e}")
        raise


def decrypt(enc_public_key, enc_private_key, cipherstring):
    try:
        private_key = serialization.load_der_private_key(
            base64.b64decode(enc_private_key),
            password=None
        )
        public_key = serialization.load_der_public_key(
            base64.b64decode(enc_public_key)
        )
        shared_key = private_key.exchange(public_key)
        cipher = AES.new(shared_key, AES.MODE_ECB)
        ciphertxt = base64.b64decode(cipherstring)
        return unpad(cipher.decrypt(ciphertxt), AES.block_size).decode('utf-8')
    except Exception as e:
        print(f"Error in decryption: {e}")
        raise


def create_html(subscriber, subscriber_id):
    try:
        print(f"Subscriber ID :: {subscriber_id}, Subscriber :: {subscriber['requestId']}, {subscriber['signingPrivateKey']}")
        signature = sign(subscriber['requestId'], subscriber['signingPrivateKey'])
        print(f"Signature :: {signature}")
        html_file = f'''
        <html>
            <head>
                <meta name="ondc-site-verification" content="{signature}" />
            </head>
            <body>
                ONDC Site Verification Page
            </body>
        </html>
        '''
        print(f"HTML File----- :: {html_file}")

        path = f'templates/{subscriber_id[slice(len(bapBaseUrl) + 1, len(subscriber_id))]}'
        if not os.path.exists(path):
            os.makedirs(path)
        with open(f"{path}/ondc-site-verification.html", "w+") as file:
            file.write(html_file)
    except Exception as e:
        print(f"Error in creating HTML file: {e}")
        raise


@csrf_exempt
def on_subscribe(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        subscriber_id = data['subscriber_id']
        unique_key_id = subscribers_uniquekey_store[subscriber_id]
        subscriber = subscribers[f"{subscriber_id} | {unique_key_id}"]
        response = {
            "answer": decrypt(subscriber['ondcPublicKey'], subscriber['encPrivateKey'], data['challenge'])
        }
        return JsonResponse(response)


def subscribe_helper():
    if subscribers is not None:
        global subscribers_uniquekey_store
        for subscriber_uk_id, subscriber in subscribers.items():
            try:
                [subscriber_id, unique_key_id] = subscriber_uk_id.split(' | ')
                print(f"Subscriber ID :: {subscriber_id}, Unique Key ID :: {unique_key_id}")
                subscribers_uniquekey_store[subscriber_id] = unique_key_id
                request_id = str(uuid.uuid4())
                subscribers[subscriber_uk_id]['requestId'] = request_id
                print(f"Subscriber==== :: {subscriber}, subscribers_uniquekey_store===== :: {subscribers_uniquekey_store}")
                create_html(subscriber, subscriber_id)
            except Exception as e:
                print(f"Error in subscribe_helper (initialization): {e}")
                continue

        time.sleep(5)

        for subscriber_uk_id, subscriber in subscribers.items():
            try:
                [subscriber_id, unique_key_id] = subscriber_uk_id.split(' | ')
                request_id = subscriber['requestId']

                print(f"Request ID +++:: {request_id}, Subscriber ID +++:: {subscriber_id}, Unique Key ID +++:: {unique_key_id}")
                current_datetime = datetime.datetime.now().astimezone(pytz.timezone('Asia/Kolkata'))
                current_datetime_iso8601 = current_datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

                if subscriber['type'] == 'BAP':
                    bapSubscribeBody['message']['request_id'] = request_id
                    bapSubscribeBody['message']['timestamp'] = current_datetime_iso8601
                    bapSubscribeBody['message']['entity']['subscriber_id'] = subscriber_id
                    bapSubscribeBody['message']['entity']['unique_key_id'] = unique_key_id
                    bapSubscribeBody['message']['entity']['key_pair']['signing_public_key'] = subscriber['signingPublicKey']
                    bapSubscribeBody['message']['entity']['key_pair']['encryption_public_key'] = subscriber['encPublicKey']
                    bapSubscribeBody['message']['entity']['key_pair']['valid_from'] = current_datetime_iso8601
                    bapSubscribeBody['message']['network_participant'][0]['city_code'] = [subscriber['city']]

                    print(json.dumps(bapSubscribeBody))

                    response = requests.post(registry_url, json=bapSubscribeBody)
                    if response.status_code == 200:
                        print(f"/subscribe for {subscriber_uk_id} request successful :: {response.json()}")
                    else:
                        print(f"/subscribe for {subscriber_uk_id} request failed :: {response.json()}")
            except Exception as e:
                print(f"Error in subscribe_helper (subscription): {e}")
                continue

        time.sleep(300)


@csrf_exempt
def subscribe(request):
    if request.method == 'POST':
        global subscribers
        try:
            subscribers = json.loads(request.body)
            print(f"/subscribe called :: Request -> {subscribers}")
            thread1 = threading.Thread(target=subscribe_helper)
            thread1.start()
            return JsonResponse({"success": "ACK"})
        except Exception as e:
            print(f"Error in subscribe: {e}")
            return JsonResponse({"error": str(e)}, status=500)


def verify_html(request):
    return render(request, 'ondc-site-verification.html')
