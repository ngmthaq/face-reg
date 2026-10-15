"""Keeps the gallery in sync with the photos folder (photos/<person_id>/<angle>.jpg).

A background thread scans the folder on a timer: new or changed folders are enrolled,
people whose folder is gone are removed. The running pipeline reloads the gallery files itself.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path

from face_reg.entry.step_4_enroll import IMAGE_EXT, PERSON_ID_RE, Enroller, audit, expand_photos
from face_reg.configs import config as config_mod
from face_reg.stages.step_6_recognize import Gallery

log = logging.getLogger("face_reg.enroll")

STATE_FILE = "scan_state.json"
SOURCE = "scan"
Signature = list[list]


class PhotoScanner:
    def __init__(self, cfg: config_mod.Config):
        self.cfg = cfg
        self.photos_dir = cfg.path(cfg.enroll.photos_dir)
        self.state_path = cfg.path(cfg.persons).with_name(STATE_FILE)
        self._enroller: Enroller | None = None
        self._warned_names: set[str] = set()
        self._missing_warned = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------ thread
    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="photo-scan", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
            if self._thread.is_alive():
                log.warning("photo scan thread did not stop within %.0f s", timeout)

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.scan_once()
            except Exception:
                log.exception("photo scan failed, retry in %.0f s", self.cfg.enroll.scan_interval_s)
            self._stop.wait(self.cfg.enroll.scan_interval_s)

    # ------------------------------------------------------------------ one scan
    def scan_once(self) -> bool:
        """Sync the gallery with the photos folder. Returns True when the gallery changed."""
        en = self._get_enroller()
        en.gallery = Gallery.load(self.cfg.path(self.cfg.gallery), self.cfg.path(self.cfg.persons))
        old_state = self._load_state()
        folders = self._list_folders()
        state: dict[str, Signature] = {}
        enrolled = removed = 0
        changed = False

        gone = (set(en.gallery.persons) | set(en.gallery.person_ids)) - set(folders)
        if gone and not folders:
            log.warning("no person folders in %s: removing everyone from the gallery", self.photos_dir)
        for pid in sorted(gone):
            n = en.gallery.remove(pid)
            removed += 1
            changed = True
            audit(self.cfg, "remove", {"person_id": pid, "vectors": n, "source": SOURCE})
            log.info("%-10s removed (folder is gone)", pid)

        for pid, folder in folders.items():
            sig = self._signature(folder)
            state[pid] = sig
            if old_state.get(pid) == sig:
                continue
            result = en.enroll(pid, None, expand_photos([str(folder)]))
            for line in result.lines:
                bad = "rejected" in line or "NOT ENROLLED" in line
                log.log(logging.WARNING if bad else logging.INFO, line)
            if result.count:
                enrolled += 1
                changed = True
                audit(self.cfg, "enroll", {"person_id": pid, "vectors": result.count, "source": SOURCE})

        if changed:
            en.save()
            log.info("scan: +%d enrolled, -%d removed, gallery %d vectors / %d people",
                     enrolled, removed, len(en.gallery.person_ids), en.gallery.num_people)
        if state != old_state:
            self._save_state(state)
        return changed

    def _get_enroller(self) -> Enroller:
        if self._enroller is None:
            self._enroller = Enroller(self.cfg, use_liveness=not self.cfg.enroll.skip_liveness)
        return self._enroller

    # ------------------------------------------------------------------ folders and state
    def _list_folders(self) -> dict[str, Path]:
        if not self.photos_dir.is_dir():
            if not self._missing_warned:
                self._missing_warned = True
                log.warning("photos folder %s not found", self.photos_dir)
            return {}
        self._missing_warned = False
        out: dict[str, Path] = {}
        for d in sorted(self.photos_dir.iterdir()):
            if d.name.startswith(".") or d.is_symlink() or not d.is_dir():
                continue
            if not PERSON_ID_RE.match(d.name):
                if d.name not in self._warned_names:
                    self._warned_names.add(d.name)
                    log.warning("skipping folder %r: name must match %s", d.name, PERSON_ID_RE.pattern)
                continue
            out[d.name] = d
        return out

    @staticmethod
    def _signature(folder: Path) -> Signature:
        sig = []
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() not in IMAGE_EXT or f.is_symlink():
                continue
            try:
                st = f.stat()
            except FileNotFoundError:
                continue
            sig.append([f.name, st.st_size, st.st_mtime_ns])
        return sig

    def _load_state(self) -> dict[str, Signature]:
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            if not isinstance(state, dict):
                raise ValueError("not a JSON object")
            return state
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as e:
            log.warning("scan state unreadable (%s): treating every folder as new", e)
            return {}

    def _save_state(self, state: dict[str, Signature]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.state_path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.state_path)
