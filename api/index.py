"""
Vercel Serverless Function entry point for VG Intelligence.

Vercel expects a `handler` that extends BaseHTTPRequestHandler,
or a WSGI/ASGI app. We reuse our existing VGWebHandler.
"""

import os
import sys
import types

# ── Bootstrap the 'vg' package so all `from vg.xxx` imports resolve ──
# On Vercel, the project root IS the function root.
# We create a virtual 'vg' package pointing to the project root.
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Create the 'vg' namespace package pointing to project root
if 'vg' not in sys.modules:
    vg_mod = types.ModuleType('vg')
    vg_mod.__path__ = [ROOT_DIR]
    vg_mod.__package__ = 'vg'
    sys.modules['vg'] = vg_mod

# ── Import and expose the handler ──
from api.server import VGWebHandler  # noqa: E402

# Vercel looks for this exact name
handler = VGWebHandler
