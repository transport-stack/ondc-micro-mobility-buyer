from django.urls import path, include
from ondc_micromobility_api.views.estimate import EstimateView
app_name = "ondc_micromobility_api"

from modules.views import NoSlashRouter

router = NoSlashRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(f"estimate", EstimateView.as_view(), name="estimate"),
]

urlpatterns += router.urls
