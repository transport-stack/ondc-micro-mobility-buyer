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
from modules.env_main import GENERIC_LOGIN_PASSWORD
from modules.views import XAPIKeyPermission, CustomJSONRenderer


@extend_schema(parameters=X_API_KEY_PARAMETERS)
class MyUserViewSet(
    ViewSetPermissionByMethodMixin, mixins.UpdateModelMixin, GenericViewSet
):
    serializer_class = MyUserSerializer
    queryset = MyUser.objects.filter(is_superuser=False, is_active=True).all()
    renderer_classes = [
        CustomJSONRenderer,
    ]
    permission_classes = [XAPIKeyPermission]
    permission_action_classes = dict(
        create=(AllowAny,),
        retrieve=(IsUserOwner,),
        update=(IsUserOwner,),
        partial_update=(IsUserOwner,),
        login=(AllowAny,),
        my=(IsUserOwner,),
    )

    @extend_schema(
        tags=["Authentication"],
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
                    "username": "abc@gmail.com",
                    "first_name": "Aarav",
                    "last_name": "Patel",
                    "email": "optional@gmail.com",
                    "phone": "+917777777777",
                },
                request_only=True,  # signal that example only applies to requests
                response_only=False,  # signal that example only applies to responses
            )
        ],
    )
    @action(detail=False, methods=["POST"])
    def login(self, request, *args, **kwargs):
        body = request.data

        if "username" not in body:
            message = ""
            if "username" not in body:
                message += "Username not found in request. "
            raise Exception(message)

        username = body["username"]

        existing_users = MyUser.objects.filter(username=username)

        user = None

        if existing_users.exists():
            user = existing_users.first()
            if not user.is_active:
                # TODO: allow to send response codes with exceptions
                raise Exception("User inactive.")
            else:
                refresh_token_obj = RefreshToken.for_user(user)
                refresh_token = str(refresh_token_obj)
                access_token = str(refresh_token_obj.access_token)
                data = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                }
                return Response(data, status=status.HTTP_200_OK)
        else:
            body["password"] = GENERIC_LOGIN_PASSWORD
            user_serializer = self.get_serializer(data=body)
            if user_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()

        if user:
            refresh_token_obj = RefreshToken.for_user(user)
            refresh_token = str(refresh_token_obj)
            access_token = str(refresh_token_obj.access_token)
            data = {"access_token": access_token, "refresh_token": refresh_token}
            return Response(data, status=status.HTTP_200_OK)

        else:
            raise Exception("User not found.")

    @action(detail=False, methods=["GET"])
    def my(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
