import numpy as np
import requests
import json
import os
import datetime

def get_weather(lat, lon):
    api_key = open("openweather.token", "r").read()
    url = "https://api.openweathermap.org/data/2.5/weather?lat=%s&lon=%s&appid=%s&units=metric" % (lat, lon, api_key)

    response = requests.get(url)
    if response.status_code != 200:
        return 0,0
    data = json.loads(response.text)["main"]
    return data["temp"], data["humidity"]


def dew_point(temp, hum):
    a = 17.62
    b = 243.12
    f = np.log(hum/100)+a*temp/(b+temp)
    ts = (b*f/(a-f))
    return ts


def cloud_base(temp, dew_p):
    return ((temp-dew_p)/2.444)*1000


def cloud_get(pos):
    temp, hum = get_weather(pos[0], pos[1])
    dew_p = dew_point(temp, hum)
    cloud = cloud_base(temp, dew_p)
    return cloud, temp, hum


def parse_metar(data):
    out = []
    out.append("T:" + data['time']['repr'][2:6])
    out.append("Wind:"+data['wind_direction']['repr']+"|"+data['wind_speed']['repr'])
    out.append("Vis:"+data['visibility']['repr'])
    clds = []
    for cloud in data['clouds']:
        clds.append(cloud['repr'])
    out.append("CLDS:"+",".join(clds))
    out.append("Temp:"+str(data['temperature']['value']))
    out.append("Dew:"+str(data['dewpoint']['value']))
    out.append("Alt:"+str(data['altimeter']['value']))
    out.append("FR:"+data['flight_rules'])
    return " ".join(out)

def get_metar(coord):
    key = open("avwx.token", "r").read()
    url = f"https://avwx.rest/api/metar/{coord}?format=json&token={key}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return ""

    data = json.loads(resp.text)
    return parse_metar(data), data['station']


def airport_coord(icao):
    key = open("avwx.token", "r").read()
    url = f"https://avwx.rest/api/station/{icao}?format=json&token={key}"
    resp = requests.get(url)
    if resp.status_code != 200:
        return 0.0, 0.0

    data = json.loads(resp.text)
    return [[data['latitude'], data['longitude']]]
