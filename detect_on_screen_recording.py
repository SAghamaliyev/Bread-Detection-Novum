import cv2
import numpy as np
import mss
from ultralytics import YOLO
from final_base import *

# =========================
# MODEL
# =========================
model = YOLO("data/best.pt")

# =========================
# SCREEN (FULLSCREEN)
# =========================
sct = mss.mss()
monitor = sct.monitors[1]  # весь экран

# =========================
# ПЕРВЫЙ КАДР (ROI)
# =========================
frame = np.array(sct.grab(monitor))
frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

roi = cv2.selectROI("Select ROI (iVMS fullscreen)", frame, False, False)
cv2.destroyAllWindows()

rx, ry, rw, rh = map(int, roi)
rx2, ry2 = rx + rw, ry + rh
line_y = ry + int(rh * 0.5)

# =========================
# TRACKING
# =========================
track_history = {}
counted_ids = set()
total_count = 0

# =========================
# GUI
# =========================
def nothing(x):
    pass

cv2.namedWindow("Controls")
cv2.createTrackbar("Confidence x100", "Controls", 90, 100, nothing)
cv2.createTrackbar("Exit (0/1)", "Controls", 0, 1, nothing)

print("Работает. Оставь iVMS на весь экран.")

# =========================
# MAIN LOOP
# =========================
while True:
    # захват экрана
    frame = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # GUI
    conf_thres = cv2.getTrackbarPos("Confidence x100", "Controls") / 100.0
    exit_flag = cv2.getTrackbarPos("Exit (0/1)", "Controls")

    if exit_flag == 1:
        Base_Write(total_count)
        break

    # 🔥 ускорение — работаем только внутри ROI
    roi_frame = frame[ry:ry2, rx:rx2]

    results = model.track(
        roi_frame,
        persist=True,
        conf=conf_thres,
        iou=0.45,
        imgsz=640,
        tracker="bytetrack.yaml",
        device="0",
        verbose=False
    )

    for r in results:
        if r.boxes is None or r.boxes.id is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy()
        ids = r.boxes.id.cpu().numpy().astype(int)
        confs = r.boxes.conf.cpu().numpy()

        for box, tid, conf in zip(boxes, ids, confs):

            x1, y1, x2, y2 = map(int, box)

            # возвращаем координаты в общий экран
            x1 += rx
            x2 += rx
            y1 += ry
            y2 += ry

            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if tid in track_history:
                prev_y = track_history[tid]

                if prev_y < line_y <= cy and tid not in counted_ids:
                    total_count += 1
                    counted_ids.add(tid)

            track_history[tid] = cy

            color = (0, 255, 0) if tid not in counted_ids else (255, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID:{tid} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)

    # линия и ROI
    cv2.line(frame, (rx, line_y), (rx2, line_y), (0, 0, 255), 2)
    cv2.rectangle(frame, (rx, ry), (rx2, ry2), (255, 255, 0), 2)

    # счетчик
    cv2.rectangle(frame, (10, 10), (260, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"TOTAL: {total_count}",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 255, 255), 2)

    cv2.imshow("Screen YOLO (iVMS)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        Base_Write(total_count)
        break

cv2.destroyAllWindows()