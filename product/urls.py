from django.urls import path
from .views import product_list , product_detail

app_name = "product"
urlpatterns = [
    # لیست محصولات
    path('', product_list, name='product_list'),
    
    # لیست محصولات بر اساس دسته‌بندی
    path('category/<slug:category_slug>/', 
         product_list, 
         name='product_list_by_category'),
    
    # جزئیات محصول
    path('<int:id>/<slug:slug>/', 
         product_detail, 
         name='product_detail'),
]
