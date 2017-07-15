import requests
import ujson
from datetime import datetime, timedelta
from pprint import pprint
from uuid import uuid4
from argparse import ArgumentParser


def search_flight(one_way, departure_from=None, arrival_to=None, datetime_from=None, datetime_to=None, daysInDestination=0):
    """
        Find flights
    """
    url = "https://api.skypicker.com/flights?"
    params = "flyFrom={}&to={}&dateFrom={}&dateTo={}&partner=picky&passengers=1&curr=CZK&directFlights=1&locale=CZ".format(departure_from, arrival_to, datetime_from.strftime("%d/%m/%Y"), datetime_to.strftime("%d/%m/%Y"), daysinDest = daysInDestination)
    if(daysInDestination>0):
        one_way=False
        params += "&daysInDestinationFrom={daysinDest}&daysInDestinationTo={daysinDest}".format(daysinDest = daysInDestination)
    if(one_way): params + "&typeFlight=oneway"
    data = requests.get(url + params).json()

    if(data['_results']==0):
        # print(" {} prechazim plus jeden den".format(datetime_to))
        data = search_flight(one_way,departure_from,arrival_to, datetime_from, datetime_to + timedelta(days = 1),daysInDestination)

    return data

def check_n_save(booking_token):
    """
        Confirms the price of the flights, and save
    """
    parameters = {'v':2,                    # default
                  'pnum':1,                 # passenger number
                  'bnum':0,                 # number of bags
                  'booking_token':booking_token
                  }
    response = requests.get('https://booking-api.skypicker.com/api/v0.1/check_flights', params=parameters ).json()
    checked = response['flights_checked']
    invalid = response['flights_invalid']
    if (checked and not invalid) :
        #SAVE booking
        data = {
          "passengers": [
            {
              "lastName": "test",
              "firstName": "test",
              "birthday": "1982-05-30",
              "nationality": "UK",
              "documentID": "123456789",
              "title": "Mr",
              "email": "jaroslav-kramar@outlook.com"
            }
          ],
          "currency": "CZK",
          "booking_token": booking_token,
          "affily": "affilid",
          "booked_at": "affilid"
        }
        url = "http://37.139.6.125:8080/booking?v=2"

        response = requests.post(url,
                                headers={"Content-Type": "application/json; charset=utf-8",},
                                data = ujson.dumps(data)).json()
    else: print("Check flight error {}".format(response))
    return response

def argparser_init():
    """
        Setting command line parser
    """
    cmd_input = ArgumentParser()
    cmd_input.add_argument('--date',
                           required=True )
    cmd_input.add_argument('--from',
                           dest="fly_from",
                           required=True )
    cmd_input.add_argument('--to',
                           required=True)
    cmd_input.add_argument('--one-way',
                           action="store_true",
                           dest="one_way",
                           default=True,
                           help="one way ticket")
    cmd_input.add_argument('--return',
                           dest="days_in_destination",
                           default=0,
                           type=int,
                           help="days to return")
    cmd_input.add_argument('--cheapest',
                           action="store_true",
                           default=True)
    cmd_input.add_argument('--shortest',
                           action="store_true",
                           default=False)
    return cmd_input.parse_args()

if __name__ == '__main__':
    #init cmd parser
    cmd_arg = argparser_init()
    #convert flight date
    flight_date = datetime.strptime(cmd_arg.date,"%Y-%m-%d").date()
    flight_date_return = flight_date
    #search_flights
    founded_flights = search_flight(cmd_arg.one_way,
                      cmd_arg.fly_from,
                      cmd_arg.to,
                      flight_date,
                      flight_date_return,
                      cmd_arg.days_in_destination)
    #choose first flight
    choosen_flight=founded_flights['data'][0]
    #choose flight according to parameters
    for flight_x in founded_flights['data']:
          if cmd_arg.cheapest :
              if flight_x['conversion']['CZK'] < choosen_flight['conversion']['CZK']: choosen_flight=flight_x
          if cmd_arg.shortest :
              if flight_x['duration']['total'] < choosen_flight['duration']['total']:
                  choosen_flight=flight_x
    #print flight info
    # print("from: {}\nto: {}\nduration: {}\nprice CZK: {}\nreturn: {}".format(choosen_flight['mapIdto'],
    #                                                                          choosen_flight['mapIdfrom'],
    #                                                                          choosen_flight['fly_duration'],
    #                                                                          choosen_flight['conversion']['CZK'],
    #                                                                          choosen_flight['duration']['return']))
    #check n save flight
    save_result = check_n_save(choosen_flight['booking_token'])

    if(save_result['status']=="confirmed"):
        #show PNR
        print(save_result["pnr"])
    else: print("failed with status: {}".format(save_result['status']))
