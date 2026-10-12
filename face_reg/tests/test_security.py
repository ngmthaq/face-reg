"""Security regression tests: relay without a shell, person_id checks, model hash check."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from face_reg.src.cli import enroll
from face_reg.src.cli import enroll_wrapper as enroll_cli
from face_reg.src.cli.enroll import EnrollResult
from face_reg.src.configs.config import Config
from face_reg.src.configs.relay_cfg import RelayCfg
from face_reg.src.tools.sinks import RelaySink

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "download_models.sh"
MODEL_FILES = [
    "face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx",
    "minifasnet_v1se_4.0_80x80.onnx",
    "minifasnet_v2_2.7_80x80.onnx",
]


@pytest.fixture
def run_calls(monkeypatch):
    calls: list[tuple[list[str], dict]] = []
    sleeps: list[float] = []
    monkeypatch.setattr("face_reg.src.tools.sinks.subprocess.run",
                        lambda cmd, **kw: calls.append((cmd, kw)))
    monkeypatch.setattr("face_reg.src.tools.sinks.time.sleep", sleeps.append)
    return calls, sleeps


def test_relay_command_runs_on_then_off_without_shell(run_calls):
    calls, sleeps = run_calls
    sink = RelaySink(RelayCfg(mode="command", command=["relay", "on"],
                              off_command=["relay", "off"], pulse_s=0.5))

    sink._pulse()

    assert [c for c, _ in calls] == [["relay", "on"], ["relay", "off"]]
    assert all(kw["shell"] is False for _, kw in calls)
    assert sleeps == [0.5]


def test_relay_off_command_runs_when_on_command_fails(monkeypatch):
    calls: list[tuple[list[str], dict]] = []
    sleeps: list[float] = []

    def fake_run(cmd, **kw):
        calls.append((cmd, kw))
        if cmd == ["relay", "on"]:
            raise subprocess.TimeoutExpired(cmd, 10)

    monkeypatch.setattr("face_reg.src.tools.sinks.subprocess.run", fake_run)
    monkeypatch.setattr("face_reg.src.tools.sinks.time.sleep", sleeps.append)
    sink = RelaySink(RelayCfg(mode="command", command=["relay", "on"],
                              off_command=["relay", "off"], pulse_s=0.5))

    sink._pulse()

    assert [c for c, _ in calls] == [["relay", "on"], ["relay", "off"]]
    assert calls[1][1]["shell"] is False
    assert sleeps == []


def test_relay_empty_command_runs_nothing(run_calls):
    calls, _ = run_calls
    sink = RelaySink(RelayCfg(mode="command", command=[]))

    sink._pulse()

    assert calls == []


def test_relay_without_off_command_runs_once(run_calls):
    calls, _ = run_calls
    sink = RelaySink(RelayCfg(mode="command", command=["relay", "on"], off_command=[]))

    sink._pulse()

    assert len(calls) == 1


def test_relay_string_command_is_rejected():
    with pytest.raises(ValidationError):
        Config.model_validate({"relay": {"command": "usbrelay x"}})


@pytest.mark.parametrize("pid", ["emp_0142", "A-1", "a" * 64])
def test_person_id_regex_accepts_valid(pid):
    assert enroll.PERSON_ID_RE.match(pid)


@pytest.mark.parametrize("pid", ["../x", "/abs", "a/b", "a b", "", "a" * 65])
def test_person_id_regex_rejects_invalid(pid):
    assert enroll.PERSON_ID_RE.match(pid) is None


@pytest.fixture
def audit_calls(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(enroll, "audit", lambda *a, **k: calls.append(a))
    return calls


@pytest.mark.parametrize("argv", [["--person-id", "../x"], ["--remove", "../x"]])
def test_bad_person_id_exits_2_without_audit(argv, audit_calls):
    with pytest.raises(SystemExit) as exc:
        enroll_cli.main(argv)

    assert exc.value.code == 2
    assert audit_calls == []


def test_batch_skips_invalid_folder_names(tmp_path, monkeypatch, capsys, audit_calls):
    for name in ("emp_1", "bad.name", "a b"):
        (tmp_path / name).mkdir()
    enrolled: list[str] = []

    class FakeLive:
        enabled = True

    class FakeGallery:
        person_ids: list[str] = []
        num_people = 0

    class FakeEnroller:
        def __init__(self, cfg, use_liveness=True):
            self.live = FakeLive()
            self.gallery = FakeGallery()

        def enroll(self, person_id, name, photos):
            enrolled.append(person_id)
            return EnrollResult(0, [])

        def save(self):
            pass

    monkeypatch.setattr(enroll, "Enroller", FakeEnroller)
    monkeypatch.setattr(enroll.config_mod, "load", lambda path: object())

    code = enroll_cli.main(["--batch", str(tmp_path)])

    err = capsys.readouterr().err
    assert code == 0
    assert enrolled == ["emp_1"]
    assert "bad.name" in err and "a b" in err


def test_download_models_rejects_tampered_model(tmp_path):
    originals = [ROOT / "models" / n for n in MODEL_FILES]
    if not all(p.is_file() for p in originals):
        pytest.skip("real model files not present")
    models = tmp_path / "models"
    models.mkdir()
    for p in originals:
        shutil.copy(p, models / p.name)
    tampered = MODEL_FILES[3]
    (models / tampered).write_bytes(b"tampered")

    res = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, env={"PATH": "/usr/bin:/bin:/usr/local/bin",
                         "MODELS_DIR": str(models)}, capture_output=True, text=True, timeout=120)

    assert res.returncode == 1
    assert tampered in res.stderr
    assert "fetch" not in res.stdout
