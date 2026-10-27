# Architecture

CareerOS is a modular monolith: one Python package (`careeros/`) with **one folder
per feature**, a thin HTTP/CLI layer (`apps/api`, `apps/cli`) and a Next.js web app
(`apps/web`) that talks only to the API.

```
apps/web (Next.js) ──HTTP──▶ apps/api (FastAPI, HTTP only)
                                     │
apps/cli (Typer: career-os) ─────────┤
                                     ▼
careeros/
  identity · onboarding · evidence · jobs · applications · companies · market · resume · briefing · knowledge
                                     │
                                     ▼
  shared (config, llm, logging, background, crypto)          db (Base, connection, registry, migrations)
                                     │
                                     ▼
                           PostgreSQL · OpenRouter · GitHub · HN · TechCrunch
```

## Layers and rules

| Layer | Holds | May import |
|---|---|---|
| `apps/web` | pages, components, `features/*` (types + API calls) | the API over HTTP only (`lib/api/client.ts`, `lib/api/server.ts`) |
| `apps/api` | routers (HTTP only), schemas, auth dependency | `careeros.*` |
| `apps/cli` | Typer commands | `careeros.*` |
| `careeros/<feature>` | models, repositories, domain, services | other features, `shared`, `db` |
| `careeros/shared`, `careeros/db` | infrastructure | nothing feature-specific (except `db/models.py`, the registry) |

Enforced by `tests/smoke/test_architecture.py`:

1. Configuration is read only in `careeros/shared/config.py` (`get_settings()`).
2. The LLM HTTP API is called only from `careeros/shared/llm.py` (`get_llm_client()`).
3. Library code logs (`logging.getLogger(__name__)`); only CLIs, scripts and `__main__` blocks print.
4. No `sys.path` manipulation — the repo is installed with `pip install -e .`.
5. `domain/` modules never import the DB layer.
6. `evidence_items` is the only evidence store; the legacy `evidence` table is unused.
7. Routers contain no queries or raw SQL.
8. `careeros` never imports `apps`.

## Features

| Package | Owns |
|---|---|
| `identity` | users, roles (catalog + search), preferences, current role → profession category, GitHub account linking (OAuth) |
| `onboarding` | the wizard state machine, identity/goals steps, CV upload job, Career Graph build job, goals catalog |
| `evidence` | `evidence_items` from GitHub repos, the CV (PDF → LLM) and a portfolio site; skill matching; cross-source aggregation; source registry |
| `jobs` | company boards (`sources/ats/`) + sync, ApplyPilot import, text extraction, scoring (`scoring/`), Decision Contract v1, incremental scan, scheduler, opportunities + reasoning |
| `applications` | the application pipeline (`to_apply → applied → interview → offer`) |
| `companies` | company profiles, hiring trends, interview memory |
| `market` | HN "Who is hiring" + TechCrunch signals (`sources/`), skill registry, refresh job |
| `resume` | target-aware resume generation (prompts, templates) from `evidence_items` |
| `briefing` | facts for the dashboard home page (the web composes the copy) |
| `knowledge` | reference data: countries, visas, salaries, skill graph; **all seeding** (`seeds.py`) |

A feature typically contains `models/`, `repositories/`, optional `domain/` (pure
dataclasses/enums) and service modules. Cross-feature use goes through another
feature's service or model, never its internals.

## Data

- **Schema**: SQLAlchemy models live in their feature; `careeros/db/models.py` imports
  them all so foreign keys and relationships resolve (`db/connection.py` and Alembic import it).
- **Migrations**: `alembic -c careeros/db/alembic.ini upgrade head` (single linear chain).
- **Reference data**: `infra/seeds/v1/*.yaml` → `career-os seed` (idempotent upserts).
- **Legacy tables** (`careeros/db/legacy/`): `evidence`, `timeline_*` — kept in the
  database, not read or written by code.

## Request lifecycle (API)

1. The browser only talks to the web app; Next rewrites `/api/*` to the internal API, so
   cookies are first-party and there is no CORS.
2. CSRF middleware: every non-GET/HEAD/OPTIONS request needs `X-CareerOS-CSRF: 1`
   (a cross-site form cannot set it), else 403.
3. `apps/api/app/main.py` mounts every router with `Depends(get_user_id)` — secure by
   default. Exceptions: `/api/auth/login|logout` and the GitHub OAuth callback
   (single-use state token).
4. `get_user_id` resolves the `careeros_session` cookie (`careeros/identity/auth/`); no
   anonymous fallback. `CAREEROS_E2E_AUTH_BYPASS=1` enables the `X-User-Id: user_e2e_*` header for
   local e2e scripts only.
5. The router validates input (Pydantic schema), calls a service, maps service errors to
   HTTP status codes and serializes the result.

## Authentication

Private, invite-only — there is no sign-up page. `careeros/identity/auth/`:

| Module | Does |
|---|---|
| `passwords.py` | argon2id hashes, ≥ 12 characters; unknown emails still pay one hash (no timing oracle) |
| `sessions.py` | random 256-bit token in an httpOnly `SameSite=Lax` cookie; the DB keeps only its sha256 (`auth_sessions`); 30-day sliding expiry |
| `throttle.py` | 5 failed logins per email / 20 per IP per 15 min → 429 (in memory, one worker) |
| `accounts.py` | create, set password (signs out everywhere), enable/disable, authenticate |
| `cli.py` | `career-os user add / passwd / list / disable / enable / signout` |

`apps/web/proxy.ts` only checks that the cookie exists (fast redirect to `/sign-in`); the
API is the authority on every request.

## Jobs pipeline

```
infra/config/companies.yaml ──► ingest.sync_all ──► jobs ──► scan.run_scan ──► career_scores ──► inbox
  74 boards: Greenhouse,         fetch (6 boards       shared    the user's titles,   one row per
  Lever, Ashby, Workday          at a time), keep      by all    rescore only what    (user, job)
                                 relevant titles,      users     changed
                                 close what vanished
```

- **Sources** (`careeros/jobs/sources/ats/`): one module per ATS, public JSON APIs only.
  Greenhouse, Lever and Ashby return a whole board in one request. Workday pages 20 at a
  time without descriptions, so it searches server-side (`workday_search`), skips detail
  requests for stored or irrelevant postings and caps details per run (`MAX_DETAILS`).
- **Sync** (`ingest.py`): postings whose title matches `titles.include` (plus every
  user's target roles) and no `titles.exclude` phrase are upserted into `jobs`. Unchanged
  postings only get `last_seen_at`; changed ones get a new `content_hash`; postings gone
  from a fully read board get `closed_at` (a partial read closes nothing). Each board's
  outcome is kept in `job_board_runs`. A Postgres advisory lock serializes syncs.
- **Extraction** (`extraction.py`): skills, seniority, remote, salary range, visa
  stance from the posting text — deterministic, shared with the ApplyPilot import.
- **Scan** (`scan.py`): open jobs whose title has every word of one of the user's roles
  (any order), scored only when `input_hash` = posting content + profile fingerprint +
  `SCORER_VERSION` changed. Scores are upserted; closed jobs drop out of every list.
- **Scheduler** (`scheduler.py`): with `JOB_SYNC_INTERVAL_HOURS` > 0 the API runs sync +
  rescore-everyone on that interval in a daemon thread.
- **Apply**: every posting links to the company's own page (`application_url`).

## Background work

Long operations (job scan, CV extraction, Career Graph build, market refresh) run as
FastAPI background tasks tracked by `careeros/shared/background.py`:

- `JobStore.create(owner)` → the client polls `…/{job_id}/status`
  (`status`, `progress`, `logs`, `result`, `error`).
- Owner-checked (`get_owned` → 403 for other users); finished jobs are pruned after 6 h.
- `create_unless_active(label)` gives single-flight behaviour (one market crawl at a time).
- State is in process memory: **one API worker only** until it is moved to Redis.

## External services

| Service | Where | Notes |
|---|---|---|
| OpenRouter (LLM) | `careeros/shared/llm.py` | retries 429/5xx/timeouts; `LLMNotConfiguredError` lets callers fall back (reasoning → template) |
| GitHub | `careeros/evidence/github.py`, `careeros/identity/github_account.py` | user's OAuth token, encrypted at rest (`careeros/shared/crypto.py`) |
| Company job boards | `careeros/jobs/sources/ats/` | public Greenhouse / Lever / Ashby APIs and Workday's site JSON; retries 429/5xx |
| ApplyPilot | `careeros/jobs/sources/applypilot/` | optional import from a local SQLite file (`career-os jobs import-applypilot`) |

## Web app

- `app/` = routing only. Dashboard pages are Server Components that fetch the first
  render through `lib/api/server.ts` and hand it to a client view in `_components/`.
  Each route has `loading.tsx` and `error.tsx`.
- `features/<name>/` = types + API calls (`api.ts` for the browser, `server.ts` for
  Server Components).
- No direct database access from the web app.

## Known limits

- In-process background jobs and OAuth state (single worker).
- Portfolio crawler fetches user-supplied URLs without blocking private addresses (SSRF).
- Known bugs pinned as strict `xfail` tests: HN parser substring matching and visa negation.
- Job requirements come from keyword matching (`extraction.py`); scores inherit its blind
  spots until extraction moves to the LLM layer.
