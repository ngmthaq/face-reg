"""The `run` command: start the gate pipeline."""
from __future__ import annotations

import argparse

from face_reg.configs.display_cfg import parse_window


def add_run_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    run = sub.add_parser("run", help="run the gate pipeline")
    run.add_argument("--config", default=None, help="default: config.yaml")
    run.add_argument("--show", action=argparse.BooleanOptionalAction, default=None,
                     help="open a preview window on the monitor (default: display.show in config.yaml)")
    run.add_argument("--window", default=None, metavar="WxH",
                     help="max preview window size, frames are shrunk to fit (default: display.window in config.yaml)")
    run.add_argument("--source", help="override camera.source (RTSP URL, video file, or webcam index)")
    run.add_argument("--mirror", action=argparse.BooleanOptionalAction, default=None,
                     help="mirror the --show preview left-right (default: on for a webcam index, off for RTSP / video files)")
    run.add_argument("-v", "--verbose", action="store_true")
    return run


def should_mirror(source: str | int, flag: bool | None) -> bool:
    return flag if flag is not None else isinstance(source, int)


def resolve_display(args: argparse.Namespace, cfg) -> tuple[bool, tuple[int, int]]:
    """CLI flags win over the display: block of the config. Raises ValueError on a bad --window."""
    show = args.show if args.show is not None else cfg.display.show
    window = parse_window(args.window) if args.window is not None else cfg.display.size
    return show, window


def run_command(args: argparse.Namespace, ap: argparse.ArgumentParser) -> int:
    from face_reg.configs import config
    from face_reg.cli.pipeline import Pipeline
    cfg = config.load(args.config or config.DEFAULT_CONFIG)
    if args.source is not None:
        cfg.camera.source = int(args.source) if args.source.isdigit() else args.source
    try:
        show, window = resolve_display(args, cfg)
    except ValueError:
        ap.error("--window must look like 1280x720")
    mirror = should_mirror(cfg.camera.source, args.mirror)
    Pipeline(cfg).run(show=show, window=window, mirror=mirror)
    return 0
