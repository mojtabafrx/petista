from django import forms
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm
from .models import Profile , VerificationCode
from captcha.fields import CaptchaField
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '09123456789'})
    )
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPES,
        widget=forms.RadioSelect,
        label='نوع حساب کاربری'
    )
    captcha = CaptchaField(label='کپچا')

    class Meta:
        model = User
        fields = ('phone_number', 'password1', 'password2', 'user_type')



class VerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': 'کد دریافتی'})
    )
    captcha = CaptchaField(label='کپچا')



class PasswordLoginForm(forms.Form):
    username = forms.CharField(
        label="شماره تلفن",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'})
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'})
    )
    captcha = CaptchaField(label='کپچا')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'شماره تلفن'

class OTPLoginForm(forms.Form):
    phone = forms.CharField(
        label="شماره تلفن",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'})
    )
    captcha = CaptchaField(label='کپچا')

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if not User.objects.filter(username=phone).exists():
            raise forms.ValidationError("کاربری با این شماره تلفن ثبت‌نام نکرده است.")
        return phone


