"""Loads config.yaml into typed settings (pydantic).

Relative paths in the file (models, gallery, data, video files) are resolved against the
PROJECT ROOT (the folder that contains `face_reg/`), not the `face_reg/` folder, so models and
biometric data stay out of the source tree and the app works from any working directory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

from face_reg.configs.camera_cfg import CameraCfg
from face_reg.configs.decision_cfg import DecisionCfg
from face_reg.configs.display_cfg import DisplayCfg
from face_reg.configs.enroll_cfg import EnrollCfg
from face_reg.configs.models_cfg import ModelsCfg
from face_reg.configs.thresholds_cfg import ThresholdsCfg
from face_reg.configs.tracker_cfg import TrackerCfg

MODULE_DIR = Path(__file__).resolve().parents[1]      # face_reg (this file is in configs/)
PROJECT_ROOT = MODULE_DIR.parent                       # folder that contains face_reg/
DEFAULT_CONFIG = PROJECT_ROOT / "config.yaml"


class Config(BaseModel):
    device_id: str = "gate-1"
    camera: CameraCfg = Field(default_factory=CameraCfg)
    detect_width: int = 640    # frame is downscaled to this width for detection only
    models: ModelsCfg = Field(default_factory=ModelsCfg)
    thresholds: ThresholdsCfg = Field(default_factory=ThresholdsCfg)
    tracker: TrackerCfg = Field(default_factory=TrackerCfg)
    decision: DecisionCfg = Field(default_factory=DecisionCfg)
    gallery: str = "data/gallery/gallery.npz"
    persons: str = "data/gallery/persons.json"
    data_dir: str = "data"
    sinks: list[Literal["jsonl", "snapshot", "console"]] = Field(
        default_factory=lambda: ["jsonl", "snapshot", "console"])
    display: DisplayCfg = Field(default_factory=DisplayCfg)
    enroll: EnrollCfg = Field(default_factory=EnrollCfg)
    retention_days: int = 30
    min_free_gb: float = 1.0
    heartbeat_s: float = 60.0

    base_dir: Path = PROJECT_ROOT  # relative paths resolve here; not read from the file

    def path(self, p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else (self.base_dir / p)


def load(path: str | Path = DEFAULT_CONFIG) -> Config:
    path = Path(path).resolve()
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    cfg = Config.model_validate(raw)
    src = cfg.camera.source
    # "0" in YAML quotes -> USB index; relative video file -> resolve against the project root
    if isinstance(src, str):
        if src.isdigit():
            cfg.camera.source = int(src)
        elif "://" not in src and not Path(src).is_absolute():
            cfg.camera.source = str(cfg.path(src))
    return cfg
