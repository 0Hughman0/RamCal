import requests
from urllib.parse import urlencode
import json

from flask import url_for

# Set this to the id of where you are
LOCATION_ID = 350731


with open('credentials/metoffice.creds') as f:
    API_KEY = f.read()

BASE_URL = "http://datapoint.metoffice.gov.uk/public/data/"
LOCATION_URL = "val/wxfcs/all/datatype/{location_id}"


with open('weather.json') as f:
    weather_map = [name.lower().replace(" ", "-").replace("(", "").replace(")", "") for name in json.load(f)]


class Forecast:

    WEATHER_MAP = weather_map

    @classmethod
    def current(cls):
        dat = weather_at(LOCATION_ID, 'daily')['SiteRep']['DV']['Location']['Period']
        today = dat[0]
        day, night = today['Rep']
        tomorrow = dat[1]['Rep'][0]
        return (Forecast(cls.WEATHER_MAP[int(day['W'])], day['FDm'], day['PPd'], 'Day'),
                Forecast(cls.WEATHER_MAP[int(night['W'])], night['FNm'], night['PPn'], 'Night'),
                Forecast(cls.WEATHER_MAP[int(tomorrow['W'])], tomorrow['FDm'], tomorrow['PPd'], 'Day'))

    def __init__(self, cat, feels_temp, pp, time='Day'):
        self.cat = cat
        self.temp = feels_temp
        self.pp = pp
        self.time = time

    @property
    def icon(self):
        return "weather/{}.png".format(self.cat)

    def to_json(self):
        return {'temp': self.temp,
                'pp': self.pp,
                'icon': url_for('static', filename=self.icon)}


def find_location_id(location_name):
    locations = quick('val/wxfcs/all/datatype/sitelist')['Locations']['Location']

    name_ids = [(entry['name'], entry['id']) for entry in locations]
    matches = [entry for entry in name_ids if location_name in entry[0]]
    if len(matches) == 1:
        return matches[0][1]
    raise KeyError("Ambiguous name got please refine from: {}".format([entry[0] for entry in matches]))


def quick(url, **kwargs):
    kwargs['key'] = API_KEY
    url = url.replace("/datatype/", "/json/")
    query_url = BASE_URL + url + "?" + urlencode(kwargs)
    r = requests.get(query_url)
    return r.json()


def weather_at(location_id, res="3hourly", **kwargs):
    kwargs['res'] = res
    url = LOCATION_URL.format(location_id=location_id)
    return quick(url, **kwargs)


def weather():
    return weather_at(LOCATION_ID)


if __name__ == '__main__':
    while True:
        location = input('Enter location name: ')
        try:
            print('ID is {ID}, please set the value of LOCATION_ID in weather.py to {ID}:'.format(ID=find_location_id(location)))
        except KeyError as e:
            print(e)
