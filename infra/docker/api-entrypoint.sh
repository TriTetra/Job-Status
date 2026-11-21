#!/bin/sh
# Apply migrations, load reference data, then serve. One worker on purpose:
# background jobs, login throttling and OAuth state live in process memory
# (see docs/ARCHITECTURE.md).
set -e

alembic -c careeros/db/alembic.ini upgrade head

# Reference data (countries, visas, roles, skills, goals…) — idempotent upserts
if [ "$SEED_ON_START" = "true" ]; then
  career-os seed || echo "WARNING: seed failed; the API starts anyway" >&2
fi

exec uvicorn apps.api.app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1 \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --timeout-graceful-shutdown 20 \
  --no-server-header
