#!/bin/sh
# Apply migrations, then serve. One worker on purpose: background jobs, login
# throttling and OAuth state live in process memory (see docs/ARCHITECTURE.md).
set -e

alembic -c careeros/db/alembic.ini upgrade head

exec uvicorn apps.api.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --proxy-headers \
  --forwarded-allow-ips="*"
