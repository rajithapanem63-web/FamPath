# Spec: Platform Non-Functional — Requirements

## Security
- NFR-SEC-01: OWASP Top 10 addressed for all endpoints.
- NFR-SEC-02: Field-level encryption for sensitive data (rank, income, caste).
- NFR-SEC-03: Rate limiting on auth and chatbot endpoints.
- NFR-SEC-04: RBAC enforced server-side on every endpoint.
- NFR-SEC-05: Secure headers (CSP, HSTS, X-Frame-Options, etc.) on all responses.
- NFR-SEC-06: Audit logging for all sensitive actions.
- NFR-SEC-07: DPDP Act-aligned consent, data export, and deletion flows.

## Performance
- NFR-PERF-01: API p95 ≤ 300 ms for non-LLM endpoints.
- NFR-PERF-02: System handles 500 concurrent users with error rate ≤ 1 %.
- NFR-PERF-03: LLM endpoints p95 ≤ 5 s; timeout at 30 s with graceful error.
- NFR-PERF-04: Lighthouse score ≥ 90 for performance, accessibility, best practices on key pages.

## Observability
- NFR-OBS-01: Structured JSON logs with correlation IDs on all requests.
- NFR-OBS-02: OpenTelemetry traces for all service calls.
- NFR-OBS-03: Prometheus metrics: request rate, error rate, latency histograms, DB pool usage.
- NFR-OBS-04: Health check endpoint `GET /health` and readiness `GET /ready`.
- NFR-OBS-05: Sentry-compatible error tracking with PII scrubbing.

## Reliability
- NFR-REL-01: Graceful degradation: if LLM API is unavailable, chatbot shows maintenance message; other features unaffected.
- NFR-REL-02: DB connection pooling (min 5, max 20 connections).
- NFR-REL-03: Retries with exponential backoff for external API calls (max 3 retries).
- NFR-REL-04: Health and readiness endpoints return correct status within 1 s.

## DevOps
- NFR-DEV-01: `docker compose up` starts all services from a clean state in < 2 minutes.
- NFR-DEV-02: GitHub Actions CI runs lint + test + build on every PR.
- NFR-DEV-03: Staging auto-deployed on merge to main; production requires manual approval.
- NFR-DEV-04: Zero-downtime rolling deploys via container orchestration.
- NFR-DEV-05: Database migrations run automatically on deploy (Alembic `upgrade head`).
- NFR-DEV-06: `.env.example` documents all environment variables.

## Accessibility & i18n
- NFR-A11Y-01: WCAG 2.1 AA on all pages.
- NFR-I18N-01: All visible strings in en/te/hi; no hard-coded strings.
- NFR-I18N-02: i18n key parity enforced in CI.
