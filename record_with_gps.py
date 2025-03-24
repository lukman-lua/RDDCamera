import time
import signal
import cv2
import threading
import serial
import argparse
import csv
from datetime import datetime
from JetsonCamera import Camera
from Focuser import Focuser
from Autofocus import FocusState, doFocus

# Global variables
exit_ = False
recording = False
video_writer = None
gps_port = "/dev/ttyTHS1"  # Sesuaikan port GPS
baud_rate = 115200
ser = serial.Serial(gps_port, baud_rate, timeout=3)
frame_count = 0
start_time = time.time()

# Signal handler untuk menangani shutdown
def sigint_handler(signum, frame):
    global exit_
    exit_ = True

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)

# Parsing command line arguments
def parse_cmdline():
    parser = argparse.ArgumentParser(description='Arducam IMX519 Autofocus & GPS Logger.')

    parser.add_argument('-i', '--i2c-bus', type=int, required=True,
                        help='Set i2c bus (Jetson Nano B01 = 7 atau 8).')

    parser.add_argument('-v', '--verbose', action="store_true", help='Print debug info.')

    return parser.parse_args()

# Fungsi untuk memulai perekaman video
def start_recording(frame):
    global video_writer
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    now = datetime.now()
    filename = now.strftime("output_%m_%d_%H_%M.avi")
    video_writer = cv2.VideoWriter(filename, fourcc, 30.0, (frame.shape[1], frame.shape[0]))
    print(f"Recording started: {filename}")
    return filename  # Mengembalikan nama file video

# Fungsi untuk menghentikan perekaman video
def stop_recording():
    global video_writer
    if video_writer:
        video_writer.release()
        video_writer = None
        print("Recording stopped.")

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
    return None, None

# Menyimpan metadata & GPS ke CSV
def save_gps_data(csv_filename, timestamp, latitude, longitude):
    with open(csv_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, latitude, longitude])

if __name__ == "__main__":
    args = parse_cmdline()
    camera = Camera()
    focuser = Focuser(args.i2c_bus)
    focuser.verbose = args.verbose

    focusState = FocusState()
    focusState.verbose = args.verbose
    doFocus(camera, focuser, focusState)

    frame_count = 0
    start_time = time.time()
    
    gps_filename = datetime.now().strftime("gps_%m_%d_%H_%M.csv")

    # Tulis metadata awal ke CSV
    with open(gps_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["# Metadata"])
        writer.writerow(["# Device", "Jetson Nano"])
        writer.writerow(["# GPS Model", "UBlox NEO-6M"])
        writer.writerow(["# Recording Start", datetime.now().isoformat()])
        writer.writerow(["Timestamp", "Latitude", "Longitude"])

    while not exit_:
        frame = camera.getFrame(2000)
        cv2.imshow("Camera Feed", frame)

        # Ambil data GPS
        if ser.in_waiting > 0:
            line = ser.readline().decode('ascii', errors='replace').strip()
            latitude, longitude = parse_nmea_sentence(line)
            if latitude and longitude:
                timestamp = datetime.now().isoformat()
                save_gps_data(gps_filename, timestamp, latitude, longitude)

        key = cv2.waitKey(1)
        
        if key == ord('q'):  # Tekan 'q' untuk keluar
            exit_ = True
        elif key == ord('f'):  # Tekan 'f' untuk refocus
            if focusState.isFinish():
                focusState.reset()
                doFocus(camera, focuser, focusState)
            else:
                print("Focus belum selesai.")
        elif key == ord('r'):  # Tekan 'r' untuk start/stop recording
            if recording:
                stop_recording()
                recording = False
            else:
                video_filename = start_recording(frame)
                recording = True
        
        # Menulis frame ke video jika recording aktif
        if recording and video_writer:
            video_writer.write(frame)

        # Hitung FPS
        frame_count += 1
        if time.time() - start_time >= 1:
            print(f"{frame_count} fps")
            start_time = time.time()
            frame_count = 0

    # Bersihkan resource saat keluar
    if video_writer:
        stop_recording()

    camera.close()
    ser.close()
    cv2.destroyAllWindows()

