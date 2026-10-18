# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for WeasyPrint, psycopg2, argon2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Production stage ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

# Non-root user
RUN groupadd -r fampath && useradd -r -g fampath fampath

WORKDIR /app

# Copy system libs needed at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libglib2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .
RUN chown -R fampath:fampath /app

USER fampath

EXPOSE 8000

# Default: run FastAPI (override CMD for Celery)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
