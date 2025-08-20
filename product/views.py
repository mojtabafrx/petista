from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models.expressions import RawSQL
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, permissions
from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import Profile
from user_panel.models import SellerProduct
from .models import Category, ProductImage
from .models import Product
from .serializers import ProductSerializer
from .serializers import SellerProductCreateSerializer


# Create your views here.
def category_list(request):
    return render(request, 'base/home.html')


def product_list(request, category_slug=None):
    categories = Category.objects.active()
    products = Product.objects.filter(status=1)

    category = None
    menu_list = Category.objects.filter(parent__isnull=True)
    if category_slug:
        category = Category.objects.filter(slug=category_slug).first()
        if not category:
            messages.error(request, "دسته بندی با این نام وجود ندارد.")
            return HttpResponseRedirect(reverse("product:product_list"))
        menu_list = Category.objects.filter(parent=category)
        products = products.filter(category__in=category.get_all_child())

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
    ).order_by('-total_available')

    if request.user.is_authenticated and request.user.is_superuser:
        products = products.all()
    elif not request.user.is_authenticated:
        products = products.filter(product_type=Product.RETAIL)
    elif request.user.profile.user_type == Profile.NORMAL_USER:
        products = products.filter(product_type=Product.RETAIL)
    elif request.user.profile.user_type == Profile.SELLER_USER:
        products = products.filter(product_type=Product.WHOLESALE)

    # تغییر در بخش صفحه‌بندی
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ایجاد لیستی از تمام تصاویر برای هر محصول
    product_images = {}
    for product in page_obj:
        images = ProductImage.objects.filter(product=product)
        product_images[product.id] = images

    context = {
        'products': products,
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'menu_list': menu_list,
        'product_images': product_images,  # اضافه کردن این خط
    }
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
    images = ProductImage.objects.filter(product=product)

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


# api section :


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('created_at')
    serializer_class = ProductSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    # فیلترها
    filterset_fields = ['category', 'status']  # فیلتر بر اساس دسته‌بندی/وضعیت
    search_fields = ['title', 'barcode']  # جستجو در عنوان/توضیحات
    ordering_fields = ['created_at', 'title']  # مرتب‌سازی بر اساس تاریخ/عنوان


class IsSellerUser(permissions.BasePermission):
    """بررسی اینکه کاربر حتماً فروشنده باشد"""

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                hasattr(request.user, 'profile') and
                request.user.profile.user_type == Profile.SELLER_USER
        )


class AddSellerProductAPIView(APIView):
    """
    API برای اضافه کردن محصول به لیست محصولات فروشنده
    با منطق: اگر همان محصول با همان قیمت وجود داشت، موجودی افزایش یابد
    اگر قیمت متفاوت بود، رکورد جدید ایجاد شود
    """
    permission_classes = [permissions.IsAuthenticated, IsSellerUser]

    def post(self, request):
        """
        افزودن یا به‌روزرسانی محصول برای فروشنده
        """
        serializer = SellerProductCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(
                {
                    "success": False,
                    "errors": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        product_id = serializer.validated_data['product_id']
        price = serializer.validated_data['price']
        stock = serializer.validated_data['stock']

        # بررسی وجود محصول
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": "محصولی با این ID وجود ندارد."
                },
                status=status.HTTP_404_NOT_FOUND
            )        # بررسی آیا همین محصول با همین قیمت از قبل وجود دارد


        # بررسی آیا همین محصول با همین قیمت از قبل وجود دارد
        existing_product = SellerProduct.objects.filter(
            seller=request.user,
            product=product,
            price=price
        ).first()

        if existing_product:
            # اگر وجود دارد، موجودی را افزایش می‌دهیم
            existing_product.stock += stock
            existing_product.available_count += stock
            existing_product.save()

            return Response(
                {
                    "success": True,
                    "message": "موجودی محصول با موفقیت افزایش یافت",
                    "data": {
                        "id": existing_product.id,
                        "product_id": product.id,
                        "product_title": product.title,
                        "price": existing_product.price,
                        "stock": existing_product.stock,
                        "available_count": existing_product.available_count,
                        "action": "updated"
                    }
                },
                status=status.HTTP_200_OK
            )
        else:
            # اگر وجود ندارد، رکورد جدید ایجاد می‌کنیم
            seller_product = SellerProduct.objects.create(
                seller=request.user,
                product=product,
                price=price,
                stock=stock,
                available_count=stock
            )

            return Response(
                {
                    "success": True,
                    "message": "محصول جدید با موفقیت به فروشگاه شما اضافه شد",
                    "data": {
                        "id": seller_product.id,
                        "product_id": product.id,
                        "product_title": product.title,
                        "price": seller_product.price,
                        "stock": seller_product.stock,
                        "available_count": seller_product.available_count,
                        "action": "created"
                    }
                },
                status=status.HTTP_201_CREATED
            )
