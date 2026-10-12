"""Stage 2 — face detection with YuNet (OpenCV FaceDetectorYN).

Runs on a frame downscaled to `detect_width`, then scales boxes and landmarks back to
full resolution so liveness and recognition get full-detail crops.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from face_reg.src.datatypes.face import Face


class YuNetDetector:
    name = "yunet"

    def __init__(self, model_path: str | Path, score_threshold: float = 0.9,
                 nms_threshold: float = 0.3, detect_width: int = 640, top_k: int = 50):
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"YuNet model not found: {model_path} (run: bash scripts/download_models.sh)")
        self.name = model_path.stem.replace("face_detection_", "")
        self.detect_width = detect_width
        self.net = cv2.FaceDetectorYN.create(str(model_path), "", (320, 320),
                                             score_threshold, nms_threshold, top_k)
        self._size: tuple[int, int] | None = None

    def detect(self, frame: np.ndarray) -> list[Face]:
        h, w = frame.shape[:2]
        scale = min(1.0, self.detect_width / float(w))
        small = frame if scale == 1.0 else cv2.resize(frame, (int(round(w * scale)), int(round(h * scale))))
        sh, sw = small.shape[:2]
        if self._size != (sw, sh):
            self.net.setInputSize((sw, sh))
            self._size = (sw, sh)
        _, rows = self.net.detect(small)
        faces: list[Face] = []
        if rows is None:
            return faces
        for r in rows:
            r = r.astype(np.float32).copy()
            r[:14] /= scale                           # bbox + 5 landmarks back to full-res
            faces.append(Face(bbox=r[0:4].copy(), landmarks=r[4:14].reshape(5, 2).copy(),
                              score=float(r[14]), raw=r))
        return faces
