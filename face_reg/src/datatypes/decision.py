"""Final decision for a track."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Decision:
    type: str               # RECOGNIZED | UNKNOWN | SPOOF_SUSPECTED | UNDECIDED
    person_id: str | None = None
