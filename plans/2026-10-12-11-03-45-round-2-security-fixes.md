# Title: Plan — Round 2: security fixes

- Classification: feature (security hardening)
- Description: Remove the shell from the relay, lock `config.yaml`, check model files with SHA-256, and check the `person_id` format in `enroll`.

---

## Approach Summary / Goal

- **Relay:** `RelayCfg.command` becomes `list[str]`, and a new `off_command: list[str]` is added. `RelaySink._pulse` runs `command`, waits `pulse_s`, then runs `off_command` (if set). Both use `subprocess.run(..., shell=False)`. An old string value fails at startup with a clear pydantic error.
- **Config file:** after the `chown -R`, `install.sh` sets `config.yaml` to `root:face-edge` with mode `640` on every install. The service can read it but cannot change it.
- **Models:** `download_models.sh` checks SHA-256 for all 4 model files: after a download, and also for files already there. A wrong hash stops the script with an error. The models folder comes from `MODELS_DIR` (default `models`), so a test can use a temp folder.
- **person_id:** `enroll.py` adds `PERSON_ID_RE = ^[A-Za-z0-9_-]{1,64}$`. A bad `--person-id` or `--remove` value stops with `ap.error`. With `--batch`, a folder with a bad name is skipped with a warning on stderr.
- Goal: close the 3 medium findings and the `person_id` finding from the security check.

## Functional Requirements

1. When `relay.mode: command`, `_pulse` calls `subprocess.run(command, shell=False, timeout=10, check=False)`. It then sleeps `pulse_s`, then runs `off_command` the same way if it is not empty.
2. An empty `command` list means no command is run (same as today's empty string).
3. `config.yaml` with `relay.command` as a string fails `config.load` with a validation error.
4. `config.yaml` and `README.md` show the new list format: `command: [usbrelay, HURTM_1=1]`, `off_command: [usbrelay, HURTM_1=0]`.
5. After `install.sh` runs, `config.yaml` is owned by `root:face-edge` with mode `640`.
6. `download_models.sh` holds these SHA-256 values. It prints `ok` for a good file and exits 1 for a bad one:
   - `face_detection_yunet_2023mar.onnx` `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
   - `face_recognition_sface_2021dec.onnx` `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
   - `minifasnet_v1se_4.0_80x80.onnx` `f0beff994c3f3d2c7797fdfbcc746aab61d0b3543dd68d731ba5bcf3e19a1f96`
   - `minifasnet_v2_2.7_80x80.onnx` `5add8d901d04f8ab4df159f0dbea2cef4fb18909b7f693f74bfc9d2b338b2c73`
7. A downloaded file with a bad hash is deleted (the `.part` file) and never moved into place.
8. `enroll --person-id ../x` and `enroll --remove ../x` exit with a usage error. `--batch` skips bad folder names and still enrolls the good ones.

## Non-Functional Requirements

- Use `sha256sum` on Linux. Fall back to `shasum -a 256` on macOS.
- No new Python dependencies.
- The audit log never records a rejected `person_id`.

## Files in Scope

- `modules/face_edge/src/config.py` (`RelayCfg`)
- `modules/face_edge/src/sinks.py` (`RelaySink`)
- `modules/face_edge/src/enroll.py` (`PERSON_ID_RE`, `main`)
- `modules/face_edge/config.yaml` (relay example)
- `modules/face_edge/README.md` (relay docs)
- `modules/face_edge/tools/download_models.sh`
- `modules/face_edge/deploy/install.sh`
- `modules/face_edge/tests/test_security.py` (new)

## Risks & Assumptions

- Assumption: the 4 model files in `models/` today are the right ones. Their hashes become the trusted values.
- Risk: when OpenCV updates a model on the `main` branch, the hash check fails until someone updates the hash. This is on purpose.
- Risk: a device that already uses `relay.command` as a string will fail at startup after the update. Its config must be changed by hand. The error message names the field.
- The other low findings (pinning `requirements.txt`, more systemd hardening) and moving the camera password to an env file are not in this round.

## Open Questions / Blockers

- None.

## Status

- [x] Ready to execute
- [ ] Blocked — requires user input on: —

## Task List

| # | Status | Task | Responsible Role | Dependencies | Acceptance Criteria | Skills |
|---|---|---|---|---|---|---|
| 1 | DONE | `RelayCfg`: `command: list[str] = []`, add `off_command: list[str] = []`. `RelaySink._pulse`: run `command` with `shell=False`, sleep `pulse_s`, run `off_command` if set. Add a type hint `cfg: RelayCfg`. Update the comments. | developer | none | No `shell=True` in `src/`; a string `command` fails `Config.model_validate`; pytest still passes | `clean-code`, `security-scanner` |
| 2 | DONE | Update the relay example in `config.yaml` and the relay docs in `modules/face_edge/README.md` to the list format. | developer | 1 | `config.load()` on the default config works; the example shows `command` and `off_command` lists | `clean-code` |
| 3 | DONE | `enroll.py`: add `PERSON_ID_RE`. Check `--person-id` and `--remove` with `ap.error`. In `--batch`, skip bad folder names with a stderr warning. | developer | none | FR 8 holds; no `_audit` call for a rejected ID | `clean-code`, `security-scanner` |
| 4 | DONE | `download_models.sh`: add `MODELS_DIR` (default `models`). Add a SHA-256 check for all 4 files (hashes in FR 6) for new and existing files. A bad hash means delete the `.part` file, or keep the existing file, and exit 1 with an error. | developer | none | `bash -n` passes; run on the current `models/` → 4× `ok`, exit 0 | `security-scanner` |
| 5 | DONE | `install.sh`: after `chown -R`, run `chown root:face-edge` and `chmod 640` on `$DST/$MOD/config.yaml`. | developer | none | `bash -n` passes; the two lines come after `chown -R` | `security-scanner` |
| 6 | DONE | New `tests/test_security.py`: `RelaySink` command mode (mock `subprocess.run`, `time.sleep`): on, then off, with `shell=False`; empty command → no call; string `command` → validation error. `enroll.main` with a bad `--person-id` / `--remove` → `SystemExit` and no audit; `PERSON_ID_RE` good and bad cases (parametrize). `download_models.sh` with `MODELS_DIR` pointing to a temp folder that holds 1 tampered file → exit 1. Use `tmp_path` only, never real `photos/` or `data/`. | tester | 1–5 | All new tests pass; full suite passes; AAA, one Act per test | `aaa-testing` |

## Review Note

- Review 1 (not qualified): `RelaySink._pulse` skipped `off_command` when `command` raised, so the door relay could stay on (high). Fixed with `try/finally`. Regression test `test_relay_off_command_runs_when_on_command_fails` added.
- Review 2 (not qualified): secrets scan flagged the example RTSP URL in `config.yaml:6` and `README.md:39`. User chose to change them to `rtsp://USER:PASSWORD@CAMERA_IP:554/...`.
- Review 3: accepted. 38 passed, 1 skipped. Secrets scan: no secrets. Model hash check: 4× ok.
