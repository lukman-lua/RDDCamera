import eventlet
eventlet.monkey_patch()

import cv2, sys, time
from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
from rdd.inspection import connect_to_database
import multiprocessing

frame_queue = multiprocessing.Queue(maxsize=5)

# Load the YOLO11 model
check_db = {
    'last_id': 1,
}

# Open the video file
# Define video_path globally if it's constant for the camera_reader subprocess
video_path = "testvd.mp4" # change with camera or use 0 for webcam


def check_db_updates():
    global socketio,check_db
    conn = None  # Initialize connection to None
    cursor = None  # Initialize cursor to None
    while True:
        try:
            # SocketIO sleep ini penting agar tidak memblokir event loop
            socketio.sleep(3)  # Polling setiap 3 detik
            conn = connect_to_database()
            print("id :: ", 14)
            print("last id :: ", check_db['last_id'])
            cursor = conn.cursor()
            if conn and 13 and check_db['last_id']:
                socketio.sleep(2)  # cek setiap 2 detik
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
                socketio.emit('data_update', {'data': dict_rows})
            else:
                print("SERVER: No new notification this cycle.")  # Untuk debugging
        except Exception as e:
            print(f"SERVER: ERROR in background_notification_checker: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            # Lanjutkan loop meskipun ada error
            pass

        finally:
            # Ensure connection is closed when the background task stops
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            print("SERVER: Database update checker stopped.")


# Fungsi yang berjalan di proses terpisah untuk membaca dari kamera
def camera_reader(q, video_src):
    print("Camera reader process started.")
    # Inisialisasi kamera di dalam proses ini
    # Penting: Setiap proses memiliki sumber daya sendiri, termasuk kamera
    # Use video_path defined globally or pass it as an argument
    camera = cv2.VideoCapture(video_path) # <-- Open camera HERE
    if not camera.isOpened():
        print("ERROR: Could not open camera in subprocess.", file=sys.stderr)
        return

    while True:
        try:
            success, frame = camera.read()
            if not success:
                print("Camera reader: Failed to grab frame, trying to reopen...", file=sys.stderr)
                camera.release() # Release resources
                time.sleep(1)  # Wait a bit before retrying
                camera = cv2.VideoCapture(video_path) # <-- Reopen camera HERE
                if not camera.isOpened():
                    print("ERROR: Could not reopen camera in subprocess. Waiting...", file=sys.stderr)
                    time.sleep(5)  # Wait longer if failed again
                    continue
                continue # Skip to next iteration to try reading from reopened camera

            if q.full():
                q.get() # Drop oldest frame

            q.put(frame) # Put frame into queue

        except Exception as e:
            print(f"ERROR in camera_reader subprocess: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            time.sleep(1) # Wait before retrying

app = Flask(__name__, static_folder='assets')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# =========================================================================
# Video Streaming Generator
# =========================================================================
frame_counter = 0
def generate_frames():
    global frame_counter # Requires Python 3, or pass as mutable object
    while True:
        try:
            frame = frame_queue.get(timeout=5)
        except Exception:
            print("SERVER: No frame available in queue for 5s, retrying...", file=sys.stderr)
            socketio.sleep(0.1)
            continue

        frame_counter += 1
        if frame_counter == 10: # Hanya kirim 1 dari setiap 5 frame
            frame_counter = 0
            continue # Langsung lanjut ke frame berikutnya tanpa encoding/sending

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
@app.route('/')
def index():
    return render_template('test_rl.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

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
    # Start the camera reader process
    reader_process = multiprocessing.Process(target=camera_reader, args=(frame_queue, video_path))
    reader_process.daemon = True
    reader_process.start()
    print("SERVER: Camera reader process started as daemon.")

    # Start the database checker background task
    socketio.start_background_task(target=check_db_updates)

    # Run the Flask + Socket.IO server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)