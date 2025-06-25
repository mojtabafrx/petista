from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user','user_type','phone_number']
    def active(self, obj):
        return obj.User.is_active

admin.site.register(Profile,ProfileAdmin)
