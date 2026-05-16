"""Public-safe repository checks for CI.

This script validates documentation and repository structure without requiring
private credentials or live API access.
"""

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ".env.example",
    ".gitignore",
    "README.md",
    "docs/setup-guide.md",
    "requirements.txt",
    "supabase_final_setup.sql",
    "supabase_reset_embeddings.sql",
    "scripts/app_config.py",
    "scripts/chat_ai.py",
    "scripts/eval_test.py",
    "scripts/eval_test_extended.py",
    "scripts/gradio_chat.py",
    "scripts/llm_client.py",
    "scripts/rag_core.py",
]

REQUIRED_ENV_KEYS = {
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "GOOGLE_API_KEY",
    "LLM_PROVIDER",
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "OPENROUTER_FALLBACK_MODEL",
    "NEOKENS_API_KEY",
    "NEOKENS_BASE_URL",
    "NEOKENS_MODEL",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "REQUEST_TIMEOUT",
    "GRADIO_SERVER_PORT",
}

REQUIRED_IGNORE_PATTERNS = {
    ".env",
    ".venv/",
    "reports/",
    "*.log",
    "*.rar",
}

REQUIRED_README_SNIPPETS = [
    "## Quick start",
    "## Evaluation",
    "scripts/repo_smoke_check.py",
]

REQUIRED_SETUP_GUIDE_SNIPPETS = [
    "## Quick environment setup",
    "## Database setup",
    "## Evaluation",
]


def parse_env_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def main() -> int:
    failures: list[str] = []

    for rel_path in REQUIRED_FILES:
        if not (ROOT_DIR / rel_path).exists():
            failures.append(f"Missing required file: {rel_path}")

    env_path = ROOT_DIR / ".env.example"
    env_keys = parse_env_keys(env_path)
    missing_env = sorted(REQUIRED_ENV_KEYS - env_keys)
    if missing_env:
        failures.append(
            ".env.example is missing required keys: " + ", ".join(missing_env)
        )

    gitignore_text = (ROOT_DIR / ".gitignore").read_text(encoding="utf-8")
    missing_ignore = sorted(
        pattern for pattern in REQUIRED_IGNORE_PATTERNS if pattern not in gitignore_text
    )
    if missing_ignore:
        failures.append(
            ".gitignore is missing expected ignore patterns: "
            + ", ".join(missing_ignore)
        )

    readme_text = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
    missing_readme = [
        snippet for snippet in REQUIRED_README_SNIPPETS if snippet not in readme_text
    ]
    if missing_readme:
        failures.append(
            "README.md is missing expected sections or references: "
            + ", ".join(missing_readme)
        )

    setup_guide_text = (ROOT_DIR / "docs" / "setup-guide.md").read_text(encoding="utf-8")
    missing_setup_guide = [
        snippet
        for snippet in REQUIRED_SETUP_GUIDE_SNIPPETS
        if snippet not in setup_guide_text
    ]
    if missing_setup_guide:
        failures.append(
            "docs/setup-guide.md is missing expected sections: "
            + ", ".join(missing_setup_guide)
        )

    if failures:
        print("Repository smoke check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Repository smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
