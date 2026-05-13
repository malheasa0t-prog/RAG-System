"""Helpers shared by scripts that build Supabase embeddings."""

from __future__ import annotations

import re
import time

import requests
from langchain_google_genai import GoogleGenerativeAIEmbeddings

try:
    from .app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL
except ImportError:
    from app_config import HEADERS, REQUEST_TIMEOUT, SUPABASE_URL


embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")


def extract_retry_delay(message: str) -> int | None:
    """Read Google quota retry time when the error message includes it."""
    match = re.search(r"retryDelay': '(\d+)s", message)
    if match:
        return int(match.group(1))

    match = re.search(r"retry in ([0-9.]+)s", message, re.IGNORECASE)
    if match:
        return int(float(match.group(1))) + 1

    return None


def embed_with_retry(
    text: str,
    label: str = "",
    max_attempts: int = 3,
    fallback_wait_seconds: int = 15,
):
    """Create one embedding and wait/retry when Google temporarily rate-limits us."""
    for attempt in range(1, max_attempts + 1):
        try:
            return embeddings_model.embed_query(text)
        except Exception as exc:
            message = str(exc)
            quota_error = "429" in message or "RESOURCE_EXHAUSTED" in message
            if not quota_error:
                raise

            wait_time = extract_retry_delay(message) or (fallback_wait_seconds * attempt)
            prefix = f"{label} " if label else ""
            print(f"  ⏳ {prefix}حصة Google Embeddings ممتلئة. انتظار {wait_time}ث...")
            if attempt == max_attempts:
                raise RuntimeError("Google Embeddings quota exhausted. حاول لاحقًا أو استخدم مفتاحًا آخر.") from exc
            time.sleep(wait_time)


def delete_legacy_documents(content_prefix: str, label: str) -> None:
    """Delete old rows from ai_documents by a safe content prefix."""
    response = requests.delete(
        f"{SUPABASE_URL}/rest/v1/ai_documents",
        headers=HEADERS,
        params={"content": f"like.{content_prefix}*"},
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code not in {200, 204}:
        raise RuntimeError(f"تعذر حذف {label}: {response.text[:500]}")


def insert_legacy_document(content: str, embedding) -> requests.Response:
    """Insert one row into the older ai_documents vector table."""
    return requests.post(
        f"{SUPABASE_URL}/rest/v1/ai_documents",
        headers=HEADERS,
        json={"content": content, "embedding": embedding},
        timeout=REQUEST_TIMEOUT,
    )
