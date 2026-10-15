"""Per-frame recognition result."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FrameResult:
    ts: float
    live: float             # 1.0 when liveness is disabled
    person_id: str | None   # top-1 person
    sim: float              # top-1 similarity
    sim2: float             # best similarity of a *different* person
