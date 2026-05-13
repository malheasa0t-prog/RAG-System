"""Small LLM provider layer.

The project can use either:
- Groq through langchain_groq
- OpenRouter through its OpenAI-compatible HTTP API
- Neokens through its OpenAI-compatible HTTP API
- Ollama for local models such as llama3.2 or gemma

Keeping this in one file makes the rest of the project easier to read.
"""

from __future__ import annotations

import requests
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

try:
    from .app_config import (
        GROQ_HELPER_MODEL,
        GROQ_MODEL,
        LLM_PROVIDER,
        NEOKENS_API_KEY,
        NEOKENS_BASE_URL,
        NEOKENS_HELPER_MODEL,
        NEOKENS_MODEL,
        NEOKENS_REQUEST_TIMEOUT,
        OLLAMA_BASE_URL,
        OLLAMA_HELPER_MODEL,
        OLLAMA_MODEL,
        OLLAMA_NUM_CTX,
        OLLAMA_REQUEST_TIMEOUT,
        OPENROUTER_API_KEY,
        OPENROUTER_APP_NAME,
        OPENROUTER_FALLBACK_MODEL,
        OPENROUTER_HELPER_MODEL,
        OPENROUTER_MODEL,
        OPENROUTER_SITE_URL,
        REQUEST_TIMEOUT,
        require_runtime_secrets,
    )
except ImportError:
    from app_config import (
        GROQ_HELPER_MODEL,
        GROQ_MODEL,
        LLM_PROVIDER,
        NEOKENS_API_KEY,
        NEOKENS_BASE_URL,
        NEOKENS_HELPER_MODEL,
        NEOKENS_MODEL,
        NEOKENS_REQUEST_TIMEOUT,
        OLLAMA_BASE_URL,
        OLLAMA_HELPER_MODEL,
        OLLAMA_MODEL,
        OLLAMA_NUM_CTX,
        OLLAMA_REQUEST_TIMEOUT,
        OPENROUTER_API_KEY,
        OPENROUTER_APP_NAME,
        OPENROUTER_FALLBACK_MODEL,
        OPENROUTER_HELPER_MODEL,
        OPENROUTER_MODEL,
        OPENROUTER_SITE_URL,
        REQUEST_TIMEOUT,
        require_runtime_secrets,
    )


_groq_main = None
_groq_helper = None


def _get_groq_model(helper: bool = False):
    global _groq_main, _groq_helper

    if helper:
        if _groq_helper is None:
            _groq_helper = ChatGroq(model_name=GROQ_HELPER_MODEL, temperature=0.0)
        return _groq_helper

    if _groq_main is None:
        _groq_main = ChatGroq(model_name=GROQ_MODEL, temperature=0.0)
    return _groq_main


def _message_to_dict(message) -> dict:
    if isinstance(message, SystemMessage):
        role = "system"
    elif isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, HumanMessage):
        role = "user"
    else:
        role = getattr(message, "role", "user")

    return {"role": role, "content": str(message.content)}


def _openrouter_request(model: str, messages: list) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": OPENROUTER_SITE_URL,
        "X-Title": OPENROUTER_APP_NAME,
    }
    payload = {
        "model": model,
        "messages": [_message_to_dict(message) for message in messages],
        "temperature": 0,
    }
    return requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )


def _openrouter_chat(messages: list, helper: bool = False) -> str:
    model = OPENROUTER_HELPER_MODEL if helper else OPENROUTER_MODEL
    response = _openrouter_request(model, messages)

    if response.status_code == 429 and model != OPENROUTER_FALLBACK_MODEL:
        print(f"⚠️ OpenRouter model is rate-limited; falling back to {OPENROUTER_FALLBACK_MODEL}.")
        response = _openrouter_request(OPENROUTER_FALLBACK_MODEL, messages)

    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text[:1000]}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def _neokens_request(model: str, messages: list) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {NEOKENS_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [_message_to_dict(message) for message in messages],
        "temperature": 0,
    }
    return requests.post(
        f"{NEOKENS_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=NEOKENS_REQUEST_TIMEOUT,
    )


def _neokens_chat(messages: list, helper: bool = False) -> str:
    model = NEOKENS_HELPER_MODEL if helper else NEOKENS_MODEL
    response = _neokens_request(model, messages)

    if response.status_code != 200:
        raise RuntimeError(f"Neokens error {response.status_code}: {response.text[:1000]}")

    data = response.json()
    return data["choices"][0]["message"]["content"]


def _ollama_chat(messages: list, helper: bool = False) -> str:
    model = OLLAMA_HELPER_MODEL if helper else OLLAMA_MODEL
    payload = {
        "model": model,
        "messages": [_message_to_dict(message) for message in messages],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": OLLAMA_NUM_CTX,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=OLLAMA_REQUEST_TIMEOUT,
        )
    except requests.ConnectionError as exc:
        raise RuntimeError(
            "Ollama is not running. Start Ollama, then run: "
            f"ollama pull {model}"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(f"Ollama error {response.status_code}: {response.text[:1000]}")

    data = response.json()
    return data["message"]["content"]


def chat_text(messages: list, helper: bool = False) -> str:
    """Return model text from the configured provider."""
    require_runtime_secrets(require_google=False)

    if LLM_PROVIDER == "ollama":
        return _ollama_chat(messages, helper=helper)

    if LLM_PROVIDER == "openrouter":
        return _openrouter_chat(messages, helper=helper)

    if LLM_PROVIDER == "neokens":
        return _neokens_chat(messages, helper=helper)

    if LLM_PROVIDER == "groq":
        response = _get_groq_model(helper=helper).invoke(messages)
        return response.content

    raise RuntimeError(
        f"Unsupported LLM_PROVIDER={LLM_PROVIDER!r}. Use 'groq', 'openrouter', 'neokens', or 'ollama'."
    )


def current_model_name(helper: bool = False) -> str:
    if LLM_PROVIDER == "ollama":
        return OLLAMA_HELPER_MODEL if helper else OLLAMA_MODEL
    if LLM_PROVIDER == "openrouter":
        return OPENROUTER_HELPER_MODEL if helper else OPENROUTER_MODEL
    if LLM_PROVIDER == "neokens":
        return NEOKENS_HELPER_MODEL if helper else NEOKENS_MODEL
    if LLM_PROVIDER == "groq":
        return GROQ_HELPER_MODEL if helper else GROQ_MODEL
    return LLM_PROVIDER
