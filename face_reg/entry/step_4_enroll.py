"""Enroll logic: check photos and add face vectors to the gallery."""
from __future__ import annotations

import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from face_reg.configs import config as config_mod
from face_reg.stages.step_2_detect import YuNetDetector
from face_reg.stages.step_5_liveness import Liveness
from face_reg.stages.step_4_quality import quality_check
from face_reg.stages.step_6_recognize import Gallery, SFaceRecognizer

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ANGLES = ("front", "left", "right", "up", "down")      # file name = <angle>.jpg or <angle>_<n>.jpg
ANGLE_RE = re.compile(r"^(%s)(?:[_-]\d+)?$" % "|".join(ANGLES))
PERSON_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
FRONT_MAX_YAW = 15.0     # a "front" photo turned more than this gets a note
SIDE_MIN_YAW = 8.0       # a "left"/"right" photo turned less than this gets a note

log = logging.getLogger("face_reg.enroll")


@dataclass
class EnrollResult:
    count: int
    lines: list[str]


def angle_of(path: Path) -> str | None:
    m = ANGLE_RE.match(path.stem.lower())
    return m.group(1) if m else None


class Enroller:
    def __init__(self, cfg: config_mod.Config, use_liveness: bool = True):
        t = cfg.thresholds
        self.cfg = cfg
        self.det = YuNetDetector(cfg.path(cfg.models.detector), t.detect_score, t.nms, cfg.detect_width)
        self.rec = SFaceRecognizer(cfg.path(cfg.models.recognizer))
        models = [(cfg.path(m.path), m.scale) for m in cfg.models.liveness] if use_liveness else []
        self.live = Liveness(models, cfg.models.providers)
        self.gallery = Gallery.load(cfg.path(cfg.gallery), cfg.path(cfg.persons))

    def check_photo(self, path: Path, person_id: str) -> tuple[np.ndarray | None, str, float, float]:
        """Returns (vector or None, status/reason, quality score, yaw degrees)."""
        t = self.cfg.thresholds
        img = cv2.imread(str(path))
        if img is None:
            return None, "UNREADABLE", 0.0, 0.0
        faces = self.det.detect(img)
        if not faces:
            return None, "NO_FACE", 0.0, 0.0
        if len(faces) > 1:
            return None, "MULTIPLE_FACES", 0.0, 0.0
        face = faces[0]
        q = quality_check(img, face, t.min_face_px, t.blur, t.max_yaw_deg)
        if not q.ok:
            return None, q.reason, q.score, q.yaw_deg
        if self.live.enabled:
            live = self.live.score(img, face.bbox)
            if live < t.live:
                return None, f"NOT_LIVE (live={live:.2f})", q.score, q.yaw_deg
        vec = self.rec.embed(img, face)
        ids, best = self.gallery.per_person_best(vec)
        for pid, s in zip(ids, best):
            if pid != person_id and s >= t.duplicate:
                return None, f"DUPLICATE_OF_OTHER_PERSON ({pid}, sim={s:.2f})", q.score, q.yaw_deg
        return vec, "accepted", q.score, q.yaw_deg

    def enroll(self, person_id: str, name: str | None, photos: list[Path]) -> EnrollResult:
        """Checks every photo; if the front photo passes, replaces the person's vectors."""
        lines: list[str] = []
        accepted: list[np.ndarray] = []
        angles: list[str] = []
        order = {a: i for i, a in enumerate(ANGLES)}
        photos = sorted(photos, key=lambda f: (order.get(angle_of(f) or "", 99), f.name))
        for p in photos:
            angle = angle_of(p)
            if angle is None:
                lines.append(self._row(person_id, p, False, f"BAD_FILE_NAME (use {', '.join(ANGLES)}.jpg)"))
                continue
            vec, status, qs, yaw = self.check_photo(p, person_id)
            if vec is None:
                lines.append(self._row(person_id, p, False, status))
                continue
            note = ""
            if angle == "front" and abs(yaw) > FRONT_MAX_YAW:
                note = "  note: not very frontal, retake facing the camera"
            elif angle in ("left", "right") and abs(yaw) < SIDE_MIN_YAW:
                note = "  note: looks frontal, turn the head ~15-25 deg"
            lines.append(self._row(person_id, p, True, f"quality={qs:.2f} yaw={yaw:+.0f}{note}"))
            accepted.append(vec)
            angles.append(angle)
        missing = [a for a in ANGLES if a not in angles]
        if "front" not in angles:
            lines.append(f"{person_id:<10} NOT ENROLLED: a valid front.jpg is required"
                         + (" (gallery unchanged)" if person_id in self.gallery.persons else ""))
            return EnrollResult(0, lines)
        if missing:
            lines.append(f"{person_id:<10} missing angles: {', '.join(missing)} (optional, improves recognition)")
        old = self.gallery.persons.get(person_id, {})
        if old:
            self.gallery.remove(person_id)                      # re-enroll replaces old vectors
        self.gallery.add(person_id, name or old.get("name"), accepted, angles,
                         enrolled_at=old.get("enrolled_at"))
        return EnrollResult(len(accepted), lines)

    @staticmethod
    def _row(person_id: str, p: Path, ok: bool, text: str) -> str:
        return (f"{person_id:<10} {p.name:<16} {'accepted' if ok else 'rejected':<9} {text}")

    def save(self) -> None:
        self.gallery.save(self.cfg.path(self.cfg.gallery), self.cfg.path(self.cfg.persons))
        audit(self.cfg, "save", {"vectors": len(self.gallery.person_ids), "people": self.gallery.num_people})


def expand_photos(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for s in paths:
        p = Path(s)
        if p.is_dir():
            out += sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXT)
        elif any(ch in s for ch in "*?["):
            out += sorted(Path().glob(s))
        elif p.is_file():
            out.append(p)
        else:
            print(f"warning: {s} not found", file=sys.stderr)
    return out


def audit(cfg: config_mod.Config, action: str, info: dict) -> None:
    """Who enrolled/removed whom, for biometric-data accountability."""
    import getpass
    path = cfg.path(cfg.persons).with_name("audit.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"at": datetime.now().astimezone().isoformat(timespec="seconds"),
           "user": getpass.getuser(), "action": action, **info}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
