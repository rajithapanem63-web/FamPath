# Spec: Platform Non-Functional — Tasks

### TASK-NFR-01: Middleware stack
- CorrelationIdMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware, RequestLoggingMiddleware
- Unit tests: headers present, rate limit fires, correlation ID propagated

### TASK-NFR-02: Health & readiness endpoints
- `GET /health`, `GET /ready` with DB/Redis/model checks
- Tests: healthy state, unhealthy DB → 503

### TASK-NFR-03: Structured logging (structlog)
- Replace all print() with structlog
- Request logging with correlation ID
- PII redaction processor (scrub email, rank fields from logs)

### TASK-NFR-04: OpenTelemetry integration
- OTLP exporter config, span naming conventions
- Celery task instrumentation

### TASK-NFR-05: Prometheus metrics
- `prometheus_fastapi_instrumentator` setup
- Custom metrics: prediction requests, LLM latency, cache hit rate
- Grafana dashboard JSON in `infra/grafana/`

### TASK-NFR-06: Docker Compose configuration
- `infra/docker-compose.yml` with all 9 services
- Health checks on all services
- Volume mounts for postgres data, redis data, mlflow artifacts
- `docker-compose.test.yml` for CI (no mlflow, no grafana)
- Verify: `docker compose up` starts cleanly

### TASK-NFR-07: GitHub Actions CI pipeline
- `ci.yml`: backend lint+test, frontend lint+test, E2E, security scan, build
- `deploy-staging.yml`: auto on main
- `deploy-prod.yml`: manual approval gate
- Test: CI runs green on a clean repo

### TASK-NFR-08: Environment configuration
- `.env.example` with all vars documented
- `backend/app/core/config.py` (Pydantic Settings)
- Feature flag loading
- Tests: all required vars validated on startup

### TASK-NFR-09: Database connection pooling & migration runner
- SQLAlchemy async engine config
- Alembic migration in Docker entrypoint
- Tests: pool config correct, migrations run idempotently

### TASK-NFR-10: Terraform skeleton
- Module stubs for networking, compute, database, cache, secrets
- README in infra/ with deployment guide

### TASK-NFR-11: Error tracking (Sentry)
- Sentry SDK with PII scrubbing (`before_send` hook strips email/rank)
- Test: error captured in test DSN

### TASK-NFR-12: Retries & timeouts for external calls
- httpx client with retry (3×, exponential backoff) for LLM/email APIs
- Circuit breaker pattern for LLM (return maintenance message after 5 consecutive failures)
- Tests: retry fires, circuit breaker opens
