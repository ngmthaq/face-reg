"""Unit tests for the parts with logic of their own (no models needed)."""
from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pytest

from face_reg.src.configs import config as config_mod
from face_reg.src.tools.sinks import JsonlSink, SnapshotSink, cleanup_old_data, next_event_seq
from face_reg.src.stages.decide import DecisionRules
from face_reg.src.stages.liveness import crop_box
from face_reg.src.stages.quality import estimate_yaw_deg, quality_check
from face_reg.src.stages.recognize import EMBED_DIM, Gallery
from face_reg.src.stages.tracker import IoUTracker, iou
from face_reg.src.datatypes.event import Event
from face_reg.src.datatypes.face import Face
from face_reg.src.datatypes.frame_result import FrameResult
from face_reg.src.datatypes.track import Track


def make_face(x, y, w=100, h=120, yaw_shift=0.0):
    lm = np.array([[x + 0.3 * w, y + 0.4 * h], [x + 0.7 * w, y + 0.4 * h],
                   [x + 0.5 * w + yaw_shift, y + 0.6 * h],
                   [x + 0.35 * w, y + 0.8 * h], [x + 0.65 * w, y + 0.8 * h]], np.float32)
    raw = np.concatenate([[x, y, w, h], lm.reshape(-1), [0.95]]).astype(np.float32)
    return Face(bbox=np.array([x, y, w, h], np.float32), landmarks=lm, score=0.95, raw=raw)


def fr(live=0.95, pid="a", sim=0.6, sim2=0.3):
    return FrameResult(0.0, live, pid, sim, sim2)


def track_with(frames):
    t = Track(1, np.zeros(4), 0, 0)
    t.window = list(frames)
    return t


# ---------------- decision rules ----------------
R = DecisionRules(live_t=0.8, match_t=0.45, margin=0.05)


def test_needs_three_frames():
    decision = R.decide(track_with([fr(), fr()]))

    assert decision is None


def test_recognized_after_three_votes():
    d = R.decide(track_with([fr(), fr(), fr()]))

    assert d.type == "RECOGNIZED" and d.person_id == "a"


def test_spoof_wins_ties():
    frames = [fr(live=0.1), fr(live=0.1), fr(live=0.1), fr(), fr()]
    decision = R.decide(track_with(frames))

    assert decision.type == "SPOOF_SUSPECTED"


def test_margin_rule_blocks_lookalikes():
    frames = [fr(sim=0.6, sim2=0.58)] * 5
    decision = R.decide(track_with(frames))

    assert decision.type == "UNKNOWN"


@pytest.mark.parametrize("live_frames, expected_type", [(4, None), (5, "UNKNOWN")], ids=["four_frames", "five_frames"])
def test_decide_unknown_face_waits_for_five_live_frames(live_frames, expected_type):
    decision = R.decide(track_with([fr(sim=0.2)] * live_frames))

    assert getattr(decision, "type", None) == expected_type


def test_split_votes_not_recognized():
    frames = [fr(pid="a"), fr(pid="a"), fr(pid="b"), fr(pid="b")]
    decision = R.decide(track_with(frames))

    assert decision is None


def test_only_last_window_counts():
    frames = [fr(live=0.1)] * 3 + [fr()] * 5
    decision = R.decide(track_with(frames))

    assert decision.type == "RECOGNIZED"


# ---------------- tracker ----------------
def test_iou_same_box_is_one():
    box = np.array([0, 0, 10, 10.0])

    overlap = iou(box, box)

    assert overlap == pytest.approx(1.0)


def test_iou_no_overlap_is_zero():
    box = np.array([0, 0, 10, 10.0])

    far_box = np.array([20, 20, 10, 10.0])

    overlap = iou(box, far_box)

    assert overlap == 0.0


def test_tracker_moved_face_keeps_track_id():
    tr = IoUTracker(iou=0.3, max_missed=2)
    (_, first), = tr.update([make_face(100, 100)], 0.0)

    (_, second), = tr.update([make_face(105, 102)], 0.2)

    assert second.track_id == first.track_id


@pytest.fixture
def tracker_after_two_misses():
    tr = IoUTracker(iou=0.3, max_missed=2)
    (_, track), = tr.update([make_face(100, 100)], 0.0)
    tr.update([], 0.2)
    tr.update([], 0.4)
    return tr, track


def test_tracker_third_miss_moves_track_to_removed(tracker_after_two_misses):
    tr, track = tracker_after_two_misses

    tr.update([], 0.6)

    assert [t.track_id for t in tr.removed] == [track.track_id]


def test_tracker_third_miss_empties_active_tracks(tracker_after_two_misses):
    tr, _ = tracker_after_two_misses

    tr.update([], 0.6)

    assert not tr.tracks


def test_tracker_two_faces_get_distinct_ids():
    tr = IoUTracker()

    out = tr.update([make_face(0, 0), make_face(400, 0)], 0.0)

    assert len({t.track_id for _, t in out}) == 2


def test_tracker_two_faces_keep_ids_when_order_swaps():
    tr = IoUTracker()
    tr.update([make_face(0, 0), make_face(400, 0)], 0.0)

    out = tr.update([make_face(402, 2), make_face(2, 2)], 0.2)

    ids = {round(float(f.bbox[0])): t.track_id for f, t in out}
    assert ids[2] == 1 and ids[402] == 2


# ---------------- quality ----------------
def test_yaw_frontal_face_is_near_zero():
    yaw = estimate_yaw_deg(make_face(0, 0).landmarks)

    assert abs(yaw) < 1


def test_yaw_turned_face_is_over_thirty_degrees():
    yaw = estimate_yaw_deg(make_face(0, 0, yaw_shift=35).landmarks)

    assert abs(yaw) > 30


@pytest.fixture
def sharp_frame():
    return np.random.default_rng(0).integers(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def flat_frame():
    return np.full((480, 640, 3), 128, np.uint8)


def test_quality_small_face_is_rejected_as_too_small(sharp_frame):
    result = quality_check(sharp_frame, make_face(100, 100, 40, 40))

    assert result.reason == "FACE_TOO_SMALL"


def test_quality_turned_face_is_rejected_as_pose_too_wide(sharp_frame):
    result = quality_check(sharp_frame, make_face(100, 100, yaw_shift=40))

    assert result.reason == "POSE_TOO_WIDE"


def test_quality_flat_frame_is_rejected_as_too_blurry(flat_frame):
    result = quality_check(flat_frame, make_face(100, 100))

    assert result.reason == "TOO_BLURRY"


def test_quality_sharp_frontal_face_is_ok(sharp_frame):
    result = quality_check(sharp_frame, make_face(100, 100))

    assert result.ok


# ---------------- liveness crop ----------------
def test_crop_box_stays_inside_frame():
    l, t, r, b = crop_box(640, 480, [600, 440, 30, 30], 4.0)

    assert 0 <= l < r <= 639 and 0 <= t < b <= 479
    assert r - l == pytest.approx(120, abs=2)


# ---------------- gallery ----------------
def unit(v):
    v = np.asarray(v, np.float32)
    return v / np.linalg.norm(v)


E = np.eye(EMBED_DIM, dtype=np.float32)


@pytest.fixture
def gallery():
    g = Gallery()
    g.add("a", "A", [E[0], unit(E[0] + 0.1 * E[1])])   # two vectors for the same person
    g.add("b", "B", [unit(E[0] + E[2])])
    return g


@pytest.fixture
def saved_gallery(gallery, tmp_path):
    gallery.save(tmp_path / "gallery.npz")
    return tmp_path / "gallery.npz"


@pytest.fixture
def loaded_gallery(saved_gallery):
    return Gallery.load(saved_gallery)


def test_gallery_top2_returns_best_person_and_best_other_person(gallery):
    expected_other = float(unit(E[0] + E[2])[0])   # best of person b, not a's 2nd vector

    pid, s1, s2 = gallery.top2(E[0])

    assert pid == "a" and s1 == pytest.approx(1.0)
    assert s2 == pytest.approx(expected_other)


def test_gallery_load_restores_person_ids_and_names(saved_gallery):
    g2 = Gallery.load(saved_gallery)

    assert g2.person_ids == ["a", "a", "b"] and g2.name_of("b") == "B"


def test_gallery_remove_returns_removed_vector_count(loaded_gallery):
    removed = loaded_gallery.remove("a")

    assert removed == 2


def test_gallery_after_remove_best_match_is_other_person(loaded_gallery):
    loaded_gallery.remove("a")

    pid, _, _ = loaded_gallery.top2(E[0])

    assert pid == "b"


def test_gallery_save_leaves_no_tmp_file(gallery, tmp_path):
    gallery.save(tmp_path / "gallery.npz")

    assert not list(tmp_path.glob("*.tmp"))


def test_empty_gallery():
    result = Gallery().top2(np.ones(EMBED_DIM, np.float32))

    assert result == (None, 0.0, 0.0)


# ---------------- sinks / housekeeping ----------------
def _event() -> Event:
    return Event(event_id="g-20261012-000001", type="RECOGNIZED", device_id="d", track_id=1,
                 occurred_at="2026-10-12T09:00:00.000+07:00", person_id=None, person_name=None,
                 scores={}, bbox=[10, 10, 50, 50], snapshot=None, model={})


@pytest.fixture
def emitted_event(tmp_path):
    ev = _event()
    frame = np.zeros((100, 100, 3), np.uint8)
    SnapshotSink(tmp_path, 0.0).emit(ev, frame)
    JsonlSink(tmp_path).emit(ev, frame)
    return ev


def test_snapshot_sink_sets_event_snapshot_path(emitted_event):
    assert emitted_event.snapshot == "snapshots/2026-10-12/g-20261012-000001.jpg"


def test_snapshot_sink_writes_jpg_file(emitted_event, tmp_path):
    assert (tmp_path / emitted_event.snapshot).is_file()


def test_jsonl_sink_writes_event_line(emitted_event, tmp_path):
    line = (tmp_path / "events" / "2026-10-12.jsonl").read_text().strip()

    assert json.loads(line)["event_id"] == emitted_event.event_id


def test_next_event_seq_after_one_event_is_one(emitted_event, tmp_path):
    seq = next_event_seq(tmp_path, "2026-10-12")

    assert seq == 1


@pytest.fixture
def data_dir_with_old_and_new(tmp_path):
    old = (date.today() - timedelta(days=40)).isoformat()
    new = date.today().isoformat()
    (tmp_path / "events").mkdir()
    for d in (old, new):
        (tmp_path / "events" / f"{d}.jsonl").write_text("{}\n")
        (tmp_path / "snapshots" / d).mkdir(parents=True)
    return tmp_path, old, new


def test_retention_cleanup_returns_removed_count(data_dir_with_old_and_new):
    data_dir, _, _ = data_dir_with_old_and_new

    removed = cleanup_old_data(data_dir, 30)

    assert removed == 2


def test_retention_cleanup_keeps_recent_events_file(data_dir_with_old_and_new):
    data_dir, _, new = data_dir_with_old_and_new

    cleanup_old_data(data_dir, 30)

    assert (data_dir / "events" / f"{new}.jsonl").exists()


def test_retention_cleanup_removes_old_snapshot_dir(data_dir_with_old_and_new):
    data_dir, old, _ = data_dir_with_old_and_new

    cleanup_old_data(data_dir, 30)

    assert not (data_dir / "snapshots" / old).exists()


# ---------------- config ----------------
@pytest.fixture
def cfg(tmp_path):
    (tmp_path / "c.yaml").write_text("camera: {source: '0'}\nthresholds: {match: 0.5}\n")
    return config_mod.load(tmp_path / "c.yaml")


def test_config_camera_source_digit_string_becomes_int(cfg):
    assert cfg.camera.source == 0


def test_config_overridden_threshold_is_used(cfg):
    assert cfg.thresholds.match == 0.5


def test_config_missing_threshold_uses_default(cfg):
    assert cfg.thresholds.live == 0.8


def test_config_path_resolves_against_project_root(cfg):
    resolved = cfg.path(cfg.gallery)

    assert resolved == config_mod.PROJECT_ROOT / "data/gallery/gallery.npz"


# ---------------- enrollment file names ----------------
@pytest.mark.parametrize("file_name, expected_angle", [
    ("front.jpg", "front"),
    ("Left.JPG", "left"),
    ("up_2.png", "up"),
    ("down-3.jpg", "down"),
    ("selfie.jpg", None),
    ("frontal.jpg", None),
], ids=["plain", "uppercase", "underscore_index", "dash_index", "unknown_word", "word_prefix_only"])
def test_angle_of_file_name_returns_expected_angle(file_name, expected_angle):
    from pathlib import Path
    from face_reg.src.cli.enroll import angle_of

    angle = angle_of(Path("photos/emp_1") / file_name)

    assert angle == expected_angle
