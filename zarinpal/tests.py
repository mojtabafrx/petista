import requests
from django.http import HttpRequest
from django.test import TestCase
import pytest
from django.test import RequestFactory
from unittest.mock import patch, MagicMock
from zarinpal.views import send_request, verify
from zarinpal.models import ZarinTransaction


# Fixture برای درخواست شبیه‌سازی شده
@pytest.fixture
def mock_request():
    factory = RequestFactory()
    request = factory.get('/')
    request.user = MagicMock(is_authenticated=True)
    return request


# تست‌های تابع send_request
@patch('myapp.views.requests.post')
def test_send_request_success(mock_post, mock_request):
    """ تست درخواست موفق به زرین‌پال """
    # شبیه‌سازی پاسخ زرین‌پال
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'Status': 100, 'Authority': 'A123456789'}
    mock_post.return_value = mock_response

    # فراخوانی تابع
    result = send_request(
        request=mock_request,
        amount=10000,
        description="پرداخت تستی",
        phone="09123456789",
        CallbackURL="https://example.com/callback"
    )

    # بررسی نتایج
    assert result['status'] is True
    assert 'A123456789' in result['url']
    assert ZarinTransaction.objects.count() == 1


@patch('myapp.views.requests.post')
def test_send_request_timeout(mock_post, mock_request):
    """ تست خطای تایم‌اوت """
    mock_post.side_effect = requests.exceptions.Timeout()

    result = send_request(
        mock_request,
        10000,
        "پرداخت تستی",
        "09123456789",
        "https://example.com/callback"
    )

    assert result['status'] is False
    assert result['code'] == 'timeout'
    assert ZarinTransaction.objects.count() == 0


# تست‌های تابع verify
@pytest.fixture
def create_transaction():
    """ ایجاد تراکنش تستی در دیتابیس """
    return ZarinTransaction.objects.create(
        authority='test_auth_123',
        amount=10000,
        description="Test Transaction"
    )


@patch('myapp.views.requests.post')
def test_verify_success(mock_post, create_transaction):
    """ تست تایید موفق پرداخت """
    # شبیه‌سازی پاسخ زرین‌پال
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'Status': 100, 'RefID': 'ref_123456'}
    mock_post.return_value = mock_response

    # ایجاد درخواست شبیه‌سازی شده
    request = HttpRequest()
    request.GET = {'authority': 'test_auth_123'}

    # فراخوانی تابع
    result = verify(request)

    # بررسی نتایج
    assert result['status'] is True
    assert result['RefID'] == 'ref_123456'
    create_transaction.refresh_from_db()
    assert create_transaction.ref_id == 'ref_123456'


@patch('myapp.views.requests.post')
def test_verify_transaction_not_found(mock_post):
    """ تست عدم وجود تراکنش """
    request = HttpRequest()
    request.GET = {'authority': 'invalid_auth'}

    result = verify(request)

    assert result['status'] is False
    assert result['code'] == 'transaction_not_found'
# Create your tests here.
