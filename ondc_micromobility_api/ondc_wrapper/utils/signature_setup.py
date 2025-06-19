import base64
import logging

import pytz
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


def get_private_key_from_file(file_path):
    with open(file_path, "r") as f:
        return f.read()




# Define the IST timezone globally
IST = pytz.timezone('Asia/Kolkata')


def get_datetime_obj_in_api_format(datetime_obj):
    # Define the IST timezone
    # Convert the datetime object to IST, only if it's not already in IST
    if datetime_obj.tzinfo != IST:
        datetime_obj = datetime_obj.astimezone(IST)

    return datetime_obj.strftime("%d/%m/%Y@%H-%M-%S")


if __name__ == "__main__":
    data = "asdasdasdds  asdasdasd"
    data = data.replace(" ", "")
    logging.debug(data)
