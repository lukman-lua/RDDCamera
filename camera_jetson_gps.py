import eventlet
eventlet.monkey_patch()

import csv
from geopy.geocoders import Nominatim
from datetime import datetime
import cv2, os, threading, base64
from flask import Flask, Response, render_template, jsonify, url_for
from ultralytics import YOLO
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder='assets')
socketio = SocketIO(app, cors_allowed_origins="*")
app.config["SERVER_NAME"] = "localhost:5050"   # atau domainmu
app.config["PREFERRED_URL_SCHEME"] = "http"

# Inisialisasi geolocator
geolocator = Nominatim(user_agent="my_geocoder")

location_file = "gps_04_20_07_14_test.csv"

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

stop_event = threading.Event()
thread = None


def load_gps_data(csv_path):
    gps_data = []

    with open(csv_path, mode='r') as file:
        # Lewati baris sampai menemukan header yang benar
        while True:
            pos = file.tell()
            line = file.readline()
            if line.startswith("Timestamp,Latitude,Longitude"):
                file.seek(pos)
                break

        reader = csv.DictReader(file)
        for row in reader:
            try:
                timestamp = datetime.fromisoformat(row['Timestamp'])
                latitude = float(row['Latitude'])
                longitude = float(row['Longitude'])

                gps_data.append({
                    'timestamp': timestamp,
                    'latitude': latitude,
                    'longitude': longitude
                })
            except Exception as e:
                print(f"Skipping row due to error: {e}")
                continue

    return gps_data

data_gps = load_gps_data(location_file)


def getLocation(start_time):
    global data_gps
    # current_time = time.time()
    # seconds = int(current_time - start_time)
    return [data_gps[start_time]['latitude'], data_gps[start_time]['longitude']]

# Fitur menampilkan location, fps, speed
def generate_frames():
    time_now = datetime.now()
    location_now = getLocation(590)
    while not stop_event.is_set():
        frame_count = 0  # Counter untuk frame
        success, frame = cap.read()

        _, buffer = cv2.imencode('.jpg', frame)

        frame_data = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('frame',
                      {
                          'image': frame_data,
                          'location': location_now,
                          'timestamp': time_now
                       }
                      )
        eventlet.sleep(0.05)

def location_to_adress(lat, lon):
    global geolocator
    location = geolocator.reverse((lat, lon), language="id")
    return location.address if location else None


@app.route("/rdd")
def rdd():
    global thread, stop_event
    if thread is None or not thread.is_alive():
        stop_event.clear()
        thread = threading.Thread(target=generate_frames)
        thread.start()
    return render_template(
        "detect.html",
        data={
            'menu': 'rdd',
            'location': [-6.200000, 106.816817]
        }
    )

@socketio.on('connect')
def test_connect():
    global check_db
    print('Client connected')
    # Saat klien terhubung, kirimkan notifikasi yang sudah ada (jika ada)
    if check_db['last_id']:
        emit('initial_notifications', {'data': 'ini data'})




@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    # Jalankan server Flask + Socket.IO
    socketio.run(app, debug=True, host='0.0.0.0', port=5050, allow_unsafe_werkzeug=True)
