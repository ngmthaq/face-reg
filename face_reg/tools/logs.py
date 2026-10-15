"""Logging setup shared by the CLI and the tools."""
from __future__ import annotations

import logging
import sys


def setup_logging(verbose: bool = False, level: int | None = None) -> None:
    if level is None:
        level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S", stream=sys.stdout)
