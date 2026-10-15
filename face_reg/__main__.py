"""Module entry point — the code lives in src/.

    python -m face_reg run [--show] [--source ...] [--config ...]
"""
import sys

from face_reg.src.main import main

sys.exit(main())
