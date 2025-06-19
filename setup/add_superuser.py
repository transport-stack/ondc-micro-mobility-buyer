import logging
from django.contrib.auth.models import User
from accounts.models import MyUser
import getpass

logger = logging.getLogger(__name__)


def create_superuser():
    username = "ticket-admin"
    email = ""

    # Get the password from user input
    password = getpass.getpass("Enter password for superuser: ")

    if not MyUser.objects.filter(username=username).exists():
        MyUser.objects.create_superuser(username, email, password)
        logger.info(f"Superuser {username} created")
    else:
        logger.info(f"Superuser {username} already exists")
