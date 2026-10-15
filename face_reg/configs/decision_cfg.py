from __future__ import annotations

from pydantic import BaseModel


class DecisionCfg(BaseModel):
    window: int = 5            # vote over the last N good-quality frames
    min_votes: int = 3
    cooldown_s: float = 10.0   # same person_id not re-emitted within this time
    timeout_s: float = 3.0     # undecided this long after first good frame -> UNDECIDED (log only)
