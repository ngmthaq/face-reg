"""Tracked face."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from face_reg.datatypes.decision import Decision
from face_reg.datatypes.face import Face
from face_reg.datatypes.frame_result import FrameResult
from face_reg.datatypes.quality_result import QualityResult


@dataclass
class Track:
    track_id: int
    bbox: np.ndarray
    first_ts: float
    last_ts: float
    missed: int = 0
    window: list[FrameResult] = field(default_factory=list)
    decided: bool = False
    decision: Decision | None = None
    first_good_ts: float | None = None
    last_quality: QualityResult | None = None
    face: Face | None = None
