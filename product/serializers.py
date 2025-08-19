from rest_framework import serializers

from user_panel.models import SellerProduct  # اطمینان حاصل کنید مسیر درست است
from .models import Product, ProductImage, Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug', 'image']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text']


class SellerProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProduct
        fields = ['id', 'price', 'stock', 'available_count']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(
        source='additional_images',  # استفاده از related_name اصلی
        many=True,
        read_only=True
    )
    sellers = SellerProductSerializer(  # حذف source='sellers'
        many=True,
        read_only=True
    )
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description',
            'minimum_order', 'category', 'status',
            'created_at', 'images', 'sellers', 'barcode'
        ]
