from django.urls import path, include

from journey.views.journey_setup import JourneyViewSet
from modules.views import NoSlashRouter

app_name = "journey"

router = NoSlashRouter()

# prefix = "journey"

router.register(r"", JourneyViewSet, "journey")

urlpatterns = [
    path("", include(router.urls)),
]
