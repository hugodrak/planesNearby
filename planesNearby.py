import json
import requests
import time
import os
import argparse

def parse_args():
    parser= argparse.ArgumentParser()
    parser.add_argument("--bbox", default="59.781238,58.654034,15.793447,19.970999")
    return parser.parse_args()


block_width = 30
rows, columns = os.popen('stty size', 'r').read().split()
blocks_wide = int(columns) // block_width

def get_color(code):
    colors = {"B": '\033[94m', "G": '\033[92m', "W": '\033[93m', "F": '\033[91m', "END": '\033[0m', "BOLD": '\033[1m', "UNDER": '\033[4m', "M": '\033[95m'}
    return colors[code]

def add_margin(str, length, sign):
    if len(str) > length:
        str = str[:length]
    margin = length - len(str)
    out = ""
    if margin%2==0:
        out = sign*(margin//2) + str + sign*(margin//2)
    else:
        out = sign*((margin//2)) + str + sign*((margin//2)+1)
    return out

def print_blocks(blocks):
    str_blocks = []
    for block in blocks:
        template = "{title}\n{data}\n{bottom}"
        if len(block) > 1:
            data_list = []
            for val in block[1:]:
                if "$" in val:
                    val_split = val.split("$")
                    color = get_color(val_split[1])
                    data_list.append(f'|{color}'+add_margin(str(val_split[0]), block_width-2, " ")+f'{get_color("END")}|')
                else:
                    data_list.append('|'+add_margin(str(val), block_width-2, " ")+'|')
            data = "\n".join(data_list)
        else:
            data = '|'+add_margin("", block_width-2, " ")+'|'
        info = {"title": add_margin(str(block[0]), block_width, "_"),
        "data": data,
        "bottom": add_margin("", block_width, "-")}
        str_blocks.append(template.format(**info))

    cols = [[] for i in range(blocks_wide)]

    for i, block in enumerate(str_blocks):
        block_rows = block.split("\n")
        for br in block_rows:
            cols[i%blocks_wide].append(br)
    rows = []
    for col in cols:
        rows.extend([[] for r in range(1+len(col)-len(rows)) if r > 0])
        for i, item in enumerate(col):
            rows[i].append(item)
    print("\n".join([" ".join(r) for r in rows]))



def print_stats(prev, limit, val, signs, unit, var, max=None):
    out = ""
    delta = prev - val
    if max:
        if abs(prev-val) > max//2:
            if val < prev:
                delta = -(max - abs(val-prev))
            else:
                delta = (max - abs(val-prev))
        else:
            delta = prev-val

    if abs(delta) > limit:
        p_delta = abs(round(delta, 2))
        if type(val) == int:
            val = format(val, ",d")
        if delta < 0:
            out = f"{var}: {val}{unit}|{signs[1]} {p_delta}{unit}"
        else:
            out = f"{var}: {val}{unit}|{signs[0]} {p_delta}{unit}"
    return out

def lookup_type(type):
    rows = open("./plane_types.txt", "r").read().splitlines()
    for row in rows:
        rowsplit = row.split(";")
        if type in [rowsplit[0], rowsplit[1]]:
            return rowsplit[2]
    return type

def lookup_airport(airport):
    if airport != "":
        rows = open("./airports.txt", "r").read().splitlines()
        for row in rows:
            rowsplit = row.split(";")
            if airport in [rowsplit[1], rowsplit[2]]:
                return rowsplit[3]
    return airport

def lookup_company(company):
    if company != "":
        rows = open("./companies.txt", "r").read().splitlines()
        for row in rows:
            rowsplit = row.split(";")
            if company == rowsplit[0]:
                return rowsplit[1]
    return company


class Plane:
    def __init__(self, data):
        self.type = lookup_type(data[8])
        self.squawk = data[6]
        self.company = lookup_company(data[18])
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
        self.flightno = data[13]
        self.callsign = data[16]
        self.prev = [self.time, self.lat, self.lon, self.course, self.height, self.speed]
        self.stats = [f"{self.callsign}/{self.flightno}","CRS$B","LAT$B","LON$B","LVL$B","SPD$B", "ONLINE$G", self.departure, self.destination, self.type, self.company]

    def update(self, data):
        self.time = data[10]
        self.lat = data[1]
        self.lon = data[2]
        self.course = data[3]
        self.height = data[4]
        self.speed = data[5]
        self.time = data[10]

    def get_change(self):
        course_s = print_stats(self.prev[3], 0, self.course, ["CCW", "CW"], "°", "CRS", max=360)
        if course_s != "":
            self.stats[1] = course_s
        lat_s = print_stats(self.prev[1], 0.005, self.lat, ["◀", "▶"], "°", "LAT")
        if lat_s != "":
            self.stats[2] = lat_s
        lon_s = print_stats(self.prev[2], 0.005, self.lon, ["▼", "▲"], "°", "LON")
        if lon_s != "":
            self.stats[3] = lon_s
        height_s = print_stats(self.prev[4], 10, self.height, ["▼", "▲"], "ft", "LVL")
        if height_s != "":
            self.stats[4] = height_s
        if self.speed > 0.5:
            speed_s = print_stats(self.prev[5], 1, self.speed, ["▼", "▲"], "kn", "SPD")
        else:
            speed_s = "0"
        if speed_s != "":
            self.stats[5] = speed_s

    def set_prev(self):
        self.prev = [self.time, self.lat, self.lon, self.course, self.height, self.speed]
    def update_conn(self, conn):
        self.stats[6] = conn
    def lookup_type(self, type):
        rows = open("./type_design.txt", "r").read().splitlines()
        for row in rows:
            rowsplit = row.split(";")
            if type in [rowsplit[0], rowsplit[1]]:
                self.type = rowsplit[2]

def get_data(bbox=None, read_log=None, create_log=None):
    planes = {}
    old_keys = {}

    if bbox:
        url = f"https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds={bbox}&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=1&air=1&vehicles=1&estimated=1&maxage=14400&gliders=1&stats=1&enc=WPix0NeDQJ6xOmiczStTqq2XtL_YRMqUg86w4siPKdQ"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"}
        sess = requests.session()
        if create_log:
            w_log = open(create_log, "w")
        else:
            w_log = None
        while True:
            try:
                resp = sess.get(url, headers=headers)
            except:
                print("Connection broke, retrying...")
                time.sleep(5)
                continue
            if resp.status_code != 200:
                print(f"Status {resp.status_code}")
                time.sleep(5)
                continue

            planes, old_keys = run_iteration(resp.text, planes, old_keys, w_log)
            time.sleep(3)
    elif read_log:
        r_log = open(read_log, "r").read().split("}}}")[:-1]
        for row in r_log:
            planes, old_keys = run_iteration(row+"}}}", planes, old_keys)
            time.sleep(3)
        print("LOG END")

def run_iteration(resp, planes, old_keys, w_log=None):
    if w_log:
        w_log.write(resp+"\n")
    json_data = json.loads(resp)
    json_keys = json_data.keys()
    print(chr(27) + "[2J")
    p_count = []
    for key in json_keys:
        if key[:2] == "24":
            data = json_data[key]
            if key in planes.keys():
                planes[key].update(data)
                planes[key].get_change()
                planes[key].set_prev()
            else:
                planes[key] = Plane(data)
            p_count.append(key)

    for key in planes.keys():
        if key not in p_count and key not in old_keys.keys():
            old_keys[key] = time.time()
            planes[key].update_conn("OFFLINE$F")
        elif key in p_count and key in old_keys.keys():
            del old_keys[key]
            planes[key].update_conn("ONLINE$G")

    removed = []
    for old_key, old_time in old_keys.items():
        if old_key not in removed:
            if (time.time() - old_time) > 60.0:
                del planes[old_key]
                removed.append(old_key)
    for rem in removed:
        del old_keys[rem]

    planes_list = [plane for _, plane in planes.items()]
    planes_list.sort(key=lambda x: x.callsign, reverse=False)
    plane_stats = [plane.stats for plane in planes_list]+[["Planes", f"No. {len(planes_list)}", f"TIME: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}"]]
    print_blocks(plane_stats)
    return planes, old_keys

args = parse_args()
get_data(bbox=args.bbox)
#get_data(read_log="log.txt")
