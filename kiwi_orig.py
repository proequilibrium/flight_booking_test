import requests
import ujson
from time import sleep
from random import randint
from datetime import datetime, timedelta
#just for pretty printing
from pprint import pprint
from uuid import uuid4

def search_flight(datetime_from=None, datetime_to=None):
    """Find some cheap flight first
    """
    rand_from = randint(10, 50)
    if not datetime_from:
        datetime_from = datetime.utcnow() + timedelta(days=rand_from)
    if not datetime_to:
        datetime_to = datetime.utcnow() + timedelta(days=rand_from)
    url = "https://api.skypicker.com/flights?"
    params = "flyFrom=PRG&to=LIS&dateFrom=%s&dateTo=%s&partner=picky&passengers=1&curr=RUB&directFlights=0&locale=RU" \
            % (datetime_from.strftime("%d/%m/%Y"), datetime_to.strftime("%d/%m/%Y"))
    data = requests.get(url + params).json()['data'][0]['booking_token']
    return data

def check_flights(booking_token):
    """
    Confirms the price of the flights, has to return true, otherwise the save_booking wont pass
    """
    parameters = {'v':2,                    # default
                  'pnum':1,                 # passenger number
                  'bnum':0,                 # number of bags
                  'booking_token':booking_token
                  }
    response = requests.get('https://booking-api.skypicker.com/api/v0.1/check_flights', params=parameters ).json()
    pprint(response)
    checked = response['flights_checked']
    invalid = response['flights_invalid']
    return checked, invalid

def save_booking(booking_token):
    """
    Save booking code for non deposit payments with a custom Zooz payment app
    Initiates the booking on Skypicker backend
    The specified data is sent to the API as a json payload
    The data sent to this API call should be confirmed before by the check_flights call
    Response from save_booking is nearly the same as from check_flights, with the following parameters added
    { 'transaction_id': False,
    'zooz_token': '4XWBRXPFUD4YSXXPGBKEUNSKR4', // use this token to send credit card data to Zooz
    'booking_id': 47808, // the unique booking identified (this ID will be also passed in the callbacks to identify the booking)
    'sandbox': True, // indicates if the payment is processed in a sandbox mode. Can be also triggered by using Test Test as a passenger name
    'status': 'success'
    }
    """
    data = {
        "lang":"en", # user language
        "bags":0, # number of bags
        "passengers":[ # array with passengers data
            {
                "surname":"test",
                "cardno":None, # ID card/passport ID. In case, check flights will return document_options.document_need 2,
                #this needs to be filled in by the user togerther with the expiration field. Otherwise, those field can stay hidden from the booking form to increase conversion rate
                "phone":"+44 564564568456", # needed only for the first passenger in the array
                "birthday":724118400, # passenger birth day, utc unix timestamp in seconds
                "nationality":"United Kingdom",
                "checkin":"REMOVED, DEPRECATED", # DEPRECATED, leave an empty string here
                "issuer":"REMOVED, DEPRECATED", # DEPRECATED, leave an empty string here
                "name":"test",
                "title":"mr", # mr/ms/mrs
                "expiration":None, # expiration date of the ID from the cardno field
                "email":"test@skypicker.com"    # needed only for the first passenger in the array
            }
        ],
        "locale":"en",
        "currency":"gbp",
        "customerLoginID":"unknown", # loginID for zooz payments
        "customerLoginName":"unknown", # login name for zooz payments
        "booking_token":booking_token,
        "affily":"affil_id", # affil id, can contain any subID string, max length 64
        "booked_at":"affil_id", # basic affil id, without any subIDs
    }
    url = "https://booking-api.skypicker.com/api/v0.1/save_booking?v=2"
    response = requests.post(url,data = ujson.dumps(data)).json()
    pprint(response)
    return response

def pay_booking(zooz_token):
    headers = {
        'Origin': 'https://sandbox.zooz.co',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'sk-SK,sk;q=0.8,cs;q=0.6,en-US;q=0.4,en;q=0.2',
        'X-Requested-With': 'XMLHttpRequest',
        'ZooZ-Token': zooz_token,
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'productType': 'Checkout API',
        'deviceSignature': 'zooz_' + str(uuid4()),
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36',
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Cache-Control': 'no-cache',
        'ZooZ-UDID': 'zooz_' + str(uuid4()),
        'Referer': 'https://sandbox.zooz.co/mobile/checkoutapi/checkout.jsp',
        'programId': 'skypicker_new',
        'ZooZResponseType': 'JSon'
    }
    # zooz_response is a dict received from the zooz credi card data hashing magic
    # if zooz_response['responseStatus'] == 0:
    # confirmation = confirm_to_skypicker(response,zooz_response)
    data_init = '{"cmd":"init","paymentToken":"%s"}' % (zooz_token,)
    requests.post('https://sandbox.zooz.co/mobile/ZooZClientPaymentAPI', verify=False, timeout=30, data=data_init,
                  headers=headers).json()
    expiration = datetime.utcnow() + timedelta(days=365)
    exp = '{}/{}'.format(expiration.month, expiration.year)
    data_zooz = '{"cmd":"addPaymentMethod","paymentToken":"%s","paymentMethod":{"paymentMethodType":"CreditCard","paymentMethodDetails":{"cardNumber":"4580458045804580","cardHolderName":"test test","expirationDate":"%s","cvvNumber":"123"}},"email":"test@test.com"}' % (
        zooz_token, exp)
    d = requests.post('https://sandbox.zooz.co/mobile/ZooZClientPaymentAPI', verify=False, timeout=30,
                      data=data_zooz,
                      headers=headers).json()
    return d.get('responseObject').get('paymentMethodToken')

def confirm_to_skypicker(response,add_payment_response):
    """
    Confirms the successful sending of cc data and requests a charge on the credit card for the amount sent on save_booking
    Successful response {'status': 0} (the payment is done and the booking will be processed)
    Error response {'msg': u'server error', 'status': u'error'}
    paymentToken is from the save_booking response
    paymentMethodToken is from the zooz cc data hashing magic
    """
    confirm_payment_data = dict(
            paymentToken=response["zooz_token"],
            paymentMethodToken=add_payment_response["responseObject"]["paymentMethodToken"],
    )
    final = requests.post("https://booking-api.skypicker.com/api/v0.1/confirm_payment", data = confirm_payment_data)
    pprint(final)
    return final

if __name__ == '__main__':
    t = search_flight()
    checked, invalid = False, False
    rep = 1
    while checked is not True and invalid is not True and rep < 50:
        rep += 1
        checked, invalid = check_flights(t)
        if not checked and not invalid:
            sleep(5)
    pprint(save_booking(t))
