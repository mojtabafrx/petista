from django.shortcuts import render, redirect
from django.urls import reverse
from product.models import Product
from .forms import ProductForm, ProductImageFormSet

def administrator(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and image_formset.is_valid():
            # ذخیره محصول
            product = form.save(commit=False)
            
            # تنظیم alt_text با عنوان محصول برای تمام تصاویر
            images = image_formset.save(commit=False)
            for image in images:
                image.alt_text = product.title
            
            # ذخیره نهایی
            product.save()
            print(product.title)
            for image in images:
                image.product = product
                image.save()
            
            # ذخیره فرم‌ست
            image_formset.save()
            
            return redirect(reverse('product:product_list'))  # تغییر به مسیر مناسب
    
    else:
        form = ProductForm()
        image_formset = ProductImageFormSet()
    
    context = {
        'form': form,
            'image_formset': image_formset
    }
    return render(request, 'administrator/administrator.html', context)