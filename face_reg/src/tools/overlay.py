"""Draws boxes and scores for --show."""
from __future__ import annotations

import os
import subprocess
import sys

import cv2
import numpy as np

COLORS = {
    "RECOGNIZED": (60, 200, 60),
    "UNKNOWN": (0, 200, 255),
    "SPOOF_SUSPECTED": (40, 40, 230),
    "UNDECIDED": (160, 160, 160),
    None: (220, 180, 40),
}


def fit_to(img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
    """Shrink (never enlarge) to fit inside max_w x max_h, keeping the aspect ratio."""
    h, w = img.shape[:2]
    s = min(max_w / w, max_h / h, 1.0)
    if s >= 1.0:
        return img
    return cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)


def draw_overlay(frame: np.ndarray, tracker, gallery=None, camera_state: str = "",
                 mirror: bool = False) -> np.ndarray:
    # Mirror flips the image first so text still reads normally; boxes are mirrored by hand.
    img = cv2.flip(frame, 1) if mirror else frame.copy()
    scale = max(1.0, img.shape[1] / 960)
    for tr in tracker.tracks.values():
        if tr.missed > 0:
            continue
        x, y, w, h = tr.bbox.astype(int)
        if mirror:
            x = img.shape[1] - x - w
        dtype = tr.decision.type if tr.decision else None
        color = COLORS.get(dtype, COLORS[None])
        cv2.rectangle(img, (x, y), (x + w, y + h), color, max(1, int(2 * scale)))
        lines = [f"#{tr.track_id}"]
        if tr.decision:
            label = dtype
            if dtype == "RECOGNIZED" and gallery is not None:
                label = gallery.name_of(tr.decision.person_id) or tr.decision.person_id
            lines.append(label)
        elif tr.last_quality is not None and not tr.last_quality.ok:
            lines.append(tr.last_quality.reason)
        if tr.window:
            f = tr.window[-1]
            lines.append(f"live {f.live:.2f} sim {f.sim:.2f}")
        fs, th, lh = 0.5 * scale, max(1, int(1.2 * scale)), int(20 * scale)
        top = max(0, y - lh * len(lines) - 4)
        for i, text in enumerate(lines):
            (tw, tht), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fs, th)
            ty = top + lh * (i + 1)
            cv2.rectangle(img, (x, ty - tht - 4), (x + tw + 6, ty + 4), (0, 0, 0), -1)
            cv2.putText(img, text, (x + 3, ty), cv2.FONT_HERSHEY_SIMPLEX, fs, color, th, cv2.LINE_AA)
    if camera_state:
        cv2.putText(img, camera_state, (10, int(24 * scale)), cv2.FONT_HERSHEY_SIMPLEX, 0.6 * scale,
                    (255, 255, 255), max(1, int(1.5 * scale)), cv2.LINE_AA)
    return img


_PROBE_CODE = ("import cv2; cv2.namedWindow('face_reg_probe'); cv2.waitKey(1); "
               "cv2.destroyAllWindows()")


def display_available() -> bool:
    """True when an OpenCV window can be opened. Never raises."""
    if sys.platform.startswith("linux") and not (
            os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    # Qt in opencv-python aborts the whole process when it cannot reach a display,
    # so the check runs in a child process.
    try:
        r = subprocess.run([sys.executable, "-c", _PROBE_CODE], capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return r.returncode == 0


class Preview:
    """The --show window. Resizable, sized to the first (shrunk) frame; drag the corner to change it."""

    def __init__(self, name: str = "face_reg", window: tuple[int, int] = (1280, 720),
                 mirror: bool = False):
        self.name = name
        self.mirror = mirror
        self.window = window
        self._ready = False

    def show(self, frame: np.ndarray, tracker, gallery, state: str) -> bool:
        """Draw one frame. Returns False when the user pressed q or Esc."""
        vis = fit_to(draw_overlay(frame, tracker, gallery, state, self.mirror), *self.window)
        if not self._ready:
            cv2.namedWindow(self.name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow(self.name, vis.shape[1], vis.shape[0])
            self._ready = True
        cv2.imshow(self.name, vis)
        return (cv2.waitKey(1) & 0xFF) not in (27, ord("q"))

    def close(self) -> None:
        cv2.destroyAllWindows()
