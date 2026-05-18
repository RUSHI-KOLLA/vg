"""
Shared setup utilities — BYOK (Bring Your Own Key) for API keys.
"""

import os
import sys
import getpass
from dotenv import load_dotenv

load_dotenv()

from vg.config import config


def byok_setup(interactive: bool = True) -> bool:
    """
    Check for API keys, prompt if missing.
    
    Args:
        interactive: If True, prompts user for input. If False, only checks env vars.
    
    Returns:
        True if all required keys are available, False otherwise.
    """
    has_groq = bool(os.getenv("GROQ_API_KEY") or config.groq_api_key)
    has_tavily = config.disable_web_search or bool(os.getenv("TAVILY_API_KEY") or config.tavily_api_key)

    if not interactive:
        return has_groq

    if not has_groq:
        key = getpass.getpass("🔑 Enter your Groq API key (or press Enter to skip): ").strip()
        if key:
            os.environ["GROQ_API_KEY"] = key
            config.groq_api_key = key
            has_groq = True

    if not has_tavily:
        key = getpass.getpass("🔑 Enter your Tavily API key (or press Enter to skip): ").strip()
        if key:
            os.environ["TAVILY_API_KEY"] = key
            config.tavily_api_key = key
            has_tavily = True

    return has_groq


def byok_setup_rich(console=None) -> bool:
    """
    Rich-enabled BYOK setup (for CLI with Rich formatting).
    
    Returns:
        True if GROQ_API_KEY is available (required), False otherwise.
    """
    has_groq = bool(os.getenv("GROQ_API_KEY") or config.groq_api_key)
    has_tavily = config.disable_web_search or bool(os.getenv("TAVILY_API_KEY") or config.tavily_api_key)

    if not console:
        from rich.console import Console
        console = Console()

    if not has_groq:
        key = getpass.getpass("🔑 Groq API Key: ").strip()
        if key:
            os.environ["GROQ_API_KEY"] = key
            config.groq_api_key = key
        else:
            console.print("[red]⚠ Groq API key required for LLM calls.[/red]")
            sys.exit(1)

    if config.disable_web_search:
        console.print("[dim]  Web search disabled by configuration.[/dim]")
    elif not has_tavily:
        key = getpass.getpass("🔑 Tavily API Key (Enter to skip): ").strip()
        if key:
            os.environ["TAVILY_API_KEY"] = key
            config.tavily_api_key = key
        else:
            console.print("[dim]  Tavily skipped — web search disabled.[/dim]")

    return True


def byok_require_groq() -> None:
    """Ensure GROQ_API_KEY is set, raise if not."""
    if not os.getenv("GROQ_API_KEY") and not config.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set. Add to .env or provide at runtime.")


def run_async(coro):
    """
    Run an async coroutine safely.
    
    Handles RuntimeError if already in async context (e.g., in Jupyter).
    Falls back to using asyncio.get_event_loop() in that case.
    """
    import asyncio
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
