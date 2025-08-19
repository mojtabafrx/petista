import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from user_panel.models import Cart
from .models import Transaction

# ? sandbox merchant
if settings.SANDBOX:
    sandbox = 'sandbox'
else:
    sandbox = 'www'

ZP_API_REQUEST = f"https://{sandbox}.zarinpal.com/pg/v4/payment/request.json"
ZP_API_VERIFY = f"https://{sandbox}.zarinpal.com/pg/v4/payment/verify.json"
ZP_API_STARTPAY = f"https://{sandbox}.zarinpal.com/pg/StartPay/"

amount = 0  # Rial / Required
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"  # Required
phone = 'YOUR_PHONE_NUMBER'  # Optional
# Important: need to edit for realy server.
CallbackURL = 'http://127.0.0.1:8000/transaction/verify/'


@login_required
def send_request(request, order_id):
    order = Cart.objects.get(id=order_id)
    amount = order.total_price()
    # اصلاح کلیدها به فرمت مورد انتظار زرین‌پال (حروف بزرگ)
    data = {
        "merchant_id": settings.MERCHANT,  # اصلاح: MerchantID با حروف بزرگ
        "amount": amount,
        "description": description,
        "mobile": phone,  # اصلاح: Mobile
        "callback_url": CallbackURL,
    }
    data = json.dumps(data)
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'content-length': str(len(data))
    }

    try:
        response = requests.post(ZP_API_REQUEST, data=data, headers=headers, timeout=10)

        # بررسی وضعیت پاسخ
        if response.status_code == 200:
            response_data = response.json()

            # اصلاح: استفاده از کلیدهای با حروف بزرگ
            if response_data["data"].get('code') == 100:
                # اصلاح: Authority نه authority
                Transaction.objects.create(
                    authority=response_data["data"]['authority'],
                    ref_id="",
                    code="",
                    user=request.user,
                    cart=order,

                )
                order.is_active = False
                order.status = order.PAID
                order.save()
                return redirect(ZP_API_STARTPAY + str(response_data["data"]['authority']))
                # return JsonResponse({
                #     'status': True,
                #     'url': ZP_API_STARTPAY + str(response_data["data"]['authority']),
                #     'authority': response_data["data"]['authority']  # اصلاح کلید
                # })
            else:
                order.is_active = False
                order.status = order.PENDING
                order.save()
                return JsonResponse({
                    'status': False,
                    'code': str(response_data.get('Status'))
                })
        order.is_active = False
        order.status = order.PENDING
        order.save()
        messages.error(request, "در حال حاضر درگاه پرداخت با مشکل مواجه می باشد لطفا دقایقی دیگر دوباره تست کنید.")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))

    except requests.exceptions.Timeout:
        order.is_active = False
        order.status = order.PENDING
        order.save()
        messages.error(request, "در حال حاضر درگاه پرداخت با مشکل مواجه می باشد لطفا دقایقی دیگر دوباره تست کنید.")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))
    except requests.exceptions.ConnectionError:
        order.is_active = False
        order.status = order.PENDING
        order.save()
        messages.error(request, "در حال حاضر درگاه پرداخت با مشکل مواجه می باشد لطفا دقایقی دیگر دوباره تست کنید.")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))
    except Exception as e:
        order.is_active = False
        order.status = order.PENDING
        order.save()
        messages.error(request, "در حال حاضر درگاه پرداخت با مشکل مواجه می باشد لطفا دقایقی دیگر دوباره تست کنید.")
        return HttpResponseRedirect(reverse("user_panel:my_orders"))


@login_required
def verify(request):  # اصلاح: دریافت request به عنوان پارامتر
    # دریافت پارامترهای GET از زرین‌پال
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    transaction = Transaction.objects.filter(user=request.user, authority=authority).first()
    order = transaction.cart
    if status != 'OK':
        order.is_active = False
        order.status = order.PENDING
        order.save()
        message = "پرداخت توسط کاربر لغو شد"
        return render(request, "transaction/transaction_fail.html", {"message": message})

    data = {
        "merchant_id": settings.MERCHANT,
        "amount": order.total_price(),
        "authority": authority,
    }

    data = json.dumps(data)

    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'content-length': str(len(data))
    }

    response = requests.post(ZP_API_VERIFY, data=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        # اصلاح: استفاده از کلیدهای با حروف بزرگ
        if response_data["data"].get('code') == 100:

            transaction.authority = authority
            transaction.ref_id = response_data["data"]["ref_id"]
            transaction.code = response_data["data"]["code"]
            transaction.save()
            order.status = order.PAID
            order.tracking_code = response_data["data"]["ref_id"]
            order.save()
            for order_item in order.items.all():
                # کاهش موجودی اصلی (stock) و افزایش sell_count
                seller_product = order_item.seller_product
                # seller_product.available_count -= order_item.quantity
                seller_product.sell_count += order_item.quantity
                seller_product.save()
                order_item.price = seller_product.price
                order_item.save()

            # غیرفعال کردن سبد خرید فعلی و ایجاد سبد جدید
            # cart = get_object_or_404(Cart, user=request.user, is_active=True)
            order.is_active = False
            order.status = order.PAID
            order.save()
            # Cart.objects.create(user=request.user, status=Cart.PROCESSING)
            ref_id = response_data["data"]["ref_id"]
            context = {
                "ref_id": ref_id
            }
            return render(request, "transaction/transaction_success.html", context)
        elif response_data["data"].get('code') == 101:
            message = "این پرداخت قبلا انجام شده است"
            return render(request, "transaction/transaction_fail.html", {"message": message})

        else:
            # return HttpResponse(
            #     f'خطا در پرداخت. کد خطا: {response_data["data"].get("code")}'
            # )
            ref_id = response_data["data"]["ref_id"]
            context = {
                "ref_id": ref_id
            }
            # cart = get_object_or_404(Cart, user=request.user, is_active=True)
            order.is_active = False
            order.status = order.PENDING
            order.save()
            # Cart.objects.create(user=request.user)
            return render(request, "transaction/transaction_fail.html", context)

    # return HttpResponse(f'خطای ارتباط با زرین‌پال: {response.status_code}')
    order.is_active = False
    order.status = order.PENDING
    order.save()

    # Cart.objects.create(user=request.user)
    return render(request, "transaction/transaction_fail.html")
