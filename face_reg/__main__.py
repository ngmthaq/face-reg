"""Module entry point — the CLI is in main.py.

    python -m face_reg run [--show] [--source ...] [--config ...]
"""
import sys

from face_reg.main import main

sys.exit(main())
