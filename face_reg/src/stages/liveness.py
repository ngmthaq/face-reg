"""Stage 5 — liveness with Silent-Face-Anti-Spoofing (MiniFASNet) exported to ONNX.

Matches the Minivision repo's preprocessing exactly:
  * crop around the face bbox, enlarged by the model's scale (2.7, 4.0), shifted to stay
    inside the frame (CropImage._get_new_box), resized to 80x80;
  * BGR channel order, float32, NOT divided by 255, CHW;
  * softmax over 3 classes, class 1 = real face; scores of all models are averaged.

RGB-only liveness stops printed photos and phone screens; it is weak against
high-quality masks or replay on large screens.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

ORT_THREADS = 2


def crop_box(src_w: int, src_h: int, bbox: np.ndarray, scale: float) -> tuple[int, int, int, int]:
    """Port of CropImage._get_new_box from the Minivision repo."""
    x, y, box_w, box_h = [float(v) for v in bbox]
    box_w, box_h = max(box_w, 1.0), max(box_h, 1.0)
    scale = min((src_h - 1) / box_h, min((src_w - 1) / box_w, scale))
    new_w, new_h = box_w * scale, box_h * scale
    cx, cy = box_w / 2 + x, box_h / 2 + y
    l, t = cx - new_w / 2, cy - new_h / 2
    r, b = cx + new_w / 2, cy + new_h / 2
    if l < 0:
        r -= l
        l = 0
    if t < 0:
        b -= t
        t = 0
    if r > src_w - 1:
        l -= r - src_w + 1
        r = src_w - 1
    if b > src_h - 1:
        t -= b - src_h + 1
        b = src_h - 1
    return int(l), int(t), int(r), int(b)


class _OnnxModel:
    def __init__(self, path: Path, scale: float, providers: list[str]):
        import onnxruntime as ort
        avail = ort.get_available_providers()
        use = [p for p in providers if p in avail] or ["CPUExecutionProvider"]
        so = ort.SessionOptions()
        so.intra_op_num_threads = ORT_THREADS
        self.sess = ort.InferenceSession(str(path), sess_options=so, providers=use)
        self.input = self.sess.get_inputs()[0].name
        shape = self.sess.get_inputs()[0].shape   # [1, 3, H, W]
        self.h, self.w = int(shape[2]), int(shape[3])
        self.scale = scale
        self.name = path.stem

    def prepare(self, frame: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        H, W = frame.shape[:2]
        l, t, r, b = crop_box(W, H, bbox, self.scale)
        patch = cv2.resize(frame[t:b + 1, l:r + 1], (self.w, self.h))
        return patch.transpose(2, 0, 1).astype(np.float32)

    def real_prob(self, batch: np.ndarray) -> np.ndarray:
        logits = self.sess.run(None, {self.input: batch})[0]
        e = np.exp(logits - logits.max(axis=1, keepdims=True))
        return (e / e.sum(axis=1, keepdims=True))[:, 1]


class Liveness:
    def __init__(self, models: list[tuple[str | Path, float]], providers: list[str]):
        self.models: list[_OnnxModel] = []
        for path, scale in models:
            path = Path(path)
            if not path.is_file():
                raise FileNotFoundError(
                    f"Liveness model not found: {path}. Export it with face_reg/src/tools/export_liveness_onnx.py, "
                    "or set models.liveness: [] to run without liveness (testing only).")
            self.models.append(_OnnxModel(path, scale, providers))
        self.name = "+".join(m.name for m in self.models) or "disabled"

    @property
    def enabled(self) -> bool:
        return bool(self.models)

    def score(self, frame: np.ndarray, bbox: np.ndarray) -> float:
        """live_score 0-1 (1.0 when liveness is disabled)."""
        if not self.models:
            return 1.0
        probs = [float(m.real_prob(m.prepare(frame, bbox)[None])[0]) for m in self.models]
        return float(np.mean(probs))
