# Spec: Platform Non-Functional — Design

## Observability Stack

```
FastAPI app
  → structlog (JSON) → stdout → Loki / log aggregator
  → OpenTelemetry SDK → OTLP exporter → Jaeger (traces)
  → prometheus_fastapi_instrumentator → /metrics → Prometheus → Grafana
  → Sentry SDK (errors, PII scrubbed)
```

## Middleware Stack (order matters)

1. `CorrelationIdMiddleware` — inject `X-Correlation-ID` header; attach to logger context
2. `SecurityHeadersMiddleware` — set HSTS, CSP, X-Frame-Options, etc.
3. `RateLimitMiddleware` — Redis sliding window; applied to `/api/v1/auth/*` and `/api/v1/chat/*`
4. `CORSMiddleware` — allowlist of known origins
5. `RequestLoggingMiddleware` — log method, path, status, duration, correlation_id (no body)
6. `OpenTelemetryMiddleware` — span creation per request
7. Prometheus instrumentation (via `prometheus_fastapi_instrumentator`)

## Health Endpoints

```
GET /health   → { status: "ok", timestamp }  -- always 200 if process is up
GET /ready    → { status: "ok", db: "ok", redis: "ok", ml_model: "ok" }
              -- 503 if any dependency unhealthy
```

## DB Connection Pooling (SQLAlchemy async)
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=15,
    pool_timeout=30,
    pool_recycle=3600,
)
```

## Docker Compose Services

```yaml
services:
  backend:     FastAPI + Celery worker (same image, different CMD)
  celery:      Celery worker
  celery-beat: Celery Beat scheduler
  frontend:    Next.js (production build served by Node)
  postgres:    postgres:16 + pgvector
  redis:       redis:7-alpine
  mlflow:      mlflow server (local artifact store)
  prometheus:  prom/prometheus
  grafana:     grafana/grafana
  loki:        grafana/loki
```

## CI/CD Pipeline (.github/workflows/ci.yml)

```
on: pull_request, push to main

jobs:
  backend-lint-test:
    - ruff check, black --check, mypy --strict
    - pytest --cov --cov-fail-under=80

  frontend-lint-test:
    - eslint, tsc --noEmit, prettier --check
    - vitest run --coverage

  e2e:
    - docker compose up -d (test profile)
    - playwright test
    - docker compose down

  security:
    - pip-audit, npm audit
    - trufflehog (secret scan on diff)
    - OWASP ZAP baseline (on staging deploy only)

  build:
    - docker build backend, frontend
    - push to registry

  deploy-staging: (on main only)
    - docker pull, rolling update

  deploy-prod: (manual approval)
    - same as staging
```

## Terraform Modules (IaC skeleton)

```
infra/terraform/modules/
  networking/   - VPC, subnets, security groups
  compute/      - ECS task definitions, services, ALB
  database/     - RDS PostgreSQL, parameter groups
  cache/        - ElastiCache Redis
  secrets/      - Secrets Manager resources
  monitoring/   - CloudWatch alarms (or self-hosted)
```

## Security Headers (FastAPI middleware)

```python
headers = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # Tailwind requires this
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self';"
    ),
}
```

## Feature Flags

Phase 2 features gated by environment variable `FEATURE_{NAME}=true/false`:
- `FEATURE_ROUND_SIMULATOR`
- `FEATURE_PLAN_B_GENERATOR`
- `FEATURE_PEER_PRESSURE_DETECTOR`
- `FEATURE_CLAIM_VERIFIER`
- `FEATURE_MENTOR_MATCHING`
- `FEATURE_COUNSELLOR_BOOKING`
- `FEATURE_WHATSAPP_MODE`
- `FEATURE_OTP_LOGIN`

All Phase 2 routes return HTTP 501 with `{"error_code": "FEATURE_NOT_ENABLED"}` when flag is off.
