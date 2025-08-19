import random
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login as default_login, authenticate, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import SignupForm, VerificationForm, PasswordLoginForm, OTPLoginForm
from .models import Profile, VerificationCode


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # ساخت کاربر جدید
            if not form.user_exist:
                user = form.save(commit=False)
                user.username = form.cleaned_data['phone_number']  # استفاده از شماره تلفن به عنوان نام کاربری
                user.set_password = form.cleaned_data['password1']
                user.is_active = False
                user.save()

                # ساخت پروفایل
                profile = Profile.objects.create(
                    user=user,
                    user_type=form.cleaned_data['user_type'],
                )

                ver = VerificationCode.objects.create(
                    code_type=VerificationCode.REGISTRATION_VERIFY,
                    code=str(random.randint(100000, 999999)),
                    profile=profile,
                    expires_at=timezone.now() + timedelta(minutes=2)
                )
            else:
                ver = VerificationCode.objects.create(
                    code_type=VerificationCode.REGISTER_EXIST_USER,
                    code=str(random.randint(100000, 999999)),
                    profile=form.user_exist.profile,
                    expires_at=timezone.now() + timedelta(minutes=2)
                )
            # اینجا باید کد تأیید را به شماره کاربر ارسال کنید (با استفاده از سرویس SMS)
            # send_sms(profile.phone_number, f'کد تأیید شما: {profile.verification_code}')

            return redirect('account:verify', ver.id)
        else:
            # messages.error(request, 'اطلاعات ورودی را بررسی کنید')
            for err in form.errors.values():
                messages.error(request, err)
            return render(request, 'registration/signup.html', {
                'form': form,
            })
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


def verify(request, ver_id):
    ver = VerificationCode.objects.get(id=ver_id)
    print(ver.code)
    # استفاده از user.username به جای phone_number
    phone_number = ver.profile.user.username
    if request.method == 'POST':
        form = VerificationForm(request.POST)

        # print(form.cleaned_data['verification_code'])

        if form.is_valid():
            now = timezone.now()
            expired = True if (now - ver.date_created).seconds < (2000 * 60) else False
            verification_code = form.cleaned_data['verification_code']

            if verification_code == ver.code and expired:
                if ver.code_type == VerificationCode.REGISTRATION_VERIFY:
                    # تأیید موفقیت‌آمیز
                    profile = ver.profile
                    user = profile.user
                    user.is_active = True
                    profile.is_verified = True

                    profile.save()
                    user.save()
                    default_login(request, user)
                    return redirect('home:home')
                    # صفحه اصلی بعد از ورود
                elif ver.code_type == VerificationCode.REGISTER_EXIST_USER:
                    messages.error(request,
                                   "کاربری شما با این شماره از قبل وجود داشت در دفعات بعدی برای ورود از صفحه ورود استفاده کنید.")
                    default_login(request, ver.profile.user)
                    return redirect('user_panel:dashboard')
            else:
                messages.error(request, 'کد تأیید نامعتبر است یا زمان آن به پایان رسیده است.')
                # form.add_error('verification_code', 'کد تأیید نامعتبر است')
    else:
        form = VerificationForm()

    return render(request, 'registration/verify.html', {
        'form': form,
        'phone_number': phone_number,
        'expires_at': ver.expires_at

    })


def verify_otp(request, ver_id):
    ver = VerificationCode.objects.filter(id=ver_id).first()

    if ver is None:
        expires_at = timezone.now() + timedelta(minutes=2)
        messages.error(request, "کاربری با این شماره وجود ندارد")
        return render(request, 'registration/verify_otp.html', {
            'phone': request.session['phone_number'],
            'ver_id': ver_id,
            'expires_at': expires_at,
        })
    print(ver.code)
    # print(ver.code)
    profile = ver.profile
    # استفاده از user.username به جای phone_number
    phone_number = profile.user.username

    if request.method == 'POST':
        code = request.POST.get('code')
        now = timezone.now()

        # بررسی کد
        if code == ver.code and now < ver.expires_at:
            # علامت گذاری کد به عنوان استفاده شده
            ver.delete()

            # ورود کاربر
            default_login(request, profile.user)
            return redirect('user_panel:dashboard')
        else:
            messages.error(request, 'کد وارد شده نامعتبر یا منقضی شده است')
            return render(request, 'registration/verify_otp.html', {
                'phone': phone_number,
                'ver_id': ver_id,
                'expires_at': ver.expires_at
            })
    return render(request, 'registration/verify_otp.html', {
        'phone': phone_number,
        'ver_id': ver_id,
        'expires_at': ver.expires_at
    })


def login(request):
    # اگر کاربر از قبل وارد شده باشد
    if request.user.is_authenticated:
        return redirect('home:home')

    # متغیرهای زمینه
    password_form = PasswordLoginForm(request.POST or None)
    otp_form = OTPLoginForm(request.POST or None, prefix="otp")
    tabId = "password-tab"

    # پردازش فرم ورود با رمز عبور
    if 'password-login' in request.POST and password_form.is_valid():
        username = password_form.cleaned_data['username']
        password = password_form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # بررسی فعال بودن حساب کاربری
            if user.is_active:
                default_login(request, user)
                return redirect('user_panel:dashboard')
            else:
                profile = Profile.objects.filter(user=user, is_active=False)

                ver = VerificationCode.objects.create(
                    code_type=VerificationCode.REGISTRATION_VERIFY,
                    code=str(random.randint(100000, 999999)),
                    profile=profile,
                    expires_at=timezone.now() + timedelta(minutes=2)
                )

                messages.error(request,
                               'حساب کاربری شما فعال نیست. لطفاً برای فعالسازی حساب خود کد تایید ارسال شده را وارد کنید')
                return HttpResponseRedirect(reverse('account:verify', kwargs={'ver_id': ver.id}))
                # password_form.add_error(None, "حساب کاربری شما فعال نیست. لطفاً ابتدا حساب خود را تأیید کنید")
        else:
            messages.error(request, 'شماره تلفن یا رمز عبور نادرست است.')
            # password_form.add_error(None, "شماره تلفن یا رمز عبور نادرست است")

    else:
        pass
    # بخش ورود با کد یکبار مصرف - بهینه‌سازی شده
    if 'otp-login' in request.POST and otp_form.is_valid():
        username = otp_form.cleaned_data['username']
        try:
            # پیدا کردن کاربر بر اساس username
            user = User.objects.get(username=username)
            # دسترسی به پروفایل از طریق رابطه
            profile = user.profile

            if not user.is_active:
                messages.error(request, 'حساب کاربری شما فعال نیست. لطفاً ابتدا حساب خود را تأیید کنید')
                # otp_form.add_error('phone', "حساب کاربری شما فعال نیست. لطفاً ابتدا حساب خود را تأیید کنید")
            else:
                ver = VerificationCode.objects.create(
                    profile=profile,
                    code_type=VerificationCode.LOGIN_OTP,
                    code=str(random.randint(100000, 999999)),
                    expires_at=timezone.now() + timedelta(minutes=5)
                )
                # ارسال پیامک
                # send_sms(profile.phone_number, f"کد ورود شما: {ver.code}")

                # ذخیره شناسه کاربر در سشن برای مرحله بعد
                request.session['otp_user_id'] = user.id
                #
                # request.session['expires_at'] = ver.expires_at

                return redirect('account:verify_otp', ver.id)

        except User.DoesNotExist:
            request.session['phone_number'] = username
            return redirect('account:verify_otp', uuid.uuid4())
            # messages.error(request, 'کاربری با این شماره تلفن ثبت‌نام نکرده است')

            # otp_form.add_error('phone', "کاربری با این شماره تلفن ثبت‌نام نکرده است")

    # دریافت URL تصویر کپچا
    # captcha_image_url = password_form.fields['captcha'].widget.image_url()
    # print(captcha_image_url)
    # captcha_image_url = captcha_settings.CAPTCHA_IMAGE_URL
    # if captcha_settings.CAPTCHA_IMAGE_TEMPLATE:
    #     captcha_image_url = reverse(captcha_settings.CAPTCHA_IMAGE_URL)

    context = {
        'password_form': password_form,
        'otp_form': otp_form,
        'tabId': tabId,
        # 'captcha_image_url': captcha_image_url,
    }

    # اگر در فرم OTP خطا وجود داشت، تب OTP را فعال نگه دار
    if 'otp-login' in request.POST and not otp_form.is_valid():
        tabId = "otp-tab"

    context['tabId'] = tabId

    return render(request, 'registration/login.html', context)


@csrf_exempt
def resend_otp(request, ver_id):
    if request.method == 'POST':
        # import json
        # data = json.loads(request.body)
        # data = request.POST.get('data')['ver_id']
        # ver_id = data.get('ver_id')

        try:
            ver = VerificationCode.objects.get(id=ver_id)
            if (timezone.now() < ver.expires_at):
                messages.error(request, 'هنوز زمان کافی برای ارسال دوباره کد سپری نشده')
                return HttpResponseRedirect(reverse("account:verify_otp", kwargs={"ver_id": ver_id}))
            # ایجاد کد جدید
            new_code = str(random.randint(100000, 999999))
            ver.code = new_code
            ver.expires_at = timezone.now() + timedelta(minutes=2)
            ver.save()
            # ارسال پیامک (در حالت واقعی)
            # send_sms(ver.profile.phone_number, f"کد جدید شما: {new_code}")

            messages.success(request, 'کد جدید ارسال شد')
            return HttpResponseRedirect(reverse("account:verify_otp", kwargs={"ver_id": ver_id}))
        except VerificationCode.DoesNotExist:
            messages.error(request, 'کد تأیید یافت نشد')
            return HttpResponseRedirect(reverse("account:verify_otp", kwargs={"ver_id": ver_id}))

    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})


def logout(request):
    """ویو ساده برای خروج کاربر"""
    auth_logout(request)
    messages.success(request, 'شما با موفقیت از سیستم خارج شدید.')
    return redirect('account:login')
