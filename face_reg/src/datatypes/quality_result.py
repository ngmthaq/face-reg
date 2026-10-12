"""Quality check outcome."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityResult:
    ok: bool
    reason: str | None      # FACE_TOO_SMALL, TOO_BLURRY, POSE_TOO_WIDE
    face_px: float
    blur: float
    yaw_deg: float
    score: float            # 0-1, only used to report enrollment photo quality
