import random

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from account.models import VerificationCode, Profile
from product.models import Product
from .serializer import ProductSerializer, OTPSerializer, PhoneSerializer


# @permision()
@api_view(['PUT', 'GET', 'DELETE'])
def Product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)

    except Product.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # if request.user.profile.type in []
        serializer = ProductSerializer(product, )
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# api

class ProtectedView(APIView):
    permissionclass = [IsAuthenticated]

    def get(self, request):
        return Response({'message': f"Hey, you are successfully signed in."})


class OTPLoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print(request.data)
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class SendOTPView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print("hjkn")
        serializer = PhoneSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data['phone']
        profile = Profile.objects.get(phone_number=phone)

        # تولید کد 6 رقمی
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # ایجاد رکورد تأیید (10 دقیقه اعتبار)
        ver_code = VerificationCode.objects.create(
            profile=profile,
            code_type=VerificationCode.LOGIN_OTP,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10))

        # ارسال پیامک (پیاده‌سازی واقعی این بخش)
        self.send_sms(phone, code)

        return Response({
            'status': 'success',
            'message': 'کد تأیید ارسال شد',
            'verification_id': str(ver_code.id),
            'expires_at': ver_code.expires_at
        }, status=status.HTTP_200_OK)

    def send_sms(self, phone, code):
        # پیاده‌سازی ارسال واقعی پیامک
        print(f"SMS sent to {phone}: Your verification code is {code}")
        # در محیط واقعی از سرویسی مانند کاوه نگار، پیامک یا Twilio استفاده کنید


class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ver_code = serializer.validated_data['ver_code']
        profile = ver_code.profile

        # علامت گذاری کد به عنوان استفاده شده
        ver_code.is_used = True
        ver_code.save()

        # ایجاد توکن JWT
        refresh = RefreshToken.for_user(profile.user)
        access_token = str(refresh.access_token)

        return Response({
            'status': 'success',
            'message': 'ورود موفقیت‌آمیز',
            'access': access_token,
            'refresh': str(refresh),
            'user_id': profile.user.id,
            'phone': profile.phone_number
        }, status=status.HTTP_200_OK)


class HealthView(APIView):
    permission_classes = []

    def head(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
