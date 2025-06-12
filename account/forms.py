from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
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