from django.http import JsonResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

from modules.env_main import X_API_KEY


def check_api_key(view_func):
    def _decorator(request, *args, **kwargs):
        api_key = request.META.get("HTTP_X_API_KEY", None)

        if api_key != X_API_KEY:
            return JsonResponse({"error": "Invalid API key"}, status=403)

        return view_func(request, *args, **kwargs)

    return _decorator


X_API_KEY_AND_UID_PARAMETERS = [
    OpenApiParameter(
        name="x-api-key",
        description="API key",
        required=True,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
    ),
    OpenApiParameter(
        name="x-uid",
        description="User identifier",
        required=True,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
    ),
]

X_API_KEY_PARAMETERS = [
    OpenApiParameter(
        name="x-api-key",
        description="API key",
        required=True,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
    )
]

