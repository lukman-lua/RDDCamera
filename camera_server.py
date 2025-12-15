import cv2
import time
import socketio

sio = socketio.Client()

connected = False

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

# Hubungkan ke Server 2
sio.connect("http://127.0.0.1:5050")  # ganti IP sesuai komputer Server 2

# Tunggu sampai konek
while not connected:
    print("⏳ Menunggu koneksi...")
    time.sleep(1)

# === Kamera ===
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Tidak bisa membuka kamera")
    exit()

print("🎥 Streaming ke Server 2...")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Kompres ke JPEG
    _, jpeg = cv2.imencode('.jpg', frame)
    if not ret:
        continue

    # Kirim frame hanya jika masih terkoneksi
    if connected:
        sio.emit('camera_frame', jpeg.tobytes())
