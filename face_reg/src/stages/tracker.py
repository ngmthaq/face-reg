"""Stage 3 — simple IoU tracker.

Lets the system decide once per person instead of once per frame, and lets votes
accumulate across frames. Greedy IoU matching is enough at one gate with a few people.
"""
from __future__ import annotations

import numpy as np

from face_reg.src.datatypes.face import Face
from face_reg.src.datatypes.track import Track


def iou(a: np.ndarray, b: np.ndarray) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax1 + aw, bx1 + bw), min(ay1 + ah, by1 + bh)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return float(inter / union) if union > 0 else 0.0


class IoUTracker:
    def __init__(self, iou: float = 0.3, max_missed: int = 10):
        self.iou_t = iou
        self.max_missed = max_missed
        self.tracks: dict[int, Track] = {}
        self._next_id = 1
        self.removed: list[Track] = []   # tracks dropped on the last update()

    def update(self, faces: list[Face], ts: float) -> list[tuple[Face, Track]]:
        self.removed = []
        pairs = []
        for f_i, face in enumerate(faces):
            for t_id, tr in self.tracks.items():
                v = iou(face.bbox, tr.bbox)
                if v >= self.iou_t:
                    pairs.append((v, f_i, t_id))
        pairs.sort(reverse=True)
        used_f: set[int] = set()
        used_t: set[int] = set()
        out: list[tuple[Face, Track]] = []
        for _, f_i, t_id in pairs:
            if f_i in used_f or t_id in used_t:
                continue
            used_f.add(f_i)
            used_t.add(t_id)
            tr = self.tracks[t_id]
            tr.bbox, tr.last_ts, tr.missed, tr.face = faces[f_i].bbox, ts, 0, faces[f_i]
            out.append((faces[f_i], tr))
        for f_i, face in enumerate(faces):
            if f_i in used_f:
                continue
            tr = Track(track_id=self._next_id, bbox=face.bbox, first_ts=ts, last_ts=ts, face=face)
            self._next_id += 1
            self.tracks[tr.track_id] = tr
            used_t.add(tr.track_id)
            out.append((face, tr))
        for t_id in list(self.tracks):
            if t_id in used_t:
                continue
            tr = self.tracks[t_id]
            tr.missed += 1
            tr.face = None
            if tr.missed > self.max_missed:
                self.removed.append(self.tracks.pop(t_id))
        out.sort(key=lambda p: p[1].track_id)
        return out
