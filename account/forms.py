from captcha.fields import CaptchaField, CaptchaTextInput
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class SignupForm(UserCreationForm):
    class CaptchaFieldCustomInput(CaptchaTextInput):
        template_name = "fields/custom_captcha.html"

    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '09123456789'})
    )
    user_type = forms.ChoiceField(
        choices=Profile.USER_TYPES,
        widget=forms.RadioSelect,
        label='نوع حساب کاربری'
    )
    captcha = CaptchaField(label='کپچا', widget=CaptchaFieldCustomInput)

    class Meta:
        model = User
        fields = ('phone_number', 'password1', 'password2', 'user_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        # ذخیره شماره تلفن در username
        user.username = self.cleaned_data['phone_number']
        if commit:
            user.save()
        return user


class VerificationForm(forms.Form):
    verification_code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'placeholder': 'کد دریافتی'})
    )


class CaptchaFieldCustomInput(CaptchaTextInput):
    template_name = "fields/custom_captcha.html"


class PasswordLoginForm(forms.Form):
    username = forms.CharField(
        label="شماره تلفن",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'})
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'})
    )
    captcha = CaptchaField(label='کپچا', widget=CaptchaFieldCustomInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'شماره تلفن'


class OTPLoginForm(forms.Form):
    username = forms.CharField(
        label="شماره تلفن",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'})
    )
    captcha = CaptchaField(label='کپچا', widget=CaptchaFieldCustomInput)

    #
    # def clean_username(self):
    #     username = self.cleaned_data['username']
    #     # بررسی وجود کاربر بر اساس username
    #     if not User.objects.filter(username=username).exists():
    #         raise forms.ValidationError("کاربری با این شماره تلفن ثبت‌نام نکرده است.")
    #     return username
    #
