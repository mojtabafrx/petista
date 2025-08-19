"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

app_name = "home"
urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include('home.urls'), name="home"),
                  path('captcha/', include('captcha.urls')),
                  path('account/', include('account.urls')),
                  path('products/', include('product.urls'), name="product"),
                  path('administrator/', include('administrator.urls')),
                  # path('api/', include('api.urls'), name="api"),

                  # path('api/', include('product.urls')),  # مسیر API

                  path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('panel/', include('user_panel.urls')),
                  path('transaction/', include('transaction.urls'), name='transaction'),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                                           document_root=settings.MEDIA_ROOT)
