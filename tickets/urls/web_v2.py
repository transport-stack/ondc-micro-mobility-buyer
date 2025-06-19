from django.urls import path, include

from tickets.api.v2 import TicketsViewSetWebV2API

app_name = "tickets"

from modules.views import NoSlashRouter

router = NoSlashRouter()

router.register(r"", TicketsViewSetWebV2API, "web_v2")

urlpatterns = [
    path("", include(router.urls)),
]
