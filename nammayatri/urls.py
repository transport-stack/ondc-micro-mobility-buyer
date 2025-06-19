from django.urls import path

from rest_framework import routers

from modules.env_main import ENABLE_RAPIDO_WEBHOOK
from nammayatri.views.book import BookView
from nammayatri.views.cancel import CancelView
from nammayatri.views.estimate import EstimateView
from nammayatri.views.order_update import OrderUpdateView

app_name = "nammayatri_api"

from modules.views import NoSlashRouter

router = NoSlashRouter()

urlpatterns = [
    # service end points
    path(f"book", BookView.as_view(), name="book"),
    path(f"cancel", CancelView.as_view(), name="cancel"),
    path(f"estimate", EstimateView.as_view(), name="estimate"),
    path(f"order-update-internal", OrderUpdateView.as_view(),name="order-update-internal",),
    # path(f"location-update", LocationUpdateView.as_view(), name="location-update"),
]
if ENABLE_RAPIDO_WEBHOOK:
    urlpatterns += [
        path(f"order-update", OrderUpdateView.as_view(), name="order-update"),
    ]
urlpatterns += router.urls
