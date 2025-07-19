from django import forms
from product.models import Product
from django import forms
from django.forms import inlineformset_factory
from product.models import Product, ProductImage


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'minimum_order',
            'related_product', 'product_type', 'category', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']  # حذف alt_text
        # widgets = {
            # 'image': forms.FileInput(attrs={
            #     'accept': 'image/*',
            #     'class': 'image-upload-input',
            #     'multiple': True
            #}),
        #}


# ایجاد فرم‌ست برای تصاویر
ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    extra=5,
    can_delete=True
)

# #class AddProductForm(forms.ModelForm):

#     #class Meta():
#         model = Product
#         fields = '__all__'

#     def save(self, commit=True):
#         return super().save(commit)
