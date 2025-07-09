from django.urls import path
from .views import send_request, verify
from . import views

urlpatterns = [
    path('request/', send_request, name='request'),
    path('verify/', verify , name='verify'),
]