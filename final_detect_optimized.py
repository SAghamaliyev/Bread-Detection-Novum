import cv2
import numpy as np
from ultralytics import YOLO
from final_base import *

model = YOLO("data/best.pt")
cap = cv2.VideoCapture("nigger.mp4")

ret, frame = cap.read()
if not ret:
    print("Ошибка: Видео не найдено или не читается.")
    exit()

FULL_W, FULL_H = frame.shape[1], frame.shape[0]

# ── Сколько кадров пропускать (2 = обрабатываем каждый 3-й) ──────────────────
SKIP_FRAMES = 1

# ─── 1. Выбор зоны зума (selectROI) ──────────────────────────────────────────
print("Выдели зону зума и нажми ENTER")
zoom_roi = cv2.selectROI("Select ZOOM zone (ENTER to confirm)", frame, False, False)
cv2.destroyAllWindows()

ZX, ZY, ZW, ZH = map(int, zoom_roi)
ZX2, ZY2 = ZX + ZW, ZY + ZH

# ─── 2. Рисование линии мышкой ────────────────────────────────────────────────
line_points = []

def draw_line(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(line_points) < 2:
        line_points.append((x, y))

zoomed_preview = cv2.resize(frame[ZY:ZY2, ZX:ZX2], (FULL_W, FULL_H))

cv2.namedWindow("Draw Line (2 clicks) + ENTER")
cv2.setMouseCallback("Draw Line (2 clicks) + ENTER", draw_line)

print("Кликни 2 точки для линии, затем ENTER. R — сброс.")

while True:
    temp = zoomed_preview.copy()
    cv2.rectangle(temp, (0, 0), (FULL_W-1, FULL_H-1), (255, 255, 0), 3)
    cv2.putText(temp, "ZOOM ZONE", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

    for pt in line_points:
        cv2.circle(temp, pt, 6, (0, 0, 255), -1)
    if len(line_points) == 2:
        cv2.line(temp, line_points[0], line_points[1], (0, 0, 255), 2)
        cv2.putText(temp, "ENTER для подтверждения", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Draw Line (2 clicks) + ENTER", temp)

    key = cv2.waitKey(1) & 0xFF
    if key == 13 and len(line_points) == 2:
        break
    elif key == ord('r'):
        line_points.clear()

cv2.destroyAllWindows()

lp1_zoom = line_points[0]
lp2_zoom = line_points[1]

def zoom_to_orig(px, py):
    ox = int(px * ZW / FULL_W) + ZX
    oy = int(py * ZH / FULL_H) + ZY
    return (ox, oy)

lp1 = zoom_to_orig(*lp1_zoom)
lp2 = zoom_to_orig(*lp2_zoom)

def side_of_line(px, py, ax, ay, bx, by):
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

# ─── Трекинг ──────────────────────────────────────────────────────────────────
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

track_history = {}
counted_ids   = set()
total_count   = 0
frame_idx     = 0

# Последний отрисованный результат (для пропущенных кадров)
last_boxes_draw = []   # список (ox1,oy1,ox2,oy2,cx,cy,tid,conf)

print(f"Обработка запущена. Пропуск кадров: {SKIP_FRAMES}. Нажмите 'q' для выхода.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # ── Детектируем только каждый (SKIP_FRAMES+1)-й кадр ──────────────────────
    if frame_idx % (SKIP_FRAMES + 1) == 0:

        crop   = frame[ZY:ZY2, ZX:ZX2]
        zoomed = cv2.resize(crop, (FULL_W, FULL_H))

        results = model.track(
            zoomed,
            persist=True,
            conf=0.25,
            iou=0.45,
            imgsz=320,
            tracker="bytetrack.yaml",
            device="cpu",
            verbose=False,
            stream=True
        )

        last_boxes_draw = []  # обновляем кэш боксов

        for r in results:
            if r.boxes is None or r.boxes.id is None:
                continue

            boxes = r.boxes.xyxy.cpu().numpy()
            ids   = r.boxes.id.cpu().numpy().astype(int)
            confs = r.boxes.conf.cpu().numpy()

            for box, tid, conf in zip(boxes, ids, confs):
                if conf < 0.99:
                    continue

                x1, y1, x2, y2 = map(int, box)

                ox1 = int(x1 * ZW / FULL_W) + ZX
                oy1 = int(y1 * ZH / FULL_H) + ZY
                ox2 = int(x2 * ZW / FULL_W) + ZX
                oy2 = int(y2 * ZH / FULL_H) + ZY
                cx  = (ox1 + ox2) // 2
                cy  = (oy1 + oy2) // 2

                curr_side = side_of_line(cx, cy,
                                         lp1[0], lp1[1],
                                         lp2[0], lp2[1])

                if tid in track_history:
                    if track_history[tid] * curr_side < 0 and tid not in counted_ids:
                        total_count += 1
                        counted_ids.add(tid)

                track_history[tid] = curr_side

                last_boxes_draw.append((ox1, oy1, ox2, oy2, cx, cy, tid, conf))

    # ── Рисуем последние известные боксы на текущем кадре ─────────────────────
    for (ox1, oy1, ox2, oy2, cx, cy, tid, conf) in last_boxes_draw:
        color = (255, 0, 255) if tid in counted_ids else (0, 255, 0)
        cv2.rectangle(frame, (ox1, oy1), (ox2, oy2), color, 2)
        cv2.circle(frame, (cx, cy), 4, color, -1)
        cv2.putText(frame, f"ID:{tid} {conf:.2f}", (ox1, oy1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # ── UI ────────────────────────────────────────────────────────────────────
    cv2.rectangle(frame, (ZX, ZY), (ZX2, ZY2), (255, 255, 0), 2)
    cv2.line(frame, lp1, lp2, (0, 0, 255), 2)
    cv2.circle(frame, lp1, 5, (0, 100, 255), -1)
    cv2.circle(frame, lp2, 5, (0, 100, 255), -1)

    cv2.rectangle(frame, (10, 10), (250, 60), (0, 0, 0), -1)
    cv2.putText(frame, f"TOTAL: {total_count}", (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Показываем какой кадр обрабатывается
    is_active = frame_idx % (SKIP_FRAMES + 1) == 0
    status = "DETECT" if is_active else f"SKIP {frame_idx % (SKIP_FRAMES+1)}/{SKIP_FRAMES}"
    color_s = (0, 255, 0) if is_active else (0, 165, 255)
    cv2.putText(frame, status, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_s, 2)

    cv2.imshow("Fast Counter 97% Conf", frame)
    frame_idx += 1

    if cv2.waitKey(1) & 0xFF == ord("q"):
        Base_Write(total_count)
        break

cap.release()
cv2.destroyAllWindows()
