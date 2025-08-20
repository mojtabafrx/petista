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


class SellerProductCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    price = serializers.IntegerField(min_value=1)
    stock = serializers.IntegerField(min_value=1)

    def validate_product_id(self, value):
        # بررسی وجود محصول
        try:
            Product.objects.get(id=value)
        except Product.DoesNotExist:
            raise serializers.ValidationError("محصولی با این ID وجود ندارد.")
        return value

    def validate(self, data):
        # بررسی اینکه کاربر فروشنده است
        request = self.context.get('request')
        if not request or not hasattr(request.user,
                                      'profile') or request.user.profile.user_type != request.user.profile.SELLER_USER:
            raise serializers.ValidationError("فقط فروشندگان می‌توانند محصول اضافه کنند.")

        return data
