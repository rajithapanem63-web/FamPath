# Spec: RAG Chatbot — Tasks

### TASK-RAG-01: Knowledge base models + pgvector migration
- `KnowledgeDocument`, `DocumentChunk`, `ChatSession`, `ChatMessage` models
- Migration: enable pgvector extension, create tables with ivfflat and GIN indexes

### TASK-RAG-02: Document ingestion Celery task
- Chunk documents (500-token chunks, 50-token overlap)
- Generate embeddings (configurable provider)
- Store chunks with tsvector for BM25
- Unit tests: chunking, embedding mock

### TASK-RAG-03: Hybrid retrieval service
- Vector similarity + BM25 search + Reciprocal Rank Fusion
- `RetrievalService.retrieve(query, top_k=5) -> list[Chunk]`
- Unit tests: known query → expected chunk set (deterministic with seed data)

### TASK-RAG-04: LLM provider abstraction + Anthropic implementation
- `LLMProvider` Protocol
- `AnthropicProvider` with retry/timeout
- `MockProvider` for tests
- Unit tests: mock provider returns expected structure

### TASK-RAG-05: RAG pipeline service
- Assemble context, build prompt, call LLM, parse response, validate citations
- `CitationMissingError` → refused response
- PII token replacement before LLM call
- Tests: citation validation, refusal on low retrieval score, PII not in prompt

### TASK-RAG-06: Chat API endpoints
- Session create, message send, history get
- Consent gate enforcement
- Language detection and response routing
- Tests: consent gate, full message flow, refused response

### TASK-RAG-07: Admin document upload + embed endpoints
- Document upload + metadata
- Embed job endpoint (Celery)
- Tests: upload, embed job creation

### TASK-RAG-08: Seed knowledge documents + eval dataset
- 4 synthetic .txt documents
- `backend/tests/rag/eval_pairs.json` (50 pairs)
- `scripts/eval_rag.py` evaluation script

### TASK-FE-RAG-01: Chatbot UI
- Floating chat bubble (collapsible panel)
- Message thread with citation chips
- Consent modal (first use)
- Language selector within chat
- Refused response styling ("I don't have enough information...")
- i18n all strings
