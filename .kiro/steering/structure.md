# FamPath – Repository Layout & Naming Conventions

## Repository Root

```
fampath/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # lint, type-check, test, build
│   │   ├── security-scan.yml       # secret scan, dependency audit
│   │   ├── deploy-staging.yml      # auto-deploy on main merge
│   │   └── deploy-prod.yml         # manual-approval gate
│   └── PULL_REQUEST_TEMPLATE.md
├── .kiro/
│   ├── steering/                   # (this directory)
│   └── hooks/                      # agent automation hooks
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI routers (one file per domain)
│   │   ├── core/                   # settings, security, database session
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/               # business logic (no DB imports in routers)
│   │   ├── workers/                # Celery task definitions
│   │   ├── ml/
│   │   │   ├── training/           # training scripts, feature engineering
│   │   │   ├── serving/            # model loading, prediction wrappers
│   │   │   └── model_cards/        # ModelCard.md per model
│   │   └── rag/
│   │       ├── prompts/            # versioned prompt templates
│   │       ├── retrieval/          # BM25 + vector retrieval
│   │       └── pipeline.py         # end-to-end RAG orchestration
│   ├── alembic/
│   │   ├── versions/               # migration files
│   │   └── env.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── seed_data/                  # clearly labelled synthetic CSV/JSON
│   ├── Dockerfile
│   ├── requirements.txt            # pinned exact versions
│   ├── requirements-dev.txt
│   └── pyproject.toml              # ruff, black, mypy, pytest config
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router pages & layouts
│   │   │   ├── [locale]/           # i18n root segment
│   │   │   │   ├── (auth)/         # sign-in, sign-up, verify-email
│   │   │   │   ├── (workspace)/    # family workspace routes
│   │   │   │   ├── (admin)/        # admin panel routes
│   │   │   │   └── layout.tsx
│   │   │   └── api/                # Next.js API routes (thin BFF only)
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn/ui generated components
│   │   │   ├── charts/             # Recharts wrappers
│   │   │   ├── forms/              # React Hook Form composites
│   │   │   └── {feature}/          # feature-scoped component folders
│   │   ├── hooks/                  # custom React hooks
│   │   ├── lib/
│   │   │   ├── api.ts              # typed API client (React Query base)
│   │   │   ├── auth.ts             # token management helpers
│   │   │   └── utils.ts            # cn(), formatters, etc.
│   │   ├── stores/                 # Zustand stores
│   │   ├── types/                  # shared TypeScript types & enums
│   │   └── i18n/
│   │       ├── messages/
│   │       │   ├── en.json
│   │       │   ├── te.json         # Telugu
│   │       │   └── hi.json         # Hindi
│   │       └── routing.ts
│   ├── public/
│   │   ├── icons/                  # PWA icons
│   │   └── manifest.json
│   ├── tests/
│   │   ├── unit/
│   │   └── e2e/                    # Playwright specs
│   ├── Dockerfile
│   ├── package.json                # exact versions
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.ts
├── infra/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── networking/
│   │   │   ├── compute/
│   │   │   ├── database/
│   │   │   └── secrets/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── main.tf
│   └── docker-compose.yml          # one-command local start
├── docs/
│   ├── adr/                        # Architecture Decision Records (ADR-001.md …)
│   ├── api/                        # OpenAPI export + Postman collection
│   ├── data-dictionary.md
│   ├── runbooks/
│   │   ├── incident.md
│   │   ├── backup-restore.md
│   │   └── data-refresh.md
│   ├── admin-guide.md
│   └── user-guide.md
├── scripts/
│   ├── seed_db.py                  # populate DB with synthetic seed data
│   ├── import_colleges.py          # CSV importer
│   └── run_training.py             # trigger ML training pipeline
├── .env.example                    # all required env vars, no secrets
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
└── README.md
```

---

## Naming Conventions

### Python (backend)

| Item | Convention | Example |
|------|-----------|---------|
| Module / package | `snake_case` | `college_service.py` |
| Class | `PascalCase` | `CollegePredictor` |
| Function / variable | `snake_case` | `get_cutoff_bands()` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_SHORTLIST_SIZE` |
| Pydantic schema | `PascalCase` + `Request`/`Response` suffix | `CollegePredictRequest` |
| SQLAlchemy model | `PascalCase`, no suffix | `College`, `FamilyWorkspace` |
| Alembic revision | `{datetime}_{verb}_{noun}.py` | `20240901_add_workspace_table.py` |
| Test file | `test_{module}.py` | `test_college_service.py` |

### TypeScript (frontend)

| Item | Convention | Example |
|------|-----------|---------|
| Component file | `PascalCase.tsx` | `CollegeCard.tsx` |
| Hook file | `use{Name}.ts` | `useCollegePredictor.ts` |
| Utility / lib file | `camelCase.ts` | `formatRank.ts` |
| Store file | `{domain}Store.ts` | `workspaceStore.ts` |
| Type / interface | `PascalCase`, `I` prefix only for interfaces that will be implemented | `CollegePrediction`, `IAuthProvider` |
| Enum | `PascalCase` | `UserRole` |
| Test file | `{Component}.test.tsx` | `CollegeCard.test.tsx` |
| E2E spec | `{journey}.spec.ts` | `signup.spec.ts` |

### API Endpoints

- Base: `/api/v1/{domain}/{resource}`
- Examples: `GET /api/v1/colleges/{id}`, `POST /api/v1/workspaces/{id}/members`
- Plural nouns for collections; singular for single-resource actions.
- Versioning via URL prefix (`/v1/`); never in headers for MVP.

### Database

- Tables: `plural_snake_case` — `colleges`, `cutoff_records`, `family_workspaces`
- Columns: `snake_case`
- Junction tables: `{table_a}_{table_b}` alphabetically — `college_programs`
- Indexes: `ix_{table}_{column(s)}` — `ix_cutoff_records_college_id_year`
- Foreign keys: `{referencing_table}_{column}_fk`

### i18n Keys

- Dot-notation namespaced: `{page}.{component}.{key}`
- Example: `prediction.resultCard.safeLabel`
- All three locale files (`en.json`, `te.json`, `hi.json`) must have identical key sets; CI hook enforces this.

### Environment Variables

- `FAMPATH_{SERVICE}_{NAME}` pattern
- Examples: `FAMPATH_DB_URL`, `FAMPATH_REDIS_URL`, `FAMPATH_LLM_API_KEY`
- All variables documented in `.env.example` with type, required/optional, and example value.

---

## Git Conventions

### Branch Strategy

```
main          → production-ready, protected
staging       → integration testing, auto-deployed
develop       → active development base
feat/{ticket}-{short-desc}    → feature branches
fix/{ticket}-{short-desc}     → bug fixes
chore/{desc}                  → tooling / config
```

### Commit Message Format (Conventional Commits)

```
{type}({scope}): {imperative description}

[optional body]

[optional footer: BREAKING CHANGE, Closes #issue]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

Scopes: `auth`, `workspace`, `predictor`, `aptitude`, `alignment`, `cost`, `chatbot`, `shortlist`, `admin`, `infra`, `i18n`, `ml`

Examples:
```
feat(auth): add OTP login with Twilio SMS
fix(predictor): correct category encoding for BC-D
docs(admin): add data-refresh runbook
test(workspace): add integration tests for family invite flow
```

---

## Spec Directory Layout

Each Kiro spec lives at `.kiro/specs/{domain}/`:
```
.kiro/specs/
├── auth-and-family-workspace/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── data-platform-and-admin/
│   └── …
└── {domain}/
    └── …
```
