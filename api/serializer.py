from product.models import Product
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from account.models import Profile , VerificationCode

class ProductSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Product
        fields = "__all__"


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

# User = get_user_model()
#
# class OTPSerializer(serializers.Serializer):
#     username = serializers.CharField()
#     otp = serializers.CharField(max_length=6)
#
#     def validate(self, attrs):
#         username = attrs.get('username')
#         otp = attrs.get('otp')
#
#         # 1. بررسی وجود کاربر
#         try:
#             user = User.objects.get(username=username)
#         except User.DoesNotExist:
#             raise serializers.ValidationError('User not found')
#
#         # 2. اعتبارسنجی OTP (پیاده‌سازی منطق تأیید کد)
#         if not self.verify_otp(username, otp):  # تابع دلخواه شما
#             raise serializers.ValidationError('Invalid OTP')
#
#         # 3. ایجاد توکن‌ها
#         refresh = RefreshToken.for_user(user)
#         return {
#             'user': user.username,
#             'access': str(refresh.access_token),
#             'refresh': str(refresh)
#         }
#
#     def verify_otp(self, phone, otp):
#         # پیاده‌سازی منطق بررسی OTP
#         # مثال: چک کردن با پایگاه داده یا سرویس خارجی
#         return True  # جایگزین با منطق واقعی