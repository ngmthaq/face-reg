"""Stage 1 — stream reader.

RTSP buffers frames; reading in the main loop causes growing lag. This thread reads
continuously and keeps only the newest frame, so processing always sees "now".
On disconnect it reconnects with backoff (1 s -> 30 s) and reports camera_offline.

Video files are paced at their own fps (so a recording behaves like a live camera)
and the reader stops at the end of the file.
"""
from __future__ import annotations

import logging
import os
import threading
import time

import cv2
import numpy as np

log = logging.getLogger(__name__)


class LatestFrameReader(threading.Thread):
    def __init__(self, source: str | int, reconnect_max_s: float = 30.0):
        super().__init__(daemon=True, name="frame-reader")
        self.source = source
        self.reconnect_max_s = reconnect_max_s
        self.is_file = isinstance(source, str) and os.path.isfile(source)
        self.lock = threading.Lock()
        self.stopped = False
        self.ended = False            # True when a video file has been fully read
        self.online = False
        self._frame: np.ndarray | None = None
        self._ts = 0.0
        self._seq = 0                 # increments on every new frame
        self._last_seq = -1
        self._backoff = 1.0
        self.frames_read = 0

    @property
    def state(self) -> str:
        if self.ended:
            return "ended"
        return "online" if self.online else "camera_offline"

    def _open(self) -> cv2.VideoCapture:
        if isinstance(self.source, int):
            return cv2.VideoCapture(self.source)
        if "://" in str(self.source):
            # Prefer TCP for RTSP: fewer smeared frames on lossy Wi-Fi/LAN.
            os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")
            return cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
        return cv2.VideoCapture(self.source)

    def run(self) -> None:
        while not self.stopped:
            cap = self._open()
            if not cap.isOpened():
                self._mark_offline()
                self._backoff_sleep()
                continue
            log.info("camera online: %s", redact_source(self.source))
            self.online = True
            self._backoff = 1.0
            file_period = 0.0
            if self.is_file:
                fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
                file_period = 1.0 / fps
            while cap.isOpened() and not self.stopped:
                t0 = time.monotonic()
                ok, frame = cap.read()
                if not ok:
                    break
                with self.lock:
                    self._frame, self._ts = frame, time.time()
                    self._seq += 1
                self.frames_read += 1
                if file_period:
                    time.sleep(max(0.0, file_period - (time.monotonic() - t0)))
            cap.release()
            if self.is_file:
                self.ended = True
                self.online = False
                log.info("video file ended")
                return
            self._mark_offline()
            self._backoff_sleep()

    def _mark_offline(self) -> None:
        if self.online:
            log.warning("camera_offline: %s", redact_source(self.source))
        self.online = False

    def _backoff_sleep(self) -> None:
        end = time.monotonic() + self._backoff
        while not self.stopped and time.monotonic() < end:
            time.sleep(0.1)
        self._backoff = min(self._backoff * 2, self.reconnect_max_s)

    def latest(self) -> tuple[np.ndarray | None, float]:
        """Newest frame not yet returned, else (None, 0)."""
        with self.lock:
            if self._frame is None or self._seq == self._last_seq:
                return None, 0.0
            self._last_seq = self._seq
            return self._frame, self._ts

    def stop(self) -> None:
        self.stopped = True


def redact_source(source: str | int) -> str:
    """Hide RTSP credentials in logs."""
    s = str(source)
    if "://" in s and "@" in s:
        scheme, rest = s.split("://", 1)
        return f"{scheme}://***@{rest.split('@', 1)[1]}"
    return s
