import serial

# Menghubungkan ke perangkat serial
gps_port = "/dev/ttyTHS1"  # Sesuaikan port ini
baud_rate = 115200
ser = serial.Serial(gps_port, baud_rate, timeout=3)

def parse_nmea_sentence(nmea_sentence):
    if nmea_sentence.startswith("$GNRMC"):
        parts = nmea_sentence.split(',')
        status = parts[2]  # Status 'A' untuk valid, 'V' untuk tidak valid

        if status == 'A':
            # Jika data valid, parsing latitude dan longitude
            raw_lat = float(parts[3])
            lat_dir = parts[4]
            raw_lon = float(parts[5])
            lon_dir = parts[6]

            lat_deg = int(raw_lat / 100)
            lat_min = raw_lat - (lat_deg * 100)
            latitude = lat_deg + (lat_min / 60)
            latitude = latitude if lat_dir == 'N' else -latitude

            lon_deg = int(raw_lon / 100)
            lon_min = raw_lon - (lon_deg * 100)
            longitude = lon_deg + (lon_min / 60)
            longitude = longitude if lon_dir == 'E' else -longitude

            print(f"Latitude: {latitude}, Longitude: {longitude}")
        else:
            print("Menunggu GPS untuk mendapatkan fix...")

try:
    print("Menunggu data GPS...")
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('ascii', errors='replace').strip()
            parse_nmea_sentence(line)

except KeyboardInterrupt:
    print("Program dihentikan.")
except Exception as e:
    print(f"Error: {e}")
finally:
    ser.close()

