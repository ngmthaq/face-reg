from __future__ import annotations

from pydantic import BaseModel, field_validator


class EnrollCfg(BaseModel):
    scan_interval_s: float = 300     # how often photos_dir is scanned (seconds)
    photos_dir: str = "photos"       # photos/<person_id>/<angle>.jpg
    skip_liveness: bool = False      # true: no liveness check on photos (e.g. scanned ID photos)

    @field_validator("scan_interval_s")
    @classmethod
    def _check_interval(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("scan_interval_s must be greater than 0")
        return v
