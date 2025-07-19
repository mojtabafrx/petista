from pyexpat import model
from rest_framework import serializers
from user_panel.models import SellerProduct
from django.utils.text import slugify
import uuid
from product.models import Product
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from account.models import Profile , VerificationCode




class ProductSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Product
        fields = "__all__"


class AllProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["title", "description", "base_price"]




class CreateProductSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    price = serializers.IntegerField(min_value=0)
    stock = serializers.IntegerField(min_value=0)  # موجودی اولیه

    # فیلدهای اختیاری
    minimum_order = serializers.IntegerField(min_value=1, default=1, required=False)
    product_type = serializers.IntegerField(default=1, required=False)
    # category = serializers.PrimaryKeyRelatedField(
    #     queryset=Category.objects.all(),
    #     allow_null=True,
    #     required=False
    # )

    def create(self, validated_data):
        # تولید slug منحصر به فرد
        slug = slugify(validated_data['title'], allow_unicode=True)
        if not slug:
            slug = "product"

        unique_slug = slug
        while Product.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{uuid.uuid4().hex[:6]}"

        # ایجاد محصول
        product = Product.objects.create(
            title=validated_data['title'],
            description=validated_data['description'],
            slug=unique_slug,
            minimum_order=validated_data.get('minimum_order', 1),
            product_type=validated_data.get('product_type', 1),
            # category=validated_data.get('category', None),
            status=1  # وضعیت پیش‌فرض: موجود
        )

        # ایجاد محصول فروشنده (SellerProduct)
        seller = self.context['request'].user
        SellerProduct.objects.create(
            seller=seller,
            product=product,
            price=validated_data['price'],
            stock=validated_data['stock'],
            available_count=validated_data['stock']  # مقدار اولیه = stock
        )

        return product


# serializers.py

class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        if not Profile.objects.filter(user__username=value).exists():
            raise serializers.ValidationError("شماره تلفن ثبت نشده است")
        return value


class OTPSerializer(serializers.Serializer):
    verification_id = serializers.UUIDField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        verification_id = attrs['verification_id']
        code = attrs['code']

        try:
            ver_code = VerificationCode.objects.get(
                id=verification_id,
                is_used=False
            )
        except VerificationCode.DoesNotExist:
            raise serializers.ValidationError("کد تأیید نامعتبر است")

        if not ver_code.is_valid():
            raise serializers.ValidationError("کد منقضی شده یا قبلاً استفاده شده است")

        if ver_code.code != code:
            raise serializers.ValidationError("کد وارد شده نادرست است")

        attrs['ver_code'] = ver_code
        return attrs

