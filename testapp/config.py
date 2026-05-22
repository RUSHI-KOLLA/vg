"""VG Configuration — loads from .env or environment variables."""

from dataclasses import dataclass, field
from typing import Optional
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # --- API Keys (BYOK) ---
    groq_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # --- Model Selection ---
    model_large: str = "llama-3.3-70b-versatile"
    model_small: str = "llama-3.1-8b-instant"
    # Gemini 2.5 Flash with native context caching
    gemini_model: str = "gemini-2.0-flash"
    # Provider: 'gemini' or 'groq'
    default_provider: str = "gemini"

    # --- Rate Limiting ---
    groq_rpm_limit: int = 15
    groq_max_concurrent: int = 5
    groq_request_timeout_seconds: int = 18
    groq_shadow_timeout_seconds: int = 12
    groq_max_retries: int = 2

    # --- Generation ---
    temperature: float = 0.7
    max_tokens: int = 2048
    shadow_max_tokens: int = 96
    agent_max_tokens: int = 640
    judge_max_tokens: int = 512

    # --- RAG ---
    chroma_db_path: str = "./chroma_db"
    rag_top_k: int = 2          # chunks per personality
    rag_chunk_words: int = 300

    # --- Debate ---
    max_debate_rounds: int = 2
    convergence_threshold: float = 0.8   # 80% agreement → early exit
    judge_consistency_runs: int = 3

    # --- Search ---
    disable_web_search: bool = False


def get_config() -> Config:
    """Build config from environment."""
    return Config(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        model_large=os.getenv("GROQ_MODEL_LARGE", "llama-3.3-70b-versatile"),
        model_small=os.getenv("GROQ_MODEL_SMALL", "llama-3.1-8b-instant"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        default_provider=os.getenv("LLM_PROVIDER", "gemini"),
        groq_rpm_limit=int(os.getenv("GROQ_RPM_LIMIT", "15")),
        groq_max_concurrent=int(os.getenv("GROQ_MAX_CONCURRENT", "5")),
        groq_request_timeout_seconds=int(os.getenv("GROQ_REQUEST_TIMEOUT_SECONDS", "18")),
        groq_shadow_timeout_seconds=int(os.getenv("GROQ_SHADOW_TIMEOUT_SECONDS", "12")),
        groq_max_retries=int(os.getenv("GROQ_MAX_RETRIES", "2")),
        temperature=float(os.getenv("VG_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("VG_MAX_TOKENS", "2048")),
        shadow_max_tokens=int(os.getenv("VG_SHADOW_MAX_TOKENS", "96")),
        agent_max_tokens=int(os.getenv("VG_AGENT_MAX_TOKENS", "640")),
        judge_max_tokens=int(os.getenv("VG_JUDGE_MAX_TOKENS", "512")),
        chroma_db_path=os.getenv("VG_CHROMA_PATH", "./chroma_db"),
        rag_top_k=int(os.getenv("VG_RAG_TOP_K", "2")),
        rag_chunk_words=int(os.getenv("VG_RAG_CHUNK_WORDS", "300")),
        max_debate_rounds=int(os.getenv("VG_MAX_DEBATE_ROUNDS", "2")),
        convergence_threshold=float(os.getenv("VG_CONVERGENCE_THRESHOLD", "0.8")),
        judge_consistency_runs=int(os.getenv("VG_JUDGE_CONSISTENCY_RUNS", "3")),
        disable_web_search=os.getenv("VG_DISABLE_WEB_SEARCH", "").lower() in {"1", "true", "yes", "on"},
    )


config = get_config()
