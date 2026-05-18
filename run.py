#!/usr/bin/env python3
"""Compatibility runner that now launches the VG web interface."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.main import run_web


if __name__ == "__main__":
    run_web(sys.argv[1:])
