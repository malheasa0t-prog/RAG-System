# Setup and Operations Guide

This guide combines project context with the day-to-day setup steps in one place so the repository stays clear and easy to maintain.

## Project overview

The project is a RAG assistant for the Serva-S store. When a customer question arrives, the assistant retrieves relevant services, policies, and support scenarios from Supabase, builds grounded context, sends it to the selected model provider, and returns a guarded response.

## Repository components

| Path | Purpose |
|---|---|
| `scripts/app_config.py` | Loads `.env` and prepares shared runtime settings |
| `scripts/rag_core.py` | Retrieval logic, context building, guardrails, and final response flow |
| `scripts/llm_client.py` | Provider integration for Groq, OpenRouter, Neokens, and Ollama |
| `scripts/fill_*.py` | Loads services, policies, knowledge, and safety rules into storage |
| `scripts/chat_ai.py` | Lightweight CLI test entry point |
| `scripts/gradio_chat.py` | Local Gradio interface |
| `scripts/eval_test.py` | Smoke evaluation suite |
| `scripts/eval_test_extended.py` | Extended pre-release evaluation suite |

## Quick environment setup

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy the environment file:

   ```powershell
   copy .env.example .env
   ```

3. Fill the required values in `.env`:

   ```env
   SUPABASE_URL=...
   SUPABASE_KEY=...
   GOOGLE_API_KEY=...
   LLM_PROVIDER=neokens
   NEOKENS_API_KEY=...
   ```

## Database setup

Run the following file in the Supabase SQL editor:

```text
supabase_final_setup.sql
```

This script creates the required tables and functions for chat history, vector search, and safety rules.

If you only want to clear embeddings and rebuild them without dropping the tables, use:

```text
supabase_reset_embeddings.sql
```

## Loading knowledge

Run the following steps in order:

```powershell
python scripts\fill_safety_rules.py

$env:RESET_SERVICE_DOCUMENTS='true'; python scripts\fill_ai_pro.py; Remove-Item Env:RESET_SERVICE_DOCUMENTS
$env:RESET_POLICY_DOCUMENTS='true'; python scripts\fill_policies_ai.py; Remove-Item Env:RESET_POLICY_DOCUMENTS
$env:RESET_SCENARIO_DOCUMENTS='true'; python scripts\fill_scenarios_ai.py; Remove-Item Env:RESET_SCENARIO_DOCUMENTS

python scripts\fill_risk_scenarios.py
python scripts\fill_public_knowledge.py
```

## Local usage

Start the CLI chat:

```powershell
python scripts\chat_ai.py
```

Start the Gradio interface:

```powershell
python scripts\gradio_chat.py
```

## Evaluation

Run the smoke suite:

```powershell
python scripts\eval_test.py
```

Run the extended suite:

```powershell
python scripts\eval_test_extended.py
```

All generated reports are written to `reports/` and are intentionally excluded from Git.

## Operational notes

- Never commit `.env` to GitHub.
- Use `SUPABASE_KEY` on the backend only, never in a public frontend.
- If services, policies, or scenarios change, rerun the relevant loading scripts.
- After major logic or guardrail changes, run both evaluation suites before deployment.
