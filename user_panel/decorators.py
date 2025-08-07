from django.conf import settings
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
        if request.user.profile.user_type == Profile.NORMAL_USER:
            return HttpResponseForbidden("شما به این بخش دسترسی ندارید")
        return view_func(request, *args, **kwargs)

    return wrapper


def redirect_superusers(view_func):
    """
    اگر کاربر فعلی سوپریوزر باشد، او را به پنل ادمین هدایت می‌کند.
    در غیر این‌صورت، ویوی اصلی را اجرا می‌کند.
    """

    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            # هدایت به پنل ادمین جنگو
            return redirect(settings.ADMIN_URL) if hasattr(settings, 'ADMIN_URL') else redirect('admin:index')
        return view_func(request, *args, **kwargs)

    return wrapper
