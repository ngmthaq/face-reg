"""Where events go. Each sink has one method, emit(event, frame).

A network sink (MQTT / HTTP) can be added after the MVP without touching the pipeline:
the event JSON is already the shape a server would receive.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from face_reg.configs.config import Config
from face_reg.datatypes.event import Event

log = logging.getLogger("face_reg.events")

SNAPSHOT_JPEG_QUALITY = 85
FACE_CROP_JPEG_QUALITY = 90
FACE_CROP_PAD = 0.25


class Sink(Protocol):
    def emit(self, event: Event, frame: np.ndarray | None) -> None: ...


class SnapshotSink:
    """Saves the frame + face crop for the event only, never every frame.
    Must run before JsonlSink so the event carries the snapshot path."""

    def __init__(self, data_dir: Path, min_free_gb: float):
        self.data_dir = data_dir
        self.min_free_gb = min_free_gb

    def emit(self, event: Event, frame: np.ndarray | None) -> None:
        if frame is None:
            return
        if free_gb(self.data_dir) < self.min_free_gb:
            log.warning("free disk < %.1f GB, snapshot skipped", self.min_free_gb)
            event.snapshot = None
            return
        day = event.occurred_at[:10]
        rel = Path("snapshots") / day / f"{event.event_id}.jpg"
        out = self.data_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out), frame, [cv2.IMWRITE_JPEG_QUALITY, SNAPSHOT_JPEG_QUALITY])
        bbox = event.bbox
        if bbox:
            x, y, w, h = [int(v) for v in bbox]
            H, W = frame.shape[:2]
            pad = int(FACE_CROP_PAD * max(w, h))
            crop = frame[max(0, y - pad):min(H, y + h + pad), max(0, x - pad):min(W, x + w + pad)]
            if crop.size:
                cv2.imwrite(str(out.with_name(out.stem + "_face.jpg")), crop, [cv2.IMWRITE_JPEG_QUALITY, FACE_CROP_JPEG_QUALITY])
        event.snapshot = rel.as_posix()


class JsonlSink:
    """Appends one JSON line per event to data/events/<date>.jsonl."""

    def __init__(self, data_dir: Path):
        self.dir = data_dir / "events"
        self.dir.mkdir(parents=True, exist_ok=True)

    def emit(self, event: Event, frame: np.ndarray | None) -> None:
        path = self.dir / f"{event.occurred_at[:10]}.jsonl"
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")


class ConsoleSink:
    """One-line summary (shows up in journalctl)."""

    def emit(self, event: Event, frame: np.ndarray | None) -> None:
        s = event.scores
        who = f"{event.person_id} ({event.person_name or '-'})" if event.person_id else "-"
        log.info("EVENT %-15s track=%-4s person=%s sim=%.2f/%.2f live=%.2f frames=%d",
                 event.type, event.track_id, who, s["similarity"], s["second_best"],
                 s["live"], s["frames_voted"])


SINK_FACTORIES = {      # snapshot first: it fills event.snapshot
    "snapshot": lambda cfg, data_dir: SnapshotSink(data_dir, cfg.min_free_gb),
    "jsonl": lambda cfg, data_dir: JsonlSink(data_dir),
    "console": lambda cfg, data_dir: ConsoleSink(),
}


def build_sinks(cfg: Config) -> list[Sink]:
    data_dir = cfg.path(cfg.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    return [factory(cfg, data_dir) for name, factory in SINK_FACTORIES.items() if name in cfg.sinks]


def cleanup_old_data(data_dir: Path, retention_days: int) -> int:
    """Delete event logs and snapshot folders older than retention_days. Returns count removed."""
    cutoff = date.today() - timedelta(days=retention_days)
    removed = 0
    for f in (data_dir / "events").glob("*.jsonl"):
        d = _parse_day(f.stem)
        if d and d < cutoff:
            f.unlink(missing_ok=True)
            removed += 1
    snaps = data_dir / "snapshots"
    if snaps.is_dir():
        for d_dir in snaps.iterdir():
            d = _parse_day(d_dir.name)
            if d_dir.is_dir() and d and d < cutoff:
                shutil.rmtree(d_dir, ignore_errors=True)
                removed += 1
    return removed


def _parse_day(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def free_gb(path: Path) -> float:
    try:
        return shutil.disk_usage(path).free / 1e9
    except OSError:
        return float("inf")


def next_event_seq(data_dir: Path, day: str) -> int:
    """Continue the per-day event counter after a restart."""
    path = data_dir / "events" / f"{day}.jsonl"
    if not path.is_file():
        return 0
    with open(path, "rb") as f:
        return sum(1 for _ in f)


__all__ = ["Sink", "build_sinks", "cleanup_old_data", "free_gb", "next_event_seq"]
