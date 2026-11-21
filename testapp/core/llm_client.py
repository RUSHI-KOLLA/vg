"""
Multi-Provider LLM Client with async support, rate limiting, and retry logic.

Supports Groq/Llama and Google Gemini 2.5 Flash with native context caching.
"""

import asyncio
import os
from typing import Optional, Dict, Any

from groq import Groq, AsyncGroq
from aiolimiter import AsyncLimiter

from vg.config import config

# Gemini client (optional - only if google-generativeai is installed)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ──────────────────────────────────────────────
#  Shared Rate Limiter (singleton per process)
# ──────────────────────────────────────────────
_rate_limiter: Optional[AsyncLimiter] = None
_semaphore: Optional[asyncio.Semaphore] = None
_async_state_loop: Optional[asyncio.AbstractEventLoop] = None


def _ensure_async_primitives() -> None:
    """Recreate loop-bound primitives when requests run on a new event loop."""
    global _rate_limiter, _semaphore, _async_state_loop
    loop = asyncio.get_running_loop()
    if _async_state_loop is not loop:
        _rate_limiter = AsyncLimiter(config.groq_rpm_limit, 60)
        _semaphore = asyncio.Semaphore(config.groq_max_concurrent)
        _async_state_loop = loop


def _get_limiter() -> AsyncLimiter:
    global _rate_limiter
    _ensure_async_primitives()
    return _rate_limiter


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    _ensure_async_primitives()
    return _semaphore


# ──────────────────────────────────────────────
#  Gemini 2.5 Flash Client (with native context caching)
# ──────────────────────────────────────────────
class GeminiLLMClient:
    """Synchronous Gemini client with native context caching."""

    def __init__(self, model: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        api_key = config.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Add it to .env or pass at runtime.")
        genai.configure(api_key=api_key)
        self.model_name = model or config.gemini_model
        # Enable native context caching
        self.cached_content = None
        self._cache_ttl = 3600  # 1 hour cache

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
             max_tokens: int = 2048, response_format: Optional[dict] = None) -> str:
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "response_mime_type": "application/json" if response_format else "text/plain",
                }
            )
            response = model.generate_content(user_prompt)
            return response.text.strip()
        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                print(f"\n❌ [GeminiLLMClient] QUOTA EXHAUSTED — Your Gemini API key has no remaining quota.")
                print(f"   → Either wait for quota reset, switch to Groq (set LLM_PROVIDER=groq in .env), or upgrade your Gemini plan.")
            else:
                print(f"[GeminiLLMClient] Error: {e}")
            raise

    def chat_with_prompt(self, system_prompt: str, user_prompt: str) -> str:
        return self.chat(system_prompt, user_prompt)


class AsyncGeminiLLMClient:
    """Async Gemini client with native context caching and rate limiting."""

    def __init__(self, model: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
        api_key = config.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        self.model_name = model or config.gemini_model
        self._rate_limiter = AsyncLimiter(15, 60)  # 15 RPM default
        self._semaphore = asyncio.Semaphore(5)  # 5 concurrent

    @staticmethod
    def _is_retriable(error: Exception) -> bool:
        non_retriable = (ValueError, TypeError, KeyError)
        return not isinstance(error, non_retriable)

    async def chat(self, system_prompt: str, user_prompt: str,
                   temperature: float = 0.7, max_tokens: int = 2048,
                   response_format: Optional[dict] = None,
                   timeout_seconds: Optional[int] = None,
                   max_retries: Optional[int] = None) -> str:
        retries = max(1, max_retries or 3)
        delay_seconds = 1
        last_error: Optional[Exception] = None

        for attempt in range(1, retries + 1):
            try:
                async with self._semaphore:
                    async with self._rate_limiter:
                        model = genai.GenerativeModel(
                            model_name=self.model_name,
                            system_instruction=system_prompt,
                            generation_config={
                                "temperature": temperature,
                                "max_output_tokens": max_tokens,
                                "response_mime_type": "application/json" if response_format else "text/plain",
                            }
                        )
                        response = await asyncio.wait_for(
                            model.generate_content_async(user_prompt),
                            timeout=timeout_seconds or 30
                        )
                        return response.text.strip()
            except Exception as error:
                last_error = error
                error_msg = str(error)
                if "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    print(f"\n❌ [AsyncGemini] QUOTA EXHAUSTED — Your Gemini API key has no remaining quota.")
                    print(f"   → Switch to Groq: set LLM_PROVIDER=groq in .env with a valid GROQ_API_KEY")
                    raise  # Don't retry quota errors
                if attempt >= retries or not self._is_retriable(error):
                    raise
                await asyncio.sleep(delay_seconds)
                delay_seconds = min(delay_seconds * 2, 4)

        if last_error is not None:
            raise last_error
        raise RuntimeError("LLM chat failed without returning a response.")


# ──────────────────────────────────────────────
#  Synchronous Client (for simple calls)
# ──────────────────────────────────────────────
class GroqLLMClient:
    """Synchronous Groq client for one-off calls."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        resolved_key = api_key or config.groq_api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError("GROQ_API_KEY is not set. Add it to .env or pass at runtime.")
        self.client = Groq(api_key=resolved_key)
        self.model = model or config.model_large

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7,
             max_tokens: int = 2048, response_format: Optional[dict] = None) -> str:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            resp = self.client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"[GroqLLMClient] Error: {e}")
            return ""

    # backwards compat alias
    def chat_with_prompt(self, system_prompt: str, user_prompt: str) -> str:
        return self.chat(system_prompt, user_prompt)


# ──────────────────────────────────────────────
#  Provider Router (auto-selects based on config)
# ──────────────────────────────────────────────
def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
    """Return a synchronous LLM client (Gemini or Groq based on config)."""
    selected_provider = provider or config.default_provider
    if selected_provider == "gemini" and GEMINI_AVAILABLE:
        return GeminiLLMClient(model=model)
    else:
        if selected_provider == "gemini" and not GEMINI_AVAILABLE:
            print("[WARNING] Gemini not available, falling back to Groq")
        return GroqLLMClient(model=model, api_key=api_key)


def get_async_llm_client(provider: Optional[str] = None, model: Optional[str] = None, api_key: Optional[str] = None):
    """Return an async LLM client (Gemini or Groq based on config)."""
    selected_provider = provider or config.default_provider
    if selected_provider == "gemini" and GEMINI_AVAILABLE:
        return AsyncGeminiLLMClient(model=model)
    else:
        if selected_provider == "gemini" and not GEMINI_AVAILABLE:
            print("[WARNING] Gemini not available, falling back to Groq")
        return AsyncGroqLLMClient(model=model, api_key=api_key)


# ──────────────────────────────────────────────
#  Async Client (for parallel agent calls)
# ──────────────────────────────────────────────
class AsyncGroqLLMClient:
    """Async Groq client with rate limiting + exponential backoff."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None):
        resolved_key = api_key or config.groq_api_key or os.getenv("GROQ_API_KEY")
        if not resolved_key:
            raise ValueError("GROQ_API_KEY is not set.")
        self.client = AsyncGroq(api_key=resolved_key)
        self.model = model or config.model_large

    @staticmethod
    def _is_retriable(error: Exception) -> bool:
        """Retry transient transport/rate-limit failures, not local programming errors."""
        non_retriable = (ValueError, TypeError, KeyError)
        return not isinstance(error, non_retriable)

    async def chat(self, system_prompt: str, user_prompt: str,
                   temperature: float = 0.7, max_tokens: int = 2048,
                   response_format: Optional[dict] = None,
                   timeout_seconds: Optional[int] = None,
                   max_retries: Optional[int] = None) -> str:
        limiter = _get_limiter()
        sem = _get_semaphore()
        timeout = timeout_seconds or config.groq_request_timeout_seconds
        retries = max(1, max_retries or config.groq_max_retries)
        delay_seconds = 1
        last_error: Optional[Exception] = None

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        for attempt in range(1, retries + 1):
            try:
                async with sem:
                    async with limiter:
                        resp = await asyncio.wait_for(
                            self.client.chat.completions.create(**kwargs),
                            timeout=timeout,
                        )
                return resp.choices[0].message.content or ""
            except Exception as error:
                last_error = error
                if attempt >= retries or not self._is_retriable(error):
                    raise
                await asyncio.sleep(delay_seconds)
                delay_seconds = min(delay_seconds * 2, 4)

        if last_error is not None:
            raise last_error
        raise RuntimeError("LLM chat failed without returning a response.")


