# Design: Conflict Mediator AI

## LLM Integration

**Provider:** Claude (Anthropic) via abstraction layer  
**Model:** claude-3-5-sonnet  
**Prompt:** Versioned template in `backend/app/rag/prompts/mediator_v1.txt`

## Service Architecture

`MediationService`:
- `generate_mediation(workspace_id, dimension)`
- Fetches family preferences
- Fetches relevant college data
- Constructs prompt
- Calls LLM
- Parses and validates response

## Safety

- Input sanitization (no prompt injection)
- Output validation (must match JSON schema)
- Fallback: If LLM fails, return generic mediation tips
- No PII sent to LLM (anonymize family names)

---

**Status:** Ready for tasks.md
