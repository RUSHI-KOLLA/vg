"""
Vercel Serverless Function entry point for VG Intelligence.

Uses lazy imports inside request handlers so Vercel can detect
the handler class at build time without resolving the full import chain.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import types

# Flag to track if bootstrap has run
_bootstrapped = False


def _bootstrap():
    """Bootstrap the vg package namespace. Called once on first request."""
    global _bootstrapped
    if _bootstrapped:
        return
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    if 'vg' not in sys.modules:
        vg_mod = types.ModuleType('vg')
        vg_mod.__path__ = [ROOT_DIR]
        vg_mod.__package__ = 'vg'
        sys.modules['vg'] = vg_mod
    _bootstrapped = True


class handler(BaseHTTPRequestHandler):
    """Vercel-compatible handler that delegates to VG's analysis pipeline."""

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            self._json_response(200, {
                "status": "ok",
                "service": "vg-web",
                "version": "2.0",
                "mode": "vercel",
            })
        else:
            self._json_response(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/analyze":
            self._json_response(404, {"error": "Not found"})
            return

        # Extract API key
        api_key = self.headers.get("X-API-Key", "").strip()
        if not api_key:
            self._json_response(401, {
                "error": "API key required.",
                "hint": "Send your Groq API key in the X-API-Key header.",
            })
            return

        # Read body
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self._json_response(400, {"error": "Invalid JSON body."})
            return

        question = str(body.get("question", "")).strip()
        if not question:
            self._json_response(400, {"error": "Question is required."})
            return

        # Lazy import — only runs on first request
        _bootstrap()
        import asyncio
        from vg.main import analyze_async

        try:
            result = asyncio.run(
                analyze_async(question, use_enhanced=True, api_key=api_key)
            )
        except Exception as exc:
            error_msg = str(exc)
            if any(k in error_msg.lower() for k in ("auth", "unauthorized", "invalid")):
                self._json_response(401, {"error": "Invalid API key."})
            else:
                self._json_response(500, {"error": "Analysis failed.", "detail": error_msg})
            return

        self._json_response(200, {
            "question": question,
            "enhanced": True,
            "result": result,
        })

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

    def _json_response(self, status, payload):
        body = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)
