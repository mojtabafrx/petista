from django.contrib import admin
from .models import Category

# category admin configs -->
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('position','title', 'slug' ,'parent', 'status')
    list_filter = (['status'])
    search_fields = ('title','slug')
    # prepopulated_fields = {'slug': ('title',)}

admin.site.register(Category,CategoryAdmin)

