# FamPath – Technology Stack & Conventions

## Guiding Principles

1. **Boring technology wins** – prefer stable, well-documented choices over cutting-edge; justify every deviation.
2. **Typed everywhere** – Python uses strict Pydantic v2 models and type hints; TypeScript is strict mode.
3. **Explainability over accuracy** – an ML model that explains itself is preferred over a marginally more accurate black box.
4. **Async-first backend** – FastAPI with async handlers; synchronous code only where a library forces it.
5. **Progressive enhancement** – the UI must work without JavaScript for basic browsing (Next.js SSR); JS enriches the experience.

---

## Frontend

| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | Next.js 14 (App Router) + TypeScript strict | SSR/SSG for SEO, file-based routing, built-in image optimisation |
| Styling | Tailwind CSS v3 | Utility-first, consistent design tokens, low CSS specificity conflicts |
| Component library | shadcn/ui | Accessible Radix primitives, no runtime dependency, copy-owned components |
| Charts | Recharts | React-native, accessible, composable |
| i18n | next-intl | App Router compatible, ICU messages, server-component support |
| State management | Zustand (lightweight) + React Query (server state) | Keeps global state minimal; React Query handles caching/revalidation |
| Forms | React Hook Form + Zod | Schema-driven validation shared with backend |
| PWA | next-pwa (Workbox) | Offline support, installable on mobile |
| Testing | Vitest + Testing Library | Fast, ESM-native; mirrors Jest API |
| E2E | Playwright | Multi-browser, reliable, great for auth flows |

### Conventions

- All components live in `frontend/src/components/`; shadcn components in `components/ui/`.
- Pages (route segments) live in `frontend/src/app/`.
- Hooks in `frontend/src/hooks/`, utilities in `frontend/src/lib/`.
- No inline styles; no CSS modules (Tailwind only, with `cn()` helper).
- Every interactive component must have an `aria-label` or visible label.
- Use `next/image` for all images; never raw `<img>`.
- Server Components by default; add `'use client'` only when necessary.

---

## Backend

| Concern | Choice | Reason |
|---------|--------|--------|
| Language | Python 3.12 | Latest stable, improved typing, performance gains |
| Web framework | FastAPI | Async, auto OpenAPI, Pydantic-native |
| Data validation | Pydantic v2 | 5–10× faster than v1, model-level constraints |
| ORM | SQLAlchemy 2 (async) | Industry standard, explicit queries, migration support |
| Migrations | Alembic | Pairs with SQLAlchemy, revision history |
| Auth tokens | Python-JOSE + Passlib (argon2) | Standard JWT; argon2 is OWASP recommended |
| Background jobs | Celery 5 + Redis broker | Battle-tested; supports scheduled and async tasks |
| HTTP client | httpx (async) | Modern, type-safe, replaces requests for async code |
| PDF generation | WeasyPrint | HTML→PDF; easy to style with CSS |

### Conventions

- All modules under `backend/app/`; sub-packages: `api/`, `models/`, `schemas/`, `services/`, `workers/`, `ml/`, `rag/`.
- Router files named `{domain}_router.py`; schema files `{domain}_schema.py`.
- Every endpoint has a docstring and OpenAPI summary/description tags.
- No business logic in router functions; delegate to `services/`.
- All database access through SQLAlchemy sessions injected via FastAPI `Depends()`.
- Use `structlog` for structured JSON logging; never `print()`.

---

## Database

| Concern | Choice | Reason |
|---------|--------|--------|
| Primary DB | PostgreSQL 16 | ACID, pgvector extension, JSONB, mature |
| Vector store | pgvector extension | Eliminates a separate vector DB; vectors co-located with metadata |
| Cache / Broker | Redis 7 | Fast, supports pub/sub, Celery broker, rate-limit counters |
| Migrations | Alembic auto-generate + manual review | Prevents schema drift |

### Conventions

- Table names: `snake_case`, plural (e.g., `family_workspaces`).
- All tables have `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`, `created_at`, `updated_at`.
- Soft-delete via `deleted_at TIMESTAMPTZ` column; never hard-delete user data.
- Sensitive columns (`income_range`, `caste_category`, `marks`) are encrypted at rest using pgcrypto or application-level AES-256-GCM.
- All foreign keys are named `{table}_{column}_fk`.
- Indexes documented in Alembic migrations, not added ad hoc.

---

## ML Pipeline

| Concern | Choice | Reason |
|---------|--------|--------|
| Data manipulation | pandas + numpy | Standard; familiar to most ML engineers |
| Feature engineering | scikit-learn pipelines | Reproducible, serialisable |
| Predictor model | XGBoost (gradient boosted trees) | Good accuracy on tabular data, built-in feature importance for explainability |
| Model registry | MLflow (local or hosted) | Versioning, metrics tracking, artifact storage |
| Serving | FastAPI endpoint wrapping loaded artifact | Keeps serving in-process; no separate serving infra for MVP |
| Explainability | SHAP values | Model-agnostic, human-readable feature contributions |

### Conventions

- Training scripts in `backend/ml/training/`; serving code in `backend/ml/serving/`.
- Every model artifact stored with: version tag, training date, dataset hash, metrics dict.
- Train/validation/test splits **must** be stratified by year (no data leakage across counselling rounds).
- A `ModelCard.md` is required per model before it can be promoted to production.

---

## LLM / RAG

| Concern | Choice | Reason |
|---------|--------|--------|
| LLM provider | Anthropic Claude (claude-3-5-sonnet) | Strong reasoning, large context window, good at structured output |
| Provider interface | Thin abstraction `LLMProvider` protocol | Easy to swap to OpenAI or Gemini |
| Embeddings | `text-embedding-3-small` (OpenAI) or `voyage-2` via Anthropic | Configurable; stored in pgvector |
| RAG retrieval | Hybrid: BM25 + cosine similarity re-ranked | Better recall on domain-specific acronyms |
| Prompt management | Versioned prompt templates in `backend/rag/prompts/` | Auditable; no prompts hard-coded in business logic |

### Safeguards (mandatory)

- All user inputs sanitised before insertion into prompts.
- System prompt includes explicit refusal instructions for out-of-scope or harmful requests.
- PII (name, rank, income) is **never** sent to the LLM unless the user has consented and it is strictly necessary.
- Every LLM response must include `citations: list[SourceRef]`; responses without citations are rejected by the parsing layer.
- Hallucination guard: a post-processing step checks claims against the retrieved chunks; low-confidence responses are flagged with a disclaimer.

---

## Auth

- JWT access token (15 min expiry) + refresh token (7 days, rotated on use, stored in `httpOnly` cookie).
- Roles: `student`, `parent`, `counsellor`, `admin`. Permissions checked server-side via `Depends(require_role(...))`.
- Email verification required before any data access; OTP-based login as opt-in alternative.
- Password reset via time-limited signed token (24 h).
- Rate limiting on `/auth/*` endpoints: 10 attempts / 15 min per IP.

---

## Infrastructure & DevOps

| Concern | Choice |
|---------|--------|
| Containerisation | Docker + docker-compose (local), Docker images (cloud) |
| IaC | Terraform modules (AWS ECS/RDS/ElastiCache or equivalent) |
| CI/CD | GitHub Actions |
| Secrets | `.env` locally; AWS Secrets Manager / GitHub Actions secrets in CI/CD |
| Monitoring | OpenTelemetry collector → Prometheus + Grafana; structured logs → Loki |
| Error tracking | Sentry (self-hosted or cloud, configurable DSN) |
| Load testing | k6 |

---

## Dependency Rules

- Pin all dependencies to exact versions in `requirements.txt` and `package.json` (`exact` in npm).
- No dependency is added without a written justification comment in `requirements.txt` or `package.json`.
- `pip-audit` and `npm audit` run in CI; any critical CVE blocks the build.
- Keep the dependency count low; prefer standard-library or already-present solutions.

---

## Code Quality Gates (enforced in CI and hooks)

| Tool | Scope | Standard |
|------|-------|----------|
| Ruff | Python linting | Error-free |
| Black | Python formatting | `--check` passes |
| mypy | Python type-checking | `--strict` passes |
| ESLint | TypeScript linting | Zero errors |
| Prettier | TypeScript/CSS formatting | `--check` passes |
| tsc | TypeScript compilation | Zero errors |
| pytest | Backend tests | ≥ 80 % coverage |
| Vitest | Frontend unit tests | ≥ 70 % coverage on critical paths |
| Playwright | E2E | Core journeys green |
