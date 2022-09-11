import json
import requests
import time
import argparse
import geocoder
from geopy.distance import distance
from weather_calc import cloud_get, get_metar
from terminalsize import get_terminal_size
import platform


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, help="online or log")
    parser.add_argument("--bbox", default="59.781238,58.654034,15.793447,19.970999",
                        help="59.78,58.65,15.79,19.97")
    parser.add_argument("--log-path", default="log.txt", help="path to log file")
    parser.add_argument("--write-log", default=None, help="path to log that will be created")

    return parser.parse_args()


block_width = 30
columns, rows = get_terminal_size()
#rows, columns = os.popen('stty size', 'r').read().split()
blocks_wide = int(columns) // block_width
current_os = platform.system()


def get_my_position():
    g = geocoder.ip('me')
    return g.latlng


def calc_gps_distace(my_coord, second_coord):
    dist = round(distance(my_coord, second_coord).m * 0.001, 2)
    direction = ""
    ns_tuning = 0.002
    ew_tuning = 0.002
    if abs(my_coord[0] - second_coord[0]) > dist * ns_tuning:
        if my_coord[0] < second_coord[0]:
            direction += "N"
        else:
            direction += "S"
    if abs(my_coord[1] - second_coord[1]) > dist * ew_tuning:
        if my_coord[1] < second_coord[1]:
            direction += "E"
        else:
            direction += "W"

    return dist, direction


def print_stats(prev, limit, val, signs, unit, var, max_val=None):
    delta = prev - val
    if max_val:
        if abs(prev - val) > max_val // 2:
            if val < prev:
                delta = -(max_val - abs(val - prev))
            else:
                delta = (max_val - abs(val - prev))
        else:
            delta = prev - val

    # if abs(delta) > limit:
    p_delta = abs(round(delta, 2))
    if type(val) == int:
        val = format(val, ",d")

    if delta < -0.01:
        out = f"{var}: {val}{unit} |{signs[1]} {p_delta}{unit}"
    elif delta > 0.01:
        out = f"{var}: {val}{unit} |{signs[0]} {p_delta}{unit}"
    else:
        out = f"{var}: {val}{unit} |{' ' * len(signs[1])} {p_delta}{unit}"

    return out


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
    def __init__(self, data, cloud_height):
        self.key = data[0]
        self.type = lookup_type(data[8])
        self.squawk = data[6]
        self.company = lookup_airline(data[18])
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
        self.direction_rel_to_me = ""
        self.passed_me = []
        self.has_passed = False
        self.prev = [self.time, self.lat, self.lon, self.course, self.height,
                     self.speed, self.dist_to_me]

        self.stats = [f"{self.callsign}/{self.flightno}", "CRS$B", "LAT$B", "LON$B",
                      "LVL$B", "SPD$B", "ONLINE$G",
                      self.departure, self.destination, self.type, self.company, "DIST", "LOOK TO"]

    def update(self, data, my_pos):
        if my_pos:
            dist, direction = calc_gps_distace(my_pos, (self.lat, self.lon))
            self.dist_to_me = dist
            self.direction_rel_to_me = direction
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
            self.stats[2] = print_stats(self.prev[1], 0.005, self.lat, ["◀", "▶"], "°", "LAT")

        if self.lon != self.prev[2]:
            self.stats[3] = print_stats(self.prev[2], 0.005, self.lon, ["▼", "▲"], "°", "LON")

        if self.height < 20:
            self.stats[4] = "ON GROUND$W"
        elif self.height != self.prev[4]:
            self.stats[4] = print_stats(self.prev[4], 10, self.height, ["▼", "▲"], "ft", "LVL")

        if self.speed != self.prev[5]:
            self.stats[5] = print_stats(self.prev[5], 1, self.speed, ["▼", "▲"], "kn", "SPD")

        if self.dist_to_me != self.prev[6]:
            dist_s = print_stats(self.prev[6], 0.01, self.dist_to_me, ["▼", "▲"], "km", "DIST")
            if dist_s != "":
                if self.dist_to_me < 15:  # 15 km
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

        self.stats[12] = "LOOK TO: " + self.direction_rel_to_me + cloud_status

    def set_prev(self):
        self.prev = [self.time, self.lat, self.lon, self.course, self.height, self.speed,
                     self.dist_to_me]

    def update_conn(self, conn):
        self.stats[6] = conn


class Backend:
    def __init__(self):
        self.planes = {}
        self.old_keys = {}
        self.my_pos = get_my_position()
        self.weather = cloud_get(self.my_pos)
        self.last_update = time.time()
        self.bbox = f"{self.my_pos[0] + 0.5},{self.my_pos[0] - 0.5},{self.my_pos[1] - 1.8},{self.my_pos[1] + 1.8}"
        if self.bbox:
            self.url = f"https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds={self.bbox}" \
                  f"&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1" \
                  f"&maxage=14400&gliders=1&stats=1&enc=WPix0NeDQJ6xOmiczStTqq2XtL_YRMqUg86w4siPKdQ"
            self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"}
            self.sess = requests.session()

            passed_log = open("passed.log", "a", encoding="utf8")
            current_metar = ""
            if self.my_pos:
                self.current_metar = get_metar(f"{self.my_pos[0]},{self.my_pos[1]}")

    def iterate(self):
        curr_time = time.time()
        if (curr_time - self.last_update) < 1:
            time.sleep(1 - (curr_time - self.last_update))

        try:
            resp = self.sess.get(self.url, headers=self.headers)
        except IOError:
            print("Connection broke, retrying...")
            return None
        if resp.status_code != 200:
            print(f"Status {resp.status_code}")
            return None

        json_data = json.loads(resp.text)
        json_keys = json_data.keys()

        p_count = []
        for key in json_keys:
            if key[:1] == "2":
                data = json_data[key]
                if key in self.planes.keys():
                    self.planes[key].update(data, self.my_pos)
                    self.planes[key].get_change()
                    self.planes[key].set_prev()
                else:
                    self.planes[key] = Plane(data, self.weather[0])
                p_count.append(key)

        for key in self.planes.keys():
            if key not in p_count and key not in self.old_keys.keys():
                self.old_keys[key] = time.time()
                self.planes[key].update_conn("SIGNAL LOSS$F")
            elif key in p_count and key in self.old_keys.keys():
                del self.old_keys[key]
                self.planes[key].update_conn("ONLINE$G")

        removed = []
        for old_key, old_time in self.old_keys.items():
            if old_key not in removed:
                if (time.time() - old_time) > 30.0:
                    del self.planes[old_key]
                    removed.append(old_key)
        for rem in removed:
            del self.old_keys[rem]

        planes_list = [plane for _, plane in self.planes.items()]
        planes_list.sort(key=lambda x: x.callsign, reverse=False)
        self.last_update = time.time()
        return True
