from django.urls import path
from . import views
app_name = "transaction"
urlpatterns = [
    path('request/<int:order_id>', views.send_request, name='request'),
    path('verify/', views.verify, name='verify'),
]