from django.shortcuts import render , get_object_or_404
from .models import Product, Category, ProductImage
from user_panel.models import SellerProduct
from django.core.paginator import Paginator
from django.db.models.expressions import RawSQL
# Create your views here.
def category_list(request):
    return render(request,'base/home.html')


def product_list(request, category_slug=None):
    categories = Category.objects.active()
    products = Product.objects.filter(status=1)
    
    category = None
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    products = products.annotate(
        min_price=RawSQL(
            """
            (SELECT COALESCE(
                (SELECT MIN(price) 
                 FROM user_panel_sellerproduct 
                 WHERE product_id = product_product.id AND available_count > 0),
                0
            ) AS min_price)
            """, []
        ),
        total_available=RawSQL(
            """
            (SELECT COALESCE(
            (SELECT SUM(available_count) FROM user_panel_sellerproduct 
             WHERE product_id = product_product.id AND available_count > 0
             AND price = (SELECT MIN(price) FROM user_panel_sellerproduct
                          WHERE product_id = product_product.id AND available_count > 0)
            ) , 0) AS total_available)
            """, []
        )
    ).order_by('-created_at')

    # صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products' : products ,
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
    }
    # return JsonResponse({})
    return render(request, 'shop/product/list.html', context)

def product_detail(request, id, slug):
    product = Product.objects.filter(id=id, slug=slug).annotate(
        min_price=RawSQL(
            """
            (SELECT MIN(price) FROM user_panel_sellerproduct
             WHERE product_id = product_product.id AND available_count > 0)
            """, []
        ),
        total_available=RawSQL(
            """
            (SELECT SUM(available_count) FROM user_panel_sellerproduct 
             WHERE product_id = product_product.id AND available_count > 0
             AND price = (SELECT MIN(price) FROM user_panel_sellerproduct
                          WHERE product_id = product_product.id AND available_count > 0)
            )
            """, []
        )
    ).order_by('-created_at').first()
    images = get_object_or_404(ProductImage ,product = product)
    
    # محصولات مرتبط
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]  # حداکثر 4 محصول مرتبط
    
    context = {
        'product': product,
        'images': images,
        'related_products': related_products,
    }
    return render(request, 'shop/product/detail.html', context)



