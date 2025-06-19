from django.urls import path
from .views import on_subscribe, subscribe, verify_html

urlpatterns = [
    path('on_subscribe', on_subscribe, name='on_subscribe'),
    path('subscribe', subscribe, name='subscribe'),
]
