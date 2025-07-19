from django.db import models
from django.db.models import Model

from account.models import Profile


class ZarinTransaction(models.Model):
    user = models.ForeignKey(
        Profile, on_delete=models.CASCADE,
        null=True, blank=True, related_name='zarin_transactions'
    )

    ACCEPTED = 1
    REJECTED = 2
    PENDING = 3

    STATUS_TYPES = (
        (1 , 'پذیرفته شد'),
        (2, 'رد شد'),
        (3, 'درحال پردازش')
    )
    status_types = models.IntegerField(
        choices=STATUS_TYPES,
        null=True,

    )
    amount = models.PositiveIntegerField()
    authority = models.CharField(max_length=128, unique=True)
    ref_id = models.CharField(max_length=128, blank=True, null=True)


    def __str__(self):
        return f"{self.user} - {self.authority} "
