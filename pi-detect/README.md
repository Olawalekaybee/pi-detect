# Pi-Detect 🎯

**Real-time object detection with MJPEG live streaming on Raspberry Pi Zero 2W**

View the annotated camera feed from any browser on your laptop, phone, or tablet — over WiFi or 4G — with sub-20ms inference using YOLOv8n.

---

## Architecture

```
Pi Camera → PiCamera2 → OpenCV → YOLOv8n → Flask MJPEG → ngrok → Browser
                                                          ↕
                                                   /api/stats (JSON)
```

---

## Hardware

| Component | Spec |
|-----------|------|
| Board | Raspberry Pi Zero 2W |
| Camera | Pi Camera (v1/v2/HQ via ribbon) |
| Connectivity | 4G WiFi hotspot |
| Storage | microSD (16 GB+) |

---

## Quick Start

### 1. Flash the Pi

- Download **Raspberry Pi OS Lite 64-bit** from [raspberrypi.com/software](https://www.raspberrypi.com/software/)
- Flash to microSD with **Raspberry Pi Imager**
- In Imager settings, enable **SSH** and set your **WiFi credentials** (connect to your 4G hotspot)

### 2. Clone & install on the Pi

```bash
# SSH into Pi
ssh pi@<pi-ip-address>

# Clone the repo
git clone https://github.com/YOUR_USERNAME/pi-detect.git
cd pi-detect

# Run installer (takes ~5-10 min on Pi Zero 2W)
bash scripts/install_pi.sh
```

### 3. Configure

```bash
nano .env
```

Key settings to change:

```env
USE_PICAMERA=true
NGROK_AUTHTOKEN=your_token_from_ngrok.com
DETECTION_SKIP_FRAMES=3    # increase to 5 if CPU is too hot
STREAM_QUALITY=60          # lower for slower 4G connections
```

### 4. Start

```bash
bash scripts/start_stream.sh
```

The terminal will print a public ngrok URL — open it in any browser.

---

## Development on Laptop

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/pi-detect.git
cd pi-detect

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install
pip install -r requirements.txt

# Configure (use webcam)
cp .env.example .env
# Edit .env: set USE_PICAMERA=false

# Run
python main.py --debug
```

Open: [http://localhost:5000](http://localhost:5000)

---

## Project Structure

```
pi-detect/
├── main.py                     # Entry point
├── app/
│   ├── __init__.py             # App factory
│   ├── config.py               # All configuration
│   ├── routes.py               # Main routes + API endpoints
│   ├── detection/
│   │   └── detector.py         # YOLOv8n inference engine
│   ├── streaming/
│   │   ├── camera.py           # PiCamera2 / OpenCV abstraction
│   │   └── stream.py           # MJPEG stream blueprint
│   └── utils/
│       ├── logger.py           # Rotating file logger
│       └── metrics.py          # FPS / inference metrics
├── templates/
│   ├── index.html              # Live stream view
│   └── dashboard.html          # Analytics dashboard
├── static/
│   ├── css/style.css           # Dark theme design system
│   └── js/
│       ├── main.js             # Stream page logic
│       └── dashboard.js        # Dashboard charts
├── scripts/
│   ├── install_pi.sh           # Pi one-shot installer
│   ├── start_stream.sh         # Start server + tunnel
│   └── tunnel.sh               # ngrok 4G tunnel
├── models/                     # YOLOv8n weights (git-ignored)
├── logs/                       # Rotating logs (git-ignored)
├── requirements.txt            # Laptop deps
├── requirements-pi.txt         # Pi deps
└── .env.example                # Config template
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Live stream viewer |
| `/dashboard` | GET | Analytics dashboard |
| `/stream/video` | GET | MJPEG stream |
| `/stream/snapshot` | GET | Single JPEG snapshot |
| `/api/stats` | GET | Live metrics (JSON) |
| `/api/config` | GET | Current config (JSON) |
| `/api/health` | GET | Health check |

---

## Performance Tuning (Pi Zero 2W)

| Setting | Conservative | Balanced | Aggressive |
|---------|-------------|----------|------------|
| `DETECTION_SKIP_FRAMES` | 5 | 3 | 1 |
| `STREAM_QUALITY` | 50 | 70 | 85 |
| `STREAM_MAX_FPS` | 10 | 15 | 20 |
| `CAMERA_WIDTH/HEIGHT` | 320×240 | 640×480 | 640×480 |

---

## Opening Stream in VLC / OpenCV

**VLC:** `File → Open Network Stream → http://<ip>:5000/stream/video`

**OpenCV (Python):**
```python
import cv2
cap = cv2.VideoCapture("http://<public-ngrok-url>/stream/video")
while True:
    ret, frame = cap.read()
    cv2.imshow("Pi-Detect", frame)
    if cv2.waitKey(1) == ord("q"):
        break
```

---

## License

MIT
