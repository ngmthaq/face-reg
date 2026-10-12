"""Integration tests with the real ONNX models. Skipped when models/ is not populated.

Optional: point FACE_REG_SAMPLES at the Silent-Face-Anti-Spoofing repo's images/sample
folder to also check liveness on its real (T1) and spoof (F1, F2) samples.
"""
from __future__ import annotations

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from face_reg.src.configs import config as config_mod
from face_reg.src.cli.pipeline import Pipeline

CFG = config_mod.DEFAULT_CONFIG
SAMPLES = Path(os.environ.get("FACE_REG_SAMPLES", "/nonexistent"))
needs_samples = pytest.mark.skipif(not SAMPLES.is_dir(), reason="FACE_REG_SAMPLES not set")


@pytest.fixture
def cfg(tmp_path):
    cfg = config_mod.load(CFG)
    for m in [cfg.models.detector, cfg.models.recognizer] + [m.path for m in cfg.models.liveness]:
        if not cfg.path(m).is_file():
            pytest.skip(f"model missing: {m} (run: bash scripts/download_models.sh)")
    cfg.gallery = str(tmp_path / "gallery.npz")
    cfg.persons = str(tmp_path / "persons.json")
    cfg.data_dir = str(tmp_path / "data")
    return cfg


@pytest.fixture
def pipe(cfg):
    return Pipeline(cfg, sinks=[])


@pytest.fixture
def real_image():
    return cv2.imread(str(SAMPLES / "image_T1.jpg"))


def test_pipeline_blank_frames_produce_no_events(pipe):
    blank = np.zeros((360, 640, 3), np.uint8)

    results = [pipe.process(blank, float(i)) for i in range(5)]

    assert results == [[]] * 5


@needs_samples
def test_liveness_real_sample_scores_above_threshold(pipe, real_image):
    face = pipe.det.detect(real_image)[0]

    score = pipe.live.score(real_image, face.bbox)

    assert score > 0.8, f"real sample scored {score:.3f}, expected > 0.8"


@needs_samples
@pytest.mark.parametrize("sample", ["image_F1.jpg", "image_F2.jpg"], ids=["F1", "F2"])
def test_liveness_spoof_sample_scores_below_threshold(pipe, sample):
    img = cv2.imread(str(SAMPLES / sample))
    face = pipe.det.detect(img)[0]

    score = pipe.live.score(img, face.bbox)

    assert score < 0.8, f"{sample} scored {score:.3f}, expected < 0.8"


@pytest.fixture
def enrolled_pipe(pipe, real_image):
    face = pipe.det.detect(real_image)[0]
    pipe.gallery.add("p1", "Person 1", [pipe.rec.embed(real_image, face)])
    return pipe


@needs_samples
def test_recognition_same_face_over_ten_frames_emits_single_recognized_event(enrolled_pipe, real_image):
    events = []
    for i in range(10):                       # same face over 10 frames at 5 fps
        events += enrolled_pipe.process(np.roll(real_image, i, axis=1), 1000.0 + i * 0.2)

    assert [e.type for e in events] == ["RECOGNIZED"]


@needs_samples
def test_recognition_event_names_enrolled_person(enrolled_pipe, real_image):
    events = []
    for i in range(10):
        events += enrolled_pipe.process(np.roll(real_image, i, axis=1), 1000.0 + i * 0.2)

    assert events[0].person_id == "p1"
