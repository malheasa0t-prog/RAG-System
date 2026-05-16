# Serva-S RAG Assistant

This repository contains the backend-side RAG assistant used to answer store questions for Serva-S. It retrieves store services, policies, safety rules, and support guidance from Supabase, then builds grounded replies through the configured LLM provider.

The project is intentionally small and operational: one codebase for ingestion, retrieval, local testing, and evaluation.

## What the project does

- Stores structured knowledge and embeddings in Supabase.
- Retrieves relevant service and policy context per question.
- Applies store-specific guardrails before returning the final answer.
- Supports multiple providers: Groq, OpenRouter, Neokens, and local Ollama.
- Includes local chat entry points plus smoke and extended evaluation scripts.

## Repository layout

| Path | Purpose |
|---|---|
| `scripts/rag_core.py` | Main RAG flow, retrieval, guardrails, and response assembly |
| `scripts/llm_client.py` | Provider routing for Groq, OpenRouter, Neokens, and Ollama |
| `scripts/app_config.py` | Shared environment loading and runtime configuration |
| `scripts/fill_*.py` | Data-loading scripts for services, policies, scenarios, and safety rules |
| `scripts/chat_ai.py` | Simple CLI chat for local testing |
| `scripts/gradio_chat.py` | Local Gradio interface |
| `scripts/eval_test.py` | Smoke evaluation suite |
| `scripts/eval_test_extended.py` | Extended acceptance evaluation suite |
| `supabase_final_setup.sql` | Supabase schema and function setup |
| `supabase_reset_embeddings.sql` | Optional reset script for embeddings only |
| `docs/setup-guide.md` | Detailed setup and operations guide |

## Quick start

1. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy the example environment file and fill in private values.

   ```powershell
   copy .env.example .env
   ```

3. Run `supabase_final_setup.sql` in the Supabase SQL editor.

4. Load the knowledge base.

   ```powershell
   python scripts\fill_safety_rules.py

   $env:RESET_SERVICE_DOCUMENTS='true'; python scripts\fill_ai_pro.py; Remove-Item Env:RESET_SERVICE_DOCUMENTS
   $env:RESET_POLICY_DOCUMENTS='true'; python scripts\fill_policies_ai.py; Remove-Item Env:RESET_POLICY_DOCUMENTS
   $env:RESET_SCENARIO_DOCUMENTS='true'; python scripts\fill_scenarios_ai.py; Remove-Item Env:RESET_SCENARIO_DOCUMENTS

   python scripts\fill_risk_scenarios.py
   python scripts\fill_public_knowledge.py
   ```

5. Start a local interface.

   ```powershell
   python scripts\chat_ai.py
   ```

   or

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

Evaluation output is written to `reports/`, which is intentionally ignored by Git.

## Notes

- Do not commit `.env` or service-role keys.
- The service-role key belongs on the backend only.
- Generated reports, logs, archives, and local experiments are excluded from version control.
- A more detailed English setup guide is available in [docs/setup-guide.md](docs/setup-guide.md).
