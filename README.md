# Enterprise RAG-System

A high-performance Retrieval-Augmented Generation (RAG) pipeline built in Python, designed to serve as an intelligent backend assistant for e-commerce and retail platforms. The system intelligently retrieves contextual domain knowledge and grounds Large Language Model (LLM) responses to provide accurate, safe, and context-aware customer support.

## Architecture & Tech Stack
- **Core Framework:** Python, LangChain
- **Vector Database:** Supabase (`pgvector`) for efficient similarity search and high-dimensional embedding storage.
- **LLM Integrations:** Flexible multi-provider support architecture including Groq, OpenRouter, Neokens, and local Ollama models.
- **Security & Moderation:** Built-in semantic safeguards to filter out unsafe queries, malicious prompt injections, and off-topic requests.

## Key Features
- **Semantic Retrieval Pipeline:** Connects to a Supabase vector store to pull relevant policies, products, and FAQs based on user queries using cosine similarity.
- **Dynamic Context Injection:** Injects high-relevance text chunks into the LLM context window to eliminate hallucinations and ground responses.
- **Multi-LLM Routing:** Easily switch between different language models based on latency, cost, or availability constraints.
- **Policy Enforcement:** Validates inputs and outputs against predefined safety and policy rules before returning responses to the end-user.

## Getting Started

### Prerequisites
- Python 3.9+
- Supabase project with `pgvector` extension enabled
- API Keys for your preferred LLM provider (e.g., Groq, OpenAI)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/malheasa0t-prog/RAG-System.git
   cd RAG-System
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Environment Setup:
   Copy `.env.example` to `.env` and configure your Supabase credentials and LLM API keys.

### Usage
- Initialize and populate vector database embeddings (Run once):
  ```bash
  python scripts/fill_ai_pro.py
  python scripts/fill_policies_ai.py
  ```

- Start the CLI interactive testing interface:
  ```bash
  python scripts/chat_ai.py
  ```

- Start the Gradio Web UI for user interaction:
  ```bash
  python scripts/gradio_chat.py
  ```

## License
Distributed under the MIT License.
