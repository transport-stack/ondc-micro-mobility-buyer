"""ptx_core_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.views import APIView

from accounts.urls.mobile import router as accounts_router
from modules.env_main import DEBUG
from payments.urls import router as payments_router
from subscribe_app.views import verify_html
from transit.urls import router as transit_router


@extend_schema(exclude=True)
class RobotsTxtView(APIView):
    def get(self, request, format=None):
        content = "User-agent: *\nDisallow: /"
        return HttpResponse(content, content_type="text/plain")


def healthcheck_view(request):
    return HttpResponse("OK", content_type="text/plain", status=200)


def redirect_view(request):
    # Here you could add any logic if needed
    # TODO: uncomment in production
    # return HttpResponseRedirect('/api/v1/rapido/order-update')
    return 200


prefix_v1 = "api/v1"
web_prefix_v1 = "web/api/v1"
web_prefix_v2 = "web/api/v2"
urlpatterns = [
    path("robots.txt", RobotsTxtView.as_view(), name="robots-txt"),
    path("admin/", admin.site.urls),
    *accounts_router.urls,
    *payments_router.urls,
    *transit_router.urls,
    path(f"{prefix_v1}/ondc/delhi/mm/", include("ondc_micromobility_api.urls")),
    path(f"{prefix_v1}/ondc/nammayatri/", include("nammayatri.urls")),
    path(f"{prefix_v1}/ondc/", include("ondc_buyer_backend.urls.urls_with_prefix")),
    path("", include("ondc_buyer_backend.urls.urls_without_prefix")),

    path(f"{prefix_v1}/accounts/", include("accounts.urls.mobile")),
    path(f"{web_prefix_v1}/accounts/", include("accounts.urls.web")),

    path(f"{prefix_v1}/tickets/", include("tickets.urls.mobile")),
    path(f"{web_prefix_v1}/tickets/", include("tickets.urls.web")),
    path(f"{web_prefix_v2}/tickets/", include("tickets.urls.web_v2")),

    path(f"{prefix_v1}/journey/", include("journey.urls")),
    path(f"{prefix_v1}/coupons/", include("coupons.urls")),
    path(f"healthcheck", healthcheck_view, name="healthcheck"),
    path('', include('subscribe_app.urls')),
    path('ondc-site-verification.html', verify_html, name='verify_html')
]

# if DEBUG:
urlpatterns += [
    path(f"{prefix_v1}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{prefix_v1}/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        f"{prefix_v1}/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
