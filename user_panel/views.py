from django.shortcuts import render
from django.http import JsonResponse
from .decorators import user_panel_access, seller_required
from account.models import Profile
from product.models import Category, Product
from .models import SellerProduct
from django.core.paginator import Paginator


@user_panel_access
def dashboard(request):
    """ویو اصلی پنل کاربری"""
    # فقط برای فروشندگان دسته‌بندی‌ها را فراخوانی می‌کنیم
    categories = None
    if request.user.profile.user_type == Profile.SELLER_USER:
        categories = Category.objects.active()
    
    context = {
        'user_type': request.user.profile.user_type,
        'categories': categories,
        'section': 'dashboard'  # بخش پیش‌فرض
    }
    return render(request, 'user_panel/dashboard.html', context)

@user_panel_access
@seller_required
def get_products(request):
    """دریافت محصولات با AJAX بر اساس دسته‌بندی"""
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse([], safe=False)
    
    products = Product.objects.filter(
        category_id=category_id,
        status=1  # موجود
    ).values('id', 'title')
    
    return JsonResponse(list(products), safe=False)

@user_panel_access
@seller_required
def add_seller_product(request):
    """ثبت محصول برای فروشنده (با AJAX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        try:
            product = Product.objects.get(id=product_id)
            # ایجاد یا به‌روزرسانی محصول فروشنده
            SellerProduct.objects.update_or_create(
                seller=request.user,
                product=product,
                defaults={'price': price, 'stock': stock}
            )
            return JsonResponse({'success': True, 'message': 'محصول با موفقیت ثبت شد'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'محصول معتبر نیست'})
    
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})



@user_panel_access
@seller_required
def my_products(request):
    """نمایش محصولات ثبت شده توسط فروشنده"""
    # دریافت محصولات فروشنده
    seller_products = SellerProduct.objects.filter(seller=request.user).order_by('-created_at')
    
    # صفحه‌بندی
    page = request.GET.get('page', 1)
    paginator = Paginator(seller_products, 10)  # 10 محصول در هر صفحه
    
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)
    
    context = {
        'user_type': request.user.profile.user_type,
        'products_page': products_page,
        'section': 'my_products'  # برای شناسایی بخش در تمپلیت
    }
    return render(request, 'user_panel/dashboard.html', context)


@user_panel_access
@seller_required
def delete_product(request):
    """حذف محصول فروشنده با AJAX"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        try:
            product = SellerProduct.objects.get(
                id=product_id,
                seller=request.user
            )
            product.delete()
            return JsonResponse({'success': True, 'message': 'محصول با موفقیت حذف شد'})
        except SellerProduct.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'محصول یافت نشد'})
    
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})
