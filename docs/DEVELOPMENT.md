# Development

## Setup (once)

```bash
python -m venv venv && venv/Scripts/activate        # Windows; source venv/bin/activate elsewhere
pip install -r requirements-dev.txt
pip install -e .                                     # careeros + apps importable from anywhere
cp .env.example .env                                 # fill in DATABASE_URL, OPENROUTER_API_KEY, Clerk, GitHub
alembic -c careeros/db/alembic.ini upgrade head
career-os seed                                       # reference data from infra/seeds/v1
cd apps/web && npm install                           # web app (uses apps/web/.env.local for Clerk keys)
```

Re-run `pip install -e .` whenever a new top-level package is added.

## Run

| What | Command |
|---|---|
| API | `uvicorn apps.api.app.main:app --reload --port 8000` |
| Web | `cd apps/web && npm run dev` (http://localhost:3000) |
| CLI | `career-os --help` |

The web app needs the API running for every dashboard page. The API docs are at
http://localhost:8000/docs.

## Configuration

All settings come from the environment / root `.env`, read once by
`careeros.shared.config.get_settings()`. `.env.example` lists every variable.
Notable ones:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL (`postgresql+psycopg://…`) |
| `OPENROUTER_API_KEY`, `DEFAULT_MODEL`, `LLM_BASE_URL` | LLM client |
| `CLERK_JWKS_URL`, `CLERK_WEBHOOK_SECRET` | auth; the webhook answers 503 without the secret |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for stored OAuth tokens |
| `GITHUB_CLIENT_ID` / `_SECRET` / `_REDIRECT_URI` | GitHub OAuth |
| `WEB_APP_URL` | where OAuth sends the browser back (default http://localhost:3000) |
| `LOG_LEVEL` | default `INFO` |
| `CAREEROS_E2E_AUTH_BYPASS` | `1` only for local e2e scripts — never deployed |

Web (`apps/web/.env.local`): Clerk publishable/secret keys, `NEXT_PUBLIC_API_URL`, and
optionally `API_URL` for server-to-server calls.

## Tests and checks

```bash
pytest                      # offline: tests/unit + tests/smoke — no DB, network or LLM needed
pytest -m integration       # live DB / network / LLM (tests/integration)
ruff check .
cd apps/web && npx tsc --noEmit && npx eslint . && npm run build
```

| Folder | Contains |
|---|---|
| `tests/unit` | pure logic; HTTP and DB are faked |
| `tests/smoke` | wiring: every module imports, route inventory, auth on every route, architecture rules |
| `tests/integration` | needs real services; auto-marked `integration`, skipped by default |
| `tests/manual` | standalone scripts (`python tests/manual/…`), never collected |

Known bugs are pinned as `@pytest.mark.xfail(strict=True)`: fixing one turns the test
into an unexpected pass, which fails the run until the marker is removed.

## Reference data

Everything seeded lives in `infra/seeds/v1/` (YAML), loaded by
`careeros/knowledge/seeds.py`:

```bash
career-os seed                  # all, in dependency order
career-os seed roles sources    # selected datasets
```

| Dataset | File(s) | Behaviour |
|---|---|---|
| `reference` | `countries/`, `visa/`, `salaries/` | merge / update in place |
| `skills` | `skills.yaml` | insert-only (existing slugs kept) |
| `roles` | `roles.yaml` | upsert by slug; metadata merged |
| `goals` | `goals.yaml` | upsert |
| `sources` | `evidence_sources.yaml` | upsert + `suggested_source_ids` on roles; also read at runtime |

To change reference data, edit the YAML and re-run the seed — not the code.

## Database changes

1. Change or add the model in its feature's `models/`.
2. If it is a new model, import it in `careeros/db/models.py`.
3. `alembic -c careeros/db/alembic.ini revision --autogenerate -m "…"`, review, then `upgrade head`.

## Operational scripts (`scripts/`)

| Script | Use |
|---|---|
| `sync_jobs_from_applypilot.py` | import ApplyPilot's SQLite jobs into PostgreSQL |
| `backfill_job_metadata.py` | enrich old `career_scores.explanation` rows with job metadata |
| `backfill_decisions.py` | add Decision Contract v1 to old score rows (rules only, no LLM) |

## Conventions

- New feature code goes in `careeros/<feature>/`; routers stay HTTP-only.
- Settings via `get_settings()`, LLM via `get_llm_client()`, logs via `logging`.
- Web data: `features/<name>/api.ts` (browser) or `server.ts` (Server Components) — never `fetch` directly.
- Update `CHANGELOG.md` with every change.
