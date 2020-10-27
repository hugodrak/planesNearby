from math import sin, cos, sqrt, atan2, radians, degrees, acos, atan

# approximate radius of earth in km
R = 6373.0

def gps_direction(lat1, lon1, lat2, lon2, x_only=False):
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    lon_dist = None
    if not x_only:
        lon_dist = gps_direction(lat1, lon1, lat1, lon2, True)

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    if not x_only:
        if not -1 <= (lon_dist/distance) <= 1:
            return distance, 0.0
        angle = degrees(acos(lon_dist/distance))
        if dlat > 0 and dlon > 0:
            angle = 90 - angle
        elif dlat < 0 and dlon > 0:
            angle += 90
        elif dlat < 0 and dlon < 0:
            angle = (90-angle) + 180
        elif dlat > 0 and dlon < 0:
            angle += 270

        return distance, angle
    else:
        return distance

def plane_alt_angle(altitude, distance):
    if altitude < 10:
        return 0.0
    alt_metres = altitude/3.281
    angle = degrees(atan(alt_metres/(distance*1000)))
    return angle
