"""Event written to the sinks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Event:
    event_id: str
    type: str
    device_id: str
    track_id: int
    occurred_at: str
    person_id: str | None
    person_name: str | None
    scores: dict
    bbox: list[float]
    snapshot: str | None
    model: dict

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "device_id": self.device_id,
            "track_id": self.track_id,
            "occurred_at": self.occurred_at,
            "person_id": self.person_id,
            "person_name": self.person_name,
            "scores": self.scores,
            "bbox": self.bbox,
            "snapshot": self.snapshot,
            "model": self.model,
        }
