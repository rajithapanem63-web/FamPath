# Spec: RAG Chatbot — Requirements

## Overview
A multilingual, grounded chatbot that answers questions about colleges, counselling rules, and documents with mandatory source citations.

## User Stories
- US-CHAT-01: As a user, I can ask questions in English, Telugu, or Hindi and receive answers in the same language.
- US-CHAT-02: As a user, every answer I receive cites the source document and year it is drawn from.
- US-CHAT-03: As a user, when the chatbot cannot find a reliable answer, it says so clearly rather than guessing.
- US-CHAT-04: As a user, I can ask about specific colleges, branches, counselling procedures, and document requirements.
- US-CHAT-05: As a user, I must consent before the chatbot feature is activated (data sent to external LLM API).
- US-CHAT-06: As an admin, I can upload knowledge-base documents (PDF, text) that the chatbot can retrieve.

## Acceptance Criteria

### Grounding & Citations
- EVERY chatbot response that contains a factual claim MUST include at least one citation with source name and year.
- WHEN the retrieval step returns no relevant chunks (score < threshold), THEN the chatbot MUST respond: "I don't have sufficient information to answer that reliably."
- WHERE a user asks an out-of-scope question (e.g., general knowledge), the chatbot MUST politely decline and redirect to its supported topics.

### Multilingual
- WHEN a user asks in Telugu, THEN the response is in Telugu.
- WHEN a user asks in Hindi, THEN the response is in Hindi.
- Language detection is automatic; user can also explicitly set language.

### Consent
- WHERE a user has not given chatbot consent, THEN `POST /api/v1/chat/messages` MUST return HTTP 403 with error code `CHATBOT_CONSENT_REQUIRED`.

### Evaluation
- Grounded-answer rate ≥ 85 % on the 50-pair eval dataset.
- Refusal accuracy ≥ 95 % for `should_refuse=true` questions.
- Hallucination rate ≤ 10 % (claims not supported by retrieved chunks).
