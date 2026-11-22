# Development

## Setup (once)

```bash
python -m venv venv && venv/Scripts/activate        # Windows; source venv/bin/activate elsewhere
pip install -r requirements-dev.txt
pip install -e .                                     # careeros + apps importable from anywhere
cp .env.example .env                                 # fill in DATABASE_URL, OPENROUTER_API_KEY, GitHub
alembic -c careeros/db/alembic.ini upgrade head
career-os seed                                       # reference data from infra/seeds/v1
career-os jobs sync                                  # read the company boards (~5 min the first time)
cd apps/web && npm install                           # web app
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
| `OPENROUTER_API_KEY`, `DEFAULT_MODEL`, `LLM_BASE_URL` | LLM client (interactive model) |
| `LLM_FAST_MODEL`, `LLM_TASK_MODELS` | bulk model (default = `DEFAULT_MODEL`); per-task overrides `task=model,…` |
| `LLM_DAILY_BUDGET_USD`, `LLM_USER_DAILY_BUDGET_USD`, `LLM_BULK_BUDGET_SHARE` | daily caps (2.00 / 0.50 / 0.7); `0` = no cap |
| `LLM_MAX_CONCURRENCY` | calls in flight per process (4) |
| `SESSION_COOKIE_SECURE` | `true` (default) in production; `false` for http://localhost |
| `DB_CONNECT_TIMEOUT`, `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | fail fast on an unreachable DB; pool 5 + 5 |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for stored OAuth tokens |
| `GITHUB_CLIENT_ID` / `_SECRET` / `_REDIRECT_URI` | GitHub OAuth |
| `WEB_APP_URL` | where OAuth sends the browser back (default http://localhost:3000) |
| `JOB_SYNC_INTERVAL_HOURS` | API re-reads every company board and rescores everyone this often; `0` (default) = off |
| `LOG_LEVEL` | default `INFO` |
| `CAREEROS_E2E_AUTH_BYPASS` | `1` only for local e2e scripts — never deployed |

Web: only `API_URL` (default http://localhost:8000). It is read at build time for the
`/api/*` rewrite, so the browser always calls the same origin. No auth keys, no DB access.

## Accounts

On the website:

1. **First account** — open the site; while it has no account, `/sign-in` shows *Create
   account*. That account is the admin. Setup then closes for good.
2. **Friends** — Settings → Account → Invites → *Create link* (optionally for one email).
   The link is shown once, works once and expires in 7 days. Pending links can be revoked.
3. **Password** — Settings → Account → *Change password* (signs out your other devices).

From the server (api container terminal), for recovery and administration:

```bash
career-os user passwd friend@example.com                 # reset a forgotten password; signs them out everywhere
career-os user add someone@example.com --admin           # create an account directly (prompts for a password)
career-os user list | disable | enable | signout
```

Users created under Clerk keep their rows and data — give each one a password with
`career-os user passwd <email>`.

## Jobs

```bash
career-os jobs sync                        # all boards (or --company stripe --company nvidia)
career-os jobs sync --company acme --dry-run   # check a new board without writing
career-os jobs boards                      # open postings + last sync per company
career-os jobs scan you@example.com        # score what changed for one user
career-os jobs enrich --limit 300          # LLM reads new postings (also part of every scheduled cycle)
career-os jobs import-applypilot           # optional: copy a local ApplyPilot DB in
career-os llm-usage --days 7               # LLM calls, tokens and cost vs today's budget
```

Add a company: one line in `infra/config/companies.yaml` (the file explains the four
ATS formats), then `career-os jobs sync --company <key> --dry-run`. Only boards that
answer with jobs belong there. Tune what gets stored with `titles.include/exclude`;
each user's target roles (Settings) are added automatically.

## Deploy (Coolify)

Live at https://career.abdullokh.xyz (Coolify project **CareerOS**).

1. DNS (Cloudflare): `career` → CNAME `coolify.abdullokh.xyz`, proxied — like the other apps.
2. **Database** — Coolify → New resource → PostgreSQL → *PGVector 17*; name `careeros-db`,
   user and database `career_os`. Backups tab: daily `30 3 * * *` UTC, local retention
   14 backups / 14 days / 2 GB (add S3 storage for off-server copies).
3. **App** — New resource → Public repository `https://github.com/TriTetra/Job-Status`,
   branch `main`, build pack **Docker Compose**, compose file `/docker-compose.prod.yml`.
   Advanced: *Predefined network* → **Connect to predefined network** (so `api` can reach
   the database); *Build arguments* → **Managed manually in Dockerfile** (secrets stay out
   of image builds).
4. Domains: **web** → `https://career.abdullokh.xyz:3000` (`:3000` is the container port).
   `api` and `db` get no domain — they stay on the internal network.
5. Environment: `DATABASE_URL` = the database's *Postgres URL (internal)* exactly as Coolify
   shows it (`postgres://…` is accepted), `WEB_APP_URL=https://career.abdullokh.xyz`, `OPENROUTER_API_KEY`, optionally
   `GITHUB_*` (`GITHUB_REDIRECT_URI=https://career.abdullokh.xyz/api/oauth/github/callback`).
   `SERVICE_PASSWORD_64_TOKENKEY` is generated by Coolify on the first deploy and kept —
   never change it (it decrypts stored OAuth tokens).
6. Deploy. Every API start runs `alembic upgrade head` and the idempotent `career-os seed`
   (`SEED_ON_START=false` to skip).
7. Open the site and create the first (admin) account; invite friends from Settings.
   The API reads all company boards 2 minutes after start, then refreshes boards,
   extracts facts and rescores every `JOB_SYNC_INTERVAL_HOURS` (6).

Images: multi-stage, non-root, healthchecked; API ≈ slim Python + venv, web = Next.js
standalone. Memory caps 768 MB (api) / 384 MB (web); logs rotate at 3 × 10 MB. The database
is its own Coolify resource: app deploys never restart it, backups and restores are in its
Backups tab.

Moving an existing database in: `pg_dump --no-owner` from the old one, `psql` into the
`db` service, then redeploy (migrations bring it to head).

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
| `backfill_job_metadata.py` | enrich old `career_scores.explanation` rows with job metadata |
| `backfill_decisions.py` | add Decision Contract v1 to old score rows (rules only, no LLM) |

## Conventions

- New feature code goes in `careeros/<feature>/`; routers stay HTTP-only.
- Settings via `get_settings()`, LLM via `get_llm_client()`, logs via `logging`.
- Web data: `features/<name>/api.ts` (browser) or `server.ts` (Server Components) — never `fetch` directly.
- Update `CHANGELOG.md` with every change.
