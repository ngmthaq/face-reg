# Title: Plan — Remove tests, then use opencv-python and show the preview on the edge monitor

- Classification: feature
- Description: First delete all tests, test setup, and test docs. Then always install `opencv-python`, add a `display` config switch, and let the systemd service draw the preview window on the auto-login desktop. If no display is found, it logs a warning and keeps running.

---

## Approach Summary / Goal

- **Task 0 (first):** delete `face_reg/tests/`, `pytest.ini`, `scripts/test.sh`, and the pytest lines in `requirements.txt`. Remove every mention of them from `README.md`, `CODING_CONVENTIONS.md`, and `PROJECT_OVERVIEW.md`. Set `Testing Workflow` to `Skip-Testing`.
- Replace `opencv-python-headless` with `opencv-python`. `install.sh` installs the system libraries it needs with apt, and removes an old headless copy so the two builds don't clash in the venv.
- Add `display: {show, window}` to `config.yaml` and the pydantic config. `--show` / `--no-show` and `--window` on the CLI override it. The default stays `show: false`.
- The service stays as user `face_reg` and gets `DISPLAY=:0`. A desktop autostart file runs `xhost +SI:localuser:face_reg`.
- Before it opens the window, the app tests the display in a child process. This is needed because Qt aborts the whole process when it can't reach a display. If the test fails, the app logs a warning, runs without the window, and tests again every 30 s.

## Functional Requirements

- After task 0, these no longer exist: `face_reg/tests/`, `pytest.ini`, `scripts/test.sh`, `pytest` and `pytest-cov` in `requirements.txt`. No doc mentions them. The `eval_offline` / `test_photos/` docs stay.
- `PROJECT_OVERVIEW.md` says `Testing Workflow: Skip-Testing`.
- `pip install -r requirements.txt` installs `opencv-python>=4.8` and not `-headless`.
- `config.yaml` has `display.show` (default `false`) and `display.window` (default `"1280x720"`). Bad window values fail when the config loads.
- `--show` turns the window on, `--no-show` turns it off, and with no flag the config value is used. `--window` overrides `display.window`.
- If show is on and the display test fails: one WARNING log line, recognition and sinks keep running, and the test runs again every 30 s. When it passes, the window opens.
- On Linux with neither `DISPLAY` nor `WAYLAND_DISPLAY` set, the test fails at once without starting a child process.
- `install.sh` runs `apt-get install` for `libgl1`, `libglib2.0-0` (or `libglib2.0-0t64`), and `x11-xserver-utils`, only when `apt-get` exists. It uninstalls `opencv-python-headless` before the pip install. It copies the xhost autostart file to `/etc/xdg/autostart/`.
- `face_reg.service` sets `Environment=DISPLAY=:0`. It keeps `User=face_reg`, all its hardening, and `WantedBy=multi-user.target`.

## Non-Functional Requirements

- Security: display access goes only to the local user `face_reg` (`SI:localuser`), never `xhost +`. No change to the service hardening or data permissions.
- A missing display must never crash or stop the gate.
- The display test has a 10 s timeout and runs at most once every 30 s, and only while there is no window.

## Files in Scope

- **Delete:** `face_reg/tests/` (7 files), `pytest.ini`, `scripts/test.sh`
- **Change:** `requirements.txt`, `README.md`, `.claude/references/CODING_CONVENTIONS.md`, `.claude/references/PROJECT_OVERVIEW.md`, `.gitignore` and `deploy/install.sh` (only if they mention `.pytest_cache`)
- **Change:** `deploy/install.sh`, `deploy/face_reg.service`, `config.yaml`, `face_reg/src/configs/config.py`, `face_reg/src/cli/pipeline_wrapper.py`, `face_reg/src/cli/pipeline.py`, `face_reg/src/tools/overlay.py`
- **New:** `deploy/face_reg-xhost.desktop`, `face_reg/src/configs/display_cfg.py`

## Risks & Assumptions

- **Risk:** with no tests, the earlier security fixes, current behavior, and the new display code have no automatic check. The only way back is git history (`dd87901`). You chose this on purpose.
- Assumption: task 0 goes to the **developer**, because it changes docs and config as well as test files.
- Assumption: checks after the work are by hand only: `bash -n deploy/install.sh`, `python -m face_reg run --help`, and loading `config.yaml` with Python.
- Assumption: the desktop runs on display `:0` (X11, or Wayland with XWayland).
- Assumption: q or Esc in the window still stops the app, and systemd restarts it after 3 s.
- Risk: if the display goes away while the window is open, Qt may abort the app. systemd restarts it, and the next display test fails safely.
- Risk: `opencv-python` is bigger than the headless build and needs GL/GLib libraries, even on devices with no monitor.
- Developers with an old `.venv` must run `pip uninstall opencv-python-headless` once. The README will say this.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked

## Task List

| #   | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
| --- | ------ | ---- | ---------------- | ------------ | ------------------- | ------ |
| 0   | TODO   | Delete `face_reg/tests/`, `pytest.ini`, `scripts/test.sh`. Remove `pytest`, `pytest-cov`, and the `# dev` comment from `requirements.txt`. Remove the test mentions from `README.md` (lines 17, 28, 88, 195, 199, 204), the Testing section and tree lines in `CODING_CONVENTIONS.md`, and the pytest/test lines in `PROJECT_OVERVIEW.md`. Set `Testing Workflow` to `Skip-Testing`. Remove any leftover `.pytest_cache` entries. | developer | none | `git ls-files` shows no test files, `pytest.ini`, or `test.sh`. A grep for `pytest` outside `plans/`, `.claude/skills`, and `.claude/agents` finds nothing. The eval_offline docs are unchanged. | `clean-code` |
| 1   | TODO   | Add `DisplayCfg` (`show: bool=False`, `window: str="1280x720"` with a `WxH` validator) in `face_reg/src/configs/display_cfg.py`. Add `display` to `Config` and to `config.yaml`. | developer | 0 | Config loads with and without a `display:` block. `window: "abc"` raises a validation error. | `clean-code` |
| 2   | TODO   | Add `display_available()` to `overlay.py`, with the env-var pre-check on Linux and a child-process window test (timeout 10 s). | developer | 0 | Never raises. Returns False on timeout, a non-zero exit, or a missing env var. | `clean-code` |
| 3   | TODO   | `pipeline_wrapper.py`: `--show` becomes `BooleanOptionalAction` (default None), `--window` default None, add `resolve_display(args, cfg)`. `pipeline.py`: test the display before creating `Preview`, warn and re-test every 30 s, and update the comments that mention headless. | developer | 1, 2 | CLI flags override the config. With no display, the loop keeps processing and logs a warning for each failed test. `python -m face_reg run --help` works. | `clean-code` |
| 4   | TODO   | `requirements.txt` → `opencv-python>=4.8`. In `install.sh`: apt libs (only when apt-get exists, with the libglib fallback), the headless uninstall, and the autostart copy. New `deploy/face_reg-xhost.desktop`. Add `Environment=DISPLAY=:0` to `face_reg.service`. | developer | 0 | `bash -n deploy/install.sh` passes. The unit keeps all its hardening lines. xhost grants only `SI:localuser:face_reg`. | `clean-code`, `security-scanner` |
| 5   | TODO   | Update `README.md` (quick start, `--show`/`--no-show`, `display:` config, a "Monitor on the edge device" section, a note about the old venv) and the opencv rule in `CODING_CONVENTIONS.md`. | developer | 0–4 | No text still says headless is required. The docs match the real flags and config keys. | `clean-code` |

> The old task 6 (tester) is removed, as you asked. No tester sub-agent will run.
