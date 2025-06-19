import logging
from django.test import Client

from django.contrib.auth.models import AnonymousUser
from rest_framework import mixins, viewsets
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import exception_handler as drf_exception_handler

from modules.constants import ResponseMessageEnum
from modules.env_main import X_API_KEY, SERVETEL_WEBHOOK_X_API_KEY


class NoSlashRouter(DefaultRouter):
    trailing_slash = False


class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        description = ""
        try:
            description = data.get("description", "")
        except Exception as e:
            pass
        if response is not None:
            status_code = response.status_code
        else:
            status_code = 200  # Default status code

        if status_code < 300:
            message = ResponseMessageEnum.SUCCESS
            # This is a successful response, so set the original data
            data = data
        elif status_code == 401:
            message = ResponseMessageEnum.FAILED
            description = "Unauthorized"
            data = {}  # Set data to be empty for unauthorized responses
        else:
            message = ResponseMessageEnum.FAILED
            try:
                # Try getting the message/description from the response's data
                description = data.get("detail", str(data))
                data = data.get("data", {})
            except Exception as e:
                logging.error(e)
                description = str(data)
                data = {}

        response = {"message": message, "description": description, "data": data}
        return super().render(response, accepted_media_type, renderer_context)


class BaseViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    This is a base viewset that you can inherit in your other viewsets.
    You should set the `model` attribute in your child viewsets.
    """

    model = None  # You should set this attribute in your child viewsets

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get query parameters from the request
        filters = {}
        ordering = []

        valid_fields = [f.name for f in self.model._meta.get_fields()]
        valid_lookups = [
            "exact",
            "iexact",
            "contains",
            "icontains",
            "gt",
            "gte",
            "lt",
            "lte",
        ]

        for key, value in self.request.query_params.items():
            if "__" in key:
                # Split the key into components
                components = key.split("__")
                # Get the potential lookup from the end
                potential_lookup = components[-1]
                # If it's a valid lookup, consider the rest to be the field
                if potential_lookup in valid_lookups:
                    lookup = potential_lookup
                    field = "__".join(components[:-1])
                else:
                    # If it's not a valid lookup, consider all components to be part of the field
                    field = key
                    lookup = "exact"  # Use a default lookup if none is specified
                # Only add to filters if the field is valid
                if field in valid_fields:
                    filters[key] = value
            elif key == "ordering":
                ordering = [
                    o for o in value.split(",") if o.lstrip("-") in valid_fields
                ]

        # Apply filters based on query parameters
        if filters:
            queryset = queryset.filter(**filters)

        # Apply ordering if specified
        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset


class XAPIKeyPermission(BasePermission):
    """
    Authentication class for x-api-key.
    """

    def has_permission(self, request, view):
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise AuthenticationFailed("API key not found.")
        elif api_key == X_API_KEY:
            return True
        raise AuthenticationFailed("Invalid API key.")


class XAPIKeyPermissionForServetelWebhook(BasePermission):
    """
    Authentication class for x-api-key.
    """

    def has_permission(self, request, view):
        api_key = request.headers.get("x-api-key")
        if not api_key:
            raise AuthenticationFailed("API key not found.")
        elif api_key == SERVETEL_WEBHOOK_X_API_KEY:
            return True
        raise AuthenticationFailed("Invalid API key.")


def only_get(data, dataModel, dataSerializer, key="id"):
    serializer = dataSerializer(data=data)
    # logger.debug("API: Serializer: " + str(serializer))
    if key in data:
        try:
            query = {"%s__exact" % key: data[key]}
            # logger.debug("API: Query: " + str(query))
            obj = dataModel.objects.filter(**query).get()
            return obj, True
        except dataModel.DoesNotExist:
            pass
    if serializer.is_valid(raise_exception=True):
        # logger.debug("API: Only Create Saving")
        return serializer.save(), False
    return None, None
    # model_obj, if exists status


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = drf_exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data["status_code"] = response.status_code

        # Handle 401 Unauthorized error
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            response.data["message"] = ResponseMessageEnum.FAILED
            response.data["description"] = "Unauthorized"
            response.data["data"] = {}

        # Transform 5xx server error to 4xx
        if 500 <= response.status_code < 600:
            response.status_code = status.HTTP_400_BAD_REQUEST
            response.data["message"] = ResponseMessageEnum.FAILED
            # Assuming 'exc' is your exception instance
            response.data["description"] = str(exc)
            response.data["data"] = {}
    else:
        # For unhandled exceptions, return a 400 error.
        response = Response(status=status.HTTP_400_BAD_REQUEST)
        response.data = str(exc)

    return response


class JSONClient(Client):
    def post(self, path, data=None, content_type="application/json", **extra):
        return super().post(path, data, content_type=content_type, **extra)


class CustomPagination(PageNumberPagination):
    page_size = 5  # Default page size
    page_size_query_param = 'page_size'  # Allows the client to set the page size via this query parameter
    max_page_size = 100  # Optional: Set a maximum page size limit
