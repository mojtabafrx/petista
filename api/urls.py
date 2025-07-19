from django.urls import path, include
from api.views import Product_detail, ProtectedView,OTPLoginView,SendOTPView,VerifyOTPView,ProductListAPIView,HealthCheckView, CreateProductView

# app_name=

urlpatterns = [path('product/<int:pk>/', Product_detail, name="product_detail"),
               path('products/', ProductListAPIView.as_view(), name='product-list'),
               path('protected/', ProtectedView.as_view(), name='protected_api'),
               path('otp/login/', OTPLoginView.as_view(), name='otp_login'),
                path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
                path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
                path('health/', HealthCheckView.as_view(), name='healthcheck'),
                path('products/create/', CreateProductView.as_view(), name='create-product'),]



