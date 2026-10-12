from __future__ import annotations

from pydantic import BaseModel


class CameraCfg(BaseModel):
    # RTSP URL, a video file path, or an int for a USB/webcam index (0, 1, ...)
    source: str | int = 0
    process_fps: float = 5.0
    reconnect_max_s: float = 30.0
