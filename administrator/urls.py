from django.urls import path, include
from .views import administrator

# app_name=

urlpatterns = [path('', administrator, name="administrator" ),
               ]
