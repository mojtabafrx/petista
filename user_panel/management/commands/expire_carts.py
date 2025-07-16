from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from user_panel.models import Cart, CartItem, SellerProduct
from django.db import transaction


class Command(BaseCommand):
    help = 'Expires old carts and returns products stock'

    def handle(self, *args, **options):
        # تنظیم زمان انقضا (24 ساعت)
        expire_time = timezone.now() - timedelta(seconds=10)

        # یافتن سبدهای فعال قدیمی‌تر از زمان انقضا
        expired_carts = Cart.objects.filter(
            is_active=True,
            created_at__lt=expire_time
        ).select_related('user').prefetch_related('items__seller_product')

        total_expired = expired_carts.count()
        if total_expired == 0:
            self.stdout.write(self.style.SUCCESS('No expired carts found.'))
            return

        self.stdout.write(f'Found {total_expired} expired carts. Processing...')

        processed_count = 0
        failed_count = 0

        for cart in expired_carts:
            try:
                with transaction.atomic():
                    # پردازش هر آیتم در سبد
                    for item in cart.items.all():
                        seller_product = item.seller_product

                        # برگرداندن موجودی به محصول
                        seller_product.available_count += item.quantity
                        seller_product.save()

                        # حذف آیتم سبد خرید
                        item.delete()

                    # غیرفعال کردن سبد خرید
                    # cart.is_active = False
                    cart.save()

                    processed_count += 1

            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f'Error processing cart #{cart.id}: {str(e)}'
                ))

        # گزارش نهایی
        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {processed_count} carts. '
            f'Failed: {failed_count}. '
            f'Total items returned: {processed_count}'
        ))