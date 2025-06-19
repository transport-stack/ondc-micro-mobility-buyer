from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ondc_buyer_backend.views import on_search, estimate, on_select, on_init, on_estimate, on_confirm, on_update, on_track, on_status

urlpatterns = [
    # ONDC Search endpoints
    path('buyer/on_search', on_search.ONDCBuyerOnSearchViewSet.as_view({'post': 'buyer_on_search'})),
    # Buyer endpoints 
    path('buyer/on_select', on_select.ONDCBuyerOnSelectViewSet.as_view({'post': 'buyer_on_select'})),
    path('buyer/on_init', on_init.ONDCBuyerOnInitViewSet.as_view({'post': 'buyer_on_init'})),
    path('buyer/on_confirm', on_confirm.ONDCBuyerOnConfirmViewSet.as_view({'post': 'buyer_on_confirm'})),
    path('buyer/on_update', on_update.ONDCBuyerOnUpdateViewSet.as_view({'post': 'buyer_on_update'})),
    path('buyer/on_track', on_track.ONDCBuyerOnTrackViewSet.as_view({'post': 'buyer_on_track'})),
    path('buyer/on_status', on_status.ONDCBuyerOnStatusViewSet.as_view({'post': 'buyer_on_status'})),

    # Buyer Estimate endpoints
    path('buyer/buyer-on-estimate/', on_estimate.ONDCBuyerOnEstimateViewSet.as_view({'get': 'buyer_on_estimate'})),
    path('buyer/buyer-estimate/', estimate.ONDCBuyerEstimateViewSet.as_view({'post': 'buyer_estimate'})),
]
