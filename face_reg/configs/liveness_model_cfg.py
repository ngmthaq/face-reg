from __future__ import annotations

from pydantic import BaseModel


class LivenessModelCfg(BaseModel):
    path: str
    scale: float  # crop scale around the face bbox the model was trained with (2.7, 4.0 ...)
