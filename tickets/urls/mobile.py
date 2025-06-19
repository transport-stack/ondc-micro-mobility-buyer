from django.urls import path, include

from tickets.views.general import TicketsViewSet

app_name = "tickets"

from modules.views import NoSlashRouter

router = NoSlashRouter()

router.register(r"", TicketsViewSet, "ticket")

urlpatterns = [
    path("", include(router.urls)),
]
