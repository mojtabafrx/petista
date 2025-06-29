from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from account.models import Profile

def user_panel_access(view_func):
    """دکوراتور اصلی برای دسترسی به پنل کاربری"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def seller_required(view_func):
    """فقط برای فروشندگان"""
    def wrapper(request, *args, **kwargs):
        if request.user.profile.user_type != Profile.SELLER_USER:
            return HttpResponseForbidden("شما به این بخش دسترسی ندارید")
        return view_func(request, *args, **kwargs)
    return wrapper