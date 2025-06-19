import argparse
import logging
import threading
import time
from typing import Any, Optional, Dict

import firebase_admin
from firebase_admin import messaging, credentials

from settings.base import BASE_DIR


class FcmUtils:
    def __init__(self):
        creds = credentials.Certificate(
            f'{BASE_DIR}/envs/firebase_credentials.json')
        firebase_admin.initialize_app(creds)

    def send_to_channel(self, topic, title, body, priority='high',
                        extra_params: Optional[Dict[str, str]] = None) -> Any:
        data_payload = {
            "title": title,
            "message": body,
        }

        # Merging extra parameters with the data payload
        if extra_params:
            data_payload.update(extra_params)

        print(f"Data payload: {data_payload}")
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data_payload,
            topic=topic,
            android=messaging.AndroidConfig(
                priority=priority,
                ttl=300
            ),
        )
        response = messaging.send(message)
        logging.debug(response)
        return response

    def send_silent_notification(self, topic, priority='high',
                                 extra_params: Optional[Dict[str, str]] = None) -> Any:
        data_payload = extra_params if extra_params else {}

        logging.debug(f"Silent Data payload: {data_payload}")
        message = messaging.Message(
            data=data_payload,
            topic=topic,
            android=messaging.AndroidConfig(
                priority=priority,
                ttl=300
            ),
        )
        response = messaging.send(message)
        logging.debug(response)
        return response


try:
    fcm_utils_object = FcmUtils()
except Exception as e:
    logging.error(f"Error occurred while initializing FcmUtils object: {e}")
    fcm_utils_object = None


def send_fcm_notification(topic, title, body,
                          priority='high', extra_params: Optional[Dict[str, str]] = None):
    fcm_utils_object.send_to_channel(topic, title, body, priority, extra_params)


def async_send_fcm_notification(topic, title, body,
                                priority='high',
                                extra_params: Optional[Dict[str, str]] = None):
    thread = threading.Thread(target=send_fcm_notification,
                              args=(topic, title, body, priority, extra_params))
    thread.start()


def send_fcm_silent_notification(topic, priority='high',
                                 extra_params: Optional[Dict[str, str]] = None):
    fcm_utils_object.send_silent_notification(topic=topic, extra_params=extra_params)


def main(topic):
    extra_data = {'type': 'ptx_ticket_status', 'key1': 'value1', 'key2': 'value2'}
    extra_data = {'type': 'mark_current_journey_as_completed'}
    # async_send_fcm_notification(topic, title=f"{RideStatus.ACCEPTED.value['title']}",
    #                             body=f"{RideStatus.ACCEPTED.value['message_template'].format(name='Ravinder')}",
    #                             extra_params=extra_data)
    fcm_utils_object.send_silent_notification(
        topic=topic,
        extra_params=extra_data
    )


if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Send FCM notification.')
    parser.add_argument('--topic', type=str, default='test',
                        help='Topic for the FCM notification')

    # Parse arguments
    args = parser.parse_args()

    # Record start time
    st = time.time()

    # Call main function with the topic argument
    main(args.topic)

    # Record end time and print the elapsed time
    et = time.time()
    print(round(et - st))
