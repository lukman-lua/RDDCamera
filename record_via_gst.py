import cv2

gst_pipeline = "nvarguscamerasrc sensor-id=0 ! nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! appsink"
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Gagal membuka kamera!")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal membaca frame!")
        break

    cv2.imshow("Kamera CSI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

