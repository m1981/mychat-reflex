<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This is the Level 0 (30-second) onboarding document. It establishes the "Ubiquitous Language" and strict architectural boundaries for the entire project.
CONTENTS: Executive summary, domain dictionary, and the exact repository structure.
DO'S:
- DO strictly enforce the vocabulary defined here across all code, variables, and other documentation.
- DO respect the Vertical Slice Architecture. Code for a feature belongs in `src/features/[feature_name]/`, not in global horizontal folders.
- DO read `docs/execution-plan.md` before writing any code.
DON'TS:
- DO NOT invent synonyms in the codebase (e.g., if this file says "Message", do not use "ChatBubble" in the code).
- DO NOT create horizontal layers at the root of `src/` (e.g., no `src/models/` or `src/controllers/`).
-->

# 🚀 Project Overview & Domain Dictionary

## 1. Executive Summary
A commercial-grade, ChatGPT-like application featuring advanced Retrieval-Augmented Generation (RAG), semantic search, and a built-in knowledge base for note-taking. It utilizes asynchronous SSE streaming and a highly decoupled architecture to allow seamless migration between AI providers (e.g., OpenAI to Anthropic, ChromaDB to Voyage AI).

## 2. Ubiquitous Language (The Dictionary)
*   **Conversation**: The aggregate root representing a single chat session. Contains a list of Messages.
*   **Message**: A single turn in a conversation. Must have a `role` (user, assistant, system).
*   **DocumentChunk**: A piece of text extracted from a source, embedded, and stored in the Vector Store for RAG.
*   **Note**: A user-saved highlight or piece of knowledge, optionally linked to a `source_message_id`.
*   **StreamEvent**: A structured JSON object yielded during SSE streaming (e.g., `sources_found`, `content_chunk`).
*   **PromptBuilder**: A pure domain service responsible for formatting history and context into the final array sent to the LLM.

## 3. Strict Repository Structure
The codebase strictly follows **Vertical Slice Architecture**. Do not deviate from this tree.

```text
/
├── docs/                           ← Project Documentation
│   ├── .templates/                 ← LLM instruction templates
│   ├── 00-START-HERE.md            ← You are here
│   ├── execution-plan.md           ← Active sprint tracker & AI prompt driver
│   ├── /1-product-specs            ← Feature requirements (The "What")
│   ├── /2-architecture             ← Component contracts (The "How")
│   ├── /3-reference                ← API/DB schemas (The "Truth")
│   └── /4-decisions                ← Architecture Decision Records (ADRs)
│
├── src/                            ← Source Code
│   ├── core/                       ← Shared infrastructure & pure domain
│   │   ├── config/                 
│   │   ├── database/               ← SQLAlchemy setup
│   │   └── domain/                 ← Shared interfaces (IVectorStore, ILLMService)
│   │
│   ├── features/                   ← THE VERTICAL SLICES
│   │   ├── chat/                   ← Domain: Conversations & LLM Streaming
│   │   ├── knowledge_base/         ← Domain: Notes & Highlights
│   │   └── rag_engine/             ← Domain: Search & Indexing
│   │
│   └── main.py                     ← FastAPI application entry point
│
└── tests/                          ← 3-Tier Integration Testing
    ├── integration/                ← FastAPI TestClient + Fake LLMs
    └── e2e/                        
```

## 4. High-Level System Context
*   **Frontend/UI:** [Reflex]
*   **Backend/API:** Relex fastAPI (Async-first, SSE for streaming)
*   **Primary Storage:** SQLite (via SQLAlchemy)
*   **Vector Storage:** ChromaDB (Local) -> Migrating to Voyage AI
*   **LLM Provider:** OpenAI / Anthropic / Local (via strict `ILLMService` interface)

