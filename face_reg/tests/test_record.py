"""Unit tests for the footage recorder (no camera: fake reader and fake writer)."""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pytest

from face_reg.src.tools import record
from face_reg.src.tools.record import Recorder, disk_ok, part_path


class FakeReader:
    def __init__(self):
        self.online = True
        self.ended = False
        self.stopped = False
        self.frame = np.zeros((48, 64, 3), np.uint8)

    def latest(self):
        return self.frame, 0

    def stop(self):
        self.stopped = True


class FakeWriter:
    def __init__(self, path, on_write=None):
        self.path = path
        self.frames = []
        self.released = False
        self.on_write = on_write

    def write(self, frame):
        self.frames.append(frame)
        if self.on_write:
            self.on_write()

    def release(self):
        self.released = True


class WriterFactory:
    def __init__(self, on_write=None):
        self.writers = []
        self.sizes = []
        self.on_write = on_write

    def __call__(self, path, fps, size):
        writer = FakeWriter(path, self.on_write)
        self.writers.append(writer)
        self.sizes.append(size)
        return writer


def make_recorder(tmp_path, factory, reader=None):
    return Recorder(reader or FakeReader(), tmp_path / "rec", fps=15, part_min=10,
                    min_free_gb=5.0, writer_factory=factory,
                    now=lambda: datetime(2026, 10, 12, 14, 5, 9))


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(record.time, "sleep", lambda s: None)


# ---------------- part_path ----------------
def test_part_path_builds_date_folder_and_time_file(tmp_path):
    start = datetime(2026, 10, 12, 14, 5, 9)

    result = part_path(tmp_path, start)

    assert result == tmp_path / "2026-10-12" / "14-05-09.mp4"


def test_part_path_midnight_uses_zero_time_in_same_date_folder(tmp_path):
    start = datetime(2026, 10, 12, 0, 0, 0)

    result = part_path(tmp_path, start)

    assert result == tmp_path / "2026-10-12" / "00-00-00.mp4"


def test_part_path_zero_pads_single_digit_fields(tmp_path):
    start = datetime(2026, 1, 2, 3, 4, 5)

    result = part_path(tmp_path, start)

    assert result == tmp_path / "2026-01-02" / "03-04-05.mp4"


# ---------------- disk_ok ----------------
@pytest.mark.parametrize("free, expected", [(10.0, True), (5.0, True), (4.99, False)])
def test_disk_ok_compares_free_space_with_limit(monkeypatch, tmp_path, free, expected):
    monkeypatch.setattr(record, "free_gb", lambda path: free)

    result = disk_ok(tmp_path, 5.0)

    assert result is expected


# ---------------- Recorder ----------------
def test_run_returns_1_and_opens_no_writer_when_disk_low_before_first_part(monkeypatch, tmp_path):
    monkeypatch.setattr(record, "free_gb", lambda path: 1.0)
    factory = WriterFactory()
    reader = FakeReader()
    recorder = make_recorder(tmp_path, factory, reader)

    code = recorder.run()

    assert code == 1
    assert factory.writers == []
    assert reader.stopped


def test_run_releases_writer_and_returns_1_when_disk_goes_low_while_recording(monkeypatch, tmp_path):
    disk = {"free": 100.0}
    monkeypatch.setattr(record, "free_gb", lambda path: disk["free"])
    monkeypatch.setattr(record, "DISK_CHECK_EVERY_S", 0.0)
    factory = WriterFactory(on_write=lambda: disk.update(free=1.0))
    reader = FakeReader()
    recorder = make_recorder(tmp_path, factory, reader)

    code = recorder.run()

    assert code == 1
    assert len(factory.writers) == 1
    assert len(factory.writers[0].frames) >= 1
    assert factory.writers[0].released
    assert reader.stopped


def test_run_opens_part_at_expected_path_and_frame_size(monkeypatch, tmp_path):
    monkeypatch.setattr(record, "free_gb", lambda path: 100.0)
    reader = FakeReader()
    reader.ended = False
    factory = WriterFactory(on_write=lambda: setattr(reader, "ended", True))
    recorder = make_recorder(tmp_path, factory, reader)

    code = recorder.run()

    assert code == 0
    assert factory.writers[0].path == tmp_path / "rec" / "2026-10-12" / "14-05-09.mp4"
    assert factory.sizes == [(64, 48)]
    assert factory.writers[0].released
