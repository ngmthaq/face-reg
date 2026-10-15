# PROJECT OVERVIEW

---

- **Project Name**: `AIE`
- **Project Description**: `Offline face recognition with liveness for one gate camera on an edge device, code in the package face_reg/.`
- **Programming Languages**: `Python 3.10+`
- **Frameworks**: `None (plain Python CLI apps)`
- **Package Managers**: `pip (requirements.txt, virtual env in .venv)`
- **Key Libraries**: `opencv (YuNet face detection, SFace face recognition), onnxruntime (MiniFASNet liveness), numpy, pydantic, pyyaml`
- **Database**: `None`
- **Doc Directory**: `plans/`
- **Testing Workflow**: `Skip-Testing` <!-- Code-First | Test-First | Skip-Testing -->
- **Playwright Check**: `None` <!-- Always | None | Ask-User -->

> Note: DO NOT change the list format above. Only fill in the values.

## Additional Information

### Commands (run all from the project root)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m face_reg run --show           # run face_reg
bash scripts/download_models.sh   # get the YuNet and SFace models
```

### Main places

| Path | What it holds |
|---|---|
| `face_reg/` | The code package: `__main__.py`, `src/` |
| `config.yaml` | All settings (thresholds, camera, relay), loaded by `face_reg/src/configs/config.py` |
| `data/` | Runtime output: gallery, events, snapshots (git-ignored, biometric) |
| `photos/` | Enrollment photos `photos/<person_id>/<angle>.jpg` (git-ignored except `.gitkeep`, biometric) |
| `scripts/deploy/` | `install.sh`, `face_reg.service` (systemd), `face_reg-xhost.desktop` |
| `README.md` | The only README in the project. Source of truth for usage, deploy and layout |
| `face_reg/src/stages/` | Pipeline stages: stream, detect, quality, liveness, recognize, tracker, decide |
| `face_reg/src/configs/` | Config pydantic models, one class per file; `config.py` loads `config.yaml` |
| `face_reg/src/datatypes/` | Data classes passed between stages, one class per file |
| `face_reg/src/main.py` | CLI dispatcher (`run` only), started by `__main__.py` |
| `face_reg/src/cli/` | `pipeline_wrapper.py` (run command) + `pipeline.py` (stage wiring), `enroll.py` (gallery logic) + `photo_scanner.py` (thread that syncs the gallery with `photos/`) |
| `face_reg/src/tools/` | Logging setup, sinks, overlay, liveness export |
| `scripts/` | Shell helpers: download models, run |
| `models/` | ONNX model files, shared at the root |
| `requirements.txt` | Shared at the root |
| `plans/` | Plan files written by the agent |
| `docs/face_reg/SPEC.md` | The face_reg spec. **Not in the repo yet.** |
| `graphify-out/` | Graphify code graph (code-only build, git-ignored) |

### Important facts

- There are no `__init__.py` files. `face_reg/` is a namespace package (a package with no `__init__.py`).
- `config.yaml` paths that are relative start from the project root, not the `face_reg/` folder.
- `photos/` and `data/` hold biometric data (face photos, gallery, events, snapshots).
  - Never commit them. `.gitignore` already blocks them.
  - Never read them into the chat. `.graphifyignore` also blocks them.
- Large models (YuNet, SFace) are not in git. Liveness ONNX files are in git.
- The local `.venv` uses Python 3.13. The code must still work on Python 3.10.
- The project is a git repository. The main branch is `main`.
