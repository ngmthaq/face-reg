"""Stage 6 — recognition: SFace (alignCrop + feature) and a NumPy gallery.

The gallery is a matrix of all enrolled vectors (L2-normalized), so a match is one
matrix-vector product. top2() returns the best person and the best *other* person,
which the decision's margin rule needs.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import IO, Callable

import cv2
import numpy as np

from face_reg.src.datatypes.face import Face

EMBED_DIM = 128


class SFaceRecognizer:
    def __init__(self, model_path: str | Path):
        model_path = Path(model_path)
        if not model_path.is_file():
            raise FileNotFoundError(f"SFace model not found: {model_path} (run: bash scripts/download_models.sh)")
        self.name = model_path.stem.replace("face_recognition_", "")
        self.net = cv2.FaceRecognizerSF.create(str(model_path), "")

    def embed(self, frame: np.ndarray, face: Face) -> np.ndarray:
        aligned = self.net.alignCrop(frame, face.raw)      # 112x112 aligned by the 5 landmarks
        vec = self.net.feature(aligned).reshape(-1).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-12)


class Gallery:
    """vectors: N x EMBED_DIM float32 (L2-normalized), person_ids: N strings,
    persons: person_id -> {name, enrolled_at, vectors}."""

    def __init__(self, vectors: np.ndarray | None = None, person_ids: list[str] | None = None,
                 persons: dict | None = None):
        self.vectors = np.zeros((0, EMBED_DIM), np.float32) if vectors is None else vectors.astype(np.float32)
        self.person_ids = list(person_ids or [])
        self.persons: dict[str, dict] = dict(persons or {})
        self._reindex()

    def _reindex(self) -> None:
        self._unique = sorted(set(self.person_ids))
        idx = {p: i for i, p in enumerate(self._unique)}
        self._pidx = np.array([idx[p] for p in self.person_ids], dtype=np.int64)

    # ---- load / save -------------------------------------------------------------
    @classmethod
    def load(cls, npz_path: str | Path, persons_path: str | Path | None = None) -> "Gallery":
        npz_path = Path(npz_path)
        persons_path = Path(persons_path) if persons_path else npz_path.with_name("persons.json")
        if not npz_path.is_file():
            return cls(persons=_read_json(persons_path))
        with np.load(npz_path, allow_pickle=False) as z:
            vectors, ids = z["vectors"], [str(s) for s in z["person_ids"]]
        return cls(vectors, ids, _read_json(persons_path))

    def save(self, npz_path: str | Path, persons_path: str | Path | None = None) -> None:
        """Atomic: write a temp file in the same folder, then rename over the old one."""
        npz_path = Path(npz_path)
        persons_path = Path(persons_path) if persons_path else npz_path.with_name("persons.json")
        npz_path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(npz_path, "wb", lambda fh: np.savez(
            fh, vectors=self.vectors.astype(np.float32), person_ids=np.array(self.person_ids, dtype=str)))
        _atomic_write(persons_path, "w", lambda fh: json.dump(self.persons, fh, ensure_ascii=False, indent=2))

    # ---- edit ----------------------------------------------------------------------
    def add(self, person_id: str, name: str | None, vectors: list[np.ndarray],
            angles: list[str] | None = None, enrolled_at: str | None = None) -> None:
        if not vectors:
            return
        self.vectors = np.vstack([self.vectors, np.stack(vectors).astype(np.float32)])
        self.person_ids += [person_id] * len(vectors)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        p = self.persons.setdefault(person_id, {})
        if name:
            p["name"] = name
        p["enrolled_at"] = enrolled_at or p.get("enrolled_at") or now
        p["updated_at"] = now
        p["vectors"] = self.person_ids.count(person_id)
        if angles:
            p["angles"] = sorted(set(p.get("angles", [])) | set(angles))
        self._reindex()

    def remove(self, person_id: str) -> int:
        keep = [i for i, p in enumerate(self.person_ids) if p != person_id]
        n = len(self.person_ids) - len(keep)
        self.vectors = self.vectors[keep] if keep else np.zeros((0, EMBED_DIM), np.float32)
        self.person_ids = [self.person_ids[i] for i in keep]
        self.persons.pop(person_id, None)
        self._reindex()
        return n

    # ---- query ---------------------------------------------------------------------
    @property
    def num_people(self) -> int:
        return len(self._unique)

    def name_of(self, person_id: str | None) -> str | None:
        return self.persons.get(person_id, {}).get("name") if person_id else None

    def per_person_best(self, vec: np.ndarray) -> tuple[list[str], np.ndarray]:
        if not self.person_ids:
            return [], np.zeros(0, np.float32)
        sims = self.vectors @ vec
        best = np.full(len(self._unique), -1.0, np.float32)
        np.maximum.at(best, self._pidx, sims)
        return self._unique, best

    def top2(self, vec: np.ndarray) -> tuple[str | None, float, float]:
        ids, best = self.per_person_best(vec)
        if len(ids) == 0:
            return None, 0.0, 0.0
        order = np.argsort(-best)
        s1 = float(best[order[0]])
        s2 = float(best[order[1]]) if len(order) > 1 else 0.0
        return ids[order[0]], s1, s2


def _atomic_write(path: Path, mode: str, writer: Callable[[IO], None]) -> None:
    """Write to a temp file in the same folder, chmod 0600, then rename over `path`."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, mode, **({"encoding": "utf-8"} if "b" not in mode else {})) as fh:
        writer(fh)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
