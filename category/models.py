from django.db import models
# from utils.imageuploader import upload_product_image, make_image_function

# my managers :
class CategoryManager(models.Manager):
    def active(self):
        return self.filter(status = True)


# Create your models here.


class Category(models.Model):
    parent = models.ForeignKey('self',default=None,null=True,blank=True,on_delete=models.SET_NULL,related_name="children",verbose_name="زیر دسته")
    title = models.CharField(max_length=200 , verbose_name = "عنوان دسته بندی")
    slug = models.SlugField(max_length=100 , unique=True , verbose_name = "آدرس دسته بندی")
    status = models.BooleanField(default=True, verbose_name = "فعال بودن")
    position = models.IntegerField(verbose_name="پوزیشن")
    image = models.ImageField(upload_to="images", null=True, blank=True , verbose_name = "تصویر دسته بندی")

    class Meta:
        db_table = ''
        managed = True
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'
        ordering = ['parent__id','position']
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title
    
    objects = CategoryManager()
