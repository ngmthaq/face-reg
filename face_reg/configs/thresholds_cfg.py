from __future__ import annotations

from pydantic import BaseModel


class ThresholdsCfg(BaseModel):
    detect_score: float = 0.9
    nms: float = 0.3
    min_face_px: int = 80
    blur: float = 60.0         # Laplacian variance on the normalized face crop
    max_yaw_deg: float = 30.0
    live: float = 0.8
    match: float = 0.45
    margin: float = 0.05
    duplicate: float = 0.6     # enrollment: too similar to another person -> rejected
