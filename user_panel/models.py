from django.contrib.auth import get_user_model
from django.db import models

from product.models import Product

User = get_user_model()


class SellerProduct(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sellers')
    price = models.PositiveIntegerField(verbose_name="قیمت فروش")
    stock = models.PositiveIntegerField(verbose_name="موجودی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    available_count = models.PositiveIntegerField()
    sell_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'محصول فروشنده'
        verbose_name_plural = 'محصولات فروشندگان'
        # unique_together = ['seller', 'product']

    def __str__(self):
        return f"{self.product.title} توسط {self.seller.username}"

    def save(self, *args, **kwargs):
        # فقط زمانی که شیء جدید ایجاد می‌شود یا stock تغییر کرده است
        if self.pk is None or SellerProduct.objects.get(pk=self.pk).stock != self.stock:
            self.available_count = self.stock
        super(SellerProduct, self).save(*args, **kwargs)


class Cart(models.Model):
    PENDING = 0
    PAID = 1
    CANCELLED = 2
    PROCESSING = 3
    SEND = 4
    STATUS_CHOICES = (
        (PENDING, 'در انتظار پرداخت'),
        (PAID, 'پرداخت شده'),
        (CANCELLED, 'لغو شده'),
        (PROCESSING, 'در حال آماده سازی'),
        (SEND, 'تحویل به پست'),

    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)
    tracking_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="کد رهگیری")

    class Meta:
        verbose_name = 'سبد خرید'
        verbose_name_plural = 'سبدهای خرید'

    def __str__(self):
        return f"سبد خرید {self.user.username} - {self.created_at}"

    def total_price(self):
        """محاسبه مجموع قیمت تمام آیتم‌های سبد خرید"""
        return sum(item.total_price() for item in self.items.all())

    def total_items(self):
        return self.items.count()

    def get_status_display_class(self):
        status_classes = {
            self.PENDING: 'pending',
            self.PAID: 'paid',
            self.CANCELLED: 'cancelled',
            self.PROCESSING: 'processing'
        }
        return status_classes.get(self.status, '')


class CartItem(models.Model):
    START = 0
    PROCESSING = 1
    TRANSFER = 2
    SEND = 3

    STATUS_CHOICES = (
        (START, 'در انتظار تایید'),
        (PROCESSING, 'تایید شده'),
        (TRANSFER, 'در حال جمع آوری'),
        (SEND, 'تحویل به پست')
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=START)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    seller_product = models.ForeignKey(SellerProduct, on_delete=models.CASCADE, verbose_name="محصول فروشنده")
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    added_at = models.DateTimeField(auto_now_add=True)
    price = models.PositiveIntegerField(default=None, null=True, verbose_name="قیمت خریداری شده")

    # price

    class Meta:
        verbose_name = 'آیتم سبد خرید'
        verbose_name_plural = 'آیتم‌های سبد خرید'
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.quantity} عدد {self.seller_product.product.title}"

    def total_price(self):
        return self.quantity * self.price

    def unit_price(self):
        return self.seller_product.price

# Orders Section
#
# class Order(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
#     total_price = models.PositiveIntegerField(verbose_name="جمع کل")
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     STATUS_CHOICES = (
#         ('pending', 'در انتظار پرداخت'),
#         ('paid', 'پرداخت شده'),
#         ('shipped', 'ارسال شده'),
#         ('delivered', 'تحویل داده شده'),
#         ('cancelled', 'لغو شده'),
#     )
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="وضعیت")
#     tracking_code = models.CharField(max_length=50, null=True, blank=True, verbose_name="کد رهگیری")
#
#     class Meta:
#         verbose_name = 'سفارش'
#         verbose_name_plural = 'سفارشات'
#         ordering = ['-created_at']
#
#     def __str__(self):
#         return f"سفارش #{self.id} - {self.user.username}"
#
#
# class OrderItem(models.Model):
#     order = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
#     seller_product = models.ForeignKey(SellerProduct, on_delete=models.CASCADE, verbose_name="محصول فروشنده")
#     quantity = models.PositiveIntegerField(verbose_name="تعداد")
#     price = models.PositiveIntegerField(verbose_name="قیمت واحد")
#
#     class Meta:
#         verbose_name = 'آیتم سفارش'
#         verbose_name_plural = 'آیتم‌های سفارش'
#
#     def __str__(self):
#         return f"{self.quantity} عدد {self.seller_product.product.title}"
#
#     def total_price(self):
#         return self.quantity * self.price
