from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from product.models import Category, Product
from user_panel.models import SellerProduct


class ProductForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.id:
            self.fields["category"].queryset = Category.objects.filter(id=self.instance.product.category.id)
            self.fields["product"].queryset = Product.objects.filter(id=self.instance.product.id)
            self.fields["category"].initial = self.instance.product.category
        else:
            self.fields["category"].queryset = Category.objects.all()

    class Meta:
        model = SellerProduct
        fields = ['stock', 'price', 'product']


class ChangePasswordForm(PasswordChangeForm):
    error_messages = {
        "password_mismatch": "پسورد ها یکسان نیستند.",

    }

    def __init__(self, *args, **kwargs):
        super(ChangePasswordForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].error_messages["required"] = "پسورد الزامی است."
        self.fields['new_password2'].error_messages["required"] = "تکرار پسورد الزامی است."
        self.fields['old_password'].initial = "asdfg"
