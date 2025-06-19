import logging
import random
import uuid as uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from custom_cities.models import City
from modules.firebase_cloud_messaging import async_send_fcm_notification
from modules.models import DateTimeMixin
from taskschedule.tasks import send_user_silent_notification_shared_task


class SignUpMethodChoices(models.IntegerChoices):
    GOOGLE = (1, "Google")
    EMAIL = (2, "Email")
    MOBILE = (3, "Mobile")


def random_pin():
    return random.randint(1000, 9999)


class MyUser(AbstractUser, DateTimeMixin):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    signup_method = models.IntegerField(
        choices=SignUpMethodChoices.choices, default=SignUpMethodChoices.EMAIL
    )

    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone = PhoneNumberField(null=True, blank=True, unique=True)

    language_preferred = models.CharField(
        max_length=7, choices=settings.LANGUAGES, default="en", blank=True, null=True
    )
    current_city = models.ForeignKey(
        City, on_delete=models.SET_NULL, default=None, null=True, blank=True
    )
    pin = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=random_pin,
        validators=[MinValueValidator(1000), MaxValueValidator(999999)],
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-is_active", "-created_at")

    def send_user_notification(self, title, message, notification_obj):
        """
        Send notification to user based on ticket status
        """
        extra_params = {"notification_id": 3000}
        if notification_obj:
            extra_params = notification_obj.get_extra_params()

        channel_name = None
        phone_number = str(self.phone)
        if phone_number and len(phone_number) >= 10:
            channel_name = phone_number[-10:]

        if channel_name:
            async_send_fcm_notification(channel_name, title=title, body=message, extra_params=extra_params)

    def send_user_silent_notification(self, extra_params):
        """
        Send notification to user based on ticket status
        """
        logging.info("send_user_silent_notification")
        channel_name = None
        phone_number = str(self.phone)
        if phone_number and len(phone_number) >= 10:
            channel_name = phone_number[-10:]

        if channel_name:
            send_user_silent_notification_shared_task(channel_name, extra_params=extra_params)
        # send_fcm_silent_notification(channel_name, extra_params=extra_params)
