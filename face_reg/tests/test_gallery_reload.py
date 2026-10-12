"""Tests for Pipeline.reload_gallery_if_changed (gallery hot reload)."""
from __future__ import annotations

import logging
import os

import numpy as np
import pytest

from face_reg.src.cli import pipeline as pipeline_mod
from face_reg.src.configs.config import Config
from face_reg.src.cli.pipeline import Pipeline
from face_reg.src.stages.recognize import Gallery

LOGGER = "face_reg"
MTIME_STEP_NS = 1_000_000_000


def unit(i: int) -> np.ndarray:
    v = np.zeros(128, np.float32)
    v[i] = 1.0
    return v


class FakeStage:
    enabled = True
    name = "fake"

    def __init__(self, *a, **k):
        pass


def bump_mtime(path, steps=1):
    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + steps * MTIME_STEP_NS))


def build_gallery(*people):
    g = Gallery()
    for pid, name, idx in people:
        g.add(pid, name, [unit(idx)], ["front"])
    return g


def save_gallery(cfg, gallery):
    gal_path, persons_path = cfg.path(cfg.gallery), cfg.path(cfg.persons)
    gal_path.parent.mkdir(parents=True, exist_ok=True)
    gallery.save(gal_path, persons_path)
    return gal_path, persons_path


@pytest.fixture
def cfg(tmp_path):
    return Config(device_id="gate-1", base_dir=tmp_path, gallery=str(tmp_path / "g" / "gallery.npz"),
                  persons=str(tmp_path / "g" / "persons.json"), data_dir=str(tmp_path / "data"))


@pytest.fixture
def pipe(monkeypatch, cfg):
    save_gallery(cfg, build_gallery(("emp_1", "Alice", 0), ("emp_2", "Bob", 1)))
    monkeypatch.setattr(pipeline_mod, "YuNetDetector", FakeStage)
    monkeypatch.setattr(pipeline_mod, "Liveness", FakeStage)
    monkeypatch.setattr(pipeline_mod, "SFaceRecognizer", FakeStage)
    return Pipeline(cfg, sinks=[])


def errors(caplog):
    return [r for r in caplog.records if r.levelno == logging.ERROR]


def test_reload_returns_true_when_gallery_file_changed(pipe, cfg):
    gal_path, _ = save_gallery(cfg, build_gallery(("emp_1", "Alice", 0), ("emp_2", "Bob", 1), ("emp_3", "Cy", 2)))
    bump_mtime(gal_path)

    assert pipe.reload_gallery_if_changed() is True


def test_reload_swaps_in_new_gallery_contents(pipe, cfg):
    gal_path, _ = save_gallery(cfg, build_gallery(("emp_1", "Alice", 0), ("emp_2", "Bob", 1), ("emp_3", "Cy", 2)))
    bump_mtime(gal_path)

    pipe.reload_gallery_if_changed()

    assert (len(pipe.gallery.person_ids), pipe.gallery.num_people) == (3, 3)


def test_reload_logs_info_with_new_counts(pipe, cfg, caplog):
    gal_path, _ = save_gallery(cfg, build_gallery(("emp_1", "Alice", 0), ("emp_2", "Bob", 1), ("emp_3", "Cy", 2)))
    bump_mtime(gal_path)
    caplog.set_level(logging.INFO, logger=LOGGER)

    pipe.reload_gallery_if_changed()

    assert "gallery reloaded: 3 vectors / 3 people" in [r.getMessage() for r in caplog.records]


def test_no_change_returns_false_and_keeps_gallery_object(pipe):
    before = pipe.gallery

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery is before) == (False, True)


def test_second_call_after_successful_reload_returns_false(pipe, cfg):
    gal_path, _ = save_gallery(cfg, build_gallery(("emp_1", "Alice", 0)))
    bump_mtime(gal_path)
    pipe.reload_gallery_if_changed()

    assert pipe.reload_gallery_if_changed() is False


def test_persons_json_only_change_reloads_with_new_name(pipe, cfg):
    _, persons_path = save_gallery(cfg, build_gallery(("emp_1", "Alicia", 0), ("emp_2", "Bob", 1)))
    gal_path = cfg.path(cfg.gallery)
    os.utime(gal_path, ns=(os.stat(gal_path).st_atime_ns, pipe._gallery_sig[0]))
    bump_mtime(persons_path)

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery.name_of("emp_1")) == (True, "Alicia")


def test_broken_npz_returns_false_and_keeps_old_gallery(pipe, cfg):
    before = pipe.gallery
    gal_path = cfg.path(cfg.gallery)
    gal_path.write_bytes(b"not a real npz")
    bump_mtime(gal_path)

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery is before) == (False, True)


def test_broken_npz_logs_one_error(pipe, cfg, caplog):
    gal_path = cfg.path(cfg.gallery)
    gal_path.write_bytes(b"not a real npz")
    bump_mtime(gal_path)

    pipe.reload_gallery_if_changed()

    assert len(errors(caplog)) == 1
    assert "gallery reload failed, keeping old gallery" in errors(caplog)[0].getMessage()


def test_same_broken_npz_does_not_log_error_twice(pipe, cfg, caplog):
    gal_path = cfg.path(cfg.gallery)
    gal_path.write_bytes(b"not a real npz")
    bump_mtime(gal_path)
    pipe.reload_gallery_if_changed()
    caplog.clear()

    result = pipe.reload_gallery_if_changed()

    assert (result, errors(caplog)) == (False, [])


def test_fixed_file_after_broken_one_reloads(pipe, cfg):
    gal_path = cfg.path(cfg.gallery)
    gal_path.write_bytes(b"not a real npz")
    bump_mtime(gal_path)
    pipe.reload_gallery_if_changed()
    save_gallery(cfg, build_gallery(("emp_1", "Alice", 0)))
    bump_mtime(gal_path, steps=5)

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery.num_people) == (True, 1)


def test_broken_persons_json_keeps_old_gallery_and_logs_error(pipe, cfg, caplog):
    before = pipe.gallery
    persons_path = cfg.path(cfg.persons)
    persons_path.write_text("{ invalid json", encoding="utf-8")
    bump_mtime(persons_path)

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery is before, len(errors(caplog))) == (False, True, 1)


def test_deleted_npz_keeps_old_gallery_and_logs_error(pipe, cfg, caplog):
    before = pipe.gallery
    cfg.path(cfg.gallery).unlink()

    result = pipe.reload_gallery_if_changed()

    assert (result, pipe.gallery is before, len(errors(caplog))) == (False, True, 1)


def test_deleted_npz_does_not_log_error_twice(pipe, cfg, caplog):
    cfg.path(cfg.gallery).unlink()
    pipe.reload_gallery_if_changed()
    caplog.clear()

    pipe.reload_gallery_if_changed()

    assert errors(caplog) == []
