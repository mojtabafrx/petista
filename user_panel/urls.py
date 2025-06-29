from django.urls import path
from . import views

app_name = 'user_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('get-products/', views.get_products, name='get_products'),
    path('add-seller-product/', views.add_seller_product, name='add_seller_product'),
    path('my-products/', views.my_products, name='my_products'),
    path('delete-product/', views.delete_product, name='delete_product'),
]