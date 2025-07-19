from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from utils import imageuploader

# from utils.imageuploader import upload_product_image, make_image_function

# my managers :
class CategoryManager(models.Manager):
    def active(self):
        return self.filter(status=True)


# Create your models here.


class Category(models.Model):
    parent = models.ForeignKey('self', default=None, null=True, blank=True,
                               on_delete=models.SET_NULL, related_name="children", verbose_name="زیر دسته")
    title = models.CharField(max_length=200, verbose_name="عنوان دسته بندی")
    slug = models.SlugField(max_length=100, unique=True,
                            verbose_name="آدرس دسته بندی")
    status = models.BooleanField(default=True, verbose_name="فعال بودن")
    position = models.IntegerField(verbose_name="پوزیشن")
    image = models.ImageField(
        upload_to="images", null=True, blank=True, verbose_name="تصویر دسته بندی")

    class Meta:
        db_table = ''
        managed = True
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'
        ordering = ['parent__id', 'position']
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title

    objects = CategoryManager()


User = get_user_model()


class Product(models.Model):

    # وضعیت محصول

    AVAILABLE = 1
    UNAVAILABLE = 2

    STATUS_CHOICES = (
        (1, 'موجود'),
        (2, 'ناموجود'),
    )

    WHOLESALE = 1
    RETAIL = 2
    PRODUCT_TYPES = (
        (1, 'عمده'),
        (2, 'خرده'),
    )

    # اطلاعات پایه محصول
    title = models.CharField(max_length=200, verbose_name="نام محصول")
    slug = models.SlugField(max_length=100, allow_unicode=True, unique=True, null=True, blank=True, verbose_name="آدرس محصول")
    description = models.TextField(verbose_name="توضیحات محصول")
    minimum_order = models.PositiveIntegerField(verbose_name="حداقل میزان سفارس", default=1)
    related_product = models.ForeignKey('self', verbose_name="محصول مرتبط", on_delete=models.SET_NULL, null=True, blank=True)
    product_type = models.IntegerField(choices=PRODUCT_TYPES, default=1, verbose_name="نوع محصول")
    # دسته‌بندی
    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="دسته‌بندی"
    )
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        verbose_name="وضعیت محصول"
    )
    # زمان‌های ایجاد و به‌روزرسانی
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        if not self.slug:
            slug_str = f"{self.title}"
            self.slug = slugify(slug_str, allow_unicode=True)
        super(Product,self).save(*args, **kwargs)



class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='additional_images',
        verbose_name="محصول"
    )
    image = models.ImageField(
        upload_to=imageuploader.upload_product_image, verbose_name="تصویر")
    alt_text = models.CharField(
        max_length=100, blank=True, verbose_name="متن جایگزین تصویر")

    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصول'
        ordering = ['id']

    def __str__(self):
        return f"تصویر برای {self.product.title}"
