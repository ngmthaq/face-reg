"""The `run` command: start the gate pipeline."""
from __future__ import annotations

import argparse


def add_run_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    run = sub.add_parser("run", help="run the gate pipeline")
    run.add_argument("--config", default=None, help="default: config.yaml")
    run.add_argument("--show", action="store_true", help="open a preview window (needs opencv-python, not -headless)")
    run.add_argument("--window", default="1280x720", metavar="WxH",
                     help="max preview window size, frames are shrunk to fit (default 1280x720)")
    run.add_argument("--source", help="override camera.source (RTSP URL, video file, or webcam index)")
    run.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=None,
                     help="mirror the --show preview left-right (default: on for a webcam index, off for RTSP / video files)")
    run.add_argument("-v", "--verbose", action="store_true")
    return run


def should_mirror(source: str | int, flag: bool | None) -> bool:
    return flag if flag is not None else isinstance(source, int)


def run_command(args: argparse.Namespace, ap: argparse.ArgumentParser) -> int:
    from face_reg.src.configs import config
    from face_reg.src.cli.pipeline import Pipeline
    cfg = config.load(args.config or config.DEFAULT_CONFIG)
    if args.source is not None:
        cfg.camera.source = int(args.source) if args.source.isdigit() else args.source
    try:
        w, h = (int(v) for v in args.window.lower().split("x"))
    except ValueError:
        ap.error("--window must look like 1280x720")
    mirror = should_mirror(cfg.camera.source, args.mirror)
    Pipeline(cfg).run(show=args.show, window=(w, h), mirror=mirror)
    return 0
