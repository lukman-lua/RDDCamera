import math
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # radius bumi (meter)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # meter

def speed_kmh(lat1, lon1, t1, lat2, lon2, t2):
    # jarak (meter)
    distance = haversine(lat1, lon1, lat2, lon2)

    # selisih waktu (detik)
    delta_time = (t2 - t1).total_seconds()
    if delta_time <= 0:
        return 0

    # m/s
    speed_mps = distance / delta_time

    # km/h
    speed_kmh = speed_mps * 3.6
    return speed_kmh

def getSpeed(prev, lat, lon, timestamp):
    lat1, lon1, t1 = prev
    speed = speed_kmh(lat1, lon1, t1, lat, lon, timestamp)
    prev = (lat, lon, timestamp)
    return speed


# example
# lat1, lon1 = -6.2000, 106.8168
# lat2, lon2 = -6.2005, 106.8175
#
# t1 = datetime.fromisoformat("2025-12-13T10:00:00")
# t2 = datetime.fromisoformat("2025-12-13T10:00:05")
#
# v = speed_kmh(lat1, lon1, t1, lat2, lon2, t2)
# print(f"Kecepatan: {v:.2f} km/h")
