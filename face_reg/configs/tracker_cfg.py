from __future__ import annotations

from pydantic import BaseModel


class TrackerCfg(BaseModel):
    iou: float = 0.3
    max_missed: int = 10
