from django.db import transaction

from drf_spectacular.utils import OpenApiResponse, extend_schema, OpenApiExample
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.decorators import X_API_KEY_PARAMETERS
from accounts.models.user_setup import MyUser
from accounts.permissions import IsUserOwner
from accounts.serializers import MyUserSerializer
from common.mixins import ViewSetPermissionByMethodMixin
from messaging_service.wrapper.base import MessagingServiceWrapper
from modules.env_main import GENERIC_LOGIN_PASSWORD
from modules.views import CustomJSONRenderer
from phonenumber_field.modelfields import PhoneNumberField
from django.core.exceptions import ValidationError


def is_valid_phone_number(phone_number_str):
    phone_number_field = PhoneNumberField()
    try:
        phone_number = phone_number_field.to_python(phone_number_str)
        phone_number_field.run_validators(phone_number)
        return True
    except ValidationError:
        return False


class MyUserViewSetWebAPI(
    ViewSetPermissionByMethodMixin, mixins.UpdateModelMixin, GenericViewSet
):
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.filter(is_superuser=False, is_active=True).all()
    renderer_classes = [
        CustomJSONRenderer,
    ]
    permission_action_classes = dict(
        create=(AllowAny,),
        retrieve=(IsUserOwner,),
        update=(IsUserOwner,),
        partial_update=(IsUserOwner,),
        login=(AllowAny,),
        my=(IsUserOwner,),
    )

    @extend_schema(
        tags=["Web API"],
        responses={
            200: OpenApiResponse(
                description="Successful", response=TokenObtainPairSerializer
            )
        },
        examples=[
            OpenApiExample(
                "Example 1",
                summary="Simple user login",
                description="only username is mandatory",
                value={
                    "username": "+919876543211"
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],
    )
    @action(detail=False, methods=["POST"])
    def login(self, request, *args, **kwargs):
        username = request.data.get("username")

        if not username:
            raise Exception("Username not found in request.")

        # assert the phone number should be a valid phone number with country code, make it country agnostic
        if not is_valid_phone_number(username):
            raise Exception("Invalid phone number")

        # Sending OTP
        messaging_service_wrapper = MessagingServiceWrapper()
        response = messaging_service_wrapper.send_otp(username[-10:])
        if response.status_code not in range(200, 300):
            description = response.json().get("description", "OTP sending failed")
            raise Exception(description)

        return Response({"description": "OTP sent successfully"}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Web API"],
        responses={
            200: OpenApiResponse(
                description="Successful", response=TokenObtainPairSerializer
            )
        },
        examples=[
            OpenApiExample(
                "Example 1",
                summary="Simple user verification",
                description="username and otp are mandatory",
                value={
                    "username": "+919876543211",
                    "otp": "1234"
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],
    )
    @action(detail=False, methods=["POST"], url_path="verify-otp")
    def verify_otp(self, request, *args, **kwargs):
        username = request.data.get("username")
        otp = request.data.get("otp")

        if not username or not otp:
            raise Exception("Username and OTP required.")

        # assert the phone number should be a valid phone number with country code, make it country agnostic
        if not is_valid_phone_number(username):
            raise Exception("Invalid phone number")

        # Verifying OTP
        messaging_service_wrapper = MessagingServiceWrapper()
        verify_otp_response = messaging_service_wrapper.verify_otp(username[-10:], otp)

        if verify_otp_response.status_code not in range(200, 300):
            description = verify_otp_response.json().get("description", "OTP verification failed")
            raise Exception(description)

        # Proceed with user validation and token generation
        return self._process_user_and_generate_tokens(username)

    @staticmethod
    def _process_user_and_generate_tokens(username):
        user = MyUser.objects.filter(username=username).first()

        if not user:
            user = MyUser.objects.create(
                username=username,
                password=GENERIC_LOGIN_PASSWORD,
                phone=username
            )
            # Additional user setup can be done here

        if not user.is_active:
            return Response({"message": "User inactive."}, status=status.HTTP_403_FORBIDDEN)

        refresh_token_obj = RefreshToken.for_user(user)
        access_token = str(refresh_token_obj.access_token)

        return Response({
            "access_token": access_token,
            "refresh_token": str(refresh_token_obj)
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"])
    def my(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
