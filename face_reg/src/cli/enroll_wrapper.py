"""Gallery tool: enroll, remove and list people.

    python -m face_reg enroll --person-id emp_0142 --name "Nguyen Van A"     # uses photos/emp_0142/
    python -m face_reg enroll --person-id emp_0142 some/other/path/*.jpg     # or explicit files
    python -m face_reg enroll --remove emp_0142
    python -m face_reg enroll --list
    python -m face_reg enroll --batch                                         # every sub-folder of photos/

Photo layout: photos/<employee_id>/<angle>.jpg (git-ignored), where <angle> is
one of front, left, right, up, down (optionally numbered: front_2.jpg). front is required.
Enrolling a person REPLACES their previous vectors. Delete the photos after enrolling:
only the vectors are needed.

Every photo goes through the same detection, quality and liveness stages as the
stream, so a bad photo is rejected here, not discovered at the gate. The gallery
is written atomically; the running service loads it within 5 seconds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from face_reg.src.cli import enroll as enroll_mod
from face_reg.src.configs import config as config_mod
from face_reg.src.stages.recognize import Gallery


def _cmd_list(cfg: config_mod.Config) -> int:
    g = Gallery.load(cfg.path(cfg.gallery), cfg.path(cfg.persons))
    for pid in sorted(set(g.person_ids)):
        angles = ",".join(g.persons.get(pid, {}).get("angles", []))
        print(f"{pid:<12} {g.person_ids.count(pid):>2} vectors  {angles:<26} {g.name_of(pid) or ''}")
    print(f"-> {len(g.person_ids)} vectors / {g.num_people} people")
    return 0


def _cmd_remove(cfg: config_mod.Config, person_id: str) -> int:
    g = Gallery.load(cfg.path(cfg.gallery), cfg.path(cfg.persons))
    n = g.remove(person_id)
    if n == 0:
        print(f"{person_id} not in gallery")
        return 1
    g.save(cfg.path(cfg.gallery), cfg.path(cfg.persons))
    enroll_mod.audit(cfg, "remove", {"person_id": person_id, "vectors": n})
    print(f"-> removed {person_id} ({n} vectors), gallery now {len(g.person_ids):,} vectors / {g.num_people:,} people")
    return 0


def _cmd_batch(cfg: config_mod.Config, en: enroll_mod.Enroller, root: str) -> int:
    total = 0
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        if not enroll_mod.PERSON_ID_RE.match(d.name):
            print(f"warning: skipping folder {d.name!r}: invalid person id", file=sys.stderr)
            continue
        result = en.enroll(d.name, None, enroll_mod.expand_photos([str(d)]))
        print("\n".join(result.lines))
        if result.count:
            enroll_mod.audit(cfg, "enroll", {"person_id": d.name, "vectors": result.count})
            total += result.count
    en.save()
    print(f"-> {total} vectors enrolled, gallery now {len(en.gallery.person_ids):,} vectors / {en.gallery.num_people:,} people")
    return 0


def _cmd_enroll(cfg: config_mod.Config, en: enroll_mod.Enroller, ap: argparse.ArgumentParser,
                args: argparse.Namespace) -> int:
    if not args.person_id:
        ap.error("--person-id is required (or use --list / --remove / --batch)")
    photo_args = args.photos or [str(config_mod.PHOTOS_DIR / args.person_id)]
    photos = enroll_mod.expand_photos(photo_args)
    if not photos:
        ap.error(f"no photos found in {photo_args[0]} (put them in photos/{args.person_id}/)")
    result = en.enroll(args.person_id, args.name, photos)
    print("\n".join(result.lines))
    n = result.count
    if n:
        en.save()
        enroll_mod.audit(cfg, "enroll", {"person_id": args.person_id, "vectors": n})
    print(f"-> {n} vectors enrolled for {args.person_id}, gallery now {len(en.gallery.person_ids):,} vectors / {en.gallery.num_people:,} people")
    if n:
        print("   the running service loads the new gallery within 5 seconds")
    return 0 if n else 2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m face_reg enroll", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None, help="default: config.yaml")
    ap.add_argument("--person-id")
    ap.add_argument("--name")
    ap.add_argument("--remove", metavar="PERSON_ID")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--batch", metavar="DIR", nargs="?", const=str(config_mod.PHOTOS_DIR),
                    help="folder with one sub-folder per person_id (default: photos)")
    ap.add_argument("--skip-liveness", action="store_true",
                    help="do not run liveness on enrollment photos (e.g. scanned ID photos)")
    ap.add_argument("photos", nargs="*", help="default: photos/<person-id>/")
    args = ap.parse_args(argv)

    for pid in (args.person_id, args.remove):
        if pid is not None and not enroll_mod.PERSON_ID_RE.match(pid):
            ap.error(f"invalid person id {pid!r}: use 1-64 letters, digits, '_' or '-'")

    cfg = config_mod.load(args.config or config_mod.DEFAULT_CONFIG)

    if args.list:
        return _cmd_list(cfg)
    if args.remove:
        return _cmd_remove(cfg, args.remove)

    en = enroll_mod.Enroller(cfg, use_liveness=not args.skip_liveness)
    if args.skip_liveness or not en.live.enabled:
        print("note: liveness is NOT checked on these photos", file=sys.stderr)

    if args.batch:
        return _cmd_batch(cfg, en, args.batch)
    return _cmd_enroll(cfg, en, ap, args)
