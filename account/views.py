from django.shortcuts import render, redirect
from django.contrib.auth import login  as default_login, authenticate
from django.contrib.auth.models import User
from .forms import SignupForm, VerificationForm , PasswordLoginForm, OTPLoginForm
from .models import Profile , VerificationCode
import random
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt




def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # ساخت کاربر جدید
            user = form.save(commit=False)
            user.username = form.cleaned_data['phone_number'] # استفاده از شماره تلفن به عنوان نام کاربری
            # user.password = form.cleaned_data['password1']
            user.is_active=False 
            user.save()
            
            # ساخت پروفایل
            profile = Profile.objects.create(
                user=user,
                phone_number=form.cleaned_data['phone_number'],
                user_type=form.cleaned_data['user_type'],
            )
            
            ver = VerificationCode.objects.create(
                code_type = VerificationCode.REGISTRATION_VERIFY,
                code = str(random.randint(100000, 999999)) ,
                profile = profile
            )
            # اینجا باید کد تأیید را به شماره کاربر ارسال کنید (با استفاده از سرویس SMS)
            # send_sms(profile.phone_number, f'کد تأیید شما: {profile.verification_code}')
            
            return redirect('account:verify', ver.id)
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})



def verify(request, ver_id):
    ver = VerificationCode.objects.get(id=ver_id)
    print(ver.code)
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        
        # print(form.cleaned_data['verification_code'])

        if form.is_valid():
            now = timezone.now()
            expired = True if (now - ver.date_created).seconds < (2000 * 60) else False
            verification_code = form.cleaned_data['verification_code']
            
            if verification_code == ver.code  and expired:
                if ver.code_type == VerificationCode.REGISTRATION_VERIFY:
                # تأیید موفقیت‌آمیز
                    profile =ver.profile
                    user = profile.user
                    user.is_active = True
                    profile.is_verified = True
                
                    profile.save()
                    user.save()
                    default_login(request, user)
                    return redirect('home:home')  # صفحه اصلی بعد از ورود

            else:
                form.add_error('verification_code', 'کد تأیید نامعتبر است')
    else:
        form = VerificationForm()
    
    return render(request, 'registration/verify.html', {
        'form': form,
        'phone_number': ver.profile.phone_number,
        'expires_at': ver.expires_at

    })



def login(request):
    # اگر کاربر از قبل وارد شده باشد
    if request.user.is_authenticated:
        return redirect('home:home')
    
    # متغیرهای زمینه
    password_form = PasswordLoginForm(request.POST or None, prefix='password')
    otp_form = OTPLoginForm(request.POST or None, prefix='otp')
    active_tab = 'password'  # تب پیش‌فرض
    # پردازش فرم ورود با رمز عبور
    if 'password-login' in request.POST and password_form.is_valid():
        username = password_form.cleaned_data['username']
        password = password_form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # بررسی فعال بودن حساب کاربری
            if user.is_active:
                default_login(request, user)
                return redirect('home:home')
            else:
                password_form.add_error(None, "حساب کاربری شما فعال نیست. لطفاً ابتدا حساب خود را تأیید کنید")
        else:
            password_form.add_error(None, "شماره تلفن یا رمز عبور نادرست است")

    else:
        print(password_form.errors)
    
    # پردازش فرم ورود با کد یکبار مصرف
    if 'otp-login' in request.POST and otp_form.is_valid():
        phone = otp_form.cleaned_data['phone']
        user = User.objects.get(username=phone)
        profile = Profile.objects.get(phone_number=phone)
        active_tab = 'otp'


        try:
            profile = Profile.objects.get(phone_number=phone)
            active_tab = 'otp'
            
            # بررسی فعال بودن حساب کاربری
            if not profile.user.is_active:
                otp_form.add_error('phone', "حساب کاربری شما فعال نیست. لطفاً ابتدا حساب خود را تأیید کنید")
            else:
                # تولید کد یکبار مصرف
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
                
                return redirect('account:verify_otp', ver.id)
        
        except Profile.DoesNotExist:
            otp_form.add_error('phone', "کاربری با این شماره تلفن ثبت‌نام نکرده است")
    else:
        pass
    
    context = {
        'password_form': password_form,
        'otp_form': otp_form,
        'active_tab': active_tab
    }

    # اگر در فرم OTP خطا وجود داشت، تب OTP را فعال نگه دار
    if 'otp-login' in request.POST and not otp_form.is_valid():
        context['active_tab'] = 'otp'
    
    return render(request, 'registration/login.html', context)


def verify_otp(request, ver_id):
    ver = VerificationCode.objects.get(id=ver_id)
    profile = ver.profile
    
    if request.method == 'POST':
        code = request.POST.get('code')
        now = timezone.now()
        
        # بررسی کد
        if code == ver.code and now < ver.expires_at:
            # علامت گذاری کد به عنوان استفاده شده
            ver.delete()
            
            # ورود کاربر
            default_login(request, profile.user)
            return redirect('home:home')
        else:
            error = "کد وارد شده نامعتبر یا منقضی شده است"
            return render(request, 'registration/verify_otp.html', {
                'error': error,
                'phone': profile.phone_number,
                'ver_id': ver_id,
                'expires_at': ver.expires_at
            })
    
    return render(request, 'registration/verify_otp.html', {
        'phone': profile.phone_number,
        'ver_id': ver_id,
        'expires_at': ver.expires_at
    })




@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        ver_id = data.get('ver_id')
        
        try:
            ver = VerificationCode.objects.get(id=ver_id)
            # ایجاد کد جدید
            new_code = str(random.randint(100000, 999999))
            ver.code = new_code
            ver.expires_at = timezone.now() + timedelta(minutes=5)
            ver.save()
            
            # ارسال پیامک (در حالت واقعی)
            # send_sms(ver.profile.phone_number, f"کد جدید شما: {new_code}")
            
            return JsonResponse({'success': True})
        except VerificationCode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'کد تأیید یافت نشد'})
    
    return JsonResponse({'success': False, 'error': 'درخواست نامعتبر'})