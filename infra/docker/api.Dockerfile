# syntax=docker/dockerfile:1.7
# CareerOS API (FastAPI + `career-os` CLI). Build context: repository root.
#
#   deps     → a virtualenv with requirements.txt only (cached until it changes)
#   runtime  → slim Python + that venv + the source; no compilers, no pip caches
ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim-bookworm AS deps
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    /opt/venv/bin/pip install -r /tmp/requirements.txt \
    && /opt/venv/bin/pip uninstall -y pip setuptools wheel   # build-time only


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SEED_ON_START=true
WORKDIR /app

RUN useradd --create-home --uid 10001 careeros
COPY --from=deps /opt/venv /opt/venv

# Source runs from /app (not site-packages): config resolves the repo root from
# the package location, and infra/config + infra/seeds are read from there.
COPY careeros ./careeros
COPY apps/__init__.py ./apps/__init__.py
COPY apps/api ./apps/api
COPY apps/cli ./apps/cli
COPY infra/config ./infra/config
COPY infra/seeds ./infra/seeds
COPY --chmod=755 infra/docker/api-entrypoint.sh /usr/local/bin/api-entrypoint
COPY --chmod=755 <<'EOF' /usr/local/bin/career-os
#!/bin/sh
exec python -m apps.cli.main "$@"
EOF

# Uploaded CVs (a volume in production)
RUN mkdir -p /app/personal && chown careeros:careeros /app/personal

USER careeros
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["api-entrypoint"]
