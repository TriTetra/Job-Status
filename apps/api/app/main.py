"""CareerOS FastAPI Gateway."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from careeros.shared.logging import configure_logging

from .dependencies import get_user_id
from .routers import applications, companies, evidence, goals, jobs, market, onboarding, resume, settings, webhooks, roles, preferences, oauth

configure_logging()

app = FastAPI(
    title="CareerOS API",
    description="AI-native career operating system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure by default: every router requires a signed-in user.
# Exceptions are deliberate and few:
#   webhooks — authenticated by Svix signature
#   oauth    — per-endpoint auth; /github/callback is a GitHub redirect
#              authenticated by its single-use state token
authenticated = [Depends(get_user_id)]

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
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(oauth.router)


@app.get("/")
def root():
    return {"name": "CareerOS API", "version": "1.0.0", "status": "healthy", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
