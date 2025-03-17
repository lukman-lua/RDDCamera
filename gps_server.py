import gpxpy
import time


# Fungsi untuk membaca file GPX dan mensimulasikan pergerakan
def simulate_gps_log(gpx_file, speed=1):
    # Membaca file GPX
    with open(gpx_file, "r") as file:
        gpx = gpxpy.parse(file)

    # Mendapatkan koordinat dari file GPX
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))

    # Mensimulasikan log pergerakan
    print("Memulai simulasi pergerakan...")
    for i, location in enumerate(points):
        print(f"Titik {i + 1}/{len(points)}: {location}")
        time.sleep(1 / speed)  # Kontrol kecepatan (1/speed detik)
    print("Simulasi selesai.")


# Jalankan simulasi
simulate_gps_log("gps/20250107-163143 - Test1.gpx", speed=2)
