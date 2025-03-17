import math
import time


# Fungsi untuk menghitung koordinat baru berdasarkan jarak dan arah
def generate_new_point(lat, lon, distance_km, bearing_deg):
    R = 6371.0  # Radius Bumi dalam km
    lat, lon, bearing = map(math.radians, [lat, lon, bearing_deg])

    # Hitung koordinat baru
    new_lat = math.asin(math.sin(lat) * math.cos(distance_km / R) +
                        math.cos(lat) * math.sin(distance_km / R) * math.cos(bearing))
    new_lon = lon + math.atan2(math.sin(bearing) * math.sin(distance_km / R) * math.cos(lat),
                               math.cos(distance_km / R) - math.sin(lat) * math.sin(new_lat))

    # Konversi kembali ke derajat
    return math.degrees(new_lat), math.degrees(new_lon)


# Fungsi untuk mensimulasikan pergerakan mobil
def gps_simulator(start_lat, start_lon, speed_kmh, bearing_deg, duration_sec, interval_sec):
    current_lat, current_lon = start_lat, start_lon
    distance_per_interval = (speed_kmh / 3600) * interval_sec  # Jarak dalam km per interval
    gps_points = [(current_lat, current_lon)]  # Simpan titik awal

    for _ in range(int(duration_sec / interval_sec)):
        current_lat, current_lon = generate_new_point(current_lat, current_lon, distance_per_interval, bearing_deg)
        gps_points.append((current_lat, current_lon))
        print(f"Titik GPS: {current_lat:.6f}, {current_lon:.6f}")
        time.sleep(interval_sec)  # Simulasi waktu nyata

    return gps_points


# Parameter simulasi
start_lat = -6.200000  # Jakarta
start_lon = 106.816666
speed_kmh = 60  # Kecepatan dalam km/jam
bearing_deg = 90  # Arah perjalanan (90 derajat = timur)
duration_sec = 60  # Durasi simulasi (detik)
interval_sec = 1  # Interval pembaruan GPS (detik)

# Jalankan simulasi
gps_data = gps_simulator(start_lat, start_lon, speed_kmh, bearing_deg, duration_sec, interval_sec)
