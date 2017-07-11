import requests
import ujson
from time import sleep
from random import randint
from datetime import datetime, timedelta
from pprint import pprint
from uuid import uuid4
from argparse import ArgumentParser


def search_flight(departure_from=None, arrival_to=None, datetime_from=None, datetime_to=None):
    """Find some cheap flight first
    """
    rand_from = randint(10, 50)
    if not datetime_from:
        datetime_from = datetime.utcnow() + timedelta(days=rand_from)
    if not datetime_to:
        datetime_to = datetime.utcnow() + timedelta(days=rand_from)
    url = "https://api.skypicker.com/flights?"
    params = "flyFrom={}&to={}&dateFrom={}&dateTo={}&daysInDestinationFrom=5&daysInDestinationTo=5&partner=picky&passengers=1&curr=CZK&directFlights=1&locale=CZ".format(departure_from, arrival_to, datetime_from.strftime("%d/%m/%Y"), datetime_to.strftime("%d/%m/%Y"))
    data = requests.get(url + params).json()
    for flight_avail in data['data']:
        print(flight_avail['conversion']['CZK'], "____",flight_avail['fly_duration'],'_____',flight_avail['duration']['total'])
    departure_time = data['data'][0]['dTime']
    print(len(data['data']))
    return departure_time

def check_n_save(booking_token):
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
    #SAVE booking
    data = {
        "lang":"en", # user language
        "bags":0, # number of bags
        "passengers":[ # array with passengers data
            {
                "surname":"John Doe",
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
                "email":"jaroslav-kramar@outlook.com"    # needed only for the first passenger in the array
            }
        ],
        "locale":"en",
        "currency":"czk",
        "customerLoginID":"unknown", # loginID for zooz payments
        "customerLoginName":"unknown", # login name for zooz payments
        "booking_token":booking_token,
        "affily":"affil_id", # affil id, can contain any subID string, max length 64
        "booked_at":"affil_id", # basic affil id, without any subIDs
    }
    url = "https://booking-api.skypicker.com/api/v0.1/save_booking?v=2"
    response = requests.post(url,data = ujson.dumps(data)).json()
    pprint(response)


if __name__ == '__main__':
    cmd_input = ArgumentParser()
    cmd_input.add_argument(--date,
                           required=True )
    cmd_input.add_argument('--from',
                           required=True )
    cmd_input.add_argument(--to,
                           required=True)
    cmd_input.add_argument(--one-way,
                           action="store_true",
                           default=False,
                           help="one way ticket")
    cmd_input.add_argument('--return',
                           default=0,
                           help="days to return")
    cmd_input.add_argument(--cheapest,
                           action="store_true",
                           default=False)
    cmd_input.add_argument(--shortest,
                           action="store_true",
                           default=False)

    flight_date = cmd_input.date.strftime("%d/%m/%Y")
    flight_date_return= flight_date + timedelta(days=5)
    t = search_flight("PRG",
                      cmd_input.to,
                      flight_date,
                      flight_date_return)
    pprint(t)
