from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

# Create your models here.



class Profile(models.Model):

    NORMAL_USER = 1
    PRODUCER_USER = 2
    SELLER_USER = 3
    ADMIN_USER = 4
    MARKERE_USER = 5

    USER_TYPES = (
        (1, 'خریدار معمولی'),
        (2, 'تولیدکننده'),
        (3, 'فروشنده'),
        (4, 'ادمین'),
        (5, 'بازاریاب'),
    )


    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.IntegerField(
        choices=USER_TYPES,
        default=1,
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


class VerificationCode(models.Model):
    REGISTRATION_VERIFY = 1
    LOGIN_OTP = 2
    PASSWORD_RESET = 3
    PHONE_CHANGE = 4

    VERIFICATIONCODE_TYPE = (
        (REGISTRATION_VERIFY, 'ثبت نام'),
        (LOGIN_OTP, 'ورود یکبار مصرف'),
        (PASSWORD_RESET, 'بازیابی رمز عبور'),
        (PHONE_CHANGE, 'تغییر شماره تلفن'),
        
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_type = models.IntegerField(choices=VERIFICATIONCODE_TYPE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    date_created = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # افزودن فیلد انقضا
    is_used = models.BooleanField(default=False)  # افزودن فیلد وضعیت استفاده

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at