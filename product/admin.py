from django.contrib import admin
from .models import Category , Product , ProductImage

# category admin configs -->
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('position','title', 'slug' ,'parent', 'status')
    list_filter = (['status'])
    search_fields = ('title','slug')
    # prepopulated_fields = {'slug': ('title',)}

admin.site.register(Category,CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['title','slug','category']

admin.site.register(Product,ProductAdmin)

class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product','image','alt_text']

admin.site.register(ProductImage,ProductImageAdmin)
