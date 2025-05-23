import time
from datetime import datetime
import cv2, threading, os
from flask import Flask, request, Response, render_template, jsonify
from ultralytics import YOLO
from queue import Queue
from inspection import save_cracks, create_inspection, update_inspections, displacement, update_cracks, \
    create_inspection_folder

app = Flask(__name__, static_folder='assets')

# Load the YOLO11 model
model = YOLO("model/best.pt")

# Open the video file
video_path = "0104.mp4"
cap = cv2.VideoCapture(video_path)

detect_start = True

gps = [
    [-6.200000, 106.816817],
    [-6.200000, 106.816968],
    [-6.200000, 106.817118],
    [-6.200000, 106.817269],
    [-6.200000, 106.817420],
    [-6.200000, 106.817571],
    [-6.200000, 106.817721],
    [-6.200000, 106.817872],
    [-6.200000, 106.818023],
    [-6.200000, 106.818174],
    [-6.200000, 106.818324],
    [-6.200000, 106.818475],
    [-6.200000, 106.818626],
    [-6.200000, 106.818777],
    [-6.200000, 106.818928],
    [-6.200000, 106.819078],
    [-6.200000, 106.819229],
    [-6.200000, 106.819380],
    [-6.200000, 106.819531],
    [-6.200000, 106.819681],
    [-6.200000, 106.819832],
    [-6.200000, 106.819983],
    [-6.200000, 106.820134],
    [-6.200000, 106.820284],
    [-6.200000, 106.820435],
    [-6.200000, 106.820586],
    [-6.200000, 106.820737],
    [-6.200000, 106.820888],
    [-6.200000, 106.821038],
    [-6.200000, 106.821189],
    [-6.200000, 106.821340],
    [-6.200000, 106.821491],
    [-6.200000, 106.821641],
    [-6.200000, 106.821792],
    [-6.200000, 106.821943],
    [-6.200000, 106.822094],
    [-6.200000, 106.822244],
    [-6.200000, 106.822395],
    [-6.200000, 106.822546],
    [-6.200000, 106.822697],
    [-6.200000, 106.822848],
    [-6.200000, 106.822998],
    [-6.200000, 106.823149],
    [-6.200000, 106.823300],
    [-6.200000, 106.823451],
    [-6.200000, 106.823601],
    [-6.200000, 106.823752],
    [-6.200000, 106.823903],
    [-6.200000, 106.824054],
    [-6.200000, 106.824204],
    [-6.200000, 106.824355],
    [-6.200000, 106.824506],
    [-6.200000, 106.824657],
    [-6.200000, 106.824808],
    [-6.200000, 106.824958],
    [-6.200000, 106.825109],
    [-6.200000, 106.825260],
    [-6.200000, 106.825411],
    [-6.200000, 106.825561],
    [-6.200000, 106.825712],
    [-6.200000, 106.825863],
    [-6.200000, 106.826014],
    [-6.200000, 106.826164],
    [-6.200000, 106.826315],
    [-6.200000, 106.826466],
    [-6.200000, 106.826617],
    [-6.200000, 106.826767],
    [-6.200000, 106.826918],
    [-6.200000, 106.827069],
    [-6.200000, 106.827220],
    [-6.200000, 106.827370],
    [-6.200000, 106.827521],
    [-6.200000, 106.827672],
    [-6.200000, 106.827823],
    [-6.200000, 106.827973],
    [-6.200000, 106.828124],
    [-6.200000, 106.828275],
    [-6.200000, 106.828426],
    [-6.200000, 106.828576],
    [-6.200000, 106.828727],
    [-6.200000, 106.828878],
    [-6.200000, 106.829029],
    [-6.200000, 106.829179],
    [-6.200000, 106.829330],
    [-6.200000, 106.829481]
]

now_cracks_id = 0
old_coordinat = None
now_inspection_id = None
now_inspection_folder = None

inspection_batch_size = 10
crack_batch_size = 10

inspection_batch_now = 0
crack_batch_now = 0

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


def save_frame_to_assets(frame, filename, inspection_folder):
    # Tentukan path folder assets
    assets_folder = os.path.join(
        os.getcwd(),
        'assets/inspections/nth_all'
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
    global gps
    current_time = time.time()
    elapsed_time = int(current_time - start_time)
    seconds = elapsed_time % 84
    return gps[seconds]


def generate_frames():
    global old_coordinat, crack_batch_now, \
        inspection_batch_now, detect_start, \
        now_inspection_folder, now_inspection_id, now_cracks_id
    now_inspection_id = 1

    while True:
        frame_count = 0  # Counter untuk frame
        success, frame = cap.read()
        if not success:
            # Restart video jika sudah selesai
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        annotated_frame = frame
        results = model.track(frame, conf=0.4, iou=0.4, persist=True, tracker="model/botsort.yaml")
        annotated_frame = results[0].plot()
        # Menyimpan gambar kerusakan ke folder assets
        crack_file_name = "frame_{0}.jpg".format(
            now_cracks_id
        )
        now_cracks_id += 1

        save_frame_to_assets(
            annotated_frame,
            crack_file_name,
            now_inspection_folder
        )

        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame = buffer.tobytes()
        frame_count += 1

        # Stream frame sebagai byte
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route("/")
def beranda():
    return render_template(
        "beranda.html",
        data={'menu': 'rdd'}
    )


@app.route("/rdd")
def report():
    return render_template(
        "detect.html",
        data={
            'menu': 'rdd',
            'location': [-6.200000, 106.816817]
        }
    )


@app.route("/rdd/start")
def start_inspect():
    global detect_start, now_inspection_folder
    inspection = create_inspection("-6.200000,106.816817")
    now_inspection_folder = create_inspection_folder(
        inspection['inspection_id'],
        "-6.200000,106.816817",
        datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    )
    if inspection and now_inspection_folder:
        detect_start = True

    status = detect_start
    print("detect_start : ", status)
    return jsonify({
        "message": "Inspection Started",
        "status": status
    })


@app.route("/rdd/end")
def end_inspect():
    global detect_start, now_inspection_id
    status = False

    if crack_batch_now >= crack_batch_size:
        save_status_crack = save_cracks(now_inspection_id, crack_data_list)
        if save_status_crack:
            crack_data_list.clear()

    save_status_inspection = update_inspections(now_inspection_id, inspection_session_data)
    if save_status_inspection:
        # Update informasi inspeksi batch terbaru
        inspection_session_data["count_crack"] = 0
        inspection_session_data["count_longitudinal_cracks"] = 0
        inspection_session_data["count_transverse_cracks"] = 0
        inspection_session_data["count_alligator_cracks"] = 0
        inspection_session_data["count_potholes"] = 0

    if inspection_session_data["count_crack"] == 0 and len(crack_data_list) == 0:
        detect_start = False
        status = True

    return jsonify({
        "message": "Inspection End",
        "status": status
    })


@app.route("/keluar")
def keluar():
    return render_template("keluar.html")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
