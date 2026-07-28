# Restaurant ERP — API server (production multi-stage)
FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production \
    DEBUG=false \
    LOG_FORMAT=json \
    MPLCONFIGDIR=/tmp/matplotlib \
    HOME=/tmp

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --chown=app:app . .

RUN mkdir -p /app/uploads /app/logs /app/backups \
    && chown -R app:app /app/uploads /app/logs /app/backups

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD sh -c 'curl -fsS "http://127.0.0.1:${PORT:-${API_PORT:-8000}}/health/live" || exit 1'

# PORT is required by Render; UVICORN_WORKERS defaults to 1 on Render (512MB), else 2 for ECS.
CMD ["sh", "-c", "WORKERS=${UVICORN_WORKERS:-$( [ -n \"$RENDER\" ] && echo 1 || echo 2 )}; uvicorn app.main:app --host ${API_HOST:-0.0.0.0} --port ${PORT:-${API_PORT:-8000}} --workers ${WORKERS}"]
