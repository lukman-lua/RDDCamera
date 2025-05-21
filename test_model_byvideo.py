import cv2
import time
import torch
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("model/best.pt")

video_path = "0104.mp4"

cap = cv2.VideoCapture(video_path)

prev_time = 0	

while True:
    frame_count = 0  # Counter for frames
    success, frame = cap.read()
    if not success:
        print("Gagal membuka video.")
        break
    results = model.track(
        frame, 
        conf=0.4, 
        iou=0.4, 
        persist=True, 
        tracker="model/botsort.yaml",
        device="cuda"
    )
    
    for result in results:  # 'results' is plural, so loop over it
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            track_id = int(box.id[0]) if box.id is not None else -1  # Fixed inst -> int
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
    
    # Calculate FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    
    cv2.putText(
        frame, 
        f"FPS: {int(fps)}",
        (10, 30),  # Display at the top-left of the frame
        cv2.FONT_HERSHEY_SIMPLEX, 
        1,
        (0, 0, 255),
        2
    )
    
    cv2.imshow("YOLOv1 Tracking", frame)
    
    # Wait for 'q' key press to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
        
cap.release()
cv2.destroyAllWindows()  # Fixed typo

