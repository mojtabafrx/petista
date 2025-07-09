from django.shortcuts import render , get_object_or_404
from .models import Product, Category, ProductImage
from django.core.paginator import Paginator

# Create your views here.
def category_list(request):
    return render(request,'base/home.html')



def product_list(request, category_slug=None):
    # دریافت دسته‌بندی‌ها
    categories = Category.objects.active()
    
    # فیلتر محصولات بر اساس دسته‌بندی
    products = Product.objects.filter(status=1)  # فقط محصولات موجود
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    else:
        category = None
    
    # صفحه‌بندی
    paginator = Paginator(products, 12)  # نمایش 12 محصول در هر صفحه
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
    product = get_object_or_404(Product, id=id, slug=slug)
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