# Bread Detection System (Novum)

Real-time bread detection and tracking using YOLOv8 with live camera feed. Includes desktop app (Electron) and data augmentation pipeline.

## 📁 Structure

```
Bread-Detection-Novum/
├── final_detect_live.py       # Real-time camera detection
├── final_detect.py            # Video file detection
├── final_base.py              # Base utilities
├── dataAugmentation.py        # Data augmentation
├── AllOurTransformations.py   # Augmentation transforms
├── requirements.txt           # Python dependencies
├── README.md
├── APP/                       # Electron desktop app
│   ├── src/                   # React components
│   ├── electron/              # Electron main process
│   ├── package.json
│   └── vite.config.js
└── data/                      # Models
    ├── best.pt                # Custom detection model
    ├── yolov8s.pt
    └── yolov8s-seg.pt
```

## 📄 Files

- **final_detect_live.py** - Real-time detection from RTSP camera
- **final_detect.py** - Video file processing
- **dataAugmentation.py** - Data augmentation with Albumentations
- **APP/** - Electron desktop application (React frontend)

## 🚀 Setup

**Python:**
```bash
pip install -r requirements.txt
python final_detect_live.py        # Live camera detection
python final_detect.py             # Video file detection
```

**Electron App:**
```bash
cd APP
npm install
npm run dev                         # Development
npm run dist                        # Build

## ⚙️ Configuration

**Camera (final_detect_live.py):**
```python
rtsp_url = "rtsp://192.168.0.112:554/rtsp/streaming?channel=01&subtype=0"
```

**Detection Settings:**
- `device="0"` → GPU (change to `"cpu"` if no GPU)
- `imgsz=640` → Image size (use 416 for weaker GPU)
- `conf=0.25` → Confidence threshold

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not found | Check RTSP URL |
| Slow detection | Use `imgsz=416` or `device="cpu"` with YOLOv8 Nano |
| Import errors | Run `pip install -r requirements.txt` |

## 📦 Models

- `best.pt` - Custom bread detection model
- `yolov8s.pt` - YOLOv8 Small detection
- `yolov8s-seg.pt` - YOLOv8 segmentation

---
**License:** ISC
