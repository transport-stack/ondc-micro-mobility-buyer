from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ondc_buyer_backend.views import on_search, estimate, on_select, on_init, on_estimate, on_confirm, on_update, on_track, on_status, on_cancel

urlpatterns = [
    # ONDC Search endpoints
    path('on_search', on_search.ONDCBuyerOnSearchViewSet.as_view({'post': 'buyer_on_search'})),
    # Buyer endpoints 
    path('on_select', on_select.ONDCBuyerOnSelectViewSet.as_view({'post': 'buyer_on_select'})),
    path('on_init', on_init.ONDCBuyerOnInitViewSet.as_view({'post': 'buyer_on_init'})),
    path('on_confirm', on_confirm.ONDCBuyerOnConfirmViewSet.as_view({'post': 'buyer_on_confirm'})),
    path('on_update', on_update.ONDCBuyerOnUpdateViewSet.as_view({'post': 'buyer_on_update'})),
    path('on_track', on_track.ONDCBuyerOnTrackViewSet.as_view({'post': 'buyer_on_track'})),
    path('on_status', on_status.ONDCBuyerOnStatusViewSet.as_view({'post': 'buyer_on_status'})),
    path('on_cancel', on_cancel.ONDCBuyerOnCancelViewSet.as_view({'post': 'buyer_on_cancel'})),

    # Buyer Estimate endpoints
    path('buyer/buyer-on-estimate/', on_estimate.ONDCBuyerOnEstimateViewSet.as_view({'get': 'buyer_on_estimate'})),
    path('buyer/buyer-estimate/', estimate.ONDCBuyerEstimateViewSet.as_view({'post': 'buyer_estimate'})),
]
