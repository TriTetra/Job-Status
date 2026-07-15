"""CareerOS FastAPI Gateway."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import applications, companies, evidence, jobs, market, onboarding, resume, settings, webhooks, roles, preferences

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

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(evidence.router, prefix="/api/evidence", tags=["evidence"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(roles.router)
app.include_router(preferences.router)


@app.get("/")
def root():
    return {"name": "CareerOS API", "version": "1.0.0", "status": "healthy", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
