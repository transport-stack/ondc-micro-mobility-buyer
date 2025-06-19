from django.urls import path, include

from tickets.api.v1 import TicketsViewSetWebAPI

app_name = "tickets"

from modules.views import NoSlashRouter

router = NoSlashRouter()

router.register(r"", TicketsViewSetWebAPI, "web")

urlpatterns = [
    path("", include(router.urls)),
]
