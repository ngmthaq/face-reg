"""Stage 7 — decision by voting over each track's last good-quality frames.

| Decision        | Rule (over the last 5 frames that passed quality)                         |
|-----------------|---------------------------------------------------------------------------|
| RECOGNIZED      | >= 3 live frames with the same top-1 person, sim >= match, top1-top2 >= margin |
| SPOOF_SUSPECTED | >= 3 frames with live < live threshold (spoof wins ties: checked first)   |
| UNKNOWN         | 5 live frames and nobody reaches the recognized rule                      |
| UNDECIDED       | track lost / timed out before any rule fires -> log only, no event        |
"""
from __future__ import annotations

from collections import Counter

from face_reg.datatypes.decision import Decision
from face_reg.datatypes.track import Track


class DecisionRules:
    def __init__(self, live_t: float = 0.8, match_t: float = 0.45, margin: float = 0.05,
                 window: int = 5, min_votes: int = 3):
        self.live_t, self.match_t, self.margin = live_t, match_t, margin
        self.window, self.min_votes = window, min_votes

    def decide(self, track: Track) -> Decision | None:
        w = track.window[-self.window:]
        if len(w) < self.min_votes:
            return None
        if sum(f.live < self.live_t for f in w) >= self.min_votes:
            return Decision("SPOOF_SUSPECTED")
        live = [f for f in w if f.live >= self.live_t]
        votes = Counter(f.person_id for f in live
                        if f.person_id is not None
                        and f.sim >= self.match_t and f.sim - f.sim2 >= self.margin)
        if votes:
            pid, n = votes.most_common(1)[0]
            if n >= self.min_votes:
                return Decision("RECOGNIZED", person_id=pid)
        if len(live) >= self.window:
            return Decision("UNKNOWN")
        return None
