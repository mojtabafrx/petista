from django.urls import path
from . import views

app_name = 'user_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('get-products/', views.get_products, name='get_products'),
    path('add-seller-product/', views.add_seller_product, name='add_seller_product'),
    path('my-products/', views.my_products, name='my_products'),
    path('delete-product/', views.delete_product, name='delete_product'),
    path('get_product_details/', views.get_product_details, name='get_product_details'),
    path('edit_seller_product/', views.edit_seller_product, name='edit_seller_product'),
    path('change-password/', views.change_password, name='change_password'),
    path('change-password-ajax/', views.change_password_ajax, name='change_password_ajax'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('orders/<int:order_id>/details/', views.order_details, name='order_details'),
]