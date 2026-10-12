"""Characterization tests: lock in external outputs (files, stdout, call order) before the refactor."""
from __future__ import annotations

import json
import os
import time

import numpy as np
import pytest

from face_reg.src.configs import config as config_mod
from face_reg.src.cli import enroll as enroll_mod
from face_reg.src.cli import enroll_wrapper as enroll_cli
from face_reg.src.cli import pipeline as pipeline_mod
from face_reg.src.configs.config import Config
from face_reg.src.datatypes.face import Face
from face_reg.src.datatypes.quality_result import QualityResult
from face_reg.src.cli.pipeline import Pipeline
from face_reg.src.tools.sinks import ConsoleSink, JsonlSink, SnapshotSink, build_sinks
from face_reg.src.stages.recognize import Gallery

TS0 = 1_700_000_000.0          # 2023-11-14 22:13:20 UTC
DAY = "2023-11-14"


def unit(i: int) -> np.ndarray:
    v = np.zeros(128, np.float32)
    v[i] = 1.0
    return v


def make_face(x=100.0, y=100.0, w=100.0, h=120.0) -> Face:
    lm = np.zeros((5, 2), np.float32)
    raw = np.zeros(15, np.float32)
    return Face(bbox=np.array([x, y, w, h], np.float32), landmarks=lm, score=0.95, raw=raw)


class FakeDetector:
    name = "fake-det"

    def __init__(self, *a, **k):
        pass

    def detect(self, frame):
        return FakeDetector.script.pop(0) if FakeDetector.script else []


class FakeLiveness:
    enabled = True
    name = "fake-live"

    def __init__(self, *a, **k):
        pass

    def score(self, frame, bbox):
        return FakeLiveness.script.pop(0)


class FakeRecognizer:
    name = "fake-rec"

    def __init__(self, *a, **k):
        pass

    def embed(self, frame, face):
        return FakeRecognizer.script.pop(0)


@pytest.fixture(autouse=True)
def utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.fixture
def cfg(tmp_path):
    return Config(device_id="gate-1", base_dir=tmp_path, gallery=str(tmp_path / "g" / "gallery.npz"),
                  persons=str(tmp_path / "g" / "persons.json"), data_dir=str(tmp_path / "data"))


@pytest.fixture
def make_pipe(monkeypatch, cfg):
    def _make(sinks, faces_per_frame, lives, vecs):
        FakeDetector.script = list(faces_per_frame)
        FakeLiveness.script = list(lives)
        FakeRecognizer.script = list(vecs)
        gal = Gallery()
        gal.add("emp_1", "Alice", [unit(0)], ["front"])
        gal.add("emp_2", "Bob", [unit(1)], ["front"])
        monkeypatch.setattr(pipeline_mod, "YuNetDetector", FakeDetector)
        monkeypatch.setattr(pipeline_mod, "Liveness", FakeLiveness)
        monkeypatch.setattr(pipeline_mod, "SFaceRecognizer", FakeRecognizer)
        monkeypatch.setattr(Gallery, "load", classmethod(lambda cls, *a, **k: gal))
        monkeypatch.setattr(pipeline_mod, "quality_check",
                            lambda *a, **k: QualityResult(True, None, 100.0, 100.0, 0.0, 1.0))
        return Pipeline(cfg, sinks=sinks)
    return _make


FRAME = np.zeros((480, 640, 3), np.uint8)


def run_frames(pipe, n, start=TS0, step=0.2):
    for i in range(n):
        pipe.process(FRAME, start + i * step)


def read_jsonl(cfg):
    path = cfg.path(cfg.data_dir) / "events" / f"{DAY}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


# ---------------------------------------------------------------- pipeline
def test_recognized_event_jsonl_content(make_pipe, cfg):
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 3, [0.9, 0.95, 0.9], [unit(0)] * 3)

    run_frames(pipe, 3)

    events = read_jsonl(cfg)
    assert events == [{
        "event_id": "gate-1-20231114-000001", "type": "RECOGNIZED", "device_id": "gate-1", "track_id": 1,
        "occurred_at": "2023-11-14T22:13:20.400+00:00", "person_id": "emp_1", "person_name": "Alice",
        "scores": {"similarity": 1.0, "second_best": 0.0, "live": 0.917, "frames_voted": 3},
        "bbox": [100.0, 100.0, 100.0, 120.0], "snapshot": None,
        "model": {"detector": "fake-det", "liveness": "fake-live", "recognizer": "fake-rec"},
    }]


def test_recognized_event_key_order(make_pipe, cfg):
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 3, [0.9] * 3, [unit(0)] * 3)

    run_frames(pipe, 3)

    assert list(read_jsonl(cfg)[0].keys()) == [
        "event_id", "type", "device_id", "track_id", "occurred_at", "person_id", "person_name",
        "scores", "bbox", "snapshot", "model"]


def test_spoof_event_jsonl_content(make_pipe, cfg):
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 3, [0.1, 0.2, 0.3], [unit(0)] * 3)

    run_frames(pipe, 3)

    events = read_jsonl(cfg)
    assert events == [{
        "event_id": "gate-1-20231114-000001", "type": "SPOOF_SUSPECTED", "device_id": "gate-1", "track_id": 1,
        "occurred_at": "2023-11-14T22:13:20.400+00:00", "person_id": None, "person_name": None,
        "scores": {"similarity": 1.0, "second_best": 0.0, "live": 0.2, "frames_voted": 3},
        "bbox": [100.0, 100.0, 100.0, 120.0], "snapshot": None,
        "model": {"detector": "fake-det", "liveness": "fake-live", "recognizer": "fake-rec"},
    }]


def test_cooldown_suppresses_second_event_for_same_person(make_pipe, cfg):
    faces = [[make_face()]] * 3 + [[]] * 12 + [[make_face()]] * 3
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], faces, [0.9] * 6, [unit(0)] * 6)

    run_frames(pipe, 18)

    assert [e["event_id"] for e in read_jsonl(cfg)] == ["gate-1-20231114-000001"]


def test_undecided_timeout_entry(make_pipe, cfg):
    vecs = [unit(0), unit(1), unit(2), unit(0)]
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 4, [0.9] * 4, vecs)

    for ts in (TS0, TS0 + 1.0, TS0 + 2.0, TS0 + 4.0):
        pipe.process(FRAME, ts)

    assert json.dumps(pipe.undecided) == json.dumps([{
        "track_id": 1, "why": "timeout", "frames": 4, "best_person": "emp_1", "best_sim": 1.0,
        "second": 0.0, "live_min": 0.9, "live_max": 0.9}])
    assert read_jsonl(cfg) == []


def test_track_lost_undecided_entry(make_pipe, cfg):
    faces = [[make_face()]] * 2 + [[]] * 11
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], faces, [0.9, 0.5], [unit(0), unit(1)])

    run_frames(pipe, 13)

    assert json.dumps(pipe.undecided) == json.dumps([{
        "track_id": 1, "why": "track_lost", "frames": 2, "best_person": "emp_1", "best_sim": 1.0,
        "second": 0.0, "live_min": 0.5, "live_max": 0.9}])


def test_failing_sink_does_not_block_jsonl(make_pipe, cfg):
    class Boom:
        def emit(self, event, frame):
            raise RuntimeError("boom")

    pipe = make_pipe([Boom(), JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 3, [0.9] * 3, [unit(0)] * 3)

    run_frames(pipe, 3)

    assert [e["type"] for e in read_jsonl(cfg)] == ["RECOGNIZED"]


def test_event_id_continues_from_existing_file(make_pipe, cfg):
    events_dir = cfg.path(cfg.data_dir) / "events"
    events_dir.mkdir(parents=True)
    (events_dir / f"{DAY}.jsonl").write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")
    pipe = make_pipe([JsonlSink(cfg.path(cfg.data_dir))], [[make_face()]] * 3, [0.9] * 3, [unit(0)] * 3)

    run_frames(pipe, 3)

    assert read_jsonl(cfg)[-1]["event_id"] == "gate-1-20231114-000003"


# ---------------------------------------------------------------- sinks
def test_build_sinks_order(cfg):
    cfg.sinks = ["relay", "console", "jsonl", "snapshot"]

    sinks = build_sinks(cfg)

    assert [type(s).__name__ for s in sinks] == ["SnapshotSink", "JsonlSink", "ConsoleSink", "RelaySink"]


def test_snapshot_path_is_written_to_jsonl(make_pipe, cfg):
    data_dir = cfg.path(cfg.data_dir)
    sinks = [SnapshotSink(data_dir, 0.0), JsonlSink(data_dir)]
    pipe = make_pipe(sinks, [[make_face()]] * 3, [0.9] * 3, [unit(0)] * 3)

    run_frames(pipe, 3)

    assert read_jsonl(cfg)[0]["snapshot"] == f"snapshots/{DAY}/gate-1-20231114-000001.jpg"


# ---------------------------------------------------------------- enroll
class FakeModel:
    enabled = True
    name = "fake"

    def __init__(self, *a, **k):
        pass


@pytest.fixture
def enroll_env(monkeypatch, cfg, tmp_path):
    monkeypatch.setattr(enroll_mod, "YuNetDetector", FakeModel)
    monkeypatch.setattr(enroll_mod, "Liveness", FakeModel)
    monkeypatch.setattr(enroll_mod, "SFaceRecognizer", FakeModel)
    monkeypatch.setattr(config_mod, "load", lambda *a, **k: cfg)
    photos = tmp_path / "pics"
    photos.mkdir()

    def scripted(results):
        monkeypatch.setattr(enroll_mod.Enroller, "check_photo",
                            lambda self, path, pid: results[path.name])

    def files(*names):
        out = []
        for n in names:
            (photos / n).write_bytes(b"")
            out.append(str(photos / n))
        return out

    return scripted, files


def seed_gallery(cfg):
    g = Gallery()
    g.add("emp_1", "Alice", [unit(0), unit(1)], ["front", "left"], enrolled_at="2023-01-01T00:00:00+00:00")
    g.add("emp_2", None, [unit(2)], ["front"])
    g.save(cfg.path(cfg.gallery), cfg.path(cfg.persons))


def test_single_enroll_stdout(enroll_env, capsys):
    scripted, files = enroll_env
    scripted({"front.jpg": (unit(0), "accepted", 0.9, 3.0), "left.jpg": (unit(1), "accepted", 0.8, -20.0),
              "right.jpg": (None, "NO_FACE", 0.0, 0.0)})
    paths = files("front.jpg", "left.jpg", "right.jpg")

    rc = enroll_cli.main(["--person-id", "emp_9", "--name", "Zed", *paths])

    assert (rc, capsys.readouterr().out) == (0, (
        "emp_9      front.jpg        accepted  quality=0.90 yaw=+3\n"
        "emp_9      left.jpg         accepted  quality=0.80 yaw=-20\n"
        "emp_9      right.jpg        rejected  NO_FACE\n"
        "emp_9      missing angles: right, up, down (optional, improves recognition)\n"
        "-> 2 vectors enrolled for emp_9, gallery now 2 vectors / 1 people\n"
        "   the running service loads the new gallery within 5 seconds\n"))


def test_enroll_without_valid_front(enroll_env, capsys):
    scripted, files = enroll_env
    scripted({"front.jpg": (None, "NO_FACE", 0.0, 0.0)})
    paths = files("front.jpg")

    rc = enroll_cli.main(["--person-id", "emp_9", *paths])

    assert (rc, capsys.readouterr().out) == (2, (
        "emp_9      front.jpg        rejected  NO_FACE\n"
        "emp_9      NOT ENROLLED: a valid front.jpg is required\n"
        "-> 0 vectors enrolled for emp_9, gallery now 0 vectors / 0 people\n"))


def test_enroll_bad_file_name_row(enroll_env, capsys):
    scripted, files = enroll_env
    scripted({"front.jpg": (unit(0), "accepted", 0.9, 0.0)})
    paths = files("front.jpg", "selfie.jpg")

    enroll_cli.main(["--person-id", "emp_9", *paths])

    assert "emp_9      selfie.jpg       rejected  BAD_FILE_NAME (use front, left, right, up, down.jpg)\n" \
        in capsys.readouterr().out


def test_list_stdout(cfg, capsys, monkeypatch):
    seed_gallery(cfg)
    monkeypatch.setattr(config_mod, "load", lambda *a, **k: cfg)

    rc = enroll_cli.main(["--list"])

    assert (rc, capsys.readouterr().out) == (0, (
        "emp_1         2 vectors  front,left                 Alice\n"
        "emp_2         1 vectors  front                      \n"
        "-> 3 vectors / 2 people\n"))


def test_remove_stdout(cfg, capsys, monkeypatch):
    seed_gallery(cfg)
    monkeypatch.setattr(config_mod, "load", lambda *a, **k: cfg)

    rc = enroll_cli.main(["--remove", "emp_1"])

    assert (rc, capsys.readouterr().out) == (
        0, "-> removed emp_1 (2 vectors), gallery now 1 vectors / 1 people\n")


def test_remove_not_in_gallery(cfg, capsys, monkeypatch):
    seed_gallery(cfg)
    monkeypatch.setattr(config_mod, "load", lambda *a, **k: cfg)

    rc = enroll_cli.main(["--remove", "ghost"])

    assert (rc, capsys.readouterr().out) == (1, "ghost not in gallery\n")


# ---------------------------------------------------------------- gallery
def test_gallery_save_load_round_trip_and_mode(tmp_path):
    g = Gallery()
    g.add("emp_1", "Alice", [unit(0), unit(1)], ["front", "left"])
    g.add("emp_2", "Bob", [unit(2)], ["front"])
    npz, js = tmp_path / "g" / "gallery.npz", tmp_path / "g" / "persons.json"

    g.save(npz, js)
    loaded = Gallery.load(npz, js)

    assert loaded.person_ids == g.person_ids
    assert loaded.persons == g.persons
    assert np.array_equal(loaded.vectors, g.vectors)
    assert (os.stat(npz).st_mode & 0o777, os.stat(js).st_mode & 0o777) == (0o600, 0o600)
