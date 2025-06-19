import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=f"envs/.env.common")
load_dotenv(dotenv_path=f"envs/.env.ondc")
load_dotenv(dotenv_path=f"envs/.env.paytm")
load_dotenv(dotenv_path=f"envs/.env.keys")

# Retrieve logging level from environment variables
log_level = os.getenv(
    "LOG_LEVEL", "INFO"
)  # 'INFO' is the default level if LOG_LEVEL is not set in .env

# Set the logging level
logging.basicConfig(level=log_level)

# .env.general
debug_env = os.getenv("DEBUG")  # Convert DEBUG to a boolean value
if debug_env is not None:
    DEBUG = debug_env.lower() in ["true", "1", "yes", "on"]
else:
    # Default value if DEBUG environment variable is not set
    DEBUG = False

# DEBUG will be True if the environment variable is set and any of the following conditions are met:
# - DEBUG="True"
# - DEBUG="true"
# - DEBUG="1"
# Otherwise, DEBUG will be False.
X_API_KEY = os.getenv("X_API_KEY")
GENERIC_LOGIN_PASSWORD = os.getenv("GENERIC_LOGIN_PASSWORD")
SERVETEL_WEBHOOK_X_API_KEY = os.getenv("SERVETEL_WEBHOOK_X_API_KEY")
SERVETEL_CLICK_TO_CALL_API_KEY = os.getenv("SERVETEL_CLICK_TO_CALL_API_KEY")

REDIS_HOST = os.getenv("REDIS_HOST", None)
# RAPIDO_WEBHOOK_X_API_KEY = os.getenv("RAPIDO_WEBHOOK_X_API_KEY")
ENABLE_RAPIDO_WEBHOOK = os.getenv("ENABLE_RAPIDO_WEBHOOK")
if ENABLE_RAPIDO_WEBHOOK is not None:
    ENABLE_RAPIDO_WEBHOOK = ENABLE_RAPIDO_WEBHOOK.lower() in ["true", "1", "yes", "on"]
else:
    # Default value if ENABLE_RAPIDO_WEBHOOK environment variable is not set
    ENABLE_RAPIDO_WEBHOOK = False

SECRET_KEY = os.getenv("SECRET_KEY")
LOG_LEVEL = os.getenv("LOG_LEVEL")
CAPTURE_REQUEST_RESPONSE_CONTENT = os.getenv("CAPTURE_REQUEST_RESPONSE_CONTENT")
"""# error/all/off
CAPTURE_REQUEST_RESPONSE_CONTENT=error"""
if CAPTURE_REQUEST_RESPONSE_CONTENT is not None:
    CAPTURE_REQUEST_RESPONSE_CONTENT = CAPTURE_REQUEST_RESPONSE_CONTENT.lower()
    if CAPTURE_REQUEST_RESPONSE_CONTENT not in ["error", "all", "off"]:
        CAPTURE_REQUEST_RESPONSE_CONTENT = "off"
        logging.warning(
            "CAPTURE_REQUEST_RESPONSE_CONTENT is not set to error/all/off. Defaulting to off."
        )

# add all env variables loaded here in some dictionary and print all of them at the end, except the secret ones
env_dict = {
    "LOG_LEVEL": log_level,
    "DEBUG": DEBUG,
    "X_API_KEY": X_API_KEY,
    "SERVETEL_WEBHOOK_X_API_KEY": SERVETEL_WEBHOOK_X_API_KEY,
    "SERVETEL_CLICK_TO_CALL_API_KEY": SERVETEL_CLICK_TO_CALL_API_KEY,
    # "RAPIDO_WEBHOOK_X_API_KEY": RAPIDO_WEBHOOK_X_API_KEY,
}

# print is a huge performance bottleneck. print should never happen in prod.
if DEBUG:
    print("-" * 50, file=sys.stderr)
    for key, value in env_dict.items():
        # this for printing False as False, not as 0
        formatted_value = str(value) if isinstance(value, (bool, type(None))) else value
        print(f"{key:<20}:\t{formatted_value:<20}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)
