import serial,csv
from datetime import datetime



# GPS Global variables
gps_port = "/dev/ttyTHS1"  # Sesuaikan port GPS
baud_rate = 115200
ser = serial.Serial(gps_port, baud_rate, timeout=3)



# Ambil data GPS
if ser.in_waiting > 0:
    line = ser.readline().decode('ascii', errors='replace').strip()
    latitude, longitude = parse_nmea_sentence(line)
    if latitude and longitude:
        timestamp = datetime.now().isoformat()
        save_gps_data(gps_filename, timestamp, latitude, longitude)

def gps_to_csv(gps_filename):
    # Tulis metadata awal ke CSV
    with open(gps_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["# Metadata"])
        writer.writerow(["# Device", "Jetson Nano"])
        writer.writerow(["# GPS Model", "UBlox NEO-6M"])
        writer.writerow(["# Recording Start", datetime.now().isoformat()])
        writer.writerow(["Timestamp", "Latitude", "Longitude"])

# Menyimpan metadata & GPS ke CSV
def save_gps_data(csv_filename, timestamp, latitude, longitude):
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, latitude, longitude])

# Parsing data NMEA dari GPS
def parse_nmea_sentence(nmea_sentence):
    if nmea_sentence.startswith("$GNRMC"):
        parts = nmea_sentence.split(',')
        status = parts[2]

        if status == 'A':  # 'A' berarti data valid
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

            return latitude, longitude
        else:
            print("Menunggu GPS untuk mendapatkan fix...")
            return False
    return None, None