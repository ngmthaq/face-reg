from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from face_reg.src.cli.pipeline_wrapper import should_mirror
from face_reg.src.datatypes.track import Track
from face_reg.src.tools.overlay import COLORS, draw_overlay

BOX_COLOR = np.array(COLORS[None], dtype=np.uint8)
FRAME_W = 200


def _asymmetric_frame() -> np.ndarray:
    frame = np.zeros((100, FRAME_W, 3), dtype=np.uint8)
    frame[:, : FRAME_W // 2] = 255
    return frame


def _tracker_with_box() -> SimpleNamespace:
    track = Track(
        track_id=1,
        bbox=np.array([10, 20, 50, 50], dtype=float),
        first_ts=0.0,
        last_ts=0.0,
    )
    return SimpleNamespace(tracks={1: track})


def _has_box_color(frame: np.ndarray, row: int, col: int) -> bool:
    return bool(np.array_equal(frame[row, col], BOX_COLOR))


def test_draw_overlay_without_tracks_and_mirror_flips_frame_left_right():
    frame = _asymmetric_frame()
    tracker = SimpleNamespace(tracks={})

    result = draw_overlay(frame, tracker, mirror=True)

    assert np.array_equal(result, cv2.flip(frame, 1))


def test_draw_overlay_without_tracks_and_no_mirror_keeps_frame_unchanged():
    frame = _asymmetric_frame()
    original = frame.copy()
    tracker = SimpleNamespace(tracks={})

    result = draw_overlay(frame, tracker, mirror=False)

    assert np.array_equal(result, original)
    assert np.array_equal(frame, original)


def test_draw_overlay_with_mirror_draws_box_at_flipped_x():
    frame = np.zeros((100, FRAME_W, 3), dtype=np.uint8)
    tracker = _tracker_with_box()

    result = draw_overlay(frame, tracker, mirror=True)

    assert _has_box_color(result, 50, 140)
    assert not _has_box_color(result, 50, 10)


def test_draw_overlay_without_mirror_draws_box_at_original_x():
    frame = np.zeros((100, FRAME_W, 3), dtype=np.uint8)
    tracker = _tracker_with_box()

    result = draw_overlay(frame, tracker, mirror=False)

    assert _has_box_color(result, 50, 10)
    assert not _has_box_color(result, 50, 140)


@pytest.mark.parametrize(
    "source, flag, expected",
    [
        (0, None, True),
        (1, None, True),
        ("rtsp://cam/stream", None, False),
        ("/videos/gate.mp4", None, False),
        (0, False, False),
        ("rtsp://x", True, True),
    ],
)
def test_should_mirror_returns_flag_or_webcam_default(source, flag, expected):
    result = should_mirror(source, flag)

    assert result is expected
