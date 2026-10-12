"""Command line, started by face_reg/__main__.py.

    python -m face_reg run [--config config.yaml] [--show [--window 1280x720]]
    python -m face_reg enroll --person-id emp_0142 --name "Nguyen Van A" photos/*.jpg
"""
from __future__ import annotations

import argparse
import logging
import sys

from face_reg.src.tools.logs import setup_logging


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "enroll":
        from face_reg.src.cli.enroll_wrapper import main as enroll_main
        setup_logging(level=logging.WARNING)
        return enroll_main(argv[1:])
    else:
        from face_reg.src.cli.pipeline_wrapper import add_run_parser, run_command
        ap = argparse.ArgumentParser(prog="python -m face_reg")
        sub = ap.add_subparsers(dest="cmd", required=True)
        add_run_parser(sub)
        sub.add_parser("enroll", help="manage the gallery (see: python -m face_reg enroll -h)")
        args = ap.parse_args(argv)
        setup_logging(args.verbose)
        return run_command(args, ap)


if __name__ == "__main__":
    sys.exit(main())
