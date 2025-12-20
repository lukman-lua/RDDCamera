import eventlet
import numpy as np

eventlet.monkey_patch()

import csv
from geopy.geocoders import Nominatim
from datetime import datetime
import cv2, os, threading, base64
from flask import Flask, render_template, jsonify, url_for
from ultralytics import YOLO
from flask_socketio import SocketIO, emit
from rdd.inspection import save_cracks, create_inspection, update_inspections, displacement, create_inspection_folder, connect_to_database, get_cracks, end_inspection, getInspectionByDate, get_all_cracks
from rdd.gps import getSpeed

app = Flask(__name__, static_folder='assets')
socketio = SocketIO(app, cors_allowed_origins="*")
app.config["SERVER_NAME"] = "localhost:5050"   # atau domainmu
app.config["PREFERRED_URL_SCHEME"] = "http"

# Inisialisasi geolocator
geolocator = Nominatim(user_agent="my_geocoder")

# Load the YOLO11 model
model = YOLO("model/best.pt")
location_file = "gps_04_20_07_14_test.csv"

# Open the video file
video_path = "testvd.mp4" # change with camera
# cap = cv2.VideoCapture(video_path)
# cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
detect_start = True

stop_event = threading.Event()
thread = None


        #     #
        #     Inspect Check Variable     #

inspect_status = False

        #     #
        #     Inspecting Variable     #

now_cracks_id = 0
old_coordinat = None
now_inspection_id = None
now_inspection_folder = None

crack_batch_size = 3

inspection_batch_now = 0
crack_batch_now = 0

check_db = {
    'last_id': 1,
}
crack_data_list = []

cracks_batch = {
    "image": "",
    "type": "",
    "coordinat": "",
}

inspection_session_data = {
    "count_crack": 0,
    "count_longitudinal_cracks": 0,
    "count_transverse_cracks": 0,
    "count_alligator_cracks": 0,
    "count_potholes": 0,
}




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


def save_frame_to_assets(frame, filename, inspection_folder):
    # Tentukan path folder assets
    assets_folder = os.path.join(
        os.getcwd(),
        'assets/inspections/' + inspection_folder
    )

    # Buat folder jika belum ada
    if not os.path.exists(assets_folder):
        os.makedirs(assets_folder)

    # Path lengkap file untuk disimpan
    file_path = os.path.join(assets_folder, filename)

    # Simpan frame sebagai JPG
    cv2.imwrite(file_path, frame)
    print(f"Frame berhasil disimpan di: {file_path}")


def getLocation(start_time):
    global data_gps
    # current_time = time.time()
    # seconds = int(current_time - start_time)
    return [data_gps[start_time]['latitude'], data_gps[start_time]['longitude']]


def check_db_updates():
    global socketio,check_db
    while True:
        try:
            # SocketIO sleep ini penting agar tidak memblokir event loop
            socketio.sleep(3)  # Polling setiap 3 detik
            conn = connect_to_database()
            print("id :: ", 14)
            print("last id :: ", check_db['last_id'])
            if conn and 13 and check_db['last_id']:
                socketio.sleep(2)  # cek setiap 2 detik
                cursor = conn.cursor()
                query = "SELECT id, damage_type " \
                        "FROM Detections " \
                        "WHERE inspection_id = {0} AND id > {1}".format(14, check_db['last_id'])
                cursor.execute(query)
                rows = cursor.fetchall()
                if len(rows) == 0:
                    cursor.close()
                    return False
                dict_rows = [dict(row) for row in rows]
                # last_id = dict_rows[-1]["id"]
                print("Data berubah:", dict_rows)
                # socketio.emit('data_update', {'data': dict_rows}, namespace='/')
        except Exception as e:
            print(f"ERROR in background_notification_checker: {e}")

def draw_overlay(frame, fps, speed):
    text = f"FPS: {fps:.1f} | Speed: {speed:.1f} km/h"

    cv2.putText(
        frame,
        text,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
        cv2.LINE_AA
    )
    return frame


@socketio.on("camera_frame")
def generate_frames(data):
    global old_coordinat, crack_batch_now, inspection_batch_now, \
        detect_start, now_inspection_folder, now_inspection_id, now_cracks_id, inspect_status

    socketio.emit('frame', data["frame"])

@socketio.on("detected")
def tracking_handler(data):
    global old_coordinat, crack_batch_now, inspection_batch_now, \
        detect_start, now_inspection_folder, now_inspection_id, now_cracks_id, inspect_status

    print("Detected inspection")
    print("Detected ID : ", data["list_id"])
    if data["detected"] and inspect_status:
        if max(data["list_id"]) > now_cracks_id:
            print("Cracking ID : ", data["list_id"])
            now_cracks_id = max(data["list_id"])

            # Menyimpan gambar kerusakan ke folder assets
            crack_file_name = "{0}_{1}_{2}.jpg".format(
                str(now_inspection_id),
                now_cracks_id,
                datetime.now().strftime('%H_%M_%S')
            )

            np_arr = np.frombuffer(data["frame"], np.uint8)
            img_to_save = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            save_frame_to_assets(
                img_to_save,
                crack_file_name,
                now_inspection_folder
            )
            with app.app_context():
                image_url = url_for(
                    'static',
                    filename="inspections/{0}/{1}".format(
                        now_inspection_folder,
                        crack_file_name
                    )
                )

            print("location : ", data["location"])

            socketio.emit(
                'data_update',
                {
                    'jenis': data["list_type"],
                    'image': image_url,
                    'count': len(data["list_type"]),
                    'location': data["location"],
                },
                namespace='/'
            )

            inspection_session_data["count_crack"] += len(data["list_type"])
            inspection_session_data["count_longitudinal_cracks"] += data["list_type"].count(0)
            inspection_session_data["count_transverse_cracks"] += data["list_type"].count(1)
            inspection_session_data["count_alligator_cracks"] += data["list_type"].count(2)
            inspection_session_data["count_potholes"] += data["list_type"].count(3)

            if old_coordinat is not None:
                coordinat_displacement = displacement(
                    old_coordinat[0], old_coordinat[1],
                    data["location"][0], data["location"][1]
                )
                print("coordinat_displacement : ", coordinat_displacement)
            else:
                print("old is none")
                coordinat_displacement = 0

            if coordinat_displacement > 30:
                # Simpan data kerusakan batch sebelumnya ke list daftar kerusakan
                cracks_batch["coordinat"] = old_coordinat
                crack_data_list.append(cracks_batch.copy())
                crack_batch_now += 1
                # Update informasi kerusakan batch terbaru
                old_coordinat = data
                cracks_batch["image"] = crack_file_name
                cracks_batch["type"] = str(data["list_type"].pop(0))
                for crack_type in data["list_type"]:
                    cracks_batch["type"] += "," + str(crack_type)
            else:
                if coordinat_displacement == 0:
                    old_coordinat = data["location"]
                if cracks_batch["image"] == "":
                    print("New image")
                    cracks_batch["image"] = crack_file_name
                    cracks_batch["type"] = str(data["list_type"].pop(0))
                else:
                    print("Add image")
                    cracks_batch["image"] += "," + crack_file_name
                for crack_type in data["list_type"]:
                    cracks_batch["type"] += "," + str(crack_type)


if inspect_status and crack_batch_now > 0:
    print("crack_data_list : ", crack_data_list)
    save_status = save_cracks(now_inspection_id, crack_data_list)
    if save_status:

        save_inspects = update_inspections(now_inspection_id, inspection_session_data)
        if save_inspects:
            # Update informasi inspeksi batch terbaru
            inspection_session_data["count_crack"] = 0
            inspection_session_data["count_longitudinal_cracks"] = 0
            inspection_session_data["count_transverse_cracks"] = 0
            inspection_session_data["count_alligator_cracks"] = 0
            inspection_session_data["count_potholes"] = 0
        else:
            print("Gagal Menyimpan inspection_session_data")
        for crack_data in crack_data_list:
            socketio.emit(
                'map_update',
                {
                    'inspection_id': now_inspection_id,
                    'location': crack_data['coordinat'],
                },
                namespace='/'
            )
        crack_data_list.clear()
        crack_batch_now = 0
    else:
        print("Gagal Menyimpan crack_data_list")

@app.route("/")
def beranda():
    socketio.emit("run_stop_stream", {"data": "ini data"})
    return render_template(
        "beranda.html",
        data={'menu': 'rdd'}
    )

@app.route("/report")
def report():
    return render_template(
        "reports.html",
        data={'menu': 'report'}
    )

def location_to_adress(lat, lon):
    global geolocator
    location = geolocator.reverse((lat, lon), language="id")
    return location.address if location else None

@socketio.on('report_changes')
def onClickCracks(data):
    date = data.get('date')
    report_list = getInspectionByDate(date)
    for rp in report_list:
        lat, lon = rp['location'].split(',')
        rp['address'] = location_to_adress(float(lat), float(lon))
    emit('report_update', {'report': report_list})


@socketio.on('start_stream')
def handle_start_stream(data):
    print(f"Perintah 'start_stream' diterima. Meneruskan ke Server 2...")
    # Meneruskan perintah ke Server 2
    socketio.emit('run_start_stream', data)

@socketio.on('stop_stream')
def handle_stop_stream(data):
    print(f"Perintah 'stop_stream' diterima. Meneruskan ke Server 2...")
    socketio.emit('run_stop_stream', data)

@socketio.on('autofocus')
def handle_autofocus(data):
    print(f"Perintah 'autofocus' diterima. Meneruskan ke Server 2...")
    socketio.emit('run_autofocus', data)

@app.route("/rdd")
def rdd():
    socketio.emit("run_start_stream", {"data":"ini data"})
    return render_template(
        "detect.html",
        data={
            'menu': 'rdd',
            'location': [-6.200000, 106.816817]
        }
    )


@app.route("/rdd/start")
def start_inspect():
    global inspect_status, now_inspection_folder, data_gps, \
        now_inspection_id, thread, stop_event

    # tambahkan code mengambil lokasi
    # location = getlocation()
    inspection = create_inspection(
        "{0},{1}".format(
            data_gps[590]['latitude'], data_gps[590]['longitude']
        )
    )
    print(inspection)
    if inspection:
        now_inspection_folder = create_inspection_folder(
            str(inspection),
            "{0},{1}".format(
            data_gps[590]['latitude'], data_gps[590]['longitude']
            ),
            datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        )

    if inspection and now_inspection_folder:
        inspect_status = True
        now_inspection_id = inspection

    status = inspect_status
    print("detect_start : ", status)
    return jsonify({
        "message": "Inspection Started",
        "status": status
    })


@app.route("/rdd/end")
def end_inspect():
    global inspect_status, now_inspection_id, stop_event, thread
    status = False
    print("end inspect id : ", now_inspection_id)
    if crack_batch_now >= 1:
        save_status_crack = save_cracks(now_inspection_id, crack_data_list)
        if save_status_crack:
            crack_data_list.clear()

    # save_status_inspection = update_inspections(now_inspection_id, inspection_session_data)
    if True:
    # if save_status_inspection:
        # Update informasi inspeksi batch terbaru
        inspection_session_data["count_crack"] = 0
        inspection_session_data["count_longitudinal_cracks"] = 0
        inspection_session_data["count_transverse_cracks"] = 0
        inspection_session_data["count_alligator_cracks"] = 0
        inspection_session_data["count_potholes"] = 0

    if inspection_session_data["count_crack"] == 0 and len(crack_data_list) == 0:
        inspection_status = end_inspection(now_inspection_id)
        if inspection_status:
            print("End Inspection Success")
            # Signal the thread to stop
            stop_event.set()
            if thread is not None:
                thread.join()  # Wait for the thread to finish

            inspect_status = False
            status = True

    return jsonify({
        "message": "Inspection End",
        "status": status
    })


@app.route("/keluar")
def keluar():
    return render_template("keluar.html")

@socketio.on('connect')
def test_connect():
    global check_db
    print('Client connected')
    # Saat klien terhubung, kirimkan notifikasi yang sudah ada (jika ada)
    if check_db['last_id']:
        emit('initial_notifications', {'data': 'ini data'})

@socketio.on('on-click-map')
def onClickMap(data):
    inspection_id = data.get('inspection_id')
    cracks_coordinat = data.get('coordinat')

    cracks = get_cracks(inspection_id, cracks_coordinat)
    image_list = cracks["image"].split(",")
    with app.app_context():
        image_url = [ url_for(
            'static',
            filename="inspections/{0}/{1}".format(now_inspection_folder, image_name))
            for image_name in image_list]
    emit('clickMap', {'cracks': cracks, 'image':image_url})

@socketio.on('report_click')
def reportClick(data):
    inspection_id = data.get('inspection_id')
    cracks_coordinat = data.get('coordinat')

    cracks = get_all_cracks(inspection_id)
    inspection_folder = "{0}_{1}".format(inspection_id, cracks_coordinat)
    base_url = url_for(
        'static',
        filename="inspections/{0}/".format(inspection_folder)
    )
    emit('more_report', {'cracks': cracks,'base_url':base_url})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    # Jalankan server Flask + Socket.IO
    socketio.run(app, debug=True, host='0.0.0.0', port=5050, allow_unsafe_werkzeug=True)

# socketio = SocketIO(app, cors_allowed_origins="*")
# # === Dari Server 1 (Jetson) ===
# @socketio.on('camera_frame')
# def handle_camera_frame(data):
#     # Broadcast ke semua browser client
#     socketio.emit('frame', data)
# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=5050)
