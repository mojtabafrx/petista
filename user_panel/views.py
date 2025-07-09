from django.db.models.expressions import RawSQL
from django.shortcuts import render , get_object_or_404
from django.http import JsonResponse
from .decorators import user_panel_access, seller_required
from account.models import Profile
from product.models import Category, Product
from .models import SellerProduct , Cart , CartItem ,Order, OrderItem
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm


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

# اضافه کردن ویو برای دریافت اطلاعات محصول جهت ویرایش
@user_panel_access
@seller_required
def get_product_details(request):
    """دریافت جزئیات محصول فروشنده برای ویرایش"""
    product_id = request.GET.get('product_id')
    try:
        product = SellerProduct.objects.get(id=product_id, seller=request.user)
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'price': product.price,
                'stock': product.stock
            }
        })
    except SellerProduct.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'محصول یافت نشد'})

# اضافه کردن ویو برای ذخیره تغییرات ویرایش
@user_panel_access
@seller_required
def edit_seller_product(request):
    """ویرایش محصول فروشنده"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        
        try:
            product = SellerProduct.objects.get(id=product_id, seller=request.user)
            product.price = price
            product.stock = stock
            product.save()
            return JsonResponse({'success': True, 'message': 'تغییرات با موفقیت ذخیره شد'})
        except SellerProduct.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'محصول یافت نشد'})
    
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})


@user_panel_access
def change_password(request):
    """ویو تغییر رمز عبور"""
    context = {
        'user_type': request.user.profile.user_type,
        'section': 'change_password'
    }
    return render(request, 'user_panel/dashboard.html', context)

@user_panel_access
def change_password_ajax(request):
    """تغییر رمز عبور با AJAX"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # بروزرسانی session برای جلوگیری از خروج کاربر
            update_session_auth_hash(request, user)
            return JsonResponse({'success': True, 'message': 'رمز عبور شما با موفقیت تغییر یافت'})
        else:
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(error)
            return JsonResponse({'success': False, 'errors': errors})
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})


@user_panel_access
def view_cart(request):
    """نمایش سبد خرید"""
    # یافتن سبد خرید فعال کاربر
    cart = get_object_or_404(Cart, user=request.user, is_active=True)

    context = {
        'cart': cart,
        'user_type': request.user.profile.user_type,
        'section': 'cart'
    }
    return render(request, 'user_panel/dashboard.html', context)

@user_panel_access
def add_to_cart(request, product_id):
    """افزودن محصول به سبد خرید"""
    product = Product.objects.filter( id=product_id)
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    product = product.annotate(
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
    seller_product = SellerProduct.objects.filter(price = product.min_price).first()

    # یافتن سبد خرید فعال کاربر یا ایجاد یک سبد جدید
    cart, created = Cart.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'user': request.user}
    )

    # بررسی آیا محصول قبلاً در سبد وجود دارد
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        seller_product=seller_product,
        defaults={
            'seller_product': seller_product,
            'quantity': 1
        }
    )

    # اگر محصول قبلاً در سبد وجود داشته، تعداد را افزایش می‌دهیم
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    return JsonResponse({
        'success': True,
        'message': 'محصول به سبد خرید اضافه شد',
        'cart_items_count': cart.total_items()
    })


@user_panel_access
def cart_detail(request):
    """نمایش جزئیات سبد خرید"""
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    context = {
        'cart': cart,
        'user_type': request.user.profile.user_type,
        'section': 'cart'
    }
    return render(request, 'user_panel/cart_detail.html', context)


@user_panel_access
def update_cart_item(request, item_id):
    """به‌روزرسانی آیتم سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    action = request.POST.get('action')
    if action == 'increment':
        cart_item.quantity += 1
    elif action == 'decrement' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    cart_item.save()

    return JsonResponse({
        'success': True,
        'new_quantity': cart_item.quantity,
        'item_total': cart_item.total_price(),
        'cart_total': cart_item.cart.total_price()
    })


@user_panel_access
def remove_cart_item(request, item_id):
    """حذف آیتم از سبد خرید"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    return JsonResponse({
        'success': True,
        'cart_total': cart_item.cart.total_price(),
        'cart_items_count': cart_item.cart.total_items()
    })




# for Orders section ->

@user_panel_access
def my_orders(request):
    """نمایش سفارشات کاربر"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # صفحه‌بندی
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)  # 10 سفارش در هر صفحه

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    context = {
        'user_type': request.user.profile.user_type,
        'orders_page': orders_page,
        'section': 'my_orders'  # برای شناسایی بخش در تمپلیت
    }
    return render(request, 'user_panel/dashboard.html', context)


@user_panel_access
def order_details(request, order_id):
    """دریافت جزئیات یک سفارش به صورت JSON"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all().select_related('seller_product__product', 'seller_product__seller')

    # ساخت لیست آیتم‌ها
    items_list = []
    for item in items:
        items_list.append({
            'product_title': item.seller_product.product.title,
            'seller_username': item.seller_product.seller.username,
            'price': item.price,
            'quantity': item.quantity,
            'total_price': item.total_price()
        })

    return JsonResponse({
        'success': True,
        'order': {
            'id': order.id,
            'created_at': order.created_at.strftime("%Y/%m/%d %H:%M"),
            'status': order.status,
            'status_display': order.get_status_display(),
            'total_price': order.total_price,
            'tracking_code': order.tracking_code
        },
        'items': items_list
    })