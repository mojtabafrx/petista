from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from .forms import SignupForm, VerificationForm
from .models import Profile , VerificationCode
import random
from django.utils import timezone

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # ساخت کاربر جدید
            user = form.save(commit=False)
            user.username = form.cleaned_data['phone_number'] # استفاده از شماره تلفن به عنوان نام کاربری
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
                
                    profile.save()
                    user.save()
                    login(request, user)
                    return redirect('home:home')  # صفحه اصلی بعد از ورود

            else:
                form.add_error('verification_code', 'کد تأیید نامعتبر است')
    else:
        form = VerificationForm()
    
    return render(request, 'registration/verify.html', {
        'form': form,
        'phone_number': ver.profile.phone_number
    })