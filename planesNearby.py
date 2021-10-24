import json
import requests
import time
import argparse
import geocoder
from weather_calc import cloud_get, get_metar, airport_coord
from radar import draw_radar
from drawing import print_stats, current_os, status_box, print_blocks
from gps import gps_direction, plane_alt_angle
from math import radians
import os

DEV = False
## TODO: move functions to backend 2
## TODO: log is broken 3
## TODO: add wttr style boxes   1
## TODO: add hight curve (and maybe emiss trail) 4
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="online", help="online or log")
    parser.add_argument("--bbox", default="59.781238,58.654034,15.793447,19.970999",
                        help="59.78,58.65,15.79,19.97")
    parser.add_argument("--log-path", default="log.txt", help="path to log file")
    parser.add_argument("--write-log", default=None, help="path to log that will be created")
    parser.add_argument("--place", default=False, help="use this to name a place to center the planes around")

    return parser.parse_args()


def setup_cache():
    if not os.path.exists("latest_airlines.csv"):
        open("latest_airlines.csv", "w")

    if not os.path.exists("latest_airports.csv"):
        open("latest_airports.csv", "w")

R = 6373.0  # radius of earth

def assign_id(ids):
    if not ids:
        return [1], 1
    new_id = None
    prev = None
    for id in ids:
        if prev:
            if prev+1 != id:
                new_id = prev+1
                break
        prev = id

    if not new_id:
        new_id = ids[-1]+1
    ids.append(new_id)
    ids.sort()
    return ids, new_id


def get_my_position():
    me = geocoder.ip('me')
    return me.latlng


def get_city_pos(city):
    resp = geocoder.arcgis(city)
    if resp is None:
        print("Bad geocode, taking you position.")
    return resp.latlng


def lookup_type(plane_type):
    rows = open("./plane_types.txt", "r", encoding="utf8").read().splitlines()
    for row in rows:
        rowsplit = row.split(";")
        if plane_type in [rowsplit[0], rowsplit[1]]:
            return rowsplit[2]
    return plane_type


def lookup_airport(airport):
    if airport != "":
        rows = open("./latest_airports.csv", "r", encoding="utf8").read().splitlines()
        for row in rows:
            rowsplit = row.split(",")
            if len(rowsplit) > 3:
                if airport in [rowsplit[0], rowsplit[1]]:
                    return rowsplit[2].replace('"', '')

        rows = open("./airports.csv", "r", encoding="utf8").read().splitlines()
        for row in rows:
            rowsplit = row.split(",")
            if len(rowsplit) > 3:
                if airport in [rowsplit[0], rowsplit[1]]:
                    open("./latest_airports.csv", "a", encoding="utf8").write(row + "\n")
                    return rowsplit[2].replace('"', '')
    return airport


def lookup_airline(airline):
    if airline != "":
        rows = open("./latest_airlines.csv", "r", encoding="utf8").read().splitlines()
        for row in rows:
            rowsplit = row.split(",")
            if len(rowsplit) > 3:
                if airline == rowsplit[1]:
                    return rowsplit[2]

        rows = open("./airlines.csv", "r", encoding="utf8").read().splitlines()
        for row in rows:
            rowsplit = row.split(",")
            if len(rowsplit) > 3:
                if airline == rowsplit[1]:
                    open("./latest_airlines.csv", "a", encoding="utf8").write(row + "\n")
                    return rowsplit[2]
    return airline


class Plane:
    def __init__(self, id, data, cloud_height):
        self.id = id
        self.key = data[0]
        self.show = True
        self.type = lookup_type(data[8])
        self.squawk = data[6]
        self.company = lookup_airline(data[18])
        if self.type == "GRND":
            self.show = False
        self.node = data[7]
        self.reg = data[9]
        self.time = data[10]
        self.lat = data[1]
        self.lon = data[2]
        self.course = data[3]
        self.height = data[4]
        self.speed = data[5]
        self.departure = lookup_airport(data[11])
        self.destination = lookup_airport(data[12])
        self.cloud_height = cloud_height
        self.flightno = data[13]
        self.callsign = data[16]
        self.dist_to_me = 0
        self.angle_rel_me = ""
        self.angle_rel_ground = ""
        self.passed_me = []
        self.has_passed = False
        self.prev = [self.time, 0.0, 0.0, 0.0, 0, 0.0, 0]
        self.stats = [f"{self.id}/{self.flightno}/{self.callsign}", "CRS$B", "LAT$B", "LON$B", "LVL$B", "SPD$B", "ONLINE$G",
                      self.departure, self.destination, self.type, self.company, "DIST", "LOOK TO"]

    def update(self, data, my_pos):
        if my_pos:
            dist, direction = gps_direction(radians(my_pos[0]), radians(my_pos[1]), radians(self.lat), radians(self.lon))
            self.dist_to_me = round(dist/1.852, 1)  # to Nautical mile
            self.angle_rel_me = str(round(direction, 1))
            self.angle_rel_ground = str(round(plane_alt_angle(self.height, dist), 1))

        self.time = data[10]
        self.lat = data[1]
        self.lon = data[2]
        self.course = data[3]
        self.height = data[4]
        self.speed = data[5]
        self.time = data[10]

    def get_change(self):
        if self.course != self.prev[3]:
            self.stats[1] = print_stats(self.prev[3], 0, self.course, ["↺", "↻"], "°", "CRS", max_val=360)

        if self.lat != self.prev[1]:
            self.stats[2] = print_stats(self.prev[1], 0.005, self.lat,  ["▼", "▲"], "°", "LAT")

        if self.lon != self.prev[2]:
            self.stats[3] = print_stats(self.prev[2], 0.005, self.lon, ["◀", "▶"], "°", "LON")

        if self.height < 20:
            self.stats[4] = "ON GROUND$W"
        elif self.height != self.prev[4]:
            self.stats[4] = print_stats(self.prev[4], 5, self.height, ["▼", "▲"], "ft", "LVL")

        if self.speed != self.prev[5]:
            self.stats[5] = print_stats(self.prev[5], 1, self.speed, ["▼", "▲"], "kn", "SPD")

        if self.dist_to_me != self.prev[6]:
            dist_s = print_stats(self.prev[6], 0.01, self.dist_to_me, ["▼", "▲"], "NM", "DIST")
            if dist_s != "":
                if self.dist_to_me < 8:  # 15 km or 8 NM
                    if not self.has_passed:
                        self.passed_me = [self.key, self.time, self.type, self.reg, self.departure,
                                          self.destination, self.height]
                        self.has_passed = True
                    else:
                        self.passed_me = []
                    dist_s += "$G"
                self.stats[11] = dist_s

        cloud_status = " | ▲ ☁"
        if self.height < self.cloud_height:
            cloud_status = " | ▼ ☁"
            if self.has_passed:
                cloud_status += "$G"

        self.stats[12] = f"LOOK TO: {self.angle_rel_me},UP {self.angle_rel_ground} {cloud_status}"

    def set_prev(self):
        self.prev = [self.time, self.lat, self.lon, self.course, self.height, self.speed,
                     self.dist_to_me]

    def update_conn(self, conn):
        self.stats[6] = conn


LATEST_IDS = []


def get_data(bbox=None, read_log=None, create_log=None):
    planes = {}
    old_keys = {}
    airports = None
    my_pos = None
    if args.place:
        my_pos = get_city_pos(args.place)
        my_pos = [round(my_pos[0], 3), round(my_pos[1], 3)]
    if not my_pos:
        my_pos = get_my_position()

    weather = cloud_get(my_pos)
    lat_ext = 0.9  # 0.7
    lon_ext = 2.0  # 2.0
    bbox = f"{my_pos[0] + lat_ext},{my_pos[0] - lat_ext},{my_pos[1] - lon_ext},{my_pos[1] + lon_ext}"
    if bbox:
        url = f"https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds={bbox}" \
              f"&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1" \
              f"&maxage=14400&gliders=1&stats=1&enc=WPix0NeDQJ6xOmiczStTqq2XtL_YRMqUg86w4siPKdQ"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"}
        sess = requests.session()
        if create_log:
            w_log = open(create_log, "w", encoding="utf8")
        else:
            w_log = None

        passed_log = open("passed.log", "a", encoding="utf8")
        current_metar = ""
        if my_pos:
            current_metar, icao = get_metar(f"{my_pos[0]},{my_pos[1]}")
            airports = airport_coord(icao)

        try:
            while True:
                try:
                    resp = sess.get(url, headers=headers)
                except IOError:
                    print("Connection broke, retrying...")
                    time.sleep(5)
                    continue
                if resp.status_code != 200:
                    print(f"Status {resp.status_code}")
                    time.sleep(5)
                    continue

                planes, old_keys, planes_passed = run_iteration(resp.text, planes, old_keys, w_log,
                                                                my_pos, weather=weather, bbox=bbox,
                                                                metar=current_metar, airports=airports)
                if planes_passed:
                    passed_log.write("".join([str(plane) + "\n" for plane in planes_passed]))
                time.sleep(3)
        except KeyboardInterrupt:
            print("\tI am done. Have a nice day! :)")
            pass

    elif read_log:
        r_log = open(read_log, "r", encoding="utf8").read().split("}}}")[:-1]
        for row in r_log:
            planes, old_keys, planes_passed = run_iteration(row + "}}}", planes, old_keys,
                                                            my_pos=my_pos, weather=weather)
            time.sleep(3)
        print("LOG END")


def run_iteration(resp, planes, old_keys, w_log=None, my_pos=None, weather=(0, 0), bbox=None,
metar=None, airports=None):
    if w_log:
        w_log.write(resp + "\n")
    json_data = json.loads(resp)
    json_keys = json_data.keys()
    if not DEV:
        if current_os == "Windows":
            os.system('cls')
        else:
            os.system('clear')
    p_count = []
    for key in json_keys:
        if key[:1] == "2":
            data = json_data[key]
            if key in planes.keys():
                planes[key].update(data, my_pos)
                planes[key].get_change()
                planes[key].set_prev()
            else:
                global LATEST_IDS
                LATEST_IDS, plane_id = assign_id(LATEST_IDS)
                planes[key] = Plane(plane_id, data, weather[0])
            p_count.append(key)

    for key in planes.keys():
        if key not in p_count and key not in old_keys.keys():
            old_keys[key] = time.time()
            planes[key].update_conn("SIGNAL LOSS$F")
        elif key in p_count and key in old_keys.keys():
            del old_keys[key]
            planes[key].update_conn("ONLINE$G")

    removed = []
    for old_key, old_time in old_keys.items():
        if old_key not in removed:
            if (time.time() - old_time) > 30.0:
                del planes[old_key]
                removed.append(old_key)
    for rem in removed:
        del old_keys[rem]

    planes_list = [plane for _, plane in planes.items() if plane.show == True]
    planes_list.sort(key=lambda x: x.id, reverse=False)

    if bbox:
        draw_radar(bbox, my_pos, [[plane.lat, plane.lon, plane.id] for plane in planes_list], airports, planes_list)

    status = status_box(len(planes_list), weather, my_pos, metar)
    plane_stats = [plane.stats for plane in planes_list] + status
    print_blocks(plane_stats)
    return planes, old_keys, [plane.passed_me for plane in planes_list if plane.passed_me]


args = parse_args()
setup_cache()
if args.mode == "online":
    get_data(bbox=args.bbox, create_log=args.write_log)
elif args.mode == "log":
    get_data(read_log=args.log_path)
else:
    print("you got to provide mode")
