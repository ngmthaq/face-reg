from __future__ import annotations

from pydantic import BaseModel, field_validator


class DisplayCfg(BaseModel):
    show: bool = False        # open the preview window (needs a monitor)
    window: str = "1280x720"  # max window size WxH; frames are shrunk to fit

    @field_validator("window")
    @classmethod
    def _check_window(cls, v: str) -> str:
        parse_window(v)
        return v

    @property
    def size(self) -> tuple[int, int]:
        return parse_window(self.window)


def parse_window(text: str) -> tuple[int, int]:
    """Parse "WxH" into (w, h). Raises ValueError unless both are positive ints."""
    try:
        w, h = (int(v) for v in text.lower().split("x"))
    except ValueError:
        raise ValueError("window must look like 1280x720") from None
    if w <= 0 or h <= 0:
        raise ValueError("window must look like 1280x720")
    return w, h
