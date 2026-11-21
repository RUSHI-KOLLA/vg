"""Minimal web server for the VG browser interface.

Production-ready for public SaaS hosting:
- API keys are provided per-request via X-API-Key header (never stored on server)
- CORS enabled for cross-origin access
- No server-side key storage for multi-user safety
"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from vg.main import analyze_async
from vg.config import config


STATIC_DIR = Path(__file__).resolve().parent / "static"


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


class VGWebHandler(BaseHTTPRequestHandler):
    """Serve the browser UI and analysis API."""

    server_version = "VGWeb/2.0"

    # ─── CORS ───────────────────────────────────────────────────────
    def _send_cors_headers(self) -> None:
        """Add CORS headers to every response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")

    def do_OPTIONS(self) -> None:  # noqa: N802
        """Handle CORS preflight requests."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    # ─── GET ────────────────────────────────────────────────────────
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path in {"/", "/index.html"}:
            self._serve_file(STATIC_DIR / "index.html")
            return

        if parsed.path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "service": "vg-web",
                    "version": "2.0",
                    "mode": "saas",
                },
            )
            return

        if parsed.path.startswith("/static/"):
            rel_path = parsed.path.removeprefix("/static/").strip("/")
            file_path = (STATIC_DIR / rel_path).resolve()
            if STATIC_DIR not in file_path.parents and file_path != STATIC_DIR:
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "Forbidden"})
                return
            self._serve_file(file_path)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    # ─── POST ───────────────────────────────────────────────────────
    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/analyze":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        # Extract API key from header (per-request, never stored)
        api_key = self.headers.get("X-API-Key", "").strip()
        if not api_key:
            self._send_json(
                HTTPStatus.UNAUTHORIZED,
                {
                    "error": "API key required.",
                    "hint": "Send your Groq API key in the X-API-Key header.",
                },
            )
            return

        try:
            payload = self._read_json_body()
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        question = str(payload.get("question", "")).strip()
        use_enhanced = bool(payload.get("enhanced", True))

        if not question:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Question is required."})
            return

        try:
            result = asyncio.run(
                analyze_async(question, use_enhanced=use_enhanced, api_key=api_key)
            )
        except Exception as exc:  # pragma: no cover - runtime protection
            error_msg = str(exc)
            # Detect invalid API key errors
            if "auth" in error_msg.lower() or "unauthorized" in error_msg.lower() or "invalid" in error_msg.lower():
                self._send_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"error": "Invalid API key. Please check your Groq API key."},
                )
            else:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {
                        "error": "Analysis failed.",
                        "detail": error_msg,
                    },
                )
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "question": question,
                "enhanced": use_enhanced,
                "result": result,
            },
        )

    # ─── Helpers ────────────────────────────────────────────────────
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        """Keep request logging concise. Never log API keys."""
        print(f"[vg-web] {self.address_string()} - {format % args}")

    def _read_json_body(self) -> dict[str, Any]:
        content_length = self.headers.get("Content-Length")
        if not content_length:
            raise ValueError("Missing request body.")

        try:
            body_size = int(content_length)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length.") from exc

        raw_body = self.rfile.read(body_size)
        if not raw_body:
            raise ValueError("Empty request body.")

        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Cache-Control", "no-cache")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(file_path.read_bytes())

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    """Start the threaded VG web server."""
    print(f"  Mode: Public SaaS (per-request API keys)")
    print(f"  Server: VGWeb/2.0")

    # Check for fallback server-side key (for CLI mode)
    server_key = config.groq_api_key or os.getenv("GROQ_API_KEY")
    if server_key:
        print(f"  Server fallback key: ✓ configured (for CLI)")
    else:
        print(f"  Server fallback key: ✗ not set (web users must provide their own)")

    tavily_key = config.tavily_api_key
    if tavily_key and "your" not in tavily_key.lower():
        print(f"  Tavily key: ✓ configured")
    else:
        print(f"  Tavily key: ✗ not set (web search disabled)")

    server = ThreadingHTTPServer((host, port), VGWebHandler)
    print(f"\nVG web interface running at http://{host}:{port}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping VG web interface...")
    finally:
        server.server_close()
