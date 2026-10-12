"""Offline evaluation, no camera needed.

1) Photos (build step 1): one sub-folder per person. Enroll first, then test on other photos.
   Folders named "unknown" / "strangers" (or person_ids not in the gallery) must come back unknown.

    python -m face_reg.src.tools.eval_offline photos --dir test_photos/

2) Video (build steps 6-7): replay a recorded gate video through the full pipeline,
   using video time (not wall clock), and print events, decision latency and per-stage speed.

    python -m face_reg.src.tools.eval_offline video --file gate.mp4 [--out annotated.mp4] [--live 0.8 --match 0.45]

   Events are written to <data_dir>/eval/ (never into the real event log).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from face_reg.src.configs import config as config_mod
from face_reg.src.tools.logs import setup_logging
from face_reg.src.cli.enroll import IMAGE_EXT

UNKNOWN_DIRS = {"unknown", "strangers", "stranger", "_unknown"}


def eval_photos(cfg, root: Path) -> int:
    from face_reg.src.stages.detect import YuNetDetector
    from face_reg.src.stages.quality import quality_check
    from face_reg.src.stages.recognize import Gallery, SFaceRecognizer
    t = cfg.thresholds
    det = YuNetDetector(cfg.path(cfg.models.detector), t.detect_score, t.nms, cfg.detect_width)
    rec = SFaceRecognizer(cfg.path(cfg.models.recognizer))
    g = Gallery.load(cfg.path(cfg.gallery), cfg.path(cfg.persons))
    print(f"gallery: {len(g.person_ids)} vectors / {g.num_people} people; match>={t.match} margin>={t.margin}\n")
    stats = Counter()
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        expected = None if d.name.lower() in UNKNOWN_DIRS or d.name not in g.persons else d.name
        for f in sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXT):
            img = cv2.imread(str(f))
            faces = det.detect(img) if img is not None else []
            if not faces:
                print(f"{d.name:<12} {f.name:<28} NO_FACE")
                stats["no_face"] += 1
                continue
            face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
            q = quality_check(img, face, t.min_face_px, t.blur, t.max_yaw_deg)
            pid, s1, s2 = g.top2(rec.embed(img, face))
            got = pid if (s1 >= t.match and s1 - s2 >= t.margin) else None
            ok = got == expected
            if expected is None:
                stats["stranger_ok" if ok else "false_accept"] += 1
            else:
                stats["correct" if ok else ("false_accept" if got else "false_reject")] += 1
            flag = "OK " if ok else "ERR"
            print(f"{d.name:<12} {f.name:<28} {flag} got={got or 'unknown':<12} sim={s1:.2f} 2nd={s2:.2f}"
                  f"{'' if q.ok else '  (quality: ' + q.reason + ')'}")
    total = sum(stats.values())
    print(f"\n{total} photos: correct={stats['correct']} strangers_unknown={stats['stranger_ok']} "
          f"false_accept={stats['false_accept']} false_reject={stats['false_reject']} no_face={stats['no_face']}")
    return 1 if stats["false_accept"] else 0


def _write_overlay(writer, out: Path, pipe, frame: np.ndarray, label: str, fps: float, step: int):
    """Draw tracks on the frame and append it to the annotated video; opens the writer on first use."""
    from face_reg.src.tools.overlay import draw_overlay
    vis = draw_overlay(frame, pipe.tracker, pipe.gallery, label)
    if writer is None:
        h, w = vis.shape[:2]
        writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), fps / step, (w, h))
    writer.write(vis)
    return writer


def _replay(pipe, cap, fps: float, step: int, out: Path | None):
    """Feed video frames to the pipeline using video time; returns (frames read, process times, latencies)."""
    writer = None
    base_ts = time.time()        # video time is mapped onto "now" so event dates look normal
    idx = 0
    proc_times = []
    first_seen: dict[int, float] = {}
    latencies = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step == 0:
            ts = base_ts + idx / fps
            t0 = time.perf_counter()
            events = pipe.process(frame, ts)
            proc_times.append(time.perf_counter() - t0)
            for tr in pipe.tracker.tracks.values():
                if tr.first_good_ts is not None:
                    first_seen.setdefault(tr.track_id, tr.first_good_ts)
            for e in events:
                if e.track_id in first_seen:
                    latencies.append(ts - first_seen[e.track_id])
            if out is not None:
                writer = _write_overlay(writer, out, pipe, frame, f"t={idx / fps:6.1f}s", fps, step)
        idx += 1
    if writer is not None:
        writer.release()
    return idx, proc_times, latencies


def _print_summary(pipe, path: Path, out: Path | None, eval_dir: Path, idx: int, fps: float, step: int,
                   proc_times: list[float], latencies: list[float]) -> None:
    types = Counter(e.type for e in pipe.events)
    pt = np.array(proc_times) * 1000 if proc_times else np.zeros(1)
    print("\n==== summary ====")
    print(f"video: {path.name}  {idx} frames @ {fps:.1f} fps = {idx / fps:.1f}s, processed every {step} frames")
    print(f"events: {dict(types)}  undecided: {len(pipe.undecided)}")
    for e in pipe.events:
        print(f"  {e.occurred_at[11:23]}  {e.type:<16} track={e.track_id:<4} "
              f"person={e.person_id or '-':<12} sim={e.scores['similarity']:.2f} live={e.scores['live']:.2f}")
    if latencies:
        print(f"time to decision after first good frame: median {np.median(latencies):.2f}s, max {max(latencies):.2f}s")
    print(f"processing per frame: mean {pt.mean():.0f} ms, p95 {np.percentile(pt, 95):.0f} ms "
          f"-> max sustainable ~{1000 / max(pt.mean(), 1e-3):.1f} fps on this machine")
    print(f"per stage: {pipe.timing_summary()}")
    print(f"event log + snapshots: {eval_dir}")
    if out is not None:
        print(f"annotated video: {out}")


def eval_video(cfg, path: Path, out: Path | None, every_n: int | None) -> int:
    from face_reg.src.cli.pipeline import Pipeline
    from face_reg.src.tools.sinks import ConsoleSink, JsonlSink, SnapshotSink

    eval_dir = cfg.path(cfg.data_dir) / "eval" / time.strftime("%Y%m%d-%H%M%S")
    sinks = [SnapshotSink(eval_dir, 0.0), JsonlSink(eval_dir), ConsoleSink()]
    pipe = Pipeline(cfg, sinks=sinks)
    pipe.data_dir = eval_dir
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"cannot open {path}")
        return 2
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step = every_n or max(1, round(fps / cfg.camera.process_fps))
    idx, proc_times, latencies = _replay(pipe, cap, fps, step, out)
    for tr in list(pipe.tracker.tracks.values()):
        if not tr.decided and tr.window:
            pipe.flush_undecided(tr, "video_end")
    _print_summary(pipe, path, out, eval_dir, idx, fps, step, proc_times, latencies)
    with open(eval_dir / "undecided.json", "w", encoding="utf-8") as f:
        json.dump(pipe.undecided, f, indent=2)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="default: config.yaml")
    ap.add_argument("--live", type=float, help="override thresholds.live")
    ap.add_argument("--match", type=float, help="override thresholds.match")
    ap.add_argument("--no-liveness", action="store_true")
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("photos")
    p.add_argument("--dir", required=True)
    v = sub.add_parser("video")
    v.add_argument("--file", required=True)
    v.add_argument("--out", help="write an annotated .mp4")
    v.add_argument("--every-n", type=int, help="process every Nth frame (default: video fps / process_fps)")
    args = ap.parse_args()
    setup_logging()
    cfg = config_mod.load(args.config or config_mod.DEFAULT_CONFIG)
    if args.live is not None:
        cfg.thresholds.live = args.live
    if args.match is not None:
        cfg.thresholds.match = args.match
    if args.no_liveness:
        cfg.models.liveness = []
    if args.mode == "photos":
        return eval_photos(cfg, Path(args.dir))
    return eval_video(cfg, Path(args.file), Path(args.out) if args.out else None, args.every_n)


if __name__ == "__main__":
    sys.exit(main())
