from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.db.models import Count, Prefetch
from django.db.models.expressions import RawSQL
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from account.models import Profile
from product.models import Category, Product
from .decorators import user_panel_access, seller_required, redirect_superusers
from .forms import ProductForm, ChangePasswordForm
from .models import SellerProduct, Cart, CartItem


@login_required(login_url='account:login')
@user_panel_access
@redirect_superusers
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
def get_products(request):
    """دریافت محصولات با AJAX بر اساس دسته‌بندی"""
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse([], safe=False)
    user_type = request.user.profile.user_type
    if user_type == Profile.SELLER_USER:
        products = Product.objects.filter(
            category_id=category_id,
            product_type=2,
            status=1  # موجود
        ).values('id', 'title')
    else:
        products = Product.objects.filter(
            category_id=category_id,
            product_type=1,
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
        if price and stock:
            if type(price) != int or type(stock) != int:
                messages.error(request, 'قیمت و موجودی باید عدد وارد شود.')
                return HttpResponseRedirect(reverse('user_panel:add_seller_product'))
        else:
            messages.error(request, 'باید هر دو مقدار قیمت و موجودی را وارد کنید.')
            return HttpResponseRedirect(reverse('user_panel:add_seller_product'))
        try:
            exist = SellerProduct.objects.filter(product_id=product_id, seller=request.user, price=price).first()

            def create_seller(seller, product_id, price, stock):
                SellerProduct.objects.create(
                    seller=seller,
                    product_id=product_id,
                    price=int(price),
                    stock=int(stock),
                    available_count=int(stock)
                )

            if exist:
                exist.stock += int(stock)
                exist.save()
            else:
                create_seller(request.user, product_id, price, stock)
            return (HttpResponseRedirect(reverse('user_panel:my_products')))
        except Product.DoesNotExist:
            return (HttpResponseRedirect(reverse('user_panel:add_seller_product')))
    else:
        categories = Category.objects.active().annotate(product_count=Count('products')).filter(product_count__gt=0)
        context = {
            'user_type': request.user.profile.user_type,
            'categories': categories,
            'section': 'dashboard'  # بخش پیش‌فرض
        }
        return render(request, 'user_panel/add_seller_product.html', context)


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
    return render(request, 'user_panel/seller_products.html', context)


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
def edit_seller_product(request, product_id=None):
    """ویرایش محصول فروشنده"""
    product = SellerProduct.objects.filter(id=product_id, seller=request.user).first()
    if not product:
        messages.error(request, "این محصول در محصولات شما موجود نمی باشد.")
        return HttpResponseRedirect(reverse("user_panel:my_products"))
    form = ProductForm(request.POST or None, instance=product)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("user_panel:my_products"))

    return render(request, 'user_panel/seller_edit_product.html', context={'form': form})


@user_panel_access
def change_password(request):
    form = ChangePasswordForm(request.user, request.POST)

    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # بروزرسانی session برای جلوگیری از خروج کاربر
            update_session_auth_hash(request, user)
            return render(request, 'user_panel/dashboard.html',
                          context={'message': 'رمز عبور شما با موفقیت تغییر یافت'})
        else:
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    # errors.append(error)
                    messages.error(request, error)
            return HttpResponseRedirect(reverse("user_panel:change_password"))
    else:
        """ویو تغییر رمز عبور"""
        context = {
            'user_type': request.user.profile.user_type,
            'section': 'change_password'
        }
        return render(request, 'user_panel/change_password.html', context)


@redirect_superusers
@user_panel_access
def view_cart(request):
    """نمایش سبد خرید"""
    # یافتن سبد خرید فعال کاربر
    # cart = Cart.objects.get_or_create(user=request.user, is_active=True)
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    context = {
        'cart': cart,
        'user_type': request.user.profile.user_type,
        'section': 'cart'
    }
    if cart:
        return render(request, 'user_panel/shopping-cart.html', context)
    return render(request, 'user_panel/no_product.html', context)


@redirect_superusers
@user_panel_access
def add_to_cart(request, product_id):
    """افزودن محصول به سبد خرید"""
    try:
        with transaction.atomic():
            count = int(request.POST.get('count', 1))
            product = Product.objects.select_for_update().filter(id=product_id)
            # cart = get_object_or_404(Cart, user=request.user, is_active=True)
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
            # seller_product = SellerProduct.objects.filter(price=product.min_price).first()
            # یافتن محصول با کمترین قیمت و موجودی کافی
            seller_product = SellerProduct.objects.select_for_update().filter(
                product_id=product_id,
                available_count__gte=count,
                price=product.min_price
            ).order_by('price').first()

            if not seller_product:
                return JsonResponse({'success': False, 'error': 'موجودی محصول کافی نیست'})

            # کاهش available_count

            seller_product.available_count -= count
            seller_product.save()

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
                    'quantity': count,
                    'price': seller_product.price,
                }
            )

            # اگر محصول قبلاً در سبد وجود داشته، تعداد را افزایش می‌دهیم
            if not item_created:
                cart_item.quantity += count
                cart_item.save()

            return JsonResponse({
                'success': True,
                'message': 'محصول به سبد خرید اضافه شد',
                'cart_items_count': cart.total_items(),
                'available_count': seller_product.available_count,
            })

    except Exception as e:
        # برگرداندن خطا با جزئیات
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


#
# @user_panel_access
# def cart_detail(request):
#     """نمایش جزئیات سبد خرید"""
#     cart = get_object_or_404(Cart, user=request.user, is_active=True)
#     context = {
#         'cart': cart,
#         'user_type': request.user.profile.user_type,
#         'section': 'cart'
#     }
#     return render(request, 'user_panel/cart_detail.html', context)


@user_panel_access
def update_cart_item(request, item_id):
    """به‌روزرسانی آیتم سبد خرید"""

    try:
        with transaction.atomic():
            count = request.POST.get('count', 1)
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            seller_product = SellerProduct.objects.select_for_update().get(id=cart_item.seller_product.id)

            action = request.POST.get('action')
            if action == 'increment':
                if seller_product.available_count >= count:
                    seller_product.available_count -= count
                    seller_product.save()
                    cart_item.quantity += count
                    cart_item.save()
                else:
                    return JsonResponse({'success': False, 'error': 'موجودی کافی نیست'})

            elif action == 'decrement' and cart_item.quantity >= count:
                seller_product.available_count += count
                seller_product.save()
                cart_item.quantity -= count
                cart_item.save()

                if cart_item.quantity <= 0:
                    cart_item.delete()

            return JsonResponse({
                'success': True,
                'new_quantity': cart_item.quantity,
                'item_total': cart_item.total_price(),
                'cart_total': cart_item.cart.total_price(),
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@user_panel_access
def remove_cart_item(request, item_id):
    """حذف آیتم از سبد خرید"""
    try:
        with transaction.atomic():
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            seller_product = SellerProduct.objects.select_for_update().get(id=cart_item.seller_product.id)

            # برگرداندن موجودی
            seller_product.available_count += cart_item.quantity
            seller_product.save()

            cart_item.delete()

            return JsonResponse({
                'success': True,
                'cart_total': cart_item.cart.total_price(),
                'cart_items_count': cart_item.cart.total_items()
            })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# for Orders section ->

@user_panel_access
def my_orders(request):
    """نمایش سفارشات کاربر"""
    orders = Cart.objects.filter(user=request.user).order_by('-created_at')

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
    return render(request, 'user_panel/orders_list.html', context)


@user_panel_access
def order_details(request, order_id):
    """دریافت جزئیات یک سفارش به صورت JSON"""
    order = get_object_or_404(Cart, id=order_id, user=request.user)
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


@user_panel_access
@transaction.atomic
def checkout(request, cart_id):
    """پرداخت نهایی و ایجاد سفارش"""
    cart = get_object_or_404(Cart, user=request.user, pk=cart_id)
    if cart.status != Cart.PENDING:
        messages.error(request, "این سفارش در وضعیت انتظار پرداخت نیست.")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))

    # بررسی وجود آیتم در سبد خرید
    if cart.items.count() == 0:
        cart.delete()
        messages.error(request, "سبد خرید شما خالی است")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))

    # بررسی موجودی کافی برای همه محصولات
    for item in cart.items.all():
        if (item.seller_product.stock - item.seller_product.sell_count) < item.seller_product.available_count:
            messages.error(request, f'موجودی کافی برای محصول {item.seller_product.product.title} وجود ندارد')
            return HttpResponseRedirect(reverse("user_panel:my_orders"))

    try:
        return HttpResponseRedirect(reverse('transaction:request', kwargs={'order_id': cart.id}))
    except Exception as e:
        messages.error(request, f'خطا در ثبت سفارش: {str(e)}')
        return HttpResponseRedirect(reverse("user_panel:my_orders"))


def seller_orders(request):
    seller = request.user

    # دریافت سفارشات مرتبط با محصولات فروشنده
    carts = Cart.objects.filter(
        items__seller_product__seller=seller,
    ).exclude(status__in=[Cart.PENDING]  # فقط سفارشات پرداخت شده و در حال پردازش
              ).distinct().prefetch_related(
        Prefetch(
            'items',
            queryset=CartItem.objects.filter(seller_product__seller=seller)
            .select_related('seller_product__product'),
            to_attr='seller_items'
        )
    ).order_by('-created_at')  # مرتب سازی بر اساس تاریخ جدیدترین
    total_seller_price = 0
    for cart in carts:
        for item in cart.seller_items:
            total_seller_price += item.total_price()
    context = {
        'carts': carts,
        'user_type': request.user.profile.user_type,
        'total_seller_price': total_seller_price,
    }
    return render(request, 'user_panel/seller_orders.html', context)


@login_required
def cart_item_detail(request, cart_id):
    # دریافت سبد خرید با بررسی مالکیت کاربر
    cart = get_object_or_404(
        Cart.objects.select_related('user')
        .prefetch_related('items__seller_product__product',
                          'items__seller_product__seller'),
        id=cart_id,
        user=request.user
    )

    # محاسبه قیمت نهایی با احتساب مالیات و تخفیف (در صورت نیاز)
    # total_price = cart.total_price()
    # final_price = total_price  # می‌توانید محاسبات بیشتری انجام دهید

    context = {
        'cart': cart,
        # 'final_price': final_price,
    }
    return render(request, 'user_panel/cart_item_detail.html', context)


def chang_cart_item_status(request, cart_id):
    seller = request.user

    # دریافت سفارشات مرتبط با محصولات فروشنده
    carts = Cart.objects.filter(
        id=cart_id,
        items__seller_product__seller=seller,
    ).distinct().prefetch_related(
        Prefetch(
            'items',
            queryset=CartItem.objects.filter(seller_product__seller=seller)
            .select_related('seller_product__product'),
            to_attr='seller_items'
        )
    ).order_by('-created_at').first()
    for item in carts.items.all():
        item.status = item.PROCESSING
        item.save()

    cart = Cart.objects.get(id=cart_id)
    all_status = cart.items.first().status
    cart_status = {
        CartItem.START: Cart.PAID,
        CartItem.PROCESSING: Cart.PROCESSING,
        CartItem.TRANSFER: Cart.PROCESSING,
        CartItem.SEND: Cart.SEND,
    }

    for item in cart.items.all():
        if item.status != all_status:
            break
    else:
        cart.status = cart_status[all_status]
        cart.save()

    messages.success(request, 'وضعیت سفارش با موفقیت تغییر یافت')
    return HttpResponseRedirect(reverse('user_panel:seller_orders'))
