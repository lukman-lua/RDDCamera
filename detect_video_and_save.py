import cv2
import time
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("model/best.pt")

video_path = "./Jetson_IMX519_Focus_Example/output_1.avi"
output_video_path = "./output_detected_video.avi"  # Output video path

cap = cv2.VideoCapture(video_path)

# Cek apakah video berhasil dibuka
if not cap.isOpened():
    print("Gagal membuka video!")
    exit()

# Ambil informasi tentang ukuran frame dan FPS dari video input
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Inisialisasi VideoWriter untuk menulis video output
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Kodek video untuk .avi
out = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))

prev_time = 0

while True:
    success, frame = cap.read()
    if not success:
        print("Tidak ada frame yang dibaca dari video.")
        break

    # Proses deteksi dengan YOLO menggunakan model.detect()
    results = model.detect(frame)  # Menggunakan model.detect() untuk deteksi objek
    
    # Loop untuk menggambar bounding box dan menambahkan ID
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            track_id = int(box.id[0]) if box.id is not None else -1
            if conf > 0.5:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame, 
                    f"ID: {track_id}", 
                    (x1, y1-5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    (0, 255, 0), 
                    2
                )
    
    # Hitung FPS
    curr_time = time.time()
    fps_display = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    # Tambahkan teks FPS pada frame
    cv2.putText(
        frame, 
        f"FPS: {int(fps_display)}",
        (10, 30),  # Display at the top-left of the frame
        cv2.FONT_HERSHEY_SIMPLEX, 
        1,
        (0, 0, 255),
        2
    )

    # Simpan frame yang sudah diproses ke dalam video output
    out.write(frame)

# Bersihkan setelah selesai
cap.release()
out.release()
cv2.destroyAllWindows()

print(f"Hasil deteksi disimpan ke: {output_video_path}")

