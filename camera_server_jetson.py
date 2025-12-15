import cv2
import time
import socketio
import signal
import argparse
from datetime import datetime
from imx519.JetsonCamera import Camera
from imx519.Focuser import Focuser
from imx519.Autofocus import FocusState, doFocus

sio = socketio.Client()

connected = False
exit_ = False
recording = False
video_writer = None

def sigint_handler(signum, frame):
    global exit_
    exit_ = True

signal.signal(signal.SIGINT, sigint_handler)
signal.signal(signal.SIGTERM, sigint_handler)

def parse_cmdline():
    parser = argparse.ArgumentParser(description='Arducam IMX519 Autofocus Demo.')

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    parser.add_argument('-v', '--verbose', action="store_true", help='Print debug info.')

    return parser.parse_args()

# Callback saat berhasil konek ke Server 2
@sio.event
def connect():
    global connected
    connected = True
    print("✅ Connected to Server 2")

@sio.event
def disconnect():
    global connected
    connected = False
    print("❌ Disconnected from Server 2")


if __name__ == "__main__":
    args = parse_cmdline()
    camera = Camera()
    focuser = Focuser(args.i2c_bus)
    focuser.verbose = args.verbose

    focusState = FocusState()
    focusState.verbose = args.verbose
    doFocus(camera, focuser, focusState)

    # Hubungkan ke Server 2
    sio.connect("http://127.0.0.1:5050")  # ganti IP sesuai komputer Server 2

    # Tunggu sampai konek
    while not connected:
        print("⏳ Menunggu koneksi...")
        time.sleep(1)

    print("🎥 Streaming ke Server 2...")

    start = time.time()
    frame_count = 0

    while True:
        frame = camera.getFrame(2000)
        # Kompres ke JPEG
        _, jpeg = cv2.imencode('.jpg', frame)

        # Kirim frame hanya jika masih terkoneksi
        if connected:
            sio.emit('camera_frame', jpeg.tobytes())
