# FamPath – Testing Strategy & Standards

## Philosophy

- Tests are **first-class citizens** — never skipped, never commented out.
- Every new feature requires tests before the task is marked done.
- Tests must be **fast, deterministic, and isolated**; flaky tests are treated as bugs.
- Prefer **behaviour-driven** test names: `test_should_return_dream_band_when_rank_is_below_cutoff`.

---

## Coverage Targets

| Layer | Tool | Minimum Coverage |
|-------|------|-----------------|
| Backend unit + integration | pytest + pytest-cov | **80 %** line coverage |
| Frontend unit (critical paths) | Vitest + Testing Library | **70 %** on `components/`, `hooks/`, `lib/` |
| E2E (core journeys) | Playwright | All 7 journeys must pass |
| ML model | Custom eval script | Accuracy, calibration, fairness metrics documented |
| RAG chatbot | Eval dataset | ≥ 85 % grounded-answer rate on 50-pair eval set |

Coverage gates are enforced in CI; a build with coverage below threshold fails.

---

## Backend Testing (pytest)

### Structure

```
backend/tests/
├── conftest.py          # shared fixtures: db session, test client, auth tokens
├── unit/
│   ├── test_college_service.py
│   ├── test_predictor.py
│   └── …
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_workspace_endpoints.py
│   └── …
└── ml/
    ├── test_model_metrics.py
    └── test_fairness.py
```

### Rules

- **Unit tests** mock all I/O (database, Redis, external APIs) using `pytest-mock` or `httpx.MockTransport`.
- **Integration tests** use a real test PostgreSQL database (spun up via `docker-compose` or `pytest-docker`) and real Redis; no mocking of DB calls.
- **No shared mutable state** between tests; each test gets a fresh DB transaction rolled back after the test.
- Every API endpoint must have at minimum:
  - Happy-path test (200/201)
  - Unauthenticated test (401)
  - Wrong-role test (403)
  - Invalid input test (422)
  - Not-found test (404) where applicable
- Use `pytest.mark.parametrize` for data-driven tests (e.g., testing multiple rank/category combinations).
- Fixtures that create DB records use factories (`factory_boy`) for clarity and reuse.

### Key Fixtures

```python
# conftest.py patterns
@pytest.fixture
def db_session() -> AsyncGenerator[AsyncSession, None]: …

@pytest.fixture
def auth_headers(student_user) -> dict: …  # returns {"Authorization": "Bearer …"}

@pytest.fixture
def admin_headers(admin_user) -> dict: …
```

---

## Frontend Testing (Vitest + Testing Library)

### Structure

```
frontend/tests/
├── unit/
│   ├── components/
│   │   └── CollegeCard.test.tsx
│   ├── hooks/
│   │   └── useCollegePredictor.test.ts
│   └── lib/
│       └── formatRank.test.ts
└── e2e/                  # Playwright lives here
```

### Rules

- Use `@testing-library/react` for component tests; prefer queries that reflect user perception (`getByRole`, `getByLabelText`).
- Mock API calls with `msw` (Mock Service Worker) — no `jest.mock('../../lib/api')` inline.
- Snapshot tests are **banned** (too brittle); use explicit assertions on rendered content.
- Test i18n: components must render correctly in all three locales; use the `renderWithIntl()` helper.
- Accessibility: every component test runs `axe` checks via `jest-axe` (or vitest equivalent).

---

## E2E Testing (Playwright)

### Required Journeys

| # | Journey | Key Assertions |
|---|---------|---------------|
| 1 | Student sign-up + email verification | Account created, email verified, dashboard visible |
| 2 | Family invite (student invites parent) | Parent receives email, accepts, sees shared workspace |
| 3 | Preference questionnaire (both student and parent) | Both submitted, alignment score calculated |
| 4 | College prediction | Rank input → Safe/Target/Dream bands rendered, disclaimer visible |
| 5 | Aptitude quiz completion | 20 questions answered → Branch Fit Score displayed |
| 6 | Cost calculator | 4-year cost and EMI rendered with data-source label |
| 7 | PDF report download | PDF file downloaded, non-empty, filename correct |

### Rules

- Tests run against a seeded staging environment (synthetic data only).
- Use Page Object Model (POM) pattern; no raw `page.locator()` calls in test bodies.
- Each test is independent; use `beforeEach` to log in via API (not UI) for speed.
- Run in CI with `--workers=2` (parallel) and a max timeout of 60 s per test.
- Screenshots on failure are captured automatically.
- Test in Chromium (default) + Mobile Chrome viewport.

---

## ML Testing

### Training Data Tests

- Schema validation on every imported CSV (columns, types, value ranges).
- No null values in required fields; duplicates flagged.
- Train/validation/test split: **by counselling year** (e.g., train on 2019–2022, validate on 2023, test on 2024); never random split across years.

### Model Evaluation Requirements (before promotion to production)

| Metric | Threshold |
|--------|-----------|
| Accuracy (overall) | ≥ 0.80 |
| Calibration error (ECE) | ≤ 0.05 |
| Accuracy per category (OC/BC/SC/ST) | ≥ 0.75 each |
| Accuracy per gender | gap ≤ 0.05 |
| Accuracy per exam (AP/TS/JEE) | ≥ 0.75 each |

- A `ModelCard.md` documenting training data, metrics, known limitations, and fairness analysis is required per model.
- Drift monitoring: prediction distribution is logged; alerts fire if distribution shifts > 10 % week-over-week.

---

## RAG / Chatbot Evaluation

- Maintain an evaluation dataset: `backend/tests/rag/eval_pairs.json` — minimum **50 Q&A pairs** with:
  - `question`: natural-language question
  - `expected_sources`: list of expected document IDs
  - `expected_answer_contains`: key facts the answer must include
  - `should_refuse`: boolean (for out-of-scope questions)
- Metrics computed on every RAG pipeline change:
  - **Grounded-answer rate**: answer is supported by at least one cited chunk — target ≥ 85 %
  - **Refusal accuracy**: `should_refuse=true` questions correctly refused — target ≥ 95 %
  - **Hallucination rate**: claims not found in retrieved chunks — target ≤ 10 %
- Eval script: `scripts/eval_rag.py`; results written to `docs/rag_eval_report.md`.

---

## Load Testing (k6)

- Baseline load test: **500 concurrent virtual users**, 5-minute sustained load.
- Scenarios: sign-in, prediction request, chatbot query (heaviest endpoints).
- Thresholds:
  - p95 response time ≤ 300 ms for non-LLM endpoints
  - Error rate ≤ 1 %
- Scripts in `backend/tests/load/`; run manually before each production release.
- Report saved to `docs/load_test_report_{date}.md`.

---

## Continuous Integration Gates

Every pull request must pass:

1. `ruff check .` (backend linting)
2. `black --check .` (backend formatting)
3. `mypy --strict .` (backend types)
4. `eslint .` (frontend linting)
5. `tsc --noEmit` (frontend types)
6. `pytest --cov --cov-fail-under=80` (backend)
7. `vitest run --coverage` (frontend, fail under 70 %)
8. `playwright test` (E2E, against seeded staging)
9. `pip-audit` + `npm audit --audit-level=critical` (dependency security)
10. Secret scan (no credentials in diff)

A merge to `main` additionally triggers:
- Container image build and push
- Automated staging deploy
- OWASP ZAP baseline scan

---

## Test Data Rules

- Tests **never** connect to real external APIs (LLM, SMS); all external calls are mocked.
- Test databases are populated with synthetic seed data only; no production data in test environments.
- Seed data is deterministic (fixed random seed) so tests are reproducible.
- Sensitive fields in test data use obviously fake values (`income_range = "SEED_LOW"`, `rank = 99999`).
