from django.db import models
from django.contrib.auth import get_user_model
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
        unique_together = ['seller', 'product']

    def __str__(self):
        return f"{self.product.title} توسط {self.seller.username}"
    def save(self, *args, **kwargs):
        self.available_count = self.stock
        return super(SellerProduct, self).save(*args, **kwargs)