# Coding Conventions

> No lint or format config exists. These rules come from the current code.

## Folder tree

```text
face-reg/
├── face_reg/                 # code only
│   ├── __main__.py           # entry point: python -m face_reg
│   ├── src/                  # code: pipeline, enroll
│   │   ├── configs/          # pydantic config classes, one per file
│   │   ├── datatypes/        # dataclasses, one per file
│   │   ├── cli/              # main, run, enroll commands
│   │   ├── tools/            # sinks, overlay, offline eval, record, export
│   │   └── stages/           # stream, detect, quality, liveness, recognize, tracker, decide
├── config.yaml               # all settings
├── data/                     # biometric — never commit, never read
├── photos/                   # biometric — never commit, never read
├── scripts/                  # shell helpers: download models, run, enroll, record, eval
│   └── deploy/               # install.sh, systemd service, xhost autostart
├── models/                   # ONNX models
├── plans/
├── README.md                 # the only README in the project
└── requirements.txt
```

The root `README.md` is the only README. Do not add README files in sub-folders.

## Imports

- No `__init__.py` files. `face_reg/` is a namespace package.
- Use full import paths everywhere: `from face_reg.src.stages.detect import YuNetDetector`.
  - Do not use relative imports (`from ..datatypes import Face`). Old code in `src/` still has them.
- Order: `from __future__ import annotations`, standard library, third-party (`cv2`, `numpy`, `yaml`, `pydantic`), project. One blank line between groups.
- Run every command from the project root.

## Style

- 4 spaces. Double quotes. Lines up to about 120 characters.
- Each file starts with a docstring that says what the file does.
- Type hints on public functions. Use `X | None` and `list[int]`, with `from __future__ import annotations` so it works on Python 3.10.
- Short end-of-line comments for units and meaning (e.g. `# seconds`, `# 5x2 landmarks`).

## Naming

- Files, functions, variables: `snake_case`.
- Classes: `PascalCase` (`YuNetDetector`, `IoUTracker`, `DecisionRules`).
- Constants: `UPPER_CASE` (`PROJECT_ROOT`, `DEFAULT_CONFIG`).
- Stage files are named after the stage (`detect.py`, `liveness.py`).
- Event types and reason codes are `UPPER_CASE` strings (`RECOGNIZED`, `SPOOF_SUSPECTED`, `TOO_BLURRY`).

## File order

1. Docstring
2. Imports
3. Module constants and `log = logging.getLogger(...)`
4. Classes and functions (public first, small helpers near where they are used)

## Config and data

- Config is pydantic models in `src/configs/`, loaded from `config.yaml`. Every field has a default.
- Relative paths in `config.yaml` start from the project root. Resolve them with `cfg.path(...)`.
- Data passed between stages uses `@dataclass` types in `src/datatypes/`.
- One class per file in `src/configs/` and `src/datatypes/`. File name = snake_case of the class name. No `__init__.py`; import from the exact file.
- Models live in `models/` at the root. No database.

## Errors and logging

- Raise clear errors with a fix hint, e.g. `FileNotFoundError("YuNet model not found: ... (run: bash scripts/download_models.sh)")`.
- Use `logging` in `src/`, not `print`.
- Logger names start with the package name (`face_reg`, `face_reg.events`, `face_reg.enroll`).
- Only the CLI entry calls `logging.basicConfig`.

## Biometric data

- `photos/` and `data/` hold face photos, the gallery, events, and snapshots.
- Never commit them. Never read them into the chat. Never log face crops or embeddings.

## Third-party libraries

- Add new libraries to the root `requirements.txt` with a minimum version (`>=`).
- Use `opencv-python` (GUI build) so the edge device can show the preview on a monitor. Hardware-only libraries (e.g. `gpiozero`) stay commented out.
