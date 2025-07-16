# zarinpal/views.py
from django.conf import settings
from django.shortcuts import redirect, render
from django.views import View
from django.conf import settings
import requests
from user_panel.models import Order
from zarinpal.models import ZarinTransaction
import json

amount = Order.total_price  # Rial / Required
description = "توضیحات مربوط به تراکنش را در این قسمت وارد کنید"  # Required
phone = 'YOUR_PHONE_NUMBER'  # Optional
# Important: need to edit for realy server.
CallbackURL = 'http://127.0.0.1:8080/verify/'


def send_request(request):
    authority = request.GET.get('authority')
    data = {
        "MerchantID": "str(uuid.uuid4())",
        "Amount": amount,
        "Description": description,
        "Phone": phone,
        "CallbackURL": CallbackURL,
    }
    data = json.dumps(data)
    # set content length by data
    headers = {'content-type': 'application/json', 'content-length': str(len(data))}
    response = requests.post(settings.ZP_API_REQUEST, data=data, headers=headers, timeout=10)


    try:

        if response.status_code == 200:
            response = response.json()
            if response['Status'] == 100:
                txn = ZarinTransaction.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    amount=amount,
                    description=description,
                    authority=response.get['authority'],
                )
                return {'status': True, 'url': settings.ZP_API_STARTPAY + str(response['Authority']),
                        'authority': response['Authority']}
            else:
                return {'status': False, 'code': str(response['Status'])}
        return response


    except requests.exceptions.Timeout:
        return {'status': False, 'code': 'timeout'}
    except requests.exceptions.ConnectionError:
        return {'status': False, 'code': 'connection error'}

    txn.authority = authority
    txn.save()





def verify(request):
    # 1. دریافت authority از درخواست
    authority = request.GET.get('authority') or request.POST.get('authority')

    if not authority:
        return {'status': False, 'code': 'missing authority'}

    try:
        # 2. یافتن تراکنش مربوطه
        txn = ZarinTransaction.objects.get(authority=authority)
        amount = txn.amount  # استفاده از مبلغ ذخیره شده

        # 3. آماده‌سازی داده‌ها
        data = {
            "MerchantID": settings.MERCHANT,
            "Amount": amount,
            "Authority": authority,
        }
        data = json.dumps(data)
        headers = {
            'content-type': 'application/json',
            'content-length': str(len(data))
        }

        response = requests.post(
            settings.ZP_API_VERIFY,
            data=data,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            response_data = response.json()

            if response_data.get('Status') == 100:
                # 6. ذخیره ref_id در تراکنش
                txn.ref_id = response_data.get('RefID')
                txn.save()
                return {'status': True, 'RefID': txn.ref_id}

            return {'status': False, 'code': str(response_data.get('Status'))}

        return {'status': False, 'code': f'http_error_{response.status_code}'}

    except ZarinTransaction.DoesNotExist:
        return {'status': False, 'code': 'transaction_not_found'}

    except requests.exceptions.Timeout:
        return {'status': False, 'code': 'timeout'}

    except requests.exceptions.ConnectionError:
        return {'status': False, 'code': 'connection_error'}

    except Exception as e:
        return {'status': False, 'code': f'unexpected_error: {str(e)}'}
    return response

    # if response.status_code == 200:
    #     response = response.json()
    #     if response['Status'] == 100:
    #         return {'status': True, 'RefID': response['RefID']}
    #     else:
    #         return {'status': False, 'code': str(response['Status'])}





# Create your views here.
