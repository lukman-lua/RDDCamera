import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
import cv2
import base64
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')
video_path = "testvd.mp4"
camera = cv2.VideoCapture(video_path)  # Webcam default

def stream_frames():
    while True:
        success, frame = camera.read()
        if not success:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('frame', {'data': frame_data})
        eventlet.sleep(0.05)  # ~30 FPS

@app.route('/')
def index():
    return render_template('websocket.html')

@socketio.on('connect')
def connect():
    print('Client connected')

if __name__ == '__main__':
    threading.Thread(target=stream_frames).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
