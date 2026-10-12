"""Module entry point — the code lives in src/.

    python -m face_reg run [--show] [--source ...] [--config ...]
    python -m face_reg enroll --person-id emp_0142 --name "Nguyen Van A" photos/*.jpg
"""
import sys

from face_reg.src.main import main

sys.exit(main())
