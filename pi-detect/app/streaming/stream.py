"""
MJPEG streaming blueprint.

Endpoint /stream/video serves a multipart MJPEG stream that any
browser, VLC, or OpenCV client can consume without plugins.
"""

import time
import cv2
from flask import Blueprint, Response, current_app
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

stream_bp = Blueprint("stream", __name__, url_prefix="/stream")

_BOUNDARY = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
_MIN_FRAME_INTERVAL = 1.0 / Config.STREAM_MAX_FPS


def _generate_frames():
    """
    Generator that yields MJPEG multipart frames.
    Runs detection every DETECTION_SKIP_FRAMES frames for performance.
    """
    camera = current_app.camera
    detector = current_app.detector
    detection_enabled = current_app.config["DETECTION_ENABLED"]

    skip = Config.DETECTION_SKIP_FRAMES
    frame_index = 0
    last_boxes = []            # cache boxes between detection frames
    last_sent = 0.0

    while True:
        now = time.time()
        # Rate-limit the output stream
        if now - last_sent < _MIN_FRAME_INTERVAL:
            time.sleep(0.005)
            continue

        frame = camera.read()
        if frame is None:
            time.sleep(0.02)
            continue

        # Run detection only on every Nth frame
        if detection_enabled and detector is not None:
            if frame_index % skip == 0:
                last_boxes = detector.detect(frame)
            _draw_boxes(frame, last_boxes)

        frame_index += 1

        # Encode to JPEG
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, Config.STREAM_QUALITY]
        success, buffer = cv2.imencode(".jpg", frame, encode_params)
        if not success:
            continue

        last_sent = time.time()
        yield _BOUNDARY + buffer.tobytes() + b"\r\n"


def _draw_boxes(frame, boxes: list):
    """Draw bounding boxes and labels on the frame in-place."""
    for box in boxes:
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
        label = box["label"]
        conf = box["confidence"]
        color = box.get("color", (0, 255, 0))

        # Box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Label background
        text = f"{label} {conf:.0%}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)

        # Label text
        cv2.putText(
            frame, text, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA,
        )

    # Overlay: detection count
    count_text = f"Objects: {len(boxes)}"
    cv2.putText(
        frame, count_text, (8, 22),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA,
    )


@stream_bp.route("/video")
def video_feed():
    return Response(
        _generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@stream_bp.route("/snapshot")
def snapshot():
    """Return a single JPEG snapshot — useful for quick checks."""
    camera = current_app.camera
    detector = current_app.detector
    frame = camera.read()

    if frame is None:
        return Response("Camera not ready", status=503)

    if detector and current_app.config["DETECTION_ENABLED"]:
        boxes = detector.detect(frame)
        _draw_boxes(frame, boxes)

    _, buffer = cv2.imencode(".jpg", frame,
                              [cv2.IMWRITE_JPEG_QUALITY, 90])
    return Response(buffer.tobytes(), mimetype="image/jpeg")
