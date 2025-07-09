from django.urls import path
from .views import signup , verify , login , verify_otp , resend_otp , logout
from rest_framework_simplejwt.views import TokenObtainPairView

app_name = "account"
urlpatterns = [
    path('signup/', signup, name="signup"),
    path('verify/<str:ver_id>/', verify, name='verify'),
    path('login/', login, name="login"),
    path('verify-otp/<uuid:ver_id>/', verify_otp, name='verify_otp'),
    path('resend-otp/', resend_otp, name='resend_otp'),
    path('token/', TokenObtainPairView.as_view()),
    path('logout/', logout, name='logout'),
]

