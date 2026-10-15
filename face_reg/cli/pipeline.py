"""Wires the stages: stream -> detect -> track -> quality -> liveness -> recognize -> decide -> sinks."""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from datetime import datetime

import numpy as np

from face_reg.cli.photo_scanner import PhotoScanner
from face_reg.configs.config import Config
from face_reg.datatypes.decision import Decision
from face_reg.datatypes.event import Event
from face_reg.datatypes.face import Face
from face_reg.datatypes.frame_result import FrameResult
from face_reg.datatypes.track import Track
from face_reg.tools.sinks import Sink, build_sinks, cleanup_old_data, next_event_seq
from face_reg.stages.decide import DecisionRules
from face_reg.stages.detect import YuNetDetector
from face_reg.stages.liveness import Liveness
from face_reg.stages.quality import quality_check
from face_reg.stages.recognize import Gallery, SFaceRecognizer
from face_reg.stages.stream import LatestFrameReader, redact_source
from face_reg.stages.tracker import IoUTracker

log = logging.getLogger("face_reg")

CLEANUP_EVERY_S = 3600
DISPLAY_RETRY_S = 30
GALLERY_CHECK_S = 5
TIMER_MAX_SAMPLES = 1000
TIMER_KEEP = 500


class Pipeline:
    def __init__(self, cfg: Config, sinks: list[Sink] | None = None):
        self.cfg = cfg
        t = cfg.thresholds
        self.det = YuNetDetector(cfg.path(cfg.models.detector), t.detect_score, t.nms, cfg.detect_width)
        self.live = Liveness([(cfg.path(m.path), m.scale) for m in cfg.models.liveness], cfg.models.providers)
        if not self.live.enabled:
            log.warning("LIVENESS DISABLED (models.liveness is empty) — photos will be accepted. Testing only.")
        self.rec = SFaceRecognizer(cfg.path(cfg.models.recognizer))
        self._gallery_sig = self._gallery_signature()
        self.gallery = Gallery.load(cfg.path(cfg.gallery), cfg.path(cfg.persons))
        log.info("gallery: %d vectors / %d people", len(self.gallery.person_ids), self.gallery.num_people)
        self.tracker = IoUTracker(cfg.tracker.iou, cfg.tracker.max_missed)
        self.rules = DecisionRules(t.live, t.match, t.margin, cfg.decision.window, cfg.decision.min_votes)
        self.sinks = build_sinks(cfg) if sinks is None else sinks
        self.data_dir = cfg.path(cfg.data_dir)
        self._last_emit: dict[str, float] = {}      # person_id -> ts (cooldown)
        self._seq_day = ""
        self._seq = 0
        # stats for heartbeat / eval
        self.stage_ms: dict[str, list[float]] = defaultdict(list)
        self.frames_processed = 0
        self.faces_seen = 0
        self.events: list[Event] = []
        self.undecided: list[dict] = []
        self._next_hb = 0.0
        self._next_cleanup = 0.0
        self._next_gallery_check = 0.0
        self._hb_frames, self._hb_faces, self._hb_t = 0, 0, 0.0

    # ------------------------------------------------------------------ one frame
    def process(self, frame: np.ndarray, ts: float) -> list[Event]:
        """Run every stage on one frame. `ts` is wall-clock time."""
        out: list[Event] = []
        self.frames_processed += 1
        with self._timed("detect"):
            faces = self.det.detect(frame)
        self.faces_seen += len(faces)
        with self._timed("track"):
            pairs = self.tracker.update(faces, ts)
        self._handle_lost_tracks()
        for face, track in pairs:
            if track.decided or not self._evaluate_face(frame, face, track, ts):
                continue
            decision = self._decide(track, ts)
            if decision is None or self._in_cooldown(decision, ts):
                continue
            out.append(self._emit(decision, track, face, frame, ts))
        return out

    def _handle_lost_tracks(self) -> None:
        for tr in self.tracker.removed:
            if not tr.decided and tr.window:
                self.flush_undecided(tr, "track_lost")

    def _evaluate_face(self, frame: np.ndarray, face: Face, track: Track, ts: float) -> bool:
        """Run quality, liveness and recognition; append the result to the track window.
        Returns False when the face was skipped for quality."""
        th = self.cfg.thresholds
        with self._timed("quality"):
            q = quality_check(frame, face, th.min_face_px, th.blur, th.max_yaw_deg)
        track.last_quality = q
        if not q.ok:
            return False                                   # skipped, not rejected
        if track.first_good_ts is None:
            track.first_good_ts = ts
        with self._timed("liveness"):
            live = self.live.score(frame, face.bbox)
        with self._timed("recognize"):
            vec = self.rec.embed(frame, face)
            pid, sim, sim2 = self.gallery.top2(vec)
        track.window.append(FrameResult(ts, live, pid, sim, sim2))
        return True

    def _decide(self, track: Track, ts: float) -> Decision | None:
        """Apply the decision rules; mark the track decided (also on timeout)."""
        d = self.rules.decide(track)
        if d is None:
            if ts - track.first_good_ts > self.cfg.decision.timeout_s:
                track.decided = True
                track.decision = Decision("UNDECIDED")
                self.flush_undecided(track, "timeout")
            return None
        track.decided = True
        track.decision = d
        return d

    def _in_cooldown(self, d: Decision, ts: float) -> bool:
        """True when a RECOGNIZED person was emitted recently; otherwise records this emit."""
        if d.type != "RECOGNIZED":
            return False
        last = self._last_emit.get(d.person_id)
        if last is not None and ts - last < self.cfg.decision.cooldown_s:
            log.debug("cooldown: %s re-seen after %.1fs, not re-emitted", d.person_id, ts - last)
            return True
        self._last_emit[d.person_id] = ts
        return False

    def _emit(self, d: Decision, track: Track, face: Face, frame: np.ndarray, ts: float) -> Event:
        event = self._make_event(d, track, face, ts)
        with self._timed("sinks"):
            for s in self.sinks:
                try:
                    s.emit(event, frame)
                except Exception:
                    log.exception("sink %s failed", type(s).__name__)
        self.events.append(event)
        return event

    # ------------------------------------------------------------------ live loop
    def run(self, show: bool = False, window: tuple[int, int] = (1280, 720),
            mirror: bool = False) -> None:
        """show: open a preview window; window: its max (width, height), frames are shrunk to fit.
        mirror: flip the preview left-right only; processing and saved images stay unmirrored."""
        cam = self.cfg.camera
        reader = LatestFrameReader(cam.source, cam.reconnect_max_s)
        reader.start()
        period = 1.0 / max(0.1, cam.process_fps)
        self._next_hb = time.monotonic() + self.cfg.heartbeat_s
        self._next_cleanup = 0.0
        self._hb_frames, self._hb_faces, self._hb_t = 0, 0, time.monotonic()
        preview = None
        next_display_try = 0.0
        log.info("running device=%s source=%s fps=%.1f", self.cfg.device_id,
                 redact_source(cam.source), cam.process_fps)
        scanner = PhotoScanner(self.cfg)
        scanner.start()
        try:
            while True:
                t0 = time.monotonic()
                self._housekeeping(t0, reader)
                if show and preview is None and t0 >= next_display_try:
                    preview = self._try_open_preview(window, mirror)
                    next_display_try = t0 + DISPLAY_RETRY_S
                frame, ts = reader.latest()
                if frame is None:
                    if reader.ended:
                        break
                    time.sleep(0.02 if reader.online else 0.2)
                    continue
                self.process(frame, ts)
                if preview and not preview.show(frame, self.tracker, self.gallery, reader.state):
                    break
                time.sleep(max(0.0, period - (time.monotonic() - t0)))
        except KeyboardInterrupt:
            log.info("stopped by user")
        finally:
            scanner.stop()
            reader.stop()
            if preview:
                preview.close()

    def _try_open_preview(self, window: tuple[int, int], mirror: bool):
        """Return a Preview when a display is reachable, else None (warn; the caller retries later)."""
        from face_reg.tools.overlay import Preview, display_available
        if not display_available():
            log.warning("no display reachable; running without preview, retry in %d s", DISPLAY_RETRY_S)
            return None
        log.info("display reachable; preview window enabled")
        return Preview(window=window, mirror=mirror)

    def _housekeeping(self, now: float, reader: LatestFrameReader) -> None:
        """Hourly retention cleanup, gallery change check and periodic heartbeat log."""
        if now >= self._next_gallery_check:
            self.reload_gallery_if_changed()
            self._next_gallery_check = now + GALLERY_CHECK_S
        if now >= self._next_cleanup:
            n = cleanup_old_data(self.data_dir, self.cfg.retention_days)
            if n:
                log.info("retention cleanup removed %d old log/snapshot items", n)
            self._next_cleanup = now + CLEANUP_EVERY_S
        if now >= self._next_hb:
            dt = now - self._hb_t
            log.info("HEARTBEAT fps=%.1f faces=%d camera=%s tracks=%d events=%d %s",
                     (self.frames_processed - self._hb_frames) / dt, self.faces_seen - self._hb_faces,
                     reader.state, len(self.tracker.tracks), len(self.events), self.timing_summary())
            self._hb_frames, self._hb_faces, self._hb_t = self.frames_processed, self.faces_seen, now
            self.stage_ms.clear()
            self._next_hb = now + self.cfg.heartbeat_s

    def _gallery_signature(self) -> tuple[int | None, int | None]:
        """Modification times (ns) of gallery.npz and persons.json; None when a file is missing."""
        sig = []
        for rel in (self.cfg.gallery, self.cfg.persons):
            try:
                sig.append(os.stat(self.cfg.path(rel)).st_mtime_ns)
            except FileNotFoundError:
                sig.append(None)
        return sig[0], sig[1]

    def reload_gallery_if_changed(self) -> bool:
        """Swap in a fresh gallery when its files changed. Returns True when swapped.
        A missing or broken file keeps the old gallery and is logged once per change."""
        sig = self._gallery_signature()
        if sig == self._gallery_sig:
            return False
        self._gallery_sig = sig                            # remember first: a bad file is reported once
        if sig[0] is None:
            log.error("gallery reload failed, keeping old gallery: %s not found", self.cfg.gallery)
            return False
        try:
            new = Gallery.load(self.cfg.path(self.cfg.gallery), self.cfg.path(self.cfg.persons))
        except Exception as e:
            log.error("gallery reload failed, keeping old gallery: %s", e)
            return False
        self.gallery = new
        log.info("gallery reloaded: %d vectors / %d people", len(new.person_ids), new.num_people)
        return True

    # ------------------------------------------------------------------ helpers
    def _make_event(self, d: Decision, track: Track, face: Face, ts: float) -> Event:
        dt = datetime.fromtimestamp(ts).astimezone()
        day = dt.strftime("%Y-%m-%d")
        if day != self._seq_day:
            self._seq_day = day
            self._seq = next_event_seq(self.data_dir, day)
        self._seq += 1
        w = track.window[-self.cfg.decision.window:]
        if d.type == "RECOGNIZED":
            votes = [f for f in w if f.person_id == d.person_id and f.live >= self.rules.live_t]
            sim = max(f.sim for f in votes)
            sim2 = max(f.sim2 for f in votes)
            frames = len(votes)
        else:
            best = max(w, key=lambda f: f.sim)
            sim, sim2, frames = best.sim, best.sim2, len(w)
        recognized = d.type == "RECOGNIZED"
        return Event(
            event_id=f"{self.cfg.device_id}-{dt.strftime('%Y%m%d')}-{self._seq:06d}",
            type=d.type,
            device_id=self.cfg.device_id,
            track_id=track.track_id,
            occurred_at=dt.isoformat(timespec="milliseconds"),
            person_id=d.person_id if recognized else None,
            person_name=self.gallery.name_of(d.person_id) if recognized else None,
            scores={"similarity": round(sim, 3), "second_best": round(sim2, 3),
                    "live": round(float(np.mean([f.live for f in w])), 3), "frames_voted": frames},
            bbox=[round(float(v), 1) for v in face.bbox],
            snapshot=None,
            model={"detector": self.det.name, "liveness": self.live.name, "recognizer": self.rec.name},
        )

    def flush_undecided(self, tr: Track, why: str) -> None:
        best = max(tr.window, key=lambda f: f.sim)
        info = {"track_id": tr.track_id, "why": why, "frames": len(tr.window),
                "best_person": best.person_id, "best_sim": round(best.sim, 3),
                "second": round(best.sim2, 3),
                "live_min": round(min(f.live for f in tr.window), 3),
                "live_max": round(max(f.live for f in tr.window), 3)}
        self.undecided.append(info)
        log.info("UNDECIDED %s", info)

    def _timed(self, stage: str):
        return _Timer(self.stage_ms[stage])

    def timing_summary(self) -> str:
        return " ".join(f"{k}={np.mean(v):.1f}ms" for k, v in self.stage_ms.items() if v)


class _Timer:
    def __init__(self, bucket: list[float]):
        self.bucket = bucket

    def __enter__(self):
        self.t = time.perf_counter()

    def __exit__(self, *exc):
        self.bucket.append((time.perf_counter() - self.t) * 1000)
        if len(self.bucket) > TIMER_MAX_SAMPLES:
            del self.bucket[:TIMER_KEEP]

