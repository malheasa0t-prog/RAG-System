"""Shared runtime configuration for the Serva-S RAG assistant."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
REPORTS_DIR = ROOT_DIR / "reports"

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _load_env_file(path: Path = ENV_PATH) -> None:
    """Load simple KEY=VALUE pairs without adding a runtime dependency."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


_load_env_file()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://tvupqsxaufbcmeobvhqj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
NEOKENS_API_KEY = os.getenv("NEOKENS_API_KEY", "")

if GOOGLE_API_KEY:
    os.environ.setdefault("GOOGLE_API_KEY", GOOGLE_API_KEY)
if GROQ_API_KEY:
    os.environ.setdefault("GROQ_API_KEY", GROQ_API_KEY)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

REQUEST_TIMEOUT = _env_int("REQUEST_TIMEOUT", 30)
GRADIO_SHARE = _env_bool("GRADIO_SHARE", False)
GRADIO_SERVER_NAME = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
GRADIO_SERVER_PORT = _env_int("GRADIO_SERVER_PORT", 7860)

RESET_SERVICE_DOCUMENTS = _env_bool("RESET_SERVICE_DOCUMENTS", False)
RESET_POLICY_DOCUMENTS = _env_bool("RESET_POLICY_DOCUMENTS", False)
RESET_SCENARIO_DOCUMENTS = _env_bool("RESET_SCENARIO_DOCUMENTS", False)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_HELPER_MODEL = os.getenv("GROQ_HELPER_MODEL", "llama-3.1-8b-instant")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "qwen/qwen3-next-80b-a3b-instruct:free",
)
OPENROUTER_HELPER_MODEL = os.getenv(
    "OPENROUTER_HELPER_MODEL",
    OPENROUTER_MODEL,
)
OPENROUTER_FALLBACK_MODEL = os.getenv("OPENROUTER_FALLBACK_MODEL", "openrouter/free")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "https://serva-s.com")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Serva-S RAG Assistant")

NEOKENS_BASE_URL = os.getenv("NEOKENS_BASE_URL", "https://api.neokens.com/v1").rstrip("/")
NEOKENS_MODEL = os.getenv("NEOKENS_MODEL", "gemini-3.1-pro-low")
NEOKENS_HELPER_MODEL = os.getenv("NEOKENS_HELPER_MODEL", NEOKENS_MODEL)
NEOKENS_REQUEST_TIMEOUT = _env_int("NEOKENS_REQUEST_TIMEOUT", 120)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HELPER_MODEL = os.getenv("OLLAMA_HELPER_MODEL", OLLAMA_MODEL)
OLLAMA_NUM_CTX = _env_int("OLLAMA_NUM_CTX", 8192)
OLLAMA_REQUEST_TIMEOUT = _env_int("OLLAMA_REQUEST_TIMEOUT", 120)


def require_runtime_secrets(
    require_google: bool = True,
    require_groq: bool | None = None,
    require_openrouter: bool | None = None,
    require_neokens: bool | None = None,
    require_supabase: bool = True,
) -> None:
    """Fail fast when a runnable script is missing required private values."""
    missing = []
    if require_supabase and not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if require_google and not GOOGLE_API_KEY:
        missing.append("GOOGLE_API_KEY")
    if require_groq is None:
        require_groq = LLM_PROVIDER == "groq"
    if require_openrouter is None:
        require_openrouter = LLM_PROVIDER == "openrouter"
    if require_neokens is None:
        require_neokens = LLM_PROVIDER == "neokens"

    if require_groq and not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if require_openrouter and not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if require_neokens and not NEOKENS_API_KEY:
        missing.append("NEOKENS_API_KEY")

    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Missing required environment variable(s): {names}. "
            "Copy .env.example to .env and add your private values."
        )
