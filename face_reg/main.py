"""Command line, started by face_reg/__main__.py.

    python -m face_reg run [--config config.yaml] [--show [--window 1280x720]]

The gallery follows the photos/ folder; `run` scans it every enroll.scan_interval_s seconds.
"""
from __future__ import annotations

import argparse
import sys

from face_reg.tools.logs import setup_logging


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    from face_reg.entry.step_1_pipeline_wrapper import add_run_parser, run_command
    ap = argparse.ArgumentParser(prog="python -m face_reg")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add_run_parser(sub)
    args = ap.parse_args(argv)
    setup_logging(args.verbose)
    return run_command(args, ap)


if __name__ == "__main__":
    sys.exit(main())
