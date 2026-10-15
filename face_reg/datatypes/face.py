"""Detected face."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Face:
    bbox: np.ndarray        # x, y, w, h in full-resolution frame pixels (float32)
    landmarks: np.ndarray   # 5x2: right eye, left eye, nose tip, right mouth, left mouth
    score: float
    raw: np.ndarray         # the 15-value YuNet row (full-res), used by SFace alignCrop

    @property
    def xyxy(self) -> tuple[float, float, float, float]:
        x, y, w, h = self.bbox
        return float(x), float(y), float(x + w), float(y + h)
