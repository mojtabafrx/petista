from django.urls import path 
from .views import signup , verify

app_name = "account"
urlpatterns = [
    path('signup/' , signup, name="signup"),
    path('verify/<str:ver_id>/', verify, name='verify'),
]

