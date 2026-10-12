"""Record the gate camera into mp4 parts, to collect footage for threshold tuning.

    python -m face_reg.src.tools.record [--config cfg.yaml] [--source URL|FILE|INDEX]
                                             [--fps 15] [--part-min 10] [-v]

Files go to <data_dir>/recordings/<YYYY-MM-DD>/<HH-MM-SS>.mp4 (local time of the part start).
A new part starts every --part-min minutes and after a camera reconnect. The tool stops with
exit code 1 when free disk < min_free_gb, and with 0 on Ctrl+C or when a video file ends.
Recordings contain faces (biometric data): never commit or share them.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Protocol

import cv2
import numpy as np

from face_reg.src.configs import config as config_mod
from face_reg.src.tools.logs import setup_logging
from face_reg.src.tools.sinks import free_gb
from face_reg.src.stages.stream import LatestFrameReader, redact_source

log = logging.getLogger("face_reg.record")

DISK_CHECK_EVERY_S = 10.0


class Writer(Protocol):
    def write(self, frame: np.ndarray) -> None: ...
    def release(self) -> None: ...


WriterFactory = Callable[[Path, float, tuple[int, int]], Writer]


def part_path(root: Path, start: datetime) -> Path:
    return root / start.strftime("%Y-%m-%d") / start.strftime("%H-%M-%S.mp4")


def disk_ok(path: Path, min_free_gb: float) -> bool:
    return free_gb(path) >= min_free_gb


def cv2_writer_factory(path: Path, fps: float, size: tuple[int, int]) -> Writer:
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not w.isOpened():
        raise RuntimeError(f"cannot open video writer: {path} (mp4v codec missing in this OpenCV build?)")
    return w


def _nearest_existing(path: Path) -> Path:
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


class Recorder:
    def __init__(self, reader: LatestFrameReader, root: Path, fps: float, part_min: float,
                 min_free_gb: float, writer_factory: WriterFactory = cv2_writer_factory,
                 now: Callable[[], datetime] = datetime.now):
        self.reader = reader
        self.root = root
        self.fps = fps
        self.part_len = timedelta(minutes=part_min)
        self.min_free_gb = min_free_gb
        self.writer_factory = writer_factory
        self.now = now
        self._writer: Writer | None = None
        self._part_file: Path | None = None
        self._part_start: datetime | None = None
        self._last_frame: np.ndarray | None = None
        self._last_disk_check = float("-inf")

    def run(self) -> int:
        period = 1.0 / self.fps
        next_tick = time.monotonic()
        try:
            while True:
                code = self._step()
                if code is not None:
                    return code
                next_tick += period
                time.sleep(max(0.0, next_tick - time.monotonic()))
        except KeyboardInterrupt:
            return 0
        finally:
            self._close_part()
            self.reader.stop()

    def _step(self) -> int | None:
        """One tick. Returns an exit code when the recorder must stop."""
        if self.reader.ended:
            return 0
        if not self.reader.online:
            self._close_part()
            self._last_frame = None
            return None
        frame, _ = self.reader.latest()
        if frame is not None:
            self._last_frame = frame
        if self._last_frame is None:
            return None
        if self._writer is not None and self.now() - self._part_start >= self.part_len:
            self._close_part()
        if self._writer is None or time.monotonic() - self._last_disk_check >= DISK_CHECK_EVERY_S:
            if not self._disk_ok():
                log.warning("free disk < %.1f GB, recording stopped", self.min_free_gb)
                return 1
        if self._writer is None:
            self._open_part(self._last_frame)
        self._writer.write(self._last_frame)
        return None

    def _disk_ok(self) -> bool:
        self._last_disk_check = time.monotonic()
        return disk_ok(_nearest_existing(self.root), self.min_free_gb)

    def _open_part(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        self._part_start = self.now()
        self._part_file = part_path(self.root, self._part_start)
        self._part_file.parent.mkdir(parents=True, exist_ok=True)
        self._writer = self.writer_factory(self._part_file, self.fps, (w, h))
        log.info("part opened: %s", self._part_file)

    def _close_part(self) -> None:
        if self._writer is None:
            return
        self._writer.release()
        log.info("part closed: %s", self._part_file)
        self._writer = None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m face_reg.src.tools.record",
                                 description="Record the gate camera into mp4 parts.")
    ap.add_argument("--config", default=None, help="default: config.yaml")
    ap.add_argument("--source", help="override camera.source (RTSP URL, video file, or webcam index)")
    ap.add_argument("--fps", type=float, default=15.0, help="recording fps (default 15)")
    ap.add_argument("--part-min", type=float, default=10.0, help="minutes per file (default 10)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    if args.fps <= 0 or args.part_min <= 0:
        ap.error("--fps and --part-min must be greater than 0")

    setup_logging(args.verbose)
    cfg = config_mod.load(args.config or config_mod.DEFAULT_CONFIG)
    if args.source is not None:
        cfg.camera.source = int(args.source) if args.source.isdigit() else args.source
    root = cfg.path(cfg.data_dir) / "recordings"
    log.info("recording %s to %s", redact_source(cfg.camera.source), root)
    reader = LatestFrameReader(cfg.camera.source, cfg.camera.reconnect_max_s)
    reader.start()
    return Recorder(reader, root, args.fps, args.part_min, cfg.min_free_gb).run()


if __name__ == "__main__":
    sys.exit(main())
