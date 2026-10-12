"""Stage 4 — quality check (size, blur, pose).

The cheapest stage and the biggest accuracy win: most wrong matches come from tiny,
blurred or side-on faces. A failing face is skipped for this frame, not rejected.
"""
from __future__ import annotations

import math

import cv2
import numpy as np

from face_reg.src.datatypes.face import Face
from face_reg.src.datatypes.quality_result import QualityResult


def estimate_yaw_deg(landmarks: np.ndarray) -> float:
    """Rough yaw from 5 landmarks: how far the nose sits from the eye midpoint,
    relative to half the eye distance. 0 = frontal, ~90 = profile."""
    r_eye, l_eye, nose = landmarks[0], landmarks[1], landmarks[2]
    half_eye = np.linalg.norm(l_eye - r_eye) / 2.0
    if half_eye < 1e-3:
        return 90.0
    mid = (r_eye + l_eye) / 2.0
    # project nose offset onto the eye axis so head roll does not count as yaw
    axis = (l_eye - r_eye) / (2.0 * half_eye)
    offset = float(np.dot(nose - mid, axis)) / half_eye
    return math.degrees(math.asin(max(-1.0, min(1.0, offset))))


def blur_score(frame: np.ndarray, face: Face) -> float:
    """Laplacian variance of the face crop, normalized to 112 px wide so the value
    does not depend on how close the person stands."""
    x, y, w, h = face.bbox.astype(int)
    H, W = frame.shape[:2]
    x1, y1, x2, y2 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return 0.0
    crop = frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) if crop.ndim == 3 else crop
    gray = cv2.resize(gray, (112, max(8, int(112 * gray.shape[0] / gray.shape[1]))))
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def quality_check(frame: np.ndarray, face: Face, min_face_px: int = 80,
                  min_blur: float = 60.0, max_yaw_deg: float = 30.0) -> QualityResult:
    face_px = float(min(face.bbox[2], face.bbox[3]))
    yaw = estimate_yaw_deg(face.landmarks)
    blur = blur_score(frame, face)
    reason = None
    if face_px < min_face_px:
        reason = "FACE_TOO_SMALL"
    elif abs(yaw) > max_yaw_deg:
        reason = "POSE_TOO_WIDE"
    elif blur < min_blur:
        reason = "TOO_BLURRY"
    # 0-1 summary for enrollment output: each factor capped at 1
    score = (min(1.0, face_px / (2 * min_face_px)) * 0.3
             + min(1.0, blur / (3 * min_blur)) * 0.4
             + max(0.0, 1.0 - abs(yaw) / 90.0) * 0.3)
    return QualityResult(ok=reason is None, reason=reason, face_px=face_px,
                         blur=blur, yaw_deg=yaw, score=round(score, 2))
