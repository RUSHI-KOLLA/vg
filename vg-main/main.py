"""
VG main entry point.

Web mode:
  python -m vg.main --web --port 8080
"""

import asyncio
import sys
import os

if __package__ in (None, ""):
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if PROJECT_ROOT in sys.path:
        sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

from vg.config import config

# Default to enhanced coordinator if available
try:
    from vg.core.enhanced_debate import EnhancedDebateCoordinator as DebateCoordinator
    ENHANCED_MODE = True
except ImportError:
    from vg.core.debate import DebateCoordinator
    ENHANCED_MODE = False


async def analyze_async(
    question: str,
    use_enhanced: bool = True,
    api_key: str = None,
    provider: str | None = None,
) -> dict:
    """Run the full VG analysis pipeline."""
    if use_enhanced and ENHANCED_MODE:
        coordinator = DebateCoordinator(
            enable_optimizations=True,
            api_key=api_key,
            provider=provider,
        )
    else:
        coordinator = DebateCoordinator()
    return await coordinator.run_full_pipeline(question)


def analyze(question: str, case_name: str = None, use_enhanced: bool = True) -> dict:
    """Synchronous wrapper for the VG pipeline."""
    from vg.setup import run_async
    return run_async(analyze_async(question, use_enhanced=use_enhanced))


def _consume_option(argv: list[str], option: str, default: str) -> str:
    """Pop an option and its value from argv if present."""
    if option not in argv:
        return default
    index = argv.index(option)
    try:
        value = argv[index + 1]
    except IndexError as exc:
        raise SystemExit(f"{option} requires a value.") from exc
    del argv[index:index + 2]
    return value


def run_web(argv: list[str]) -> None:
    """Run the browser-native web server."""
    # Ensure RAG database is built at startup if missing
    from vg.config import config
    db_path = config.chroma_db_path
    sqlite_file = os.path.join(db_path, "chroma.sqlite3")
    if not os.path.exists(sqlite_file):
        print(f"📁 ChromaDB sqlite file not found at {sqlite_file}. Building RAG database now...")
        try:
            from vg.rag.builder import build_all
            build_all()
        except Exception as e:
            print(f"❌ Failed to auto-build RAG database: {e}")

    host = _consume_option(argv, "--host", os.getenv("VG_HOST", "0.0.0.0"))
    port = int(_consume_option(argv, "--port", os.getenv("PORT", os.getenv("VG_PORT", "8080"))))
    from vg.api.server import run_server
    run_server(host=host, port=port)


if __name__ == "__main__":
    run_web(sys.argv[1:])
