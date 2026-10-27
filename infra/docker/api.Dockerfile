# CareerOS API (FastAPI + CLI). Build context: repository root.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencies first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Source. Installed editable: config resolves the repo root from the package
# location, so careeros must run from /app (infra/seeds, infra/config live here).
COPY pyproject.toml ./
COPY careeros ./careeros
COPY apps/__init__.py ./apps/__init__.py
COPY apps/api ./apps/api
COPY apps/cli ./apps/cli
COPY infra/config ./infra/config
COPY infra/seeds ./infra/seeds
COPY infra/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint
RUN pip install --no-deps -e . \
    && chmod +x /usr/local/bin/api-entrypoint \
    && useradd --create-home --uid 10001 careeros \
    && mkdir -p /app/personal && chown careeros /app/personal

USER careeros
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["api-entrypoint"]
