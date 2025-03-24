import torch
import cv2
import time
import argparse
from imx519.JetsonCamera import Camera
from imx519.Focuser import Focuser
from imx519.Autofocus import FocusState, doFocus
from ultralytics import YOLO

# Load model YOLOv11
model = YOLO("model/best.pt")  # Pastikan file model ada di direktori yang benar

def parse_cmdline():
    parser = argparse.ArgumentParser(description='Arducam IMX519 Autofocus Demo.')

    parser.add_argument('-i', '--i2c-bus', type=int, nargs=None, required=True,
                        help='Set i2c bus, for A02 is 6, for B01 is 7 or 8, for Jetson Xavier NX it is 9 and 10.')

    parser.add_argument('-v', '--verbose', action="store_true", help='Print debug info.')

    return parser.parse_args()

# Inisialisasi kamera Jetson
args = parse_cmdline()
camera = Camera()
focuser = Focuser(args.i2c_bus)
focuser.verbose = args.verbose

focusState = FocusState()
focusState.verbose = args.verbose
doFocus(camera, focuser, focusState)

# Variabel untuk menghitung FPS
prev_time = 0

# Warna untuk bounding box
# COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

while True:
    frame = camera.getFrame(2000)
    if frame is None:
        continue

    # Konversi frame ke tensor untuk YOLO
    results = model(frame)

    # Gambar bounding box dan label pada frame
    # for result in results:
        # for box in result.boxes.data:
            # x1, y1, x2, y2, conf, cls = box.tolist()
            # label = f"{model.names[int(cls)]} {conf:.2f}"
            # color = COLORS[int(cls) % len(COLORS)]
            
            # Gambar bounding box
            # cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            # cv2.putText(frame, label, (int(x1), int(y1) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    annotated_frame = results[0].plot()

    # Hitung FPS
    curr_time = time.time()
    fps_display = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    # Tambahkan teks FPS pada frame
    cv2.putText(
        annotated_frame, 
        f"FPS: {int(fps_display)}",
        (10, 30),  # Display at the top-left of the frame
        cv2.FONT_HERSHEY_SIMPLEX, 
        1,
        (0, 0, 255),
        2
    )
    
    # Tampilkan hasil
    cv2.imshow("YOLOv11 Detection", annotated_frame)
    
    key = cv2.waitKey(1)
    if key == ord('f'):
        if focusState.isFinish():
            focusState.reset()
            doFocus(camera, focuser, focusState)
        else:
            print("Focus is not done yet.")

    # Tekan 'q' untuk keluar
    if key & 0xFF == ord('q'):
        break

camera.close()
cv2.destroyAllWindows()

