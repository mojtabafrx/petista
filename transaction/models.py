from django.contrib.auth.models import User
from django.db import models

from user_panel.models import  Cart


# Create your models here.
class Transaction(models.Model):
    authority = models.CharField(max_length=100,)
    date_created = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)
    ref_id = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null= True,related_name='transaction')


    class Meta:
        ordering = ['date_created']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

