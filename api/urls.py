from django.urls import path

from api.views import Product_detail, ProtectedView, OTPLoginView, SendOTPView, VerifyOTPView, HealthView

app_name = "api"

urlpatterns = [path('product/<int:pk>/', Product_detail, name="product_detail"),
               path('protected/', ProtectedView.as_view(), name='protected_api'),
               path('otp/login/', OTPLoginView.as_view(), name='otp_login'),
               path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
               path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
               path('health/', HealthView.as_view(), name='healthcheck'),
               ]
