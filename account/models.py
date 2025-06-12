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
    USER_TYPES = (
        (1, 'خریدار معمولی'),
        (2, 'تولیدکننده'),
        (3, 'فروشنده'),
    )


    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    user_type = models.IntegerField(
        choices=USER_TYPES,
        default='N',
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


class VerificationCode(models.Model):
    REGISTRATION_VERIFY = 1

    VERIFICATIONCODE_TYPE = (
        (REGISTRATION_VERIFY, 'ثبت نام'),
        
    )

    id = models.UUIDField(primary_key=True,default=uuid.uuid4())
    code_type= models.IntegerField(choices=VERIFICATIONCODE_TYPE)
    profile = models.ForeignKey(Profile,on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    date_created = models.DateTimeField(auto_now_add=True)