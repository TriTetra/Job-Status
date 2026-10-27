"""CareerOS FastAPI Gateway.

Deployed behind the web app on a single domain: the browser only ever talks to
the Next.js origin, which forwards /api/* to this service on the internal
network. There is no CORS — cross-origin browser requests are simply refused.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from careeros.shared.config import get_settings
from careeros.shared.logging import configure_logging

from .dependencies import get_user_id
from .routers import (
    applications, auth, briefing, companies, evidence, goals, jobs, market, oauth,
    onboarding, preferences, resume, roles, settings,
)

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = None
    hours = get_settings().job_sync_interval_hours
    if hours > 0:
        from careeros.jobs.scheduler import JobScheduler

        scheduler = JobScheduler(hours)
        scheduler.start()
    yield
    if scheduler:
        scheduler.stop()


app = FastAPI(
    lifespan=lifespan,
    title="CareerOS API",
    description="Private career intelligence API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CSRF ──────────────────────────────────────────────────────────────────
# Every state-changing request must carry this header. A cross-site form or
# image cannot set custom headers, and a cross-site fetch() that tries needs a
# CORS preflight this API never grants — so only our own pages can write.
CSRF_HEADER = "x-careeros-csrf"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@app.middleware("http")
async def require_csrf_header(request: Request, call_next):
    if request.method not in SAFE_METHODS and request.headers.get(CSRF_HEADER) != "1":
        return JSONResponse({"detail": "Missing CSRF header"}, status_code=403)
    return await call_next(request)


# ── routers ───────────────────────────────────────────────────────────────
# Secure by default: every router requires a signed-in user.
# Exceptions are deliberate and few:
#   auth  — /login must work signed-out; /me checks the session itself
#   oauth — per-endpoint auth; /github/callback is a GitHub redirect
#           authenticated by its single-use state token
authenticated = [Depends(get_user_id)]

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(briefing.router, prefix="/api/briefing", tags=["briefing"], dependencies=authenticated)
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"], dependencies=authenticated)
app.include_router(companies.router, prefix="/api/companies", tags=["companies"], dependencies=authenticated)
app.include_router(applications.router, prefix="/api/applications", tags=["applications"], dependencies=authenticated)
app.include_router(resume.router, prefix="/api/resume", tags=["resume"], dependencies=authenticated)
app.include_router(market.router, prefix="/api/market", tags=["market"], dependencies=authenticated)
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"], dependencies=authenticated)
app.include_router(settings.router, prefix="/api/settings", tags=["settings"], dependencies=authenticated)
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"], dependencies=authenticated)
app.include_router(roles.router, dependencies=authenticated)
app.include_router(preferences.router, dependencies=authenticated)
app.include_router(goals.router, dependencies=authenticated)
app.include_router(oauth.router)


@app.get("/")
def root():
    return {"name": "CareerOS API", "version": "1.0.0", "status": "healthy", "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness for the container healthcheck (does not touch the DB)."""
    return {"status": "ok"}
