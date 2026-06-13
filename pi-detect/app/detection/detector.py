"""
Object detection engine using YOLOv8n (ultralytics).

Design decisions for Pi Zero 2W performance:
  - CPU inference only (no CUDA/Coral on Zero 2W)
  - YOLOv8n — smallest/fastest YOLO model (~3.2 MB)
  - Input size 320×320 (instead of default 640) for ~2× speed gain
  - Thread-safe last_* properties so routes can read stats cheaply
"""

import time
import threading
import numpy as np
import cv2
from pathlib import Path
from app.config import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)

# COCO colour palette — one BGR colour per class id
_PALETTE = [
    (56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255),
    (49, 210, 207), (10, 249, 72), (23, 204, 146), (134, 219, 61),
    (52, 147, 26), (187, 212, 0), (168, 153, 44), (255, 194, 0),
    (147, 69, 52), (255, 115, 100), (236, 24, 0), (255, 56, 132),
    (133, 0, 82), (255, 56, 203), (200, 149, 255), (199, 55, 255),
]


def _class_color(class_id: int) -> tuple:
    return _PALETTE[class_id % len(_PALETTE)]


class ObjectDetector:
    """YOLOv8n detector — thread-safe, lazy-loaded."""

    def __init__(self):
        self._model = None
        self._lock = threading.Lock()

        # Stats (read by /api/stats without locking)
        self.last_detection_count: int = 0
        self.last_inference_ms: float = 0.0
        self.last_labels: list[str] = []

        self._load_model()

    # ── Public ─────────────────────────────────────────────────────────────

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Run inference on a BGR frame.

        Returns a list of dicts:
          { x1, y1, x2, y2, label, confidence, class_id, color }
        """
        if self._model is None:
            return []

        # Resize to 320 for speed on Pi — maintains aspect ratio with padding
        input_frame = cv2.resize(frame, (320, 320))

        t0 = time.perf_counter()
        with self._lock:
            results = self._model(
                input_frame,
                imgsz=320,
                conf=Config.CONFIDENCE_THRESHOLD,
                iou=Config.IOU_THRESHOLD,
                max_det=Config.MAX_DETECTIONS,
                verbose=False,
                device=Config.DEVICE,
            )
        inference_ms = (time.perf_counter() - t0) * 1000

        boxes = self._parse_results(results, frame.shape)

        # Update stats
        self.last_inference_ms = inference_ms
        self.last_detection_count = len(boxes)
        self.last_labels = list({b["label"] for b in boxes})

        return boxes

    # ── Internal ───────────────────────────────────────────────────────────

    def _load_model(self):
        try:
            from ultralytics import YOLO  # type: ignore

            model_path = Path(Config.MODEL_PATH)
            if not model_path.exists():
                logger.info(
                    "Model not found locally — downloading %s …",
                    Config.MODEL_NAME,
                )
                # ultralytics downloads automatically when given a model name
                self._model = YOLO(Config.MODEL_NAME)
                # Save for offline use
                model_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                self._model = YOLO(str(model_path))

            # Warm-up pass so first real inference isn't slow
            dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            self._model(dummy, imgsz=320, verbose=False, device=Config.DEVICE)

            logger.info("YOLOv8n loaded and warmed up ✓")

        except ImportError:
            logger.error(
                "ultralytics not installed. Run: pip install ultralytics"
            )
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)

    def _parse_results(self, results, original_shape: tuple) -> list[dict]:
        """
        Scale bounding boxes from 320×320 inference space back to the
        original frame dimensions.
        """
        h_orig, w_orig = original_shape[:2]
        scale_x = w_orig / 320
        scale_y = h_orig / 320

        boxes = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                xyxy = box.xyxy[0].cpu().numpy().astype(int)
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                label = result.names.get(cls_id, str(cls_id))

                x1 = int(xyxy[0] * scale_x)
                y1 = int(xyxy[1] * scale_y)
                x2 = int(xyxy[2] * scale_x)
                y2 = int(xyxy[3] * scale_y)

                boxes.append({
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "label": label,
                    "confidence": conf,
                    "class_id": cls_id,
                    "color": _class_color(cls_id),
                })
        return boxes
