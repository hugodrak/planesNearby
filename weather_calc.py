import numpy as np
import requests
import json
import os

def get_weather(lat, lon):
    api_key = os.environ["OPEN_WHEATHER_API_KEY"]
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
