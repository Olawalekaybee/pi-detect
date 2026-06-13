"""
Lightweight in-memory metrics collector.
No external dependencies — just a rolling window of values.
"""

import time
from collections import deque


class MetricsCollector:
    """Keeps a rolling window of FPS and inference time samples."""

    def __init__(self, window: int = 60):
        self._window = window
        self._fps_samples: deque[float] = deque(maxlen=window)
        self._inference_samples: deque[float] = deque(maxlen=window)
        self._last_tick = time.time()

    def record_fps(self, fps: float):
        self._fps_samples.append(fps)

    def record_inference(self, ms: float):
        self._inference_samples.append(ms)

    @property
    def avg_fps(self) -> float:
        return sum(self._fps_samples) / len(self._fps_samples) if self._fps_samples else 0.0

    @property
    def avg_inference_ms(self) -> float:
        return (
            sum(self._inference_samples) / len(self._inference_samples)
            if self._inference_samples else 0.0
        )
