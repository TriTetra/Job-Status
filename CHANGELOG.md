# Changelog

Her commit, her mimari karar, her belge değişikliği burada kayıt altında.  
Sıralama: en yeniden en eskiye.

---

## Phase Tamamlanma Tablosu

| Phase | İçerik | Durum | Tarih |
| Refactor Step 1 — Dead Code Removal | Removed unused core/events, memory, timeline, 6 unused core/domain subpackages, career_os/data, GapAnalyzer, MatchingService, CareerDecisionEngine, 9 debug scripts, 9 unused web components, 4 unused npm deps; API import 28s → 1.7s | ✅ Tamam | 2026-10-28 |
| Refactor Step 0 — Test Safety Net | pyproject.toml (pytest + ruff), tests split into unit/smoke/integration/manual, offline unit + smoke tests, known bugs pinned as strict xfail | ✅ Tamam | 2026-10-28 |
| Phase D — Opportunities Gating Fix | Removed min_score filtering on backend list_jobs, showing all scored opportunities (strong/look/low fit) with collapsible low fit groups | ✅ Tamam | 2026-08-09 |
| Phase D — Opportunities LinkedIn UI | Split-panel layout for Opportunities (/inbox) with compact cards, detail view panel, operational buttons, and enriched backend scoring explanation JSONB metadata | ✅ Tamam | 2026-08-08 |
| Phase D — Market Intelligence Hybrid | 3-layer hybrid extraction engine (Regex keywords + learnable registry + LLM OpenRouter fallback) for HackerNews and TechCrunch feeds | ✅ Tamam | 2026-08-08 |
| Phase C — Settings Sidebar Navigation UI | Upgraded settings interface (/settings) to use Notion/Linear-style Sol Sidebar navigation, removed emojis in favor of Lucide icons, and integrated compact grid systems | ✅ Tamam | 2026-08-07 |
| Phase C — Settings UI/UX Refactoring | Refactored Settings layout into premium card-based containers, added Recharts scoring weights pie chart with dynamic client loading, and built a profile strength completion progress bar | ✅ Tamam | 2026-08-07 |
| Phase C — Settings Page Integration | Implemented a 4-tab Settings dashboard (/settings) enabling users to modify their profiles, work preferences, scoring weights, and connected accounts with secure Clerk JWT token forwarding | ✅ Tamam | 2026-08-07 |
| Phase C — Database connection pool caching | Created centralized global postgres client caching on globalThis in development, preventing connection leaks (Error 53300) during hot reloads | ✅ Tamam | 2026-08-07 |
| Phase C — Briefing Smart Templates | Implemented rule-based greeting logic, contextual day-of-week subtitles, active verbs for brief lines, momentum-based progress narratives, and dynamic day/night closings | ✅ Tamam | 2026-08-07 |
| Phase C — Briefing Database Integration | Connected Briefing page server-side to direct PostgreSQL database, replacing mock static data with live user profiles, top opportunities, and evidence counts | ✅ Tamam | 2026-08-07 |
| Onboarding UI Bug Fixes & State Recovery | StepEvidence mount state recovery check to retrieve resume_doc_id from onboarding state on load, preventing loss of upload status after GitHub OAuth redirects | ✅ Tamam | 2026-07-16 |
| Onboarding E2E Validation | E2E integration test script (test_onboarding_e2e_wizard.py); full wizard verification (Identity -> Goals -> Evidence CV/GitHub/Portfolio -> Building -> READY state transitions); DB integrity check (Evidence items, prefs, graph nodes count) | ✅ Tamam | 2026-07-16 |
| Phase 6 — Portfolio Crawler | BeautifulSoup portfolio website crawler (portfolio_crawler.py); keyword technology heuristics; POST /portfolio/crawl, GET /portfolio/status, DELETE /portfolio routes; client API & ExtractionResult UI URL connect input form | ✅ Tamam | 2026-07-16 |
| Phase 7 — Multi-Source Evidence Aggregation | Backend aggregation engine (confidence_aggregator.py); SOURCE_WEIGHTS mapping (GitHub 0.5, Portfolio 0.3, Resume 0.2); GET /skills/aggregated API route; getAggregatedSkills onboarding client method; ExtractionResult UI rewrite with source logos & badges | ✅ Tamam | 2026-07-16 |
| Phase 4 — GitHub OAuth & Repo Analyzer | GITHUB_CLIENT_ID credentials; cryptography Fernet encryption for access tokens; OAuth endpoint registration; oauth.py authorize/callback/status/disconnect routes; GitHubAnalyzer API client; create_github_evidence; ExtractionResult UI buttons & sync stats | ✅ Tamam | 2026-07-16 |
| Phase 5 — Career Graph Integration | Real-time CareerGraph generation from DB evidence items; clearance of old nodes; creation of DB CareerGraphNodes (skills, projects, experiences); dynamic edge construction via technology matching; /career-graph API & client update; TS checks | ✅ Tamam | 2026-07-16 |
| Evidence Intelligence Phase 3 — Evidence Review UI | GET /items, DELETE /items/{id} endpoints; FastAPI routing order collision fix; onboardingApi client update; ExtractionResult review component; step-evidence.tsx integration; TS fixes | ✅ Tamam | 2026-07-16 |
| Neon WebSocket/443 Bağlantısı | @neondatabase/serverless eklendi; lib/db/onboarding.ts → port 443 HTTPS ile Neon'a bağlanıyor (WARP gerektirmez); dashboard layout FastAPI fetch yerine direkt DB fonksiyonu çağırıyor; createRouteMatcher deprecation düzeltildi | ✅ Tamam | 2026-07-16 |
| Next.js 16 Proxy Migration | middleware.ts → proxy.ts (Next.js 16 convention); proxy basitleştirildi: sadece auth.protect(), yavaş backend fetch kaldırıldı; onboarding redirect dashboard layout'ta kalıyor | ✅ Tamam | 2026-07-16 |
| Onboarding Guard — Dashboard Layout | dashboard layout.tsx'e server-side onboarding guard eklendi: state != READY ise doğru adıma redirect; middleware timeout 2s→5s; iki katmanlı koruma (middleware + layout) | ✅ Tamam | 2026-07-16 |
| Evidence Step UI — Layout Consistency | step-evidence.tsx tam yeniden yazıldı: space-y-3, identity/goals ile aynı label/chip/button stili; 3 state (upload/processing/done); done state'te Sources chips (CV ✓, + GitHub, + Portfolio inline expand) + Skills chips + Continue butonu; ExtractionResult wizard'dan çıkarıldı | ✅ Tamam | 2026-07-16 |
| Evidence Intelligence Phase 2 — Resume Pipeline | PDF→LLM→skills pipeline: PDFParser (PyMuPDF), ResumeExtractor (OpenRouter), SkillMatcher (fuzzy+alias), process_resume(); mock run_extraction replaced with real pipeline; 14 evidence items from test PDF (11/12 canonical match) | ✅ Tamam | 2026-07-16 |
| Evidence Intelligence Phase 1 — DB Foundation | 5 tables (resume_documents, skills, evidence_items, connected_accounts, career_graph_nodes), 5 SQLAlchemy models, Alembic migration (evidence_intel_001), seed script — 87 canonical skills inserted | ✅ Tamam | 2026-07-16 |
| Goals Phase 3b — UI Polish | step-goals.tsx: emoji kaldirildi, kategori grouping kaldirildi, identity ile ayni layout dili (space-y-3, py-1.5, uppercase labels, Check-only chips) | ✅ Tamam | 2026-07-16 |
| Goals Phase 3 — Frontend Refactor | step-goals.tsx rewrite (GOAL_CATEGORIES, WORK_ARRANGEMENTS, ISO country codes, progressive salary, API roles); constants.ts ISO codes; api.ts saveGoals updated; types.ts OnboardingStatus preferences field; TS clean | ✅ Tamam | 2026-07-16 |
| Goals Phase 2 — Preferences API | GET /api/preferences, PATCH /api/preferences; save_goals updated to use career_preferences table; OnboardingStateOut includes preferences; 7/7 tests passed | ✅ Tamam | 2026-07-16 |
| Goals Phase 1 — career_preferences DB | Migration (career_prefs_001), CareerPreferences model, CareerPreferencesRepository; `pref_metadata` workaround for SQLAlchemy reserved name | ✅ Tamam | 2026-07-16 |
| Country Combobox + Logo | Country dropdown → SearchableCombobox (region grouping, 55 ülke); AplioLogo sm→md; WizardShell header compact | ✅ Tamam | 2026-07-15 |
| Phase 2 Step 5+6 | Backend IdentityPayload fix (career_level_origin, slug→UUID lookup, custom_role branching) + E2E 4/4 test geçti | ✅ Tamam | 2026-07-15 |
| Phase 2 Step 3 + 4 | SearchableCombobox hybrid rewrite (debounce, categories, keyboard nav, ARIA, Loader2) + step-identity.tsx updated | ✅ Tamam | 2026-07-15 |
| Phase 2 Step 2 | Frontend rolesApi client (api/roles.ts) — Role + RoleSearchResult types, 4 method, TS temiz | ✅ Tamam | 2026-07-15 |
| Phase 2 Step 1 | Roles API: GET /api/roles, /search (scored), /categories, /{slug} — 5/5 test geçti | ✅ Tamam | 2026-07-15 |
| Roles Seed (Phase 1.5) | 180 canonical tech roles batch-upserted into `roles` table via idempotent seed script | ✅ Tamam | 2026-07-15 |
| Model Sync | SQLAlchemy model dosyaları UUID-PK migration şemasına güncellendi; CustomRole, RoleAlias modelleri oluşturuldu | ✅ Tamam | 2026-07-15 |
| Roles & UserRoles (Phase 1) | Career Intelligence Graph migrations (roles, custom_roles, user_roles with XOR constraint, role_aliases) | ✅ Tamam | 2026-07-15 |
| Phase A.3 Ext | Identity Step Redesign & Scroll-free layout fit (compact spacing, timezone removed) | ✅ Tamam | 2026-07-15 |
| Bugfix | Auto-provision user on state query (resolves login redirection error) | ✅ Tamam | 2026-07-15 |
| Phase A.7 | Onboarding BUILDING: Career Graph generation, SVG graph animation with framer-motion, typewriter logs | ✅ Tamam | 2026-07-15 |
| Phase A.6 | Onboarding Evidence: Resume upload, background extraction job, status polling, real-time typewriter logs | ✅ Tamam | 2026-07-15 |
| Phase A.5 | Onboarding Goals Step: ChipMultiSelect, SearchableMultiSelect, validation, API integration | ✅ Tamam | 2026-07-15 |
| Phase A.4 | Backend API (onboarding router + Clerk webhook) + middleware redirect | ✅ Tamam | 2026-07-15 |
| Phase A.3 | Onboarding wizard shell: WizardShell, StepWelcome, StepIdentity, StepGoals | ✅ Tamam | 2026-07-15 |
| Phase A.2 | Aplio rebrand (AplioLogo), users DB migration, UserRepository | ✅ Tamam | 2026-07-15 |
| Phase A.1 | Clerk Auth: middleware, ClerkProvider, sign-in/sign-up pages, UserButton, Aplio brand | ✅ Tamam | 2026-07-15 |
| Frontend Days 1-5 | Next.js 16 app shell, Briefing page, Inbox, Companies — typography-first design | ✅ Tamam | 2026-07-15 |
| Phase 0 | Hazırlık: git tag, backup, API key rotation, architecture planning | ✅ Tamam | 2026-07-13 |
| Phase 1A | PostgreSQL DB layer: 4 tablo, Alembic migrations, repositories | ✅ Tamam | 2026-07-13 |
| Phase 1B | Career Scores → PostgreSQL; skill extraction fix; threshold fix | ✅ Tamam | 2026-07-14 |
| Phase 1C | Scan history tracking: `scan_history` tablosu, bulk diff | ✅ Tamam | 2026-07-14 |
| Phase 2A | `packages/intelligence/` migration; backward-compat shim | ✅ Tamam | 2026-07-14 |
| Phase 2B | `services/hiring-agent/` CV scoring; OpenRouter; GitHub token fix | ✅ Tamam | 2026-07-14 |
| Phase 2G | Evidence Graph → DB: `evidence` tablosu, `EvidenceRepository`, `EvidenceBuilder` | ✅ Tamam | 2026-07-14 |
| Phase 2I | Skill Graph YAML: 68 skill, 229 topic, `SkillLoader`, hardcode sıfır | ✅ Tamam | 2026-07-14 |
| Phase 2J | Application Engine: `services/application_engine/cli.py`, 6 komut, state machine | ✅ Tamam | 2026-07-14 |
| Refactor | Plugin + Config-Driven Architecture: `config/plugins.yaml`, `ResumeParserPlugin` ABC | ✅ Tamam | 2026-07-14 |
| Event Bus | Thread-safe pub/sub: `events/`, 18 domain event tipi | ✅ Tamam | 2026-07-14 |
| ApplyPilot Plugin | `JobSourcePlugin` ABC, SQLite client/adapter, config-driven | ✅ Tamam | 2026-07-14 |
| Single DB | PostgreSQL `jobs` tablosu, `JobRepository`, 562 job sync | ✅ Tamam | 2026-07-14 |
| Multi-User | `user_id` 5 tabloya eklendi, repo/caller güncellemesi | ✅ Tamam | 2026-07-14 |
| Week 3 Domain | `packages/domain/` — identity/job/intelligence; 7/7 test | ✅ Tamam | 2026-07-14 |
| Phase 2C | Target-aware resume generator: 4 LLM call, `available_skills` constraint | ✅ Tamam | 2026-07-14 |
| Phase 3 (CI) | Company Intelligence: enricher, memory service, per-company advice | ✅ Tamam | 2026-07-14 |
| Phase 3 (MI) | Market Intelligence: HN "Who is Hiring?" scanner, TechCrunch RSS | ✅ Tamam | 2026-07-14 |
| Phase 3 (GH) | GitHub Enrichment: 9 real metrics, hallucination fix, `loc_count` | ✅ Tamam | 2026-07-14 |
| Phase 3 (TL) | Timeline Layer: `track_snapshot()`, auto-diff, `detect_changes()` | ✅ Tamam | 2026-07-14 |
| Phase 3 (KB) | Knowledge DB: 14 YAML → 5 country + 3 visa + 50+ salary rows | ✅ Tamam | 2026-07-14 |
| Phase 4A | FastAPI Gateway: 24 endpoint, CORS, Pydantic v2, live-tested | ✅ Tamam | 2026-07-14 |
| Phase 4B | Domain Migration: 15 entity → 6 subdomain (`core/domain/`) | ✅ Tamam | 2026-07-14 |
| Phase 4C | Service Extraction: `identity_service`, `job_intelligence` | ✅ Tamam | 2026-07-14 |
| Phase 4D | Unified CLI: `career-os` launcher, 4 native + 4 sub-groups (Typer) | ✅ Tamam | 2026-07-14 |
| Docs v1 | `docs/v1/` versioned layout; Phase 1/2/3 Architecture Reports | ✅ Tamam | 2026-07-14 |

---

## [Refactor Step 1] — 2026-10-28 — Dead Code Removal ✅

### Yapılan

Each removal was verified with grep (zero importers outside the module itself and its own test) and the import-all smoke test.

**Backend — removed (never wired into API/CLI/services):**
- `core/events/`, `core/memory/`, `core/timeline/` (+ their tests `test_event_bus`, `test_memory_layer`, `test_timeline_layer`)
- `core/domain/{analytics,application,company,learning,market,resume}/`; `core/domain/__init__.py` now exports only identity, job and intelligence entities
- `career_os/data/` (legacy ApplyPilot loader) and its integration test case
- `core/intelligence/gap_analyzer.py` (duplicated SkillGap/LearningRoadmap; depended on legacy `career_os`), `CareerDecisionEngine` in `opportunity_scorer.py`, `services/job_intelligence/application/matching_service.py`
- Debug scripts: `scripts/test_*.py` (6), `clear_and_test_db.py`, `check_user_evidence.py`, `diagnose_scan.py`
- Empty leftover `infrastructure/` directory

**Performance side effect:** `core/intelligence/__init__.py` no longer re-exports `SemanticMatcher`, so importing the API no longer loads sentence-transformers/torch. `app.main` import: **28s → 1.7s**. The semantic path imports it from `core.intelligence.semantic_matcher` (`scoring_service.py`).

**Web — removed:**
- 9 unused components in `components/ui/` (brief-sentence, company-organism-view, evidence-surface, insight-row, market-pulse, metric-card, opportunity-item, pipeline-stage, todays-focus-item)
- Unused deps: `@tanstack/react-query`, `date-fns`, `sonner`, `@neondatabase/serverless`

### Doğrulama
- `pytest`: 194 passed, 7 xfailed (offline suite) · `ruff check .`: clean · `tsc --noEmit`: clean · `npm run lint`: 77 problems (was 78, pre-existing)

### Bilinen / sonraki adım
- `docs/usage/*`, `career_os/README.md` still describe removed modules (were already stale) — to be rewritten in the docs step.

---

## [Refactor Step 0] — 2026-10-28 — Test Safety Net ✅

### Yapılan

- `pyproject.toml`: pytest config (`testpaths`, `pythonpath = [".", "apps/api"]`, `integration` marker deselected by default, 120s timeout) and ruff (`E9` + `F` rules; excludes `_archive`, vendored `services/hiring-agent`, migration versions)
- `requirements-dev.txt`: pytest, pytest-timeout, ruff
- `tests/` reorganized: `unit/` (pure), `smoke/` (wiring), `integration/` (live DB/network/LLM, auto-marked via `tests/conftest.py`), `manual/` (standalone scripts, not collected). Root `pytest` no longer crashes on `_archive/`.
- New offline tests: `unit/test_decision_builder.py`, `unit/test_hn_parser.py`, `unit/test_applypilot_adapter.py`, `smoke/test_api_wiring.py` (56-route inventory guard, auth dependency), `smoke/test_imports.py` (every backend module imports + cold entry-point imports)
- Known bugs pinned as `xfail(strict=True)` so fixing them forces the marker off: scan `job_dicts`/`job_meta` mismatch, anonymous → `"default"` user, e2e header bypass, `sponsors_visa = remote`, HN substring skill matching, HN "no visa sponsorship" negation, `core.domain` circular cold import
- `ruff --fix`: unused imports / placeholder-less f-strings removed; `TYPE_CHECKING` imports for `Application` ↔ `Email` forward refs
- Baseline commit of previously uncommitted Phase C/D work (`e1210d6`)

---

## [Phase C Step 6] — 2026-08-07 — Settings Sidebar Navigation UI ✅

### Yapılan

**Linear/Notion Sidebar Navigation** (`apps/web/app/(dashboard)/settings/_components/settings-shell.tsx`):
- Replaced the horizontal tabs navigation with a modern, sticky left sidebar layout.
- Configured state-aware styling (`var(--surface)`, `var(--text-primary)`, and `var(--accent)`) with smooth transitions.

**Emoji Removal & Icon Upgrades** (`apps/web/app/(dashboard)/settings/_components/scoring-tab.tsx`):
- Removed all emoticons in favor of clean Lucide React icons (`Target`, `Award`, `TrendingUp`, `Flame`).
- Wrapped Recharts inside a dynamic subcomponent to bypass React 19 server rendering hydration conflicts.

**API Parameter Alignment & Input Polish**:
- Adapted `profile-tab.tsx`, `preferences-tab.tsx`, and `scoring-tab.tsx` to call API client endpoints without passing redundant `userId` parameters (token is extracted securely server-side).
- Improved grid alignment and form inputs height.

---

## [Phase C Step 5] — 2026-08-07 — Settings UI/UX Refactoring ✅

### Yapılan

**Interactive Scoring Visualizer** (`apps/web/app/(dashboard)/settings/_components/scoring-chart.tsx` & `scoring-tab.tsx`):
- Installed `recharts` library with React 19 legacy dependency flag.
- Created `scoring-chart.tsx` subcomponent rendering a radial donut pie chart of matching weights.
- Dynamically imported the chart inside `scoring-tab.tsx` with `{ ssr: false }` to avoid SSR hydration mismatches.

**Profile Strength Tracker** (`apps/web/app/(dashboard)/settings/_components/profile-tab.tsx`):
- Added `calculateProfileCompletion` progress indicator evaluating field completeness.
- Displayed progress bar with gradient fills reflecting profile strength.

**Layout & Styling Polish**:
- Upgraded all tabs to premium `rounded-xl` card containers.
- Standardized typography with bold titles, descriptive captions, and clean margins.
- Expanded input paddings (`px-4 py-3`) and configured active ring focus states.

---

## [Phase C Step 4] — 2026-08-07 — Settings Page Integration ✅

### Yapılan

**Settings API Client** (`apps/web/features/settings/api.ts` & `index.ts`):
- Implemented `getSettings()`, `updateSettings()`, `getWeights()`, and `updateWeights()` methods.
- Built a secure `settingsFetch` helper to fetch the Clerk session token dynamically and inject the `Authorization: Bearer <token>` header, mapping to the backend's token-dependent user endpoints.

**Settings Page Router** (`apps/web/app/(dashboard)/settings/page.tsx`):
- Created a server-side route wrapper with an authentication check to redirect unauthenticated users to `/sign-in`.

**Settings Components** (`apps/web/app/(dashboard)/settings/_components/`):
- `settings-shell.tsx`: Designed the main tab wrapper supporting transitions between Profile, Preferences, Scoring, and Account.
- `profile-tab.tsx`: Created the form to edit candidate name, email, titles, years of experience, and target roles.
- `preferences-tab.tsx`: Implemented arrangement checkboxes, salary limit inputs, and preferred company size options.
- `scoring-tab.tsx`: Designed 4 interactive weight sliders (Fit, Acceptance, Career, Market) with live validation ensuring total weights sum up to exactly 100%.
- `account-tab.tsx`: Configured integrations view supporting Clerk accounts, dynamic GitHub and Portfolio deletions, and JSON backup exports carrying Clerk JWT credentials.

---

## [Phase C Step 3] — 2026-08-07 — Database Connection Leak Fix ✅

### Yapılan

**Global Database Client** (`apps/web/lib/db/client.ts`):
- Created a centralized postgres connection pool client that caches the `sql` instance on `globalThis` in development.
- Configured max connections limit to 10 and idle timeout to 20s to safeguard local postgres limits.

**Database Connection Cleanups** (`apps/web/lib/db/onboarding.ts` & `dashboard.ts`):
- Removed duplicate local instantiations of `postgres(DATABASE_URL)` and replaced them with imports of `sql` from `client.ts`. This resolves the `PostgresError: sorry, too many clients already` error during Next.js hot reloads.

---

## [Phase C Step 2] — 2026-08-07 — Briefing Smart Templates ✅

### Yapılan

**Rule-Based Greeting Helper** (`apps/web/lib/db/dashboard.ts`):
- Added `buildGreeting` defining hourly greetings ("Still up", "Good morning", "Good afternoon", "Good evening").
- Built contextual day-based subtitles (e.g. "The week starts with X strong matches waiting" on Monday, "Wrapping up the week with..." on Friday, "Planning the week ahead" on Sunday).

**Active Brief Lines Heuristics** (`apps/web/lib/db/dashboard.ts`):
- Modified `buildBriefLines` to prioritize active opportunity counts followed by skills and projects, using strong active verbs.

**Momentum-Based Progress Narratives** (`apps/web/lib/db/dashboard.ts`):
- Rewrote `buildProgressSummary` to grade the profile depth by total evidence count (>=20: "rich and well-defined", >=10: "gaining depth", >0: "taking shape").

**Contextual Day/Time Closings** (`apps/web/lib/db/dashboard.ts`):
- Configured `buildClosing` to present weekend-aware and late-night-aware closing copy lines.

**Greeting Propagations** (`apps/web/app/(dashboard)/briefing/_components/briefing-greeting.tsx` & `page.tsx`):
- Updated type definitions to include `subtitle` and passed it from server component to the greeting layout.

---

## [Phase C Step 1] — 2026-08-07 — Briefing Direct DB Integration ✅

### Yapılan

**Direct DB Query Helper** (`apps/web/lib/db/dashboard.ts`):
- Created a new database layer to query users, career_scores, evidence_items, connected_accounts, and companies in parallel.
- Calculated briefing details dynamically (greeting name, evidence counts, opportunities, hiring companies).
- Handled the empty state gracefully with a list of items we are watching, and included stats (skills, projects, honors, experiences) inside the payload.

**Briefing API & Types Update** (`apps/web/features/briefing/api.ts` & `types.ts`):
- Retrieved the Clerk user ID using `auth()` from `@clerk/nextjs/server`.
- Replaced the hardcoded `MOCK_BRIEFING` static return with `getBriefingData(userId)`.
- Updated `BriefingEmptyData` type to accept optional `stats` dictionary.

**Empty State UI Component** (`apps/web/app/(dashboard)/briefing/_components/briefing-empty.tsx`):
- Rewrote the `BriefingEmpty` component to render dynamic stats cards (Skills, Projects, Honors, Experiences) matching user graph data.
- Configured CTA text to react to profile completeness (hasCompanies vs hasEvidence vs default).
- Connected the "Scan for new opportunities" button to navigate to `/inbox` using Next.js `useRouter`.

**Briefing Page & Layout Polish** (`apps/web/app/(dashboard)/briefing/page.tsx` & subcomponents):
- Computed dynamic daypart greetings on the server (`Good morning` / `Good afternoon` / `Good evening` / `Good night`) and propagated them to `<BriefingGreeting />` and `<BriefingEmpty />`.
- Wrote opportunities visibility check to hide the section header when there are no jobs matched (`opportunities.length === 0`), resolving white space issues.
- Connected CTA buttons in `<BriefingFocus />` and `<BriefingEvidenceProgress />` to execute Next.js router transitions using `ctaHref`.

**Evidence Summary Heuristics** (`apps/web/lib/db/dashboard.ts`):
- Filtered out empty metrics (e.g. "0 achievements captured") from the summary signals array, dynamically showing only populated categories.

**Legacy Code Cleanup**:
- Deleted the unused duplicate component directory `apps/web/components/narrative/`.
- Removed `mock.ts` file from `apps/web/features/briefing/` and clean-exported types from `index.ts`.

---

## [Phase 2 Step 5+6] — 2026-07-15 — Backend Verification + E2E Tests ✅

### Yapılan

**IdentityPayload güncellemeler** (`apps/api/app/routers/onboarding.py`):
- `career_level_origin` field eklendi (`"user" | "system" | "ai_estimated"`, default `"system"`)
- `current_role_id` max_length: 50 → 200 (uzun slug'lar için)

**save_identity 3-way branching** (UUID / slug / custom_ prefix):
- **UUID**: doğrudan `users.current_role_id` FK set edilir, `source='canonical'`
- **Slug** (static fallback IDs): `roles` tablosunda slug lookup → UUID alır, `source='canonical'`
- **`custom_` prefix**: `custom_roles` tablosuna upsert (idempotent: aynı user+title tekrar kullanılır), `users.current_custom_role_id` set edilir, `source='custom'`
- `career_level_origin`, `career_level`, `years_in_role` user'a yazılıyor
- `profile_data`'ya `current_role_title` eklendi
- `user_roles` INSERT: `custom_role_id` kolonu doğru handle ediliyor

**Frontend `step-identity.tsx`** (Step 4 tamamlandı):
- `careerLevelOrigin` state eklendi
- Slider onChange: `origin = "system"` (otomatik öneri)
- Career level buton onClick: öneriyle aynıysa `"system"`, farklıysa `"user"`
- `saveIdentity` çağrısına `career_level_origin` eklendi
- `onboardingApi.saveIdentity` type'ına `career_level_origin?` eklendi

**E2E Test Sonuçları:**

| # | Test | Durum | Not |
|---|---|---|---|
| 1 | Canonical role (slug) | ✅ | slug → UUID lookup çalıştı, `current_role_id=UUID, source=canonical` |
| 2 | Custom role | ✅ | `custom_roles` kaydı oluştu, `current_custom_role_id` set |
| 3 | Career level origin=user | ✅ | `career_level=mid, career_level_origin=user` (otomatiği override etti) |
| 4 | Role değişimi history | ✅ | Önceki `is_current=False, ended_at=bugün`, yeni `is_current=True` |

TypeScript: `npx tsc --noEmit` — 0 hata

---

## [Phase 2 Step 3+4] — 2026-07-15 — Hybrid SearchableCombobox + step-identity Güncelleme

### Yapılan

**SearchableCombobox tam yeniden yazım** (`apps/web/components/shared/searchable-combobox.tsx`):
- `ComboboxOption` interface: `{ id, title, category, aliases?, slug? }` — eski `Option` tipi kaldırıldı
- `initialOptions` prop: static fallback (anında hydration, backend down olsa bile çalışır)
- `onSearch` prop: async backend API fonksiyonu (300ms debounced)
- `clientSideSearch()` fallback: title/aliases/category skorlama, en iyi 10 sonuç
- Kategori bazlı gruplandırma (sticky header, `role="group"`)
- Keyboard nav: ↑↓ Enter Esc — flat index tüm grupları kapsar
- Custom rol kaçış yolu: `allowCustom`, `customLabel` template (`{query}` placeholder)
- WAI-ARIA: `role="combobox"`, `role="listbox"`, `role="option"`, `aria-expanded`, `aria-selected`
- Loading state: `Loader2 animate-spin` hem trigger'da hem dropdown'da
- `useRef<T | undefined>(undefined)` — React 19 tip uyumluluğu

**step-identity.tsx güncelleme** (Step 4):
- `rolesApi` import edildi `@/features/onboarding`'den
- `ComboboxOption` import edildi typed
- `staticRoles`: `ROLES[]` → `ComboboxOption[]` mapping (slug yok, aliases var)
- `handleRoleSearch`: `rolesApi.search(query, 12)` → `ComboboxOption[]` (useCallback ile)
- `SearchableCombobox` prop'ları: `options` → `initialOptions` + `onSearch`, `customLabel` eklendi

## [Onboarding UI Bug Fixes & State Recovery] — 2026-07-16 — OAuth State Recovery 🚀

### Yapılan

**OAuth State Kurtarma Bug Fix (`step-evidence.tsx`):**
- **Sorun**: Kullanıcı resume yükledikten sonra "Add GitHub" deyip OAuth yönlendirmesine gittiğinde, geri dönüşte React local state'i sıfırlandığı için taranan özgeçmiş verileri kayboluyor ve arayüz resume yükleme kutusuna geri dönüyordu.
- **Çözüm**: `StepEvidence` bileşeninin mount aşamasına veritabanı kontrolü eklendi (`onboardingApi.getState()`). Eğer kullanıcı daha önce resume yüklediyse DB'den gelen `resume_doc_id` tespit edilerek otomatik olarak `completed` durumuna geçilmesi (yüklü durumun korunması) sağlandı.

**Doğrulama**:
- TypeScript derleme denetimi (`npx tsc --noEmit`) 0 hatayla tamamlandı.

---

## [Onboarding E2E Validation] — 2026-07-16 — Full Wizard Integration Verification 🧙‍♂️

### Yapılan

**E2E Entegrasyon Test Betiği (`tests/test_onboarding_e2e_wizard.py`):**
- Identity, Goals, Evidence (CV Upload + GitHub Account Setup + Portfolio Connect) ve Building state geçişlerini sırasıyla tetikleyerek doğrulayan test betiği eklendi.
- **Mock PDF Üretimi**: fitz (PyMuPDF) kütüphanesi kullanılarak programlama dilleri, deneyimler ve projeler içeren mock bir CV PDF'i dinamik olarak oluşturuldu.
- **Veritabanı Durum (State) Kontrolleri**:
  - `connected_accounts` tablosunda mock GitHub entegrasyonu doğrulandı.
  - `evidence_items` tablosunda eklenen CV verilerinden 15 adet yetenek, deneyim ve proje kanıtı çıktığı doğrulandı.
  - `career_graph_nodes` tablosunda dinamik olarak 15 düğümlü (nodes) Career Graph oluşturulduğu ve bağlantıların (edges) kurulduğu doğrulandı.
  - `career_preferences` tablosundaki hedeflerin (goals) ve rollerin (roles) doğru formatta kaydedildiği doğrulandı.
- **Onboarding Durum Geçişi**: Kullanıcının onboarding durumunun en sonda hatasız bir şekilde `READY` aşamasına ulaştığı kanıtlandı.

**Doğrulama**:
- `test_onboarding_e2e_wizard.py` testi uvicorn sunucusu üzerinden başarıyla çalıştırıldı ve `[OK] E2E WIZARD TEST PASSED!` çıktısı elde edildi.

---

## [Phase 6 — Portfolio Crawler] — 2026-07-16 — BeautifulSoup Portfolio Scraper & Evidence Extraction 🌐

### Yapılan

**Portfolio Web Tarayıcısı (`apps/api/app/core/evidence/portfolio_crawler.py`):**
- Verilen herhangi bir portfolyo URL'ini HTTP ile çekip BeautifulSoup4 ile ayrıştıran `PortfolioCrawler` modülü eklendi.
- **Teknoloji Keyword Eşleştirme**: İçerisinde 30'dan fazla yaygın yazılım dilini, framework'ü ve veritabanı ismini barındıran regex/string anahtar kelime motoru entegre edildi.
- **Proje Çıkarımı (Heuristics)**: HTML içerisinde projelere, vaka çalışmalarına veya geçmiş işlere ait olabilecek bölümleri (`portfolio`, `project`, `case-study`) tespit edip proje ismi ve açıklamalarını ayıklayan algoritma tasarlandı.

**Backend API Rotaları (`apps/api/app/routers/evidence.py`):**
- **POST `/api/evidence/portfolio/crawl`**: Portfolyo URL'ini `connected_accounts` tablosuna yazar, web sitesini tarar ve ayıklanan yetenek/projeleri `portfolio` kaynağıyla veritabanına idempotently kaydeder.
- **GET `/api/evidence/portfolio/status`**: Kullanıcının bağlı portfolyo sitesini ve son senkronizasyon zaman damgasını döndürür.
- **DELETE `/api/evidence/portfolio`**: Portfolyo bağlantısını siler ve portfolio kaynaklı tüm verileri temizler.
- Rota çakışmalarını önlemek için parametrik `/{skill}` rotasının üzerinde tanımlandı.

**Frontend API & UI Güncellemeleri:**
- `onboardingApi` istemcisine `crawlPortfolio`, `getPortfolioStatus` ve `disconnectPortfolio` metotları entegre edildi.
- **`extraction-result.tsx`**:
  - Arayüze "Portfolio" URL giriş formu, crawl yüklenme animasyonu, bağlı portfolyo bağlantısı ve "Remove" butonu eklendi.
  - Portfolyo başarıyla tarandığında listeyi anında yenileyerek yeni yetenek ve projeleri gösterir.
  - Yeteneklerin kaynak badges alanına `portfolio` rozeti ve özel `Globe` ikonu eklendi.

**Doğrulama**:
- Mock HTML portfolio test betiği (`test_portfolio_crawler.py`) ile crawler metin tarama, proje yakalama, DB'ye yazma ve status/disconnect rotaları uçtan uca test edildi ve başarıyla geçti (`[OK] All Portfolio Crawler and router tests passed successfully!`).
- Frontend TypeScript derlemesi (`npx tsc --noEmit`) 0 hatayla tamamlandı.

---

## [Phase 7 — Multi-Source Evidence Aggregation] — 2026-07-16 — Multi-Source Aggregation & Weighted Scoring 📊

### Yapılan

**Backend Aggregation Motoru (`apps/api/app/core/evidence/confidence_aggregator.py`):**
- Kullanıcının tüm evidence_item'larını çekip `type == "skill"` olanları gruplayan ve her yetenek için ağırlıklı güven puanı hesaplayan yeni motor eklendi.
- **SOURCE_WEIGHTS**: GitHub (0.5), Portfolio (0.3), Resume (0.2) olacak şekilde kaynak ağırlıkları belirlendi.
- Ağırlıklı matematiksel formül: `weighted_sum / total_weight` hesaplamasıyla güven skoru harmonizasyonu yapıldı.
- Her yetenek için kaynak dökümü (`type`, `confidence`, `count`) hazırlandı.

**Backend API Endpoint (`apps/api/app/routers/evidence.py`):**
- **GET `/api/evidence/skills/aggregated`**: Ağırlıklı puanlara göre azalan sırada sıralanmış birleştirilmiş yetenek listesini döndürür.
- Rota çakışmalarını önlemek için parametrik `/{skill}` rotasının üzerinde tanımlandı.

**Frontend API & UI Güncellemeleri:**
- `onboardingApi` istemcisine `getAggregatedSkills()` metodu eklendi.
- **`extraction-result.tsx`**:
  - `skills` verileri `getAggregatedSkills` üzerinden, projeler ve iş deneyimleri ise `getEvidenceItems` üzerinden `Promise.all` ile paralel fetch edilecek şekilde güncellendi.
  - Her yeteneğin altında yer alan kaynaklara ait rozetler (`Resume (1)`, `GitHub (2)` vb.) ve bunlara özel kaynak ikonları (Lucide Github, FileText vb.) görselleştirildi.
  - Arayüz yerel state filtresi sayesinde yetenek silme tıklandığında anında kaldırılma simülasyonu eklendi.

**Doğrulama**:
- Mock veri test betiği (`test_multi_source_aggregation.py`) ile overlapping resume/github kanıtları eklendi, `/skills/aggregated` endpoint'i üzerinden matematiksel hesaplamanın doğruluğu (%93.6 confidence) başarıyla test edildi.
- Frontend tip denetimleri (`npx tsc --noEmit`) 0 hatayla tamamlandı.

---

## [Phase 4 — GitHub OAuth & Repo Analyzer] — 2026-07-16 — GitHub Integration & Token Encryption 🐙

### Yapılan

**Çevre Değişkenleri ve Token Güvenliği (`.env` & `token_encryption.py`):**
- GitHub OAuth App Credentials (`GITHUB_CLIENT_ID` ve `GITHUB_CLIENT_SECRET`) `.env` dosyasına eklendi.
- Fernet simetrik şifreleme algoritması kullanan `token_encryption.py` yardımcı modülü oluşturuldu. Kullanıcıların üçüncü taraf erişim anahtarları veritabanında (`access_token` kolonu) şifrelenmiş olarak saklanır.
- Token şifreleme anahtarı (`TOKEN_ENCRYPTION_KEY`) üretilerek `.env` dosyasına eklendi.

**OAuth Rotaları (`apps/api/app/routers/oauth.py`):**
- **GET `/api/oauth/github/authorize`**: CSRF (state token) korumasıyla OAuth akışını başlatır ve kullanıcıyı GitHub izin ekranına yönlendirir.
- **GET `/api/oauth/github/callback`**: Yetkilendirme kodu ile erişim anahtarını takas eder, kullanıcı bilgilerini çeker, token'ı şifreleyerek `connected_accounts` tablosuna yazar ve frontend onboarding sayfasına yönlendirir.
- **GET `/api/oauth/github/status`**: Kullanıcının GitHub bağlantı durumunu, kullanıcı adını, profil resmi ve repo sayısı gibi metaverileri döndürür.
- **DELETE `/api/oauth/github`**: Kullanıcının GitHub entegrasyon bağlantısını siler.
- **POST `/api/oauth/github/sync`**: Bağlı hesaba ait repoları analiz edip yetenek kanıtı çıkarım sürecini başlatır.
- Rotalar `apps/api/app/main.py` içerisine gateway seviyesinde kaydedildi.

**GitHub API & Kanıt Çıkarımı (`github_analyzer.py` & `github_evidence.py`):**
- **`GitHubAnalyzer`**: GitHub REST API üzerinden kullanıcının son güncellenen 20 reposunu, kod dili dağılımlarını (byte cinsinden) ve stars/size istatistiklerini çeker.
- **`create_github_evidence`**:
  - Repoları `project` tipinde evidence verisi olarak veritabanına kaydeder.
  - Repolarda kullanılan programlama dillerini fuzzy eşleştirme ontolojisiyle canonical yeteneklere bağlar ve dile ait byte oranı, yıldız ve commit sayılarına göre dinamik güven skoru hesaplayarak `skill` tipinde kanıt olarak kaydeder.
  - Çakışmaları önlemek için her senkronizasyonda eski GitHub kanıtlarını temizler (idempotency).

**Frontend API & UI Entegrasyonu:**
- `onboardingApi` client'ına `getGithubStatus`, `syncGithub` ve `disconnectGithub` metotları eklendi.
- **`extraction-result.tsx`**:
  - GitHub bağlantı durumunu kontrol eder ve bağlıysa kullanıcı adı, avatar ve eşitleme durumu bildirim panelini gösterir.
  - İlk bağlantıda repoları otomatik analiz eder, verileri veritabanından yeniden çekerek resume ve GitHub yeteneklerini tek listede birleştirir.
  - Kullanıcıya repoları el ile tekrar eşitleme (resync) veya GitHub bağlantısını kesme (disconnect) özellikleri sunar.

**Doğrulama**:
- Mock entegrasyon testi (`test_github_sync.py`) üzerinden status, veritabanı yazma ve confidence skoru hesaplama süreçleri test edildi ve başarıyla geçti (`[OK] GitHub Sync Database Logic OK!`).
- TypeScript derlemesi (`npx tsc --noEmit`) 0 hatayla tamamlandı.

---

## [Phase 5 — Career Graph Integration] — 2026-07-16 — Real-time Graph Generation 🎨

### Yapılan

**Backend Endpoint'leri ve Arka Plan Görevleri (`apps/api/app/routers/onboarding.py`):**
- **Dynamic Career Graph Generation**: `run_graph_building` arka plan görevi mock veri yerine veritabanındaki gerçek `EvidenceItem` verilerini okuyacak şekilde yeniden yazıldı.
- **`career_graph_nodes` DB Senkronizasyonu**:
  - Grafik oluşturma tetiklendiğinde kullanıcının eski grafik düğümleri (`CareerGraphNode`) temizlenir.
  - Veritabanından çekilen yetenekler (`skill`), projeler (`project`) ve iş deneyimleri (`experience`) ayrı ayrı `CareerGraphNode` modeliyle veritabanına yazılır.
- **Dynamic Edge (Bağlantı) Keşfi**:
  - Proje veya deneyimlerin `technologies` verileri, kullanıcının sahip olduğu yetenek listesiyle eşleştirilir.
  - Eşleşen teknolojiler için otomatik olarak `GraphEdge` (grafik kenarı) oluşturularak düğümler birbirine bağlanır. Bu sayede frontend'de animasyonlu bağlantı çizgileri korunur.
- **GET `/api/onboarding/career-graph`**:
  - Kullanıcının önbelleğe alınmış ve oluşturulmuş olan kariyer grafiğini (`nodes`, `edges` ve `stats` verilerini) döndüren yeni API rotası.

**Frontend Değişiklikleri (`apps/web/features/onboarding/api.ts`):**
- `getCareerGraph()` metodu onboarding API istemcisine (`apiFetch` yardımcısıyla) eklendi.

**Doğrulama**:
- `test_onboarding_api.py` betiğinde Goals payload tipleri düzeltildi.
- E2E testi taze başlatılan backend üzerinde başarıyla çalıştırıldı: PDF yükleme, extraction polling, ve veritabanı verilerinden dinamik grafik oluşturma işlemleri hatasız tamamlandı.
- TypeScript derleme testi (`npx tsc --noEmit`) 0 hatayla başarıyla tamamlandı.

---

## [Evidence Intelligence Phase 3 — Evidence Review UI] — 2026-07-16 — Review UI 🚀

### Yapılan

**Backend Endpoint'leri (`apps/api/app/routers/evidence.py`):**
- **GET `/api/evidence/items`**: Kullanıcının veritabanındaki tüm `EvidenceItem` verilerini listeler, `evidence_data.type` bilgisine göre gruplandırır (skills, projects, experiences vb.) ve azalan güven skoruna (confidence score) göre sıralar.
- **DELETE `/api/evidence/items/{item_id}`**: Kullanıcının hatalı yetenek tespitlerini listeden kaldırmasını (false positive filtering) sağlayan veritabanı silme rotası.
- **FastAPI Rota Sıralaması Düzeltmesi**: `/items` ve `/items/{item_id}` rotaları, FastAPI'nin rota eşleşme önceliği çakışması (FastAPI path template collision) nedeniyle param parametresi `/{skill}` tarafından yutuluyordu. Bu rotalar `/{skill}` rotasının yukarısına taşınarak çözüldü.

**Frontend Değişiklikleri (`apps/web/features/onboarding/api.ts`):**
- `getEvidenceItems(source?)` ve `deleteEvidenceItem(itemId)` metotları API istemcisine (`onboardingApi`) eklendi.

**ExtractionResult Review UI Bileşeni (`apps/web/app/(auth)/onboarding/_components/extraction-result.tsx`):**
- Özgeçmiş analizinin sonuçlarını, güven çubukları (confidence progress bar) ile gösteren review bileşeni oluşturuldu.
- `NarrativeSize` tip uyuşmazlıkları (`size="md"` ve `size="xs"` gibi tanımlı olmayan prop değerleri) giderildi.
- Kullanıcıya yanlış analiz edilmiş yetenekleri silme ve onboarding'e devam etme yeteneği verildi.

**Onboarding Entegrasyonu (`apps/web/app/(auth)/onboarding/_components/step-evidence.tsx`):**
- Özgeçmiş yüklemesi tamamlandığında, `step-evidence.tsx` artık doğrudan bir sonraki onboarding aşamasına yönlendirme yapmaz; bunun yerine `ExtractionResult` Review UI bileşenini ekrana getirerek kullanıcının verileri gözden geçirmesini sağlar.

---

## [Model Sync] — 2026-07-15 — SQLAlchemy Model ↔ Migration Senkronizasyonu 🔧

### Yapılan

**Problem:** Model dosyaları hâlâ `String(50)` PK kullanırken, yeni migration'lar `UUID` PK ile oluşturulmuştu. Bu uyumsuzluk seed script'in import aşamasında çökmesine neden oluyordu.

**Model Güncellemeleri:**
- **`core/domain/identity/role.py`** — `Role` modeli UUID PK'ya geçirildi. `slug`, `metadata_` (JSONB), `version`, `updated_at` alanları eklendi. Eski `String(50)` PK kaldırıldı.
- **`core/domain/identity/user_role.py`** — `UserRole` modeli UUID PK'ya geçirildi. `custom_role_id` (UUID FK → `custom_roles.id`) eklendi, XOR constraint dokümente edildi.
- **`core/domain/identity/user.py`** — `current_role_id` tipi `String(50)` → `Uuid` FK olarak güncellendi. `current_custom_role_id` ve `career_level_origin` alanları eklendi.
- **[NEW] `core/domain/identity/custom_role.py`** — Migration 002'ye karşılık gelen `CustomRole` modeli oluşturuldu: AI mapping (`mapped_role_id`, `mapping_confidence`, `mapping_source`, `mapping_metadata`).
- **[NEW] `core/domain/identity/role_alias.py`** — Migration 005'e karşılık gelen `RoleAlias` modeli oluşturuldu: rol unvan değişim geçmişi takibi.
- **`core/db/models/__init__.py`** — `CustomRole` ve `RoleAlias` import ve `__all__` listesine eklendi.

---

## [Roles Seed — Phase 1.5] — 2026-07-15 — 180 Canonical Tech Roles Seeded 🌱

### Yapılan

**Problem:** `roles` tablosu boştu. Career Intelligence Graph'ın çalışması için canonical rol ontolojisinin yüklenmesi gerekiyordu.

**Seed Script (`scripts/seed_roles_v1.py`):**
- 180 canonical tech rolü zengin metadata ile tanımlandı (JSONB `aliases` ve `metadata` alanları).
- Neon Serverless DB'de 180 tekil INSERT'in long-running transaction lock'a yol açması sorunu tespit edildi.
- `session_scope()` → `create_engine()` + `engine.begin()` ile doğrudan bağlantı yönetimine geçildi.
- Tekil INSERT döngüsü → **tek batch `INSERT ... ON CONFLICT (slug) DO UPDATE`** statement'ına dönüştürüldü.
- `CAST(:param AS jsonb)` kullanılarak SQLAlchemy'nin `:param` bind syntax'i ile PostgreSQL `::jsonb` cast'i arasındaki çakışma çözüldü.
- İdempotent: tekrar çalıştırıldığında mevcut rolleri günceller, yenilerini ekler.

**Kategori Dağılımı (180 Rol):**

| Kategori | Sayı |
|---|---|
| Engineering | 69 |
| AI/ML | 26 |
| Data | 15 |
| Management | 14 |
| Other | 12 |
| DevOps | 11 |
| Product | 11 |
| Design | 9 |
| QA | 9 |
| Research | 4 |

**Yardımcı Scriptler:**
- `scripts/test_db_insert.py` — Bağımsız DB bağlantı ve insert doğrulama.
- `scripts/verify_roles.py` — Kategori dağılımı ve örnek roller raporlama.
- `scripts/clear_and_test_db.py` — Idle transaction temizleme ve DB erişim testi.

---

## [Roles & UserRoles — Phase 1] — 2026-07-15 — Migrations Setup 🚀

### Yapılan

**Veritabanı & Alembic Migrations (`core/db/migrations/versions/`):**
- Önceki birleştirilmiş migration geri alınarak (`downgrade e1f2a3b4c5d6`), 5 adet sıralı ve bağımsız migration dosyası oluşturuldu:
  - **`001_roles`:** UUID birincil anahtarlı ve GIN indeksli `roles` tablosu oluşturuldu. (PostgreSQL GIN indeks kısıtlaması nedeniyle `metadata` ve `aliases` kolonları `JSONB` olarak tanımlandı).
  - **`002_custom_roles`:** Kullanıcıların girdiği özel rolleri ve bunların canonical rollere eşleşme oranlarını/kaynaklarını tutan `custom_roles` tablosu oluşturuldu. Yabancı anahtar `users.clerk_id` (`sa.String(128)`) olacak şekilde yapılandırıldı.
  - **`003_user_roles`:** Kariyer geçmişini tutan `user_roles` tablosu oluşturuldu. Bir kullanıcının aynı anda sadece tek bir güncel rolü olabilmesini (`is_current = true`) sağlayan kısmi benzersiz indeks (partial unique index) ve ya canonical ya da custom rol seçilmesini garanti altına alan **XOR constraint** (`chk_role_xor_custom`) eklendi.
  - **`004_users_career`:** `users` tablosuna `years_in_role`, `career_level`, `career_level_origin`, ve UUID bazlı `current_role_id` / `current_custom_role_id` kolonları eklendi.
  - **`005_role_aliases`:** Roller arasındaki unvan değişim ve evrim geçmişini takip eden `role_aliases` tablosu oluşturuldu.
- Tüm migration zinciri (`e1f2a3b4c5d6` -> `001_roles` -> `002_custom_roles` -> `003_user_roles` -> `004_users_career` -> `005_role_aliases`) veritabanında başarıyla çalıştırıldı (`alembic upgrade head`).

---

## [Roles & UserRoles] — 2026-07-15 — Roles & UserRoles History Implementation 🚀

### Yapılan

**Veritabanı ve Alembic Migration (`core/db/migrations/versions/...`):**
- `roles` tablosu oluşturuldu: Yetkinlik alanları (`id`, `title`, `category`, `aliases` (JSON), `esco_id`, `soc_code`) tanımlandı.
- `user_roles` tablosu oluşturuldu: Kullanıcının kariyer geçmişini (tarihsel rol kayıtları) takip etmek amacıyla `user_id` (`users.clerk_id` yabancı anahtarı ile), `role_id` (`roles.id` yabancı anahtarı ile), `started_at`, `ended_at`, `is_current`, `source` kolonları tanımlandı.
- 80'den fazla canonical tech rolü (Engineering, AI/ML, Data, DevOps, Product, Design, QA, Management, Research) aliases verileriyle birlikte migration aşamasında `roles` tablosuna seed edildi.
- `users` tablosuna hızlı arama amaçlı `current_role_id`, `years_in_role` ve `career_level` kolonları eklendi.

**Backend Modelleri ve Repositoriler:**
- `Role` ve `UserRole` SQLAlchemy modelleri `core/domain/identity/` altında tanımlandı ve paket dışa aktarımlarına dahil edildi.
- `User` modeline yeni kariyer kolonları eklendi.
- `RoleRepository` oluşturuldu: Roller üzerinde fuzzy arama (`search`) ve kategori bazlı filtreleme metodları implement edildi.

**Backend API & Router (`apps/api/app/routers/roles.py`):**
- `/api/roles/search?q=...` ve `/api/roles/categories` endpoint'leri yazılarak router FastAPI ana uygulamasına (`main.py`) eklendi.
- `/api/onboarding/identity` endpoint'i güncellenerek yeni rol ve kıdem seviyesi parametreleri (`current_role_id`, `current_role_title`, `years_in_role`, `career_level`) kabul edilecek şekilde genişletildi. Yeni rol kaydetme işlemi, `user_roles` tablosunda eski aktif rolü kapatıp yeni aktif rolü başlatacak şekilde transactional SQL komutlarına bağlandı.

**Frontend Bileşenleri ve Veri Katmanı:**
- `apps/web/features/onboarding/data/roles.ts` — 80+ rol listesi ve fuzzy arama fonksiyonu frontend tarafına eklendi.
- `SearchableCombobox` — Arama kutusunda kategorilere göre ayrılmış, klavye ile gezinme ve listede olmayan özel rol tanımı ("custom role") girmeyi destekleyen autocomplete dropdown bileşeni yazıldı.
- `step-identity.tsx` — Kimlik formu tamamen yenilendi:
  - Kullanıcıdan meslek başlığı `SearchableCombobox` ile alınıyor.
  - "Years in this role" kaydırıcısı (slider) eklendi ve seçilen yıla göre kariyer seviyesi otomatik tavsiye ediliyor (junior, mid, senior, staff, principal).
  - Kullanıcı tavsiye edilen kariyer seviyesini kart butonlar yardımıyla değiştirebiliyor.
- `step-goals.tsx` — Yeni `Role` veri yapısı doğrultusunda çoklu rol seçici alanı güncellendi.

---

## [Phase A.3 Extension] — 2026-07-15 — Identity Step Alignment & Redesign 🛠️

### Yapılan

**Layout Güncellemesi (`apps/web/app/(auth)/onboarding/layout.tsx`):**
- Layout bileşeni `h-screen w-screen flex flex-col overflow-hidden` yapısına geçirilerek ana pencere kaydırma çubukları gizlendi.
- İçerik alanı `flex-1 overflow-y-auto custom-scrollbar` olarak ayarlandı; böylelikle 1366x768 gibi ortalama dizüstü bilgisayar ekranlarında formun tamamen dikey kaydırma gerektirmeden tam sığması sağlandı, daha küçük ekranlarda ise iç kaydırma çubuğu devreye girecek şekilde responsive hale getirildi.

**Identity Step UI (`apps/web/app/(auth)/onboarding/_components/step-identity.tsx`):**
- İstemci bileşeni, backend veri şeması (`IdentityPayload`) ile %100 uyumlu şekilde kompakt form spacing kurallarına göre güncellendi:
  - Form elemanları arası dikey boşluklar daraltıldı (`space-y-4` ve daha sıkı grid aralıkları uygulandı).
  - Başlık yazı boyutları ve alt boşlukları küçültüldü (`NarrativeText` `xl` ve `sm` boyutlarına çekildi).
  - Giriş alanlarının dikey padding'i sıkılaştırıldı (`py-2.5` -> `py-2`).
  - Çalışma izni (Work Authorization) kart boyutları ve açıklama metinleri kısaltılarak dikeyde yer kazanıldı.
  - Sadece görsel gösterim amaçlı olan ve form kirliliği yaratan **Timezone (Saat Dilimi) alanı arayüzden kaldırıldı** (timezone değeri arka planda otomatik tespit edilerek gönderilmeye devam ediyor).
  - Toplamda dikey boyutta yaklaşık **270px** yer kazanıldı ve form 1366x768 çözünürlüğe mükemmel şekilde oturdu.

**Sayfa Entegrasyonu (`apps/web/app/(auth)/onboarding/page.tsx`):**
- `StepIdentity` bileşeni güncellenerek `initialData={status?.profile_data}` ve `onComplete` callback'ini alacak şekilde yapılandırıldı.

---

## [Bugfix] — 2026-07-15 — Auto-Provision User on first API State Query 🛠️

### Yapılan

**Onboarding API (`apps/api/app/routers/onboarding.py`):**
- `_require_user` helper fonksiyonu güncellenerek, kullanıcının veritabanında bulunmaması durumunda `404 Not Found` hatası döndürmek yerine otomatik olarak bir taslak kullanıcı kaydı oluşturması (`upsert_from_clerk`) sağlandı.
- Bu sayede, yerel geliştirme (local dev) ortamlarında Clerk webhook'larının (özellikle `user.created` olayının) ulaşıp tetiklenemediği durumlarda, giriş yapan kullanıcıların API durum isteklerinde takılması (ve Next.js middleware katmanının 404 dönen istekler nedeniyle onboarding'e yönlendiremeyip fail-open olarak boş sayfaya geçirmesi) engellendi.
- İlk kez `/api/onboarding/state` sorgusunu atan yeni bir Clerk kullanıcısı otomatik olarak `NOT_STARTED` durumuyla veri tabanına kaydedilecek ve Next.js middleware'i tarafından `/onboarding?step=IDENTITY` sayfasına sorunsuzca yönlendirilecektir.

**Entegrasyon Testi (`tests/test_onboarding_api.py`):**
- Test akışı güncellenerek, sıfırdan oluşturulan bir kullanıcının webhook çağrılmadan önce doğrudan `GET /api/onboarding/state` ile sorgulanması durumu ve bu sorgulama sonucu başarılı bir şekilde veritabanına `NOT_STARTED` durumuyla otomatik olarak provizyon edilip onboarding adımlarına devam edebildiği doğrulandı.

---

## [Phase A.7] — 2026-07-15 — Onboarding BUILDING Step Implementation ✅

### Yapılan

**Backend API (`apps/api/app/routers/onboarding.py`):**
- `/api/onboarding/build-graph` — Özgeçmiş analizi verilerini kullanarak Career Graph derleyen ve `ExtractionJob` başlatan POST endpoint'i eklendi.
- `/api/onboarding/build-graph/{job_id}/status` — Yürütülen graph oluşturma işinin durumunu ve log akışını dönen GET polling endpoint'i eklendi.
- `run_graph_building` — Aşamalı Career Graph oluşturma adımlarını simüle eden, yetkinlikleri ve projeleri ilişkilendiren asenkron arka plan görevi eklendi.
- Derlenen Career Graph veri modeli (`GraphNode`, `GraphEdge`, `CareerGraph`) Pydantic şemalarıyla tanımlandı ve veri tabanında kullanıcının `profile_data` JSONB kolonundaki `career_graph` alanına kaydedilerek state `READY` durumuna geçirildi.

**BUILDING UI (`apps/web/app/(auth)/onboarding/_components/step-building.tsx`):**
- Graph derleme sürecinin yüzdesini, typewriter log ekranını ve SVG bileşenini koordine eden BUILDING aşama arayüzü yazıldı.
- İşlem tamamlandığında kullanıcıyı 3 saniye gecikmeyle `/briefing` sayfasına yönlendiren akış entegre edildi.

**Career Graph Animation (`apps/web/app/(auth)/onboarding/_components/career-graph.tsx`):**
- Çıkarılan yetkinlikleri (skill), projeleri (project) ve şirketleri (company) dairesel bir yerleşimle görselleştiren interaktif SVG bileşeni oluşturuldu.
- Düğüm (node) ve kenarların (edge) sırayla ve akıcı bir şekilde ekrana gelmesini sağlayan `framer-motion` animasyonları entegre edildi.

**Sayfa Entegrasyonu & API Client:**
- `apps/web/features/onboarding/api.ts` — `buildGraph` ve `getGraphStatus` metotları eklenerek API istemcisi güncellendi.
- `apps/web/app/(auth)/onboarding/page.tsx` — `BUILDING` adımında `StepBuilding` bileşeninin render edilmesi sağlandı.

---

## [Phase A.6] — 2026-07-15 — Onboarding Evidence Step Implementation ✅

### Yapılan

**Backend API (`apps/api/app/routers/onboarding.py`):**
- `/api/onboarding/resume` — PDF formatında özgeçmiş dosyasını kabul eden ve `ExtractionJob` başlatan POST endpoint'i eklendi.
- `/api/onboarding/resume/{job_id}/status` — Yürütülen extraction işinin durumunu (`pending` | `parsing` | `extracting` | `completed` | `failed`) ve gerçek zamanlı log akışını dönen GET polling endpoint'i eklendi.
- `run_extraction` — Arka planda `Hiring-Agent` entegrasyonunu ve aşamalı log üretimini simüle eden asyncio tabanlı arka plan görevi (background task) eklendi.
- Dosya yükleme desteği ve `UploadFile` tip ayrıştırması için `python-multipart` paket bağımlılığı projeye dahil edildi (`requirements.txt` güncellendi).
- `.env` içerisindeki `DATABASE_URL`'den `channel_binding=require` parametresi kaldırılarak, bazı Windows ortamlarındaki TCP bağlantı kilitlenmesi sorunu giderildi.

**Evidence UI (`apps/web/app/(auth)/onboarding/_components/step-evidence.tsx`):**
- PDF dosyaları için sürükle-bırak (drag & drop) ve dosya seçici alanı oluşturuldu.
- Yükleme sonrası başlayan extraction sürecinin ilerleme çubuğu (progress bar) ve dosya bilgisi kartı entegre edildi.
- Tamamlanma durumunda `skills_extracted`, `companies_found`, `evidence_items` ve `confidence_score` verilerini gösteren özet kartı eklendi.
- İşlem bittiğinde 1.5 saniye gecikmeyle otomatik olarak bir sonraki adım olan `CONNECTIONS` adımına yönlendirme sağlandı.

**Extraction Log (`apps/web/app/(auth)/onboarding/_components/extraction-log.tsx`):**
- Gerçek zamanlı logları aşamalı olarak ekrana yansıtan, daktilo efektli (typewriter animation) terminal bileşeni geliştirildi.

**Sayfa Entegrasyonu & API Client:**
- `apps/web/features/onboarding/api.ts` — `uploadResume` ve `getResumeStatus` metotları eklenerek API istemcisi güncellendi.
- `apps/web/app/(auth)/onboarding/page.tsx` — `EVIDENCE` adımında `StepEvidence` bileşeninin render edilmesi sağlandı.

---

## [Phase A.5] — 2026-07-15 — Onboarding Goals Step Implementation ✅

### Yapılan

**Onboarding Goals UI (`apps/web/app/(auth)/onboarding/_components/step-goals.tsx`):**
- Gelişmiş goals seçim formu, linear/conversational stiline göre yeniden tasarlandı.
- ChipMultiSelect ve SearchableMultiSelect bileşenleri eklenerek, eski comma-separated input yöntemi kaldırıldı.
- `optimizing_for` alanına max 3 limitli chip seçici eklendi.
- target roles (`preferred_roles`) ve target countries (`preferred_countries`) için max 5 seçim limitli searchable select eklendi.
- İsteğe bağlı (optional) salary min, max ve para birimi (`salary_currency`) alanları entegre edildi.
- Form doğrulama (validation) ve hata yakalama (error handling) durumları eklendi.
- `onboardingApi.saveGoals` API entegrasyonu tamamlanarak bir sonraki adım olan `EVIDENCE` adımına yönlendirme yapıldı.

**Yeni Bileşenler:**
- `apps/web/app/(auth)/onboarding/_components/chip-multi-select.tsx` — Çoklu chip seçim arayüzü.
- `apps/web/app/(auth)/onboarding/_components/searchable-multi-select.tsx` — Arama destekli dropdown çoklu seçim kutusu.

**Veri Sabitleri (`apps/web/features/onboarding/constants.ts`):**
- `GOALS` (optimizing_for seçenekleri), `ROLES`, `COUNTRIES` ve `CURRENCIES` listeleri onboarding veri modeliyle uyumlu olarak eklendi.

**Sayfa Entegrasyonu (`apps/web/app/(auth)/onboarding/page.tsx`):**
- `StepGoals` bileşeni `onComplete` callback desteği ile güncellenerek `/onboarding?step=EVIDENCE` yönlendirmesi sağlandı.

**Düzeltmeler & İyileştirmeler:**
- `apps/web/app/(dashboard)/inbox/page.tsx` — `MOCK_OPPORTUNITIES` array elemanlarının TypeScript tip uyuşmazlığı giderildi (recommendation "SKIP" tipi eklendi).
- `apps/web/components/shared/label-text.tsx` — `LabelTextProps` arayüzüne style prop desteği eklendi.
- `apps/web/components/ui/insight-row.tsx` — `typeConfig` tip tanımına `style` prop desteği eklenerek upgraded `lucide-react` uyumluluğu sağlandı.
- `apps/web/package.json` — TypeScript derleyici hatalarını önlemek için `lucide-react` paketi `^0.470.0` sürümüne güncellendi.
- Database: Alembic migration (`add_users_table`) çalıştırıldı.

---

## [Phase A.4] — 2026-07-15 — Backend API + Clerk Webhook + Middleware Redirect ✅

### Yapılan

**Backend API (`apps/api/app/routers/onboarding.py`):**
- `GET /api/onboarding/state` — mevcut state + profile_data + goals + next_step döner
- `POST /api/onboarding/identity` — IdentityPayload kaydeder, NOT_STARTED/IDENTITY → GOALS'a ilerler
- `POST /api/onboarding/goals` — GoalsPayload kaydeder, GOALS → EVIDENCE'a ilerler
- `POST /api/onboarding/advance` — generic state ilerletme (EVIDENCE/CONNECTIONS/BUILDING için)
- `POST /api/onboarding/complete` — direkt READY'ye geçer
- `apps/api/app/main.py`'e register edildi (`/api/onboarding` prefix)

**Clerk Webhook (`apps/api/app/routers/webhooks.py`):**
- `POST /api/webhooks/clerk` — `user.created`, `user.updated`, `user.deleted` handle eder
- Svix imza doğrulama: HMAC-SHA256, 5 dk timing check; `CLERK_WEBHOOK_SECRET` yoksa dev'de skip eder
- `upsert_from_clerk()` idempotent — aynı webhook iki kez gelse sorun olmaz

**Middleware Redirect (`apps/web/middleware.ts`):**
- Her protected route'da `/api/onboarding/state` fetch eder (2 sn timeout)
- `STATE_TO_URL` map: NOT_STARTED/IDENTITY/GOALS/EVIDENCE/CONNECTIONS/BUILDING → ilgili `/onboarding?step=X`
- READY → redirect yok, kullanıcı geçer
- Backend down ise fail-open (kullanıcı bloklanmaz)
- `/onboarding(.*)` route'u redirect döngüsünden muaf tutuldu

**Frontend Integration:**
- `features/onboarding/api.ts` — `onboardingApi` object: getState, saveIdentity, saveGoals, advance, complete
- `app/(auth)/onboarding/page.tsx` — mount'ta gerçek API'dan state çeker; step routing; "Skip for now" butonu
- `app/(auth)/onboarding/_components/step-goals.tsx` — chip multi-select (max 3), roller/ülkeler, salary range
- `features/onboarding/types.ts` — `OnboardingStatus` tipi API shape'e güncellendi

**Model Güncellemeleri:**
- `core/domain/identity/user.py` — `profile_data`, `goals`, `image_url` kolonları eklendi; `OnboardingState.next_state()` static method eklendi
- `core/db/migrations/versions/20260715_e1f2a3b4c5d6_add_users_table.py` — yeni kolonlar migration'a dahil edildi
- `core/db/repositories/user_repo.py` — `create_user()`, `patch_profile_data()`, `patch_goals()` eklendi
- `core/db/repositories/__init__.py` — `UserRepository` export edildi

---

## [Phase A.3] — 2026-07-15 — Onboarding Wizard Shell ✅

### Yapılan

**`features/onboarding/` modülü:**
- `types.ts` — `OnboardingState` union, `ONBOARDING_STEPS`, `IdentityData`, `GoalsData`, `OnboardingStatus`
- `constants.ts` — `STEP_META` (label + description), `STEP_ORDER` array
- `state-machine.ts` — `nextState()`, `stepIndex()`, `isComplete()` pure fonksiyonlar
- `api.ts` — `getOnboardingStatus()`, `advanceOnboarding()` (placeholder, A.4'te gerçekle değiştirildi)
- `index.ts` — barrel export

**`app/(auth)/onboarding/` route:**
- `layout.tsx` — bare centered layout (auth layout ile aynı stil)
- `_components/wizard-shell.tsx` — amber hairline progress bar (5 adım), step label, wordmark header
- `_components/step-welcome.tsx` — Clerk'ten first name çeker, "Get started" butonu
- `_components/step-identity.tsx` — isim/soyisim, current title, years of experience formu
- `page.tsx` — URL `?step=` parametresiyle step routing, `<Suspense>` wrapper

**Middleware:**
- `/onboarding(.*)` public route'dan çıkarıldı (Clerk auth gerekli)
- State-based redirect logic eklendi (A.4'te tamamlandı)

---

## [Phase A.2] — 2026-07-15 — Aplio Rebrand + Users Table ✅

### Yapılan

**AplioLogo Component:**
- `components/shared/aplio-logo.tsx` — `variant: icon|wordmark`, `size: sm|md|lg`; `/logo-white.png` kullanır
- `components/shared/index.ts` — `AplioLogo` export edildi

**Rebrand:**
- `app/layout.tsx` — title: "Aplio — Your career, understood."
- `components/layout/sidebar.tsx` — amber "C" kutusu kaldırıldı → `AplioLogo`; `useUser()` ile gerçek Clerk adı/initials
- `components/layout/topbar.tsx` — breadcrumb "CareerOS" → "Aplio"
- `app/(auth)/sign-in/page.tsx` + `sign-up/page.tsx` — direkt `Image` → `<AplioLogo variant="icon" size="lg" />`

**Briefing Greeting:**
- `app/(dashboard)/briefing/page.tsx` — `currentUser()` ile Clerk'ten gerçek `firstName` çeker; mock'un hardcoded adını bypass eder

**Users DB (backend):**
- `core/db/migrations/versions/20260715_e1f2a3b4c5d6_add_users_table.py` — `users` tablosu: clerk_id (PK), email (unique), first/last_name, onboarding_state, profile_data, goals, image_url
- `core/domain/identity/user.py` — `User` SQLAlchemy model + `OnboardingState` enum (`NOT_STARTED → IDENTITY → GOALS → EVIDENCE → CONNECTIONS → BUILDING → READY`)
- `core/db/repositories/user_repo.py` — `upsert_from_clerk()`, `create_user()`, `advance_onboarding()`, `patch_profile_data()`, `patch_goals()`
- `core/db/models/__init__.py` + `core/domain/__init__.py` — `User` ve `OnboardingState` export edildi

---

## [Phase A.1] — 2026-07-15 — Clerk Authentication + Aplio Brand ✅

### Yapılan

**Clerk Auth:**
- `@clerk/nextjs` kurulumu, `clerk init` ile `CarrerOs` app'ine bağlandı (`app_3GX2U5t5zNWGmujfYoX6vow8wBN`)
- `middleware.ts` — tüm route'lar protected, public: `/sign-in`, `/sign-up`, `/api/webhooks`
- `app/layout.tsx` — `ClerkProvider` eklendi
- `components/layout/topbar.tsx` — placeholder avatar → `UserButton` (gerçek Clerk avatar + dropdown)
- `.env.local` — `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, redirect URL'leri

**Route Reorganizasyonu:**
- `app/(dashboard)/layout.tsx` — AppShell artık sadece dashboard'da (sidebar + topbar)
- `app/(auth)/layout.tsx` — sign-in/sign-up için temiz centered layout
- `app/inbox/` + `app/companies/` → `app/(dashboard)/inbox/` + `app/(dashboard)/companies/`
- `app/(auth)/sign-in/[[...sign-in]]/page.tsx` — özel Clerk sign-in sayfası
- `app/(auth)/sign-up/[[...sign-up]]/page.tsx` — özel Clerk sign-up sayfası

**Aplio Brand:**
- Ürün adı: **Aplio** (CareerOS → Aplio)
- `public/logo-white.png` + `public/logo-black.png` eklendi
- Sign-in / sign-up sayfalarında wordmark: Outfit 200 + amber accent çizgi + italic tagline

---

## [Frontend Days 1-5] — 2026-07-15 — Next.js App Shell + Briefing ✅

### Yapılan

**Mimari:**
- Next.js 16.2 App Router, Tailwind v4, MP072 paleti (`--accent` #FFB162, `--background` #1B2632)
- `components/shared/` — NarrativeText, NarrativeSection, MetricText, LabelText, Button, FadeInSection
- `components/patterns/` — DecisionList, SpotlightCard, EvidenceBlock, ProgressBlock
- `features/briefing/` — types.ts, mock.ts, api.ts (discriminated union `BriefingResult`)

**Briefing Page (typography-first, CareerOS Design Manifesto v1.0):**
- `app/(dashboard)/briefing/page.tsx` — async server component, `getBriefing()` ile veri çeker
- Hairline `border-top` divider sistemi (`Movement` component) — kutu yok, sadece tipografi
- `loading.tsx` (skeleton), `error.tsx` (`unstable_retry`), `_components/` (8 bileşen)
- Newsreader Variable italic serif kapanış bölümü (`.font-editorial`)

**Diğer Sayfalar:**
- `app/(dashboard)/inbox/page.tsx` — Opportunities listesi
- `app/(dashboard)/companies/page.tsx` + `[name]/page.tsx` — Company detail

---

## [Docs v1] — 2026-07-14 — Versioned Architecture Reports ✅

### Yapılan
`docs/` dizini versioned `docs/v1/` layoutuna taşındı. Her fazın tam teknik raporu yazıldı ve codebase'e karşı doğrulandı.

**Dizin Yapısı:**
```
docs/v1/
├── ARCHITECTURE.md          — Genel mimari
├── CODEBASE_OVERVIEW.md     — Tam codebase anatomisi
├── SYSTEM_SUMMARY.md        — Executive summary
├── VISION.md                — Ürün doktrini
├── DIRECTORY_MAP.md         — Klasör açıklamaları
├── development/
│   ├── DATABASE_AUDIT.md
│   └── MIGRATION_REPORT.md
└── phases/
    ├── PHASE_1_REPORT.md    — Foundation (DB, Events, CLI, Plugins, 24 endpoint)
    ├── PHASE_2_REPORT.md    — Intelligence Core (Evidence Graph, Resume AI, Hiring-Agent)
    └── PHASE_3_REPORT.md    — Company & Market Intelligence (8 DB tablo, Timeline, Knowledge DB)
```

**Raporlarda Doğrulanan Düzeltmeler:**
- Faz 1: Endpoint sayısı 21→24 (companies 4, settings 4, main +root+health)
- Faz 1: `POST /api/jobs/score` yok → `GET /api/jobs/pipeline`
- Faz 2: Feature Registry `_archive/features/` altında (aktif dizinde değil)
- Faz 2: Test sayısı 5→4 aktif (`test_feature_registry.py` → `_archive/scripts/`)
- Faz 3: `CompanyMemoryRepository` ayrı dosyada değil — `company_repo.py` (L67) içinde

---

## [Phase 4D] — 2026-07-14 — Unified CLI ✅

**Commit:** `654085c`

### Yapılan

**`apps/cli/main.py`** (182 satır) — Typer tabanlı unified CLI
- 4 native komut: `version`, `status`, `scan`, `strategy`
- 4 mounted sub-group: `track`, `resume`, `company`, `market`
- Try/except mounting pattern — import failure silently skip edilir
- `career-os` launcher script: `apps/cli/career_os_launcher.py`

**Sub-group CLI'ları:**
- `track` → `services/application_engine/cli.py`
- `resume` → `services/resume_intelligence/cli.py`
- `company` → `services/company_intelligence/cli.py`
- `market` → `services/market_intelligence/cli.py`

**Kullanım:**
```
career-os version
career-os status
career-os track add --url ... --title ... --company ...
career-os resume generate --company Google --title "ML Engineer"
career-os company show --name Google
career-os market signals --source hackernews
```

---

## [Phase 4C] — 2026-07-14 — Service Extraction ✅

**Commit:** `a613a33`

### Yapılan

`packages/domain/` içinde iki yeni service modülü:

**`core/services/identity_service.py`**
- `IdentityService` — user profile, skill management, evidence CRUD
- `get_user_profile()`, `add_skill()`, `get_evidence_summary()`

**`core/services/job_intelligence.py`**
- `JobIntelligenceService` — job scoring, pipeline filtering, career score queries
- `score_jobs()`, `get_pipeline()`, `get_top_opportunities()`

Her iki servis de `BaseRepository[T]` üzerinden DB'ye erişir; FastAPI router'ları bu servisleri dependency injection ile kullanır.

---

## [Phase 4B] — 2026-07-14 — Domain Migration ✅

**Commit:** `f7c577d`

### Yapılan

15 entity, 6 subdomain'e migrate edildi:

```
core/domain/
├── identity/     user.py, skill.py, profile.py
├── job/          job.py, scan.py
├── evidence/     evidence.py, github_metrics.py
├── application/  application.py, email.py
├── company/      company.py, memory.py
└── market/       signal.py, timeline.py
```

**Backward-compat shim'ler:** `packages/domain/*.py` → `core/domain/*` re-export

---

## [Phase 4A] — 2026-07-14 — FastAPI Gateway ✅

**Commit:** `3dd3fa2`

### Yapılan

**`apps/api/app/main.py`** — FastAPI app
- 7 router mount + root + health = **24 endpoint** (live-tested)
- CORS: `localhost:3000`, `localhost:3001`, `127.0.0.1:3000`

**Router → Endpoint Tablosu:**

| Router | Endpoint'ler | Sayı |
|---|---|---|
| jobs | GET /api/jobs, GET /api/jobs/pipeline, GET /api/jobs/{url} | 3 |
| applications | GET /, GET /summary, POST /, PUT /{url} | 4 |
| evidence | GET /, POST /build, GET /{skill}, DELETE /{id} | 4 |
| companies | GET /, GET /hiring, GET /{name}, GET /{name}/memory | 4 |
| market | GET /signals, GET /summary, GET /trend/{skill} | 3 |
| settings | GET /, PUT /, GET /validate, POST /reload | 4 |
| resume | GET /templates, POST /generate | 2 |
| main | GET /, GET /health | 2 |

**Dependency injection:** `get_db_session()`, `get_user_id()` — tüm router'larda tutarlı
**Schemas:** Pydantic v2, `model_config = ConfigDict(from_attributes=True)`

---

## [Phase 3 — Knowledge DB] — 2026-07-14 ✅

**Commit:** `4afc006` (DB-First Knowledge Layer)

### Yapılan

14 YAML dosyası → PostgreSQL (one-time seed, sonrası DB source of truth)

**`scripts/seed_knowledge_from_yaml.py`** (213 satır)
- `seed_countries()` → 5 kayıt (`germany`, `canada`, `netherlands`, `uae`, `usa`)
- `seed_visas()` → 3 kayıt (EU Blue Card, US H1B, UK Skilled Worker)
- `seed_salaries()` → 50+ kayıt (backend_eu, ml_us, frontend_global)
- `session.merge()` upsert (iso_code / visa_type PK)
- Salary: composite key manual upsert

**DB Modeller:** `countries`, `visas`, `salary_ranges` — JSONB columns for flexible data

**YAML Seed Dosyaları (14 adet, ~2,500 satır):**
```
infra/seeds/v1/countries/  → germany, canada, netherlands, uae, usa
infra/seeds/v1/visa/       → eu_blue_card, us_h1b, uk_skilled_worker
infra/seeds/v1/salaries/   → backend_eu, ml_us, frontend_global
infra/seeds/v1/companies/  → big_tech, unicorns, company_memory_schema
```

**Sonuç:** `Total: 58 records seeded` — DB artık knowledge'ın canonical kaynağı

---

## [Phase 3 — Timeline Layer] — 2026-07-14 ✅

### Yapılan

**`core/timeline/timeline.py`** (295 satır)
- `track_snapshot(entity_type, entity_id, data)` — zaman serisi snapshot
- `_detect_and_record_changes()` — auto-diff: field-by-field önceki snapshot ile karşılaştır
- `get_entity_history(entity_type, entity_id, days)` — temporal query
- `detect_changes(entity_type, entity_id, field, days)` — field-level change query
- `get_trending_entities(entity_type, field, days, limit)` — en çok değişen entity'ler

**`core/db/models/timeline.py`** (53 satır)
- `TimelineSnapshot` — entity state at a point in time (JSONB)
- `TimelineChange` — field-level diff record (`old_value`, `new_value`, `change_type`)

**Migration:** `add_timeline_tables.py` — 2 tablo + indexes

**Kullanım Örneği:**
```python
timeline.track_snapshot("job", job_url, {"career_score": 91, "company": "Google"})
# Otomatik diff → "career_score: 78 → 91 (↑ 16.7%)"
```

---

## [Phase 3 — GitHub Enrichment] — 2026-07-14 ✅

### Yapılan

**Problem:** Evidence confidence'ı heuristik hesaplanıyordu (commit sayısı + star). LLM resume oluştururken GitHub URL yoksa project details hallucinate ediyordu.

**Çözüm:** PyGithub → 9 gerçek metrik → `evidence` tablosuna yazıldı.

**`plugins/enrichment/github/repo_analyzer.py`** (88 satır)
- 9 metrik: `loc_count`, `language`, `topics`, `has_tests`, `has_docs`, `has_releases`, `pr_count`, `issue_count`, `contributor_count`

**`plugins/enrichment/github/evidence_enricher.py`** (117 satır)
- Her `evidence` kaydı için GitHub URL → repo_analyzer → DB UPDATE
- Confidence formula güncellendi: LOC, has_tests, has_docs ağırlık eklenildi

**`scripts/enrich_github_evidence.py`** (69 satır) — CLI runner

**`services/resume_intelligence/application/resume_generator.py`**
- `_load_evidence()` artık `loc_count`, `has_tests`, `pr_count` vs. DB'den okuyor
- `_tailor_evidence()` → `available_skills=list(evidence.keys())` — LLM'e gerçek skill listesi verildi
- `_normalize_skill_names()` — fuzzy match: LLM döndürdüğü skill adları → gerçek evidence key'leri

**Sonuç:** LLM artık gerçek metriklerle çalışıyor, hallucination büyük ölçüde çözüldü.

---

## [Phase 3 — Market Intelligence] — 2026-07-14 ✅

### Yapılan

**HN "Who is Hiring?" Scanner:**
- `plugins/market_signals/hackernews/client.py` (67 satır) — Algolia API
- `plugins/market_signals/hackernews/who_is_hiring_parser.py` (72 satır) — comment → structured job
- `plugins/market_signals/hackernews/signal_extractor.py` (122 satır)
  - 272 job posting → 42 signal (Temmuz 2026)
  - Top 20 skill demand, Top 20 company hiring spikes, remote/visa stats

**TechCrunch Scanner:**
- `plugins/market_signals/techcrunch/rss_client.py` (40 satır) — feedparser
- `plugins/market_signals/techcrunch/signal_extractor.py` (105 satır) — funding/layoff detection

**`core/db/models/market_signal.py`** — `signal_type`, `skills_affected` (JSONB array), `magnitude`
**`core/db/repositories/market_signal_repo.py`** (182 satır)
- `get_skill_trend()` — period-over-period (current window vs previous window)
- `source_id` ile dedup

**`services/market_intelligence/cli.py`** (97 satır) — `signals scan`, `trend show`, `summary`

---

## [Phase 3 — Company Intelligence] — 2026-07-14 ✅

### Yapılan

**`services/company_intelligence/application/company_enricher.py`** (75 satır)
- Job posting → tech stack aggregation
- `CompanyRepository.update_tech_stack()` — JSONB merge, existing skills korunur

**`services/company_intelligence/application/company_memory.py`** (96 satır)
- `record_interview_fact()` — "Google'da Docker ve Redis soruldu"
- `get_advice_for_company()` — rejection pattern detection + advice generation
- 3+ reject → "6 ay bekle", 1 reject → "phone screen'e hazırlan"

**`core/db/repositories/company_repo.py`** (135 satır)
- `CompanyRepository` + `CompanyMemoryRepository` — **aynı dosyada**
- `get_or_create()`, `get_hiring_now()`, `find_by_tech_stack()`, `update_tech_stack()`
- `add_fact()`, `get_facts_for_company()`, `get_company_summary()`

**`services/company_intelligence/cli.py`** (97 satır) — `show`, `enrich`, `memory`

**Migration:** `add_companies_and_memory.py` — `companies` + `company_memory` tabloları

---

## [Phase 2C] — 2026-07-14 — Target-Aware Resume Generator ✅

### Yapılan

**`services/resume_intelligence/application/resume_generator.py`** (357 satır)

5-adımlı pipeline:
1. Evidence DB + GitHub cache yükle
2. `_extract_priorities()` — job title/company → `{must_have, important, culture_signals}`
3. `_tailor_evidence()` — `available_skills` constraint → LLM hallucination önlendi
4. `_select_projects()` — max 4 proje, score-based ranking
5. `_generate_summary()` — 2-satır özet, max 200 token

**`_normalize_skill_names()`** (35 satır)
- LLM çıktısındaki skill adları → gerçek evidence key'leri
- Exact match → lowercase match → skill_mappings dict → partial match → top-confidence fallback

**`_role_hint()`** — JD yoksa role tipine göre domain hint injection (10 role tipi)

**Jinja2 template rendering:** `services/resume_intelligence/templates/resume/`
- `ml_research.md.jinja`, `backend.md.jinja`

**Output:** `personal/{Name}_{Company}_{Role}.md` — Markdown CV

---

## [Week 3 Domain Migration] — 2026-07-14 ✅

### Yapılan
`career_os/models/` → `packages/domain/` migration: entity'ler 3 domain'e dağıtıldı.

**Yeni yapı:**
```
packages/domain/
├── identity/   skill.py, profile.py  (Skill, SkillLevel, UserProfile, Experience, UserPreferences)
├── job/        job.py                (Job)
└── intelligence/ match.py, scoring.py (MatchResult, OpportunityScore)
```

**Güncellemeler:**
- `packages/intelligence/*.py` — `from packages.domain import ...` kullanıyor
- `career_os/data/applypilot_loader.py` — `from packages.domain import ...`
- `career_os/core/skill_graph.py` — `from packages.domain.identity.skill import Skill`
- `career_os/models/` — backward-compat shim (re-export, aynı class instance)

**Sınıf identity korundu:** `career_os.models.Skill is packages.domain.Skill` → True

### Test
```
python scripts/test_domain_migration.py  # 7/7 PASS
```

---

## [Multi-User] — 2026-07-14 — Multi-user foundation ✅

### Ne Yapıldı
- **Alembic migration** `b2c3d4e5f6a7` — `user_id VARCHAR(100) NOT NULL DEFAULT 'default'`
  5 tabloya eklendi: `career_scores`, `applications`, `emails`, `scan_history`, `evidence`
- **Mevcut veriler** otomatik `user_id='default'` olarak backfill edildi (200 score, 562 scan, 25 evidence)
- **Tüm repository metotları** `user_id: str = "default"` parametresi aldı:
  `CareerScoreRepository`, `ApplicationRepository`, `EvidenceRepository`, `ScanHistoryRepository`
- **Caller güncelleme**: `apply_strategy.py`, `run_full_scan.py`, `evidence_builder.py`
  artık `config.yaml → user.id`'den `user_id` alıyor
- **`config.yaml`** `user.id = "abdullokh"` bloğu eklendi
- **`config_loader.py`** `user.id` yoksa otomatik `"default"` fallback

### Test
```
python scripts/test_multiuser_migration.py
# 5/5 PASS
```

### Mimari
- PKs değiştirilmedi (emails FK bozulmaması için)
- `user_id` filtre kolonu + index — tüm sorgular user'a göre izole
- `jobs` tablosu shared (global katalog, user_id yok)
- Phase 3 Auth'ta kolayca JWT/session → user_id mapping yapılabilir

---

## [Single DB] — 2026-07-14 — PostgreSQL tek veritabanı ✅

### Problem
`ApplyPilotPlugin` iş ilanlarını harici bir SQLite dosyasından (`~/.applypilot/applypilot.db`)
okuyordu. Proje kendi veritabanında sadece URL ve skorları tutuyordu; başlık/şirket/açıklama
bilgileri PostgreSQL'de yoktu.

### Çözüm
- **`packages/db/models/job.py`** — yeni `Job` modeli (url PK, title, company, description,
  required_skills JSONB, salary_min/max, remote, vb.)
- **`packages/db/repositories/job_repo.py`** — `JobRepository` (`upsert_many`, `get_unscored`,
  `known_urls`)
- **Alembic migration** `a1b2c3d4e5f6` — `jobs` tablosu + 6 index (GIN dahil)
- **`scripts/sync_jobs_from_applypilot.py`** — SQLite → PostgreSQL tek seferlik/tekrarlı sync
  (`--min-score`, `--hours` flag'leri)

### Sonuç
```
python scripts/sync_jobs_from_applypilot.py
# → 562 job PostgreSQL jobs tablosuna aktarıldı
# → company known: 261/562, remote: 388/562
```

SQLite artık sadece ApplyPilot tarafından yazılan harici bir INPUT kaynağı.
Projenin kendi pipeline'ı tamamen PostgreSQL üzerinde çalışıyor.

---

## [ApplyPilot Plugin] — 2026-07-14 — Job Source Plugin (Week 2) ✅

### Değişiklikler

**`plugins/plugin_interface.py`** — `JobSourcePlugin` ABC eklendi
- `scan(hours_old, min_score)` — raw job listesi
- `normalize(raw_job)` — canonical schema'ya dönüşüm
- `scan_and_normalize()` — convenience, hata izole

**`config/plugins.yaml`** — `job_sources.applypilot` bloğu
- `db_path`, `columns`, `table_name` — kaynak konfigürasyonu
- `company_extraction`: ATS domain listesi (13 alan), blocklist (19 kelime), pattern sırası
- `skill_extraction`: 37 keyword, requirements section scoping, `max_section_chars`
- `salary_patterns`: 3 regex (USD, EUR, bare number) — YAML single-quote regex escaping fix uygulandı
- `company_sizes`: big_tech (9 şirket), large (6 şirket)
- `seniority`: title patterns (senior/junior/lead), description `(\d+)+ years` regex

**`plugins/job_sources/applypilot/client.py`**
- `ApplyPilotClient` — SQLite I/O, `hours_old` filtresi, `count_jobs()`, `get_all_urls()`
- `ApplyPilotPlugin(JobSourcePlugin)` — high-level interface, `adapter` + `client` composition

**`plugins/job_sources/applypilot/adapter.py`**
- Company extraction: LinkedIn slug → title pattern → ATS-filtered app URL → description NLP
- Skill extraction: requirements section öncelikli, word-boundary matching
- Salary: 3 configurable regex pattern
- Seniority: title keyword → description `X years experience`
- Remote: `remote/anywhere/wfh` keyword scan

**`plugins/plugin_loader.py`**
- `load_job_source_plugin(name)` factory
- `list_available_job_sources()` → metadata dict

**`scripts/test_applypilot_plugin.py`** — 6/6 test geçti
- 562 iş DB'de, 151 son 72 saatte, şirket extraction oranı %54

---

## [Event Bus] — 2026-07-14 — Domain Event Pub/Sub Foundation ✅

### Değişiklikler

**`events/event_bus.py`** — Thread-safe singleton
- `subscribe(event_type, handler)` — direct + `@decorator` syntax her ikisi de çalışıyor
- `publish(event)` — handler hataları izole, diğer handler'ları durdurmaz
- `get_history(event_type, limit)` — debug için son N event'i tutar (`deque(maxlen=1000)`)
- `unsubscribe()`, `clear()`, `stats()` — tam kontrol
- `RLock` — nested publish için reentrant lock

**`events/event_types.py`** — `Event` base dataclass (UUID, UTC timestamp, source)

**8 domain event modülü — 18 event tipi:**
- `job_events`: `JobDiscovered`, `JobScored`, `JobExpired`, `JobMatched`
- `application_events`: `ApplicationSubmitted`, `ApplicationRejected`, `ApplicationInterview`, `ApplicationOffer`
- `resume_events`: `ResumeGenerated`, `EvidenceAdded`
- `company_events`: `CompanyUpdated`, `CompanyHiringSpike`, `CompanyLayoff`
- `market_events`: `SkillTrendDetected`, `MarketSignalDetected`, `SalaryTrendUpdated`
- `learning_events`: `SkillLearned`, `RoadmapGenerated`, `ROICalculated`
- `system_events`: `WeeklyReportGenerated`, `ModelCalibrated`, `FeatureToggled`

**`scripts/strategy/apply_strategy.py`** — entegrasyon (backward compat)
- Her `repo.save_score()` sonrası `JobScored` event'i publish ediliyor
- DB transaction'ı dışında — hata event bus'ı etkilemez, bus hatası DB'yi etkilemez

**`scripts/test_event_bus.py`** — 8 test (hepsi geçti)

**Phase 2 yol haritası:**
- Redis Streams'e geçmek = sadece `event_bus.py` içini değiştir, tüm subscriber'lar aynı kalır

---

## [Refactor] — 2026-07-14 — Plugin + Config-Driven Architecture ✅

### Değişiklikler

**Sorun:** `hiring_agent_adapter.py` ve `evidence_builder.py` içinde hardcoded path'ler, CSV column isimleri ve confidence katsayıları vardı.

**`config/plugins.yaml`** (yeni — tek kaynak)
- `install_dir`, `csv_filename`, `cache_dir`, `score_script` — tüm path'ler buradan
- `csv_columns.scores` / `csv_columns.metadata` — CSV schema buradan
- `confidence_formula` — `base_divisor`, `commit_bonus_max`, `star_bonus_max`, `production_weight` buradan
- `enrichment_keys` — hangi alanların `career_scores.explanation`'a yazılacağı buradan

**`plugins/plugin_interface.py`** (yeni)
- `ResumeParserPlugin` ABC — `parse()`, `get_metadata()`, `get_enrichment_payload()`
- `ResumeData` dataclass — parser çıktısı için tip güvenli struct

**`plugins/resume_parsers/hiring_agent/client.py`** (yeni)
- `HiringAgentPlugin(ResumeParserPlugin)` — tüm değerleri `plugins.yaml`'dan okur, sıfır hardcode

**`plugins/plugin_loader.py`** (yeni)
- `load_parser_plugin(name)` — factory pattern; yeni parser eklemek = 1 satır + klasör

**`packages/config.py`** (yeni)
- `load_plugin_config()` — `config/plugins.yaml` için `lru_cache`'li loader

**`services/resume_intelligence/application/evidence_builder.py`** (refactor)
- Artık `ResumeParserPlugin` interface'ini kabul ediyor — hiring-agent'a bağımlı değil
- Confidence katsayıları config'den okunuyor

**`services/resume_intelligence/hiring_agent_adapter.py`** (refactor)
- `HiringAgentPlugin`'i kullanıyor; `_build_enrichment_payload()` hardcoded key listesi kaldırıldı

**`scripts/test_plugin_refactor.py`** (yeni)
- 8 adımlı structural test — config yükleme, plugin instantiation, formula doğrulama

---

## [Phase 2J] — 2026-07-14 — Application Engine CLI ✅

### Değişiklikler

**`services/application_engine/__init__.py`** (yeni)

**`services/application_engine/cli.py`** (yeni — typer tabanlı CLI)
- `add` — URL, title, company, status, notes ile iş ekle (duplicate → warn, skip)
- `update` — status değiştir; `applied` status'a geçince `applied_at` otomatik set edilir; notes append edilir
- `list` — tüm işleri tablo olarak göster; `--status` ile filtrele
- `summary` — pipeline count tablosu (to_apply/applied/phone_screen/...)
- `stale` — N gündür güncellenmemiş aktif başvuruları listele (ghosted tespiti için)
- `migrate-from-markdown` — `docs/tracking/JOB_APPLICATIONS.md`'daki gerçek URL satırlarını DB'ye import et; placeholder `[Apply](link)` satırlarını atlar
- State machine: `to_apply → applied → phone_screen → technical → onsite → offer / rejected / ghosted / withdrawn`
- Windows CP1252 uyumlu çıktı (emoji/unicode yok)

**`packages/db/repositories/application_repo.py`** (güncellendi)
- `get_stale(statuses, before)` eklendi — `stale` komutu için

---

## [Phase 2B] — 2026-07-14 — CV Scoring Servisi ✅

### Değişiklikler

**`services/hiring-agent/`** (yeni, ana repo'ya entegre edildi)
- Ayrı git submodule değil — `.git` kaldırıldı, direkt repo içinde yaşıyor
- PDF → PyMuPDF → JSONResume → GitHub enrichment → LLM evaluation pipeline
- Scoring: Open Source (35) + Self Projects (30) + Production (25) + Technical (10) + bonus/deductions
- OpenRouter desteği: `openai/gpt-4o-mini` default, Ollama yok (VPS'te Ollama kurulu değil)
- **`prompt.py`:** `load_dotenv()` → `load_dotenv(Path(__file__).parent / ".env")` — token artık herhangi bir `cwd`'dan çalışınca doğru yükleniyor
- **`github.py`:** GitHub token zaten set edilmişken "Set GITHUB_TOKEN" tip mesajı gizlendi

**`services/resume-intelligence/hiring_agent_adapter.py`** (yeni)
- `score_resume(pdf_path)` — `score.py`'yi subprocess olarak çalıştırır, `resume_evaluations.csv`'nin son satırını okur, scores dict döner
- `enrich_career_scores(session, scores)` — hiring-agent sonuçlarını `career_scores.explanation` JSONB'ye `"resume_score"` key'i altında yazar; zaten enriched satırları atlar
- `HiringAgentAdapter` class API: `HiringAgentAdapter(pdf_path).run()`

### CV Değerlendirme Sonuçları — Abdullokh Abdukodirov

```
Toplam Puan: 55/100

Open Source:        0/35  (kendi projeler, başkasına katkı yok)
Self Projects:     25/30  (Sentropy Engine, IMMUNO-TCR, YADIGAR — karmaşık, gerçek etki)
Production:        20/25  (Full Stack + Computer Vision rolleri, ölçülebilir başarılar)
Technical Skills:  10/10  (Python, Rust, Go, ML/AI framework'leri)

Bonus: 0   Deduction: 0
```

**Güçlü Yönler:** Production experience, ML/AI breadth, karmaşık self-projects  
**İyileştirme:** Open source katkılar (0/35 en büyük fırsat), portfolio site, collaborative projeler

### GitHub Token Fix
- Önceki durum: `GITHUB_TOKEN` `.env`'de comment'li (`# GITHUB_TOKEN=`) → 60 req/hr (unauthenticated)
- Şimdiki durum: Token set + `load_dotenv()` path fix → **4991/5000 req/hr** ✅
- Token scope: sadece `public_repo` (read-only public repos — yeterli)

---

## [Phase 2A] — 2026-07-14 — Intelligence Paketi Migrasyonu ✅

### Değişiklikler

**`packages/intelligence/`** (yeni)
- `semantic_matcher.py`, `opportunity_scorer.py`, `gap_analyzer.py` — canonical konumları
- `__init__.py` — `SemanticMatcher`, `OpportunityScorer`, `CareerDecisionEngine`, `GapAnalyzer` export'ları

**`career_os/intelligence/__init__.py`** — backward-compat shim'e dönüştürüldü
```python
from packages.intelligence import SemanticMatcher, OpportunityScorer, ...
```

**`scripts/strategy/apply_strategy.py`** — import `career_os.intelligence` → `packages.intelligence`

---

## [Phase 1C] — 2026-07-14 — Scan History Tracking ✅

### Değişiklikler

**`packages/db/repositories/scan_history_repo.py`**
- `get_all_known_urls()` eklendi — tek sorguda tüm bilinen URL'leri set olarak döner (O(1) per-job lookup)

**`scripts/scan/run_full_scan.py`**
- `scan_timestamp = datetime.utcnow()` — tüm scan için tek timestamp
- `load_jobs_from_applypilot()` — ApplyPilot DB'den scored job'ları çeker
- `track_scan_history(jobs, scanned_at)` — bulk set-diff ile new/known ayırt eder, SAVEPOINT per job
- Step 4.5 olarak pipeline'a eklendi; Step 7'de yeni job'lar listelenir

**`scripts/test_scan_history.py`** (yeni) — verification script

---

## [Phase 1B] — 2026-07-14 — Career Scores → PostgreSQL ✅

## [Phase 1B] — 2026-07-14 — Career Scores → PostgreSQL ✅

### Değişiklikler

**`scripts/strategy/apply_strategy.py`**
- `packages.db` import'u eklendi
- Yeni adım `[4.5/5]`: `rank_opportunities()` sonrası tüm job'lar için `career_scores` tablosuna insert
- `session.begin_nested()` (SAVEPOINT) per job — bir hata diğer kayıtları bozmaz
- `float()` cast: `np.float64` → Python float (psycopg type safety)
- `str()[:100]` guard: recommendation overflow'u önler
- `.txt` çıktıları korundu — backward compatible

**`packages/db/connection.py`**
- `_load_dotenv()` eklendi — modül import edildiğinde `.env` otomatik yüklenir, her session'da `$env:DATABASE_URL` set etmeye gerek kalmaz

**`packages/db/models/career_score.py`**
- `recommendation: VARCHAR(20) → VARCHAR(100)`
  `OpportunityScorer` `'CONSIDER - Review details'` (23 karakter) döndürüyor, 20'ye sığmıyordu

**Migration: `bc16185b1de3`** — widen_recommendation_to_varchar100

**`scripts/test_db_integration.py`** (yeni)
- Toplam kayıt, son scan zamanı, recommendation dağılımı
- Top 10 APPLY fırsatı (fallback: en yüksek skorlular)
- JSONB unnest SQL: en sık eksik skill'ler
- Örnek kayıt tam detayı

### Doğrulama Sonuçları (2026-07-13 19:06 UTC)

```
Toplam kayıt:     100 / 100 job  (saved_count=100, failed=0)
Recommendation:   CONSIDER - Review details: 66
                  SKIP - Better opportunities: 20
                  CONSIDER - Build skills first: 14
Avg career score: 53.9/100
Avg acceptance:   21.2%
```

**JSONB aggregation (en sık eksik skill'ler):**
```
ai              88 ilanda eksik   ← "ai" keyword extraction sorunu (bkz. not)
javascript      50 ilanda eksik
c++             47 ilanda eksik
docker          19 ilanda eksik
aws             19 ilanda eksik
kubernetes      15 ilanda eksik
```

**Not:** `ai` 88 ilanda eksik göründü ama kullanıcının `Machine Learning`, `LLM`, `NLP` skill'leri var. "ai" bare keyword olarak match edilmiyor — bu `applypilot_loader.py`'deki skill normalization sorunu, Phase 1B değil. `company = "Unknown"` çoğu iş için aynı sebep — company extraction v0 sorunu.

---

## [Phase 1A] — 2026-07-13 — PostgreSQL Database Layer ✅

### infrastructure/docker/
- `docker-compose.yml` — PostgreSQL 16-alpine + Adminer (port 8080), healthcheck, named volume
- `init.sql` — `uuid-ossp`, `pg_trgm`, `btree_gin` extensions; `vector` Phase 2'ye ertelendi

### packages/db/models/
- `base.py` — `DeclarativeBase` + `TimestampMixin` (created_at / updated_at)
- `career_score.py` — (url, scanned_at) composite PK zaman serisi; JSONB `skill_gaps` + `explanation`; GIN index + 4 btree index
- `application.py` — pipeline state machine (`to_apply → applied → phone_screen → offer / rejected`); JSONB `interview_rounds`
- `email.py` — cold email + follow-up; `sent_at / opened_at / replied_at` tracking; FK→applications CASCADE
- `scan_history.py` — job bazında scan kaydı; `discovered_in_this_scan` flag; 3 index

### packages/db/
- `connection.py` — singleton `QueuePool` (size=10, overflow=20), `session_scope` context manager, `DB_ECHO` toggle
- `repositories/base.py` — `Generic[T]` CRUD: get / get_all / create / update / delete
- `repositories/career_score_repo.py` — `save_score`, `get_latest`, `get_top_opportunities` (window function), `get_trends`
- `repositories/application_repo.py` — `upsert`, `mark_applied`, `advance_status`, `get_pipeline_summary`
- `repositories/scan_history_repo.py` — `record_scan`, `get_first_seen`, `get_new_this_scan`
- `alembic.ini` — `DATABASE_URL` env override; file template with date prefix
- `migrations/env.py` — online + offline migration modes; auto-imports `Base.metadata`

### Migration: `49c3e6a25ee5` — initial_schema
- Alembic autogenerate ile oluşturuldu, canlı PostgreSQL 16'ya uygulandı
- 4 tablo, 8 index, 1 FK oluştu — `alembic upgrade head` clean çalıştı

### Doğrulama
```
docker-compose up -d        → career-os-postgres: Healthy ✅
alembic revision --autogenerate → 4 tablo, 8 index detected ✅
alembic upgrade head        → clean ✅
```

---

## [Phase 0] — 2026-07-13 — Hazırlık Tamamlandı

### 0.1 — Git Tag `v0-final`
- Tüm planning doc'ları commit edildi (CODEBASE_OVERVIEW, DATABASE_AUDIT, VISION, ARCHITECTURE, MIGRATION_REPORT, tam CHANGELOG)
- `git tag v0-final` — v0 kodu donduruldu

### 0.2 — Full Backup (`backups/v0-final/`)
- `~/.applypilot/applypilot.db` → `backups/v0-final/applypilot.db`
- `reports/` → `backups/v0-final/reports/`
- `docs/tracking/JOB_APPLICATIONS.md` → `backups/v0-final/JOB_APPLICATIONS.md`
- `backups/` .gitignore'da — git'e gitmez

### 0.3 — API Key Rotation
- `config.yaml`'daki plaintext API key → `.env` dosyasına taşındı
- `config.yaml` artık `${OPENROUTER_API_KEY}` placeholder kullanıyor
- `.env` .gitignore'da (ve zaten başından beri öyleydi — key hiç git'e girmedi)
- `career_os/config_loader.py` oluşturuldu: `.env` yükler, `${VAR}` substitution yapar, dış bağımlılık yok
- `config.yaml.example` güncellendi
- `.gitignore`'a eklendi: `career_os_output/`, `cold_emails/`, `learning_plan/`, `job_requirements_analysis/`, `.vscode/`, `.idea/`

---

## [Architecture Planning] — 2026-07-13 — Architecture Planning Session

Bu seans koda hiç dokunmadı. Tamamen analiz, mimari tasarım ve belgeleme üzerine.

### Eklendi — `docs/`

#### `docs/CODEBASE_OVERVIEW.md`
Mevcut v0 kod tabanının tam anatomisi. Kapsam:
- ApplyPilot ile Career OS arasındaki ayrım (dışarıdan pip paketi vs. bu repo)
- `~/.applypilot/applypilot.db` şeması (12 sütun)
- Tüm script'ler ve career_os modülleri (ne yapar, neyi okur, neye yazar)
- Kritik notlar: config.yaml'da plaintext API anahtarı, company extraction güvensizliği, Career OS skorlarının heuristik olduğu

#### `docs/DATABASE_AUDIT.md`
Hangi verinin nerede yaşadığı ve neyin DB'ye girmediğinin tam envanteri.
- ApplyPilot DB'ye yazılan 12 sütun
- DB'ye **yazılmayan** 6 veri kategorisi: Career OS skorları (.txt), skill match sonuçları (runtime), başvuru durumu (Excel Notes + Markdown), email geçmişi (.txt), skor değişim geçmişi (eziliyor)
- `data/career_os.db` önerisi: 4 tablo ile tam SQL şeması (`career_scores`, `applications`, `emails`, `scan_history`)
- Geçiş planı: ApplyPilot DB'ye dokunmadan, paralel SQLite ile çalışma

#### `docs/VISION.md`
Ürün doktrini — Career OS'un ne olmak istediği. İçerik:
- Ana vizyon: "geliştiricinin tüm kariyeri için işletim sistemi"
- 5 tasarım prensibi: Calm Technology, Explainable Always, Action Over Information, Progressive Disclosure, Evidence Over Claim
- 8 domain tanımı
- Evidence Graph konsepti (GitHub commit → confidence score → skill weight)
- Target-Aware Resume Generator
- 4 fazlı roadmap, anti-pattern'ler, ilk 30 gün planı

#### `docs/ARCHITECTURE.md`
v1.0 teknik mimari belgesi — **LOCKED**.
- Event-driven mimari: `JobDiscovered`, `JobScored`, `ApplicationSubmitted`, `CareerSnapshotCreated` event tipleri
- Plugin sistemi: `JobSourcePlugin`, `EnrichmentPlugin` ABC'leri
- Feature registry: `feature.yaml` metadata formatı
- Versioned knowledge: `knowledge/v1/`, `knowledge/v2/`
- AI Memory Layer: 5 memory tipi (candidate, company, market, conversation, learning)
- Timeline katmanı: PostgreSQL `timeline_snapshots` + `timeline_changes` tabloları
- Kilitli dizin yapısı (8 domain, 8 servis, 8 worker)
- Teknoloji stack: FastAPI + Next.js 14 + PostgreSQL + LanceDB + NetworkX→KuzuDB
- 6 fazlı roadmap

#### `docs/MIGRATION_REPORT.md`
Mevcut v0'ın v1.0 mimarisine nasıl taşınacağının tam planı.
- Her mevcut dosyanın yeni konumu ve yapılması gereken değişiklik
- 4 dosya silinecek: `setup_package.py`, `run_scan.bat`, `career_os_output/*.txt`, `logs/run_history.json`
- 4 dosya bölünecek: `applypilot_loader.py` (→ 3 parça), `profile.py` (→ 3 parça), `apply_strategy.py`, `cold_email_generator.py`
- 14 hardcoded Python dict YAML'a çıkarılacak (`knowledge/v1/`)
- Acil güvenlik: `config.yaml`'daki API anahtarı git geçmişinden temizlenmeli
- Öncelik sırası: güvenlik → veri kaybı riski → plugin sistemi → YAML extraction → modül taşıma

---

## [0.5.0] — 2026-06-24 — Kritik Bug Düzeltmeleri

**Commit:** `6020b1e` — `fix: fix company/skill extraction noise and unreachable score threshold`

### Düzeltildi

**`career_os/data/applypilot_loader.py`** (+97 satır)
- ApplyPilot DB'nin `company` sütunu yok — `_extract_company()` her zaman "Unknown" döndürüyordu. 5 kademeli fallback eklendi: LinkedIn URL parse → başlık split → `application_url` domain → açıklama regex → "Unknown"
- `_extract_skills()` bare substring matching kullanıyordu: "ai" kelimesi "maintain" içinde, "go" kelimesi "going" içinde eşleşiyordu. Word-boundary regex'e geçildi.
- İki adet `except:` → `except ValueError:` (sessiz hata yutucu kaldırıldı)

**`scripts/scan/export_to_excel_advanced.py`** (+8 satır)
- Excel skill-matching fonksiyonu aynı bare substring problemini taşıyordu. Aynı word-boundary düzeltmesi uygulandı.

**`scripts/strategy/apply_strategy.py`** (+4 satır)
- `min_score=60` hardcoded eşiği — gerçek career_score'lar bu profil için 20-45 arasında çıkıyordu. Sonuç: her çalıştırmada "0 viable job." Eşik düşürüldü.

---

## [0.4.0] — 2026-06-23 — Dokümantasyon ve Kod Kalitesi

### 0.4.3 — 2026-06-23 23:56

**Commit:** `1769308` — `docs: rewrite README.md and CHANGELOG.md for accuracy and tone`

**README.md** (-291 satır, +158 satır)
- Emoji kaldırıldı, AI-generated ses tonu temizlendi
- Doğrulanamayan iddiaları kaldırıldı: "85% correlation" (hiç başvuru logu yok), "200+ skills" (gerçekte 68 skill / 74 edge), "9x faster / 30x more relevant" (baseline hiç olmadı)
- ApplyPilot (dış pip paketi) ile Career OS (bu repo) arasındaki fark netleştirildi — önceki versiyonlar ikisini karıştırıyordu
- Gerçek sayılar: search query sayısı, filter sayısı, Excel sütun/sheet sayıları kod incelenerek düzeltildi

**CHANGELOG.md**
- Gerçek scan verisine indirgendi, template eklendi

---

### 0.4.2 — 2026-06-23 23:55

**Commit:** `f9bd422` — `refactor: reorganize docs/ into setup/usage/tracking/strategy, add index`

**Değişiklikler:**
- Aynı seviyede duran 7 doc dosyası amacına göre 4 klasöre ayrıldı:
  - `docs/setup/` — QUICK_START.md, GITHUB_GUIDE.md, WINDOWS_SCHEDULER_GUIDE.md
  - `docs/usage/` — USAGE.md, APPLY_NOW.md
  - `docs/tracking/` — JOB_APPLICATIONS.md, APPLICATION_TRACKER.md
  - `docs/strategy/` — 2_MONTH_ACTION_PLAN.md
- `docs/README.md` eklendi — navigable index
- QUICK_START.md yeniden yazıldı: eksik kurulum adımları eklendi (`applypilot init` wizard'ı, `applypilot doctor`), stale iddia düzeltildi (searches.yaml repo'da değil, `~/.applypilot/`'de yaşıyor)
- Ölü `searches.yaml` silindi (yanlış schema, hiçbir kod okumuyordu)

---

### 0.4.1 — 2026-06-23 23:55

**Commit:** `0beaef6` — `test: move tests/ into its own folder and add real assertions`

**Değişiklikler:**
- 4 test dosyası repo kökünden `tests/` klasörüne taşındı
- Tüm testler sıfır `assert` içeriyordu — "geçti" = "çökmedi" anlamına geliyordu. Gerçek assertion'lar eklendi:
  - Deterministik hesaplamalar için kesin değer testi (skill level, ROI sıralaması)
  - Embedding-tabanlı semantic matcher skorları için range/invariant testi
- `test_production.py`: ApplyPilot DB veya config.yaml yoksa `pytest.skip()` — artık sessizce hiçbir şey yapmıyor
- Windows default `cp1252` encoding'de crash eden unicode checkmark'lar düz metin ile değiştirildi
- **Sonuç:** 17/17 test geçiyor, 4 tanesi gerçek ApplyPilot DB'ye karşı

---

### 0.4.0 — 2026-06-23 23:54

**Commit:** `d017db0` — `refactor: reorganize scripts/ into scan/strategy/tracking/packaging`

**Değişiklikler:**
- 11 script düz liste → 4 klasör:
  - `scripts/scan/` — run_full_scan.py, filter_jobs.py, export_to_excel_advanced.py, schedule_info.py
  - `scripts/strategy/` — apply_strategy.py, cold_email_generator.py, skills_gap_analyzer.py, extract_requirements.py
  - `scripts/tracking/` — track_applications.py, sync_to_github.py
  - `scripts/packaging/` — setup_package.py
- **Gerçek bug düzeltmesi:** `run_full_scan.py` subprocess path'lerini repo kökünde arıyordu (`filter_jobs.py`, `export_to_excel_advanced.py`) — dosyalar zaten `scripts/`'te olduğundan pipeline'ın filter ve export adımları hiç çalışmamış olabilirdi. Path'ler düzeltildi.
- `run_scan.bat` güncellendi

---

**Commit:** `813191f` — `fix: fix skill graph crash, encoding crash, and hardcoded profile in career_os`

**Düzeltilen 3 bug:**

1. **`career_os/core/skill_graph.py`:** `shortest_learning_path()` hedef skill taxonomy'de yoksa (örn. "Redis") `networkx.NodeNotFound` fırlatıyordu — `GapAnalyzer.analyze()` gerçek iş ilanlarında crash ediyordu. `try/except NodeNotFound` eklendi.

2. **`semantic_matcher.py`, `applypilot_loader.py`:** Unicode checkmark içeren `print()` çağrıları Windows'un default `cp1252` console encoding'i ile `UnicodeEncodeError` veriyordu.

3. **`applypilot_loader.py`:** `create_user_profile_from_config()` tamamen hardcoded `UserProfile` döndürüyordu. Artık `config.yaml`'dan name/email/years_experience/target_roles/salary/preferences okuyor, resume'yu `personal/<Name>.txt`'ten yüklüyor. Not: skill proficiency seviyeleri hâlâ override table gerektiriyor (config.yaml sadece skill adlarını saklıyor, seviyeleri değil).

---

**Commit:** `6206494` — `chore: add requirements.txt and config template, drop dead artifacts`

**Eklendi:**
- `requirements.txt` — career_os/ ve scripts/'in import ettiği tüm bağımlılıklar ilk kez belgelendi
- `config.yaml.example` — `applypilot_loader.py`'nin beklediği schema ile temiz şablon

**Silindi:**
- `scripts/export_to_excel.py` — `export_to_excel_advanced.py` tarafından tamamen supersede edilmişti, hiçbir yerde referans kalmamıştı
- `excel_exports/` — 3 dosya silinmiş script'in kalıntısıydı, 1 tanesi gerçek scan sonucuydu → `reports/`'a taşındı. Kişisel başvuru verisi git'te takip edilmemeli.

---

## [0.3.0] — 2026-06-23 — Pratik Entegrasyon

### 0.3.2 — 2026-06-23 01:13

**Commit:** `e44e641` — `Update README with integrated workflow`

README Quick Start güncellendi: iki seçenek sunuldu — Option 1: `apply_strategy.py` (ApplyPilot + Career OS), Option 2: Excel direkt (ApplyPilot only). APPLY_NOW.md'ye bağlantı eklendi.

---

### 0.3.1 — 2026-06-23 01:13

**Commit:** `d6cd86a` — `Add practical apply strategy script + guide`

**`scripts/apply_strategy.py`** (256 satır)  
ApplyPilot iş ilanlarını Career OS ile analiz eden entegrasyon betiği. 4 çıktı dosyası üretir:
- `apply_today.txt` — günlük top 10
- `apply_this_week.txt` — haftalık top 20
- `prioritized_applications.txt` — şirket boyutuna göre çeşitlendirilmiş portföy
- `learning_plan.txt` — 8 haftalık roadmap

**`APPLY_NOW.md`** — Günlük/haftalık rutinler, acceptance probability rehberi, career score yorumlama, cold email zamanlaması.

---

### 0.3.0 — 2026-06-23 01:06

**Commit:** `5788179` — `Add comprehensive usage documentation`

**`USAGE.md`** — İki sistem açıklaması, 3 kullanım seçeneği, gerçek istatistikler, troubleshooting, dürüst değerlendirme (ApplyPilot tek başına yeterli; Career OS CV için güçlü ama iş başvurusu için zorunlu değil).

README: iki sistem özeti, gerçek sayılar (562 iş, 30 perfect match), öncelik listesi.

---

## [0.2.0] — 2026-06-23 — Career OS İntelligence Katmanı

### 0.2.3 — 2026-06-23 00:57

**Commit:** `85d3071` — `Update Career OS README - Production ready documentation`

`career_os/README.md` kapsamlı yeniden yazım. Not: Bu versiyondaki bazı metrikler (`15-25% başvuru başarısı`, `64% öğrenme süresi azalması`) henüz veriyle doğrulanmamıştı — bir sonraki commit cycle'ında kaldırıldı/düzeltildi.

---

### 0.2.2 — 2026-06-23 00:53

**Commit:** `85c4839` — `Add Day 4: Production Integration with ApplyPilot`

**`career_os/data/applypilot_loader.py`** (399 satır) — İlk versiyon eklendi.
- ApplyPilot SQLite'tan veri okuma
- Company extraction (URL/title'dan)
- Skill extraction (açıklamadan)
- `UserProfile` oluşturma
- `test_production.py` (243 satır) — Gerçek DB üzerinde testler

---

### 0.2.1 — 2026-06-23 00:38

**Commit:** `9be4f37` — `Add Day 3: Opportunity Scorer + Career Decision Engine`

**`career_os/intelligence/opportunity_scorer.py`** (546 satır)

`OpportunityScorer`:
- Acceptance probability: company tier (big_tech 0.25×, startup 1.2×), experience gap, remote match (1.3×), visa sponsorship (0.4×), competition
- Career value: skill development potential, salary growth, company prestige, target role alignment
- Market demand: hardcoded skill demand dict (python=0.95, aws=0.9, ...)
- Expected value ranking: `fit × acceptance × career_value`

`CareerDecisionEngine`:
- Full pipeline orchestration
- Company size diversification (max n/3 per tier)
- Integrated gap analysis + roadmap
- APPLY / CONSIDER / SKIP recommendation

`test_day3.py` (349 satır) eklendi.

---

### 0.2.0 — 2026-06-23 00:33

**Commit:** `164150c` — `Add Day 2: Semantic Matcher + Gap Analyzer`

**`career_os/intelligence/semantic_matcher.py`** (421 satır)
- `SentenceTransformer('all-MiniLM-L6-v2')` ile 5 bileşenli eşleştirme:
  - Skills match (40%) — level-aware + transfer learning credit
  - Domain cosine similarity (25%) — embedding-based
  - Seniority match (20%) — years experience / level mapping
  - Work mode match (10%) — remote/hybrid/onsite
  - AI capability bonus (5%)
- Transfer learning: `_check_transfer()` — related skill varsa 0.5 cap

**`career_os/intelligence/gap_analyzer.py`** (419 satır)
- ROI = impact / learning_cost_hours
- Transfer learning discount (min 0.3, max 70%)
- Topological sort ile öğrenme sıralaması
- 8 haftalık plan (10 saat/hafta)
- Hardcoded `_RESOURCES` ve `_VALIDATION_PROJECTS` dict'leri

`test_day2.py` (305 satır) eklendi.

---

## [0.1.0] — 2026-06-23 — Career OS Çekirdek Temeli

**Commit:** `91df3e1` — `Add Career OS core foundation`

**`career_os/models/skill.py`** (236 satır)
- `SkillLevel` IntEnum: UNKNOWN(0), AI_ASSISTED(1), WORKING(2), INDEPENDENT(3), ADVANCED(4), EXPERT(5)
- `Skill` dataclass: name, level, evidence, ai_multiplier, base_hours_to_next_level, last_used, transferability
- `learning_cost(target_level)` — üstel ölçekleme
- `transfer_discount(related_skills)` — maks %70
- `effective_level()` — level × ai_multiplier
- `SKILL_CATEGORIES` — 8 kategori

**`career_os/models/profile.py`** (290 satır)
- `Experience`, `UserPreferences`, `UserProfile`, `Job`, `MatchResult`, `OpportunityScore` dataclass'ları
- `Job.all_skills()` — required + preferred birleşimi
- `OpportunityScore.should_apply(threshold=60.0)`, `priority_tier()`

**`career_os/core/skill_graph.py`** (378 satır)
- `networkx.DiGraph` tabanlı `SkillGraph`
- `_build_taxonomy()` — 68 skill, 74 edge, Python/Java/JS/Docker/AWS ailesi
- `get_transfer_factor()`, `shortest_learning_path()` (Dijkstra, `1-weight` maliyet), `get_related_skills()` (BFS), `calculate_learning_discount()` (min 0.3)

`test_career_os.py` (224 satır) eklendi.

---

## [0.0.3] — 2026-06-22 — Takip Sistemi ve Multi-Channel Strateji

**Commit:** `fa74fb9` — `🚀 Add multi-channel job application system`

**`scripts/cold_email_generator.py`** (458 satır)
- 5 email template: value_first, problem_solution, mutual_interest, direct_value, sponsorship_upfront
- 3'lü follow-up serisi (7, 14, 21. gün)
- `YOUR_INFO` ve `ACHIEVEMENTS` kodu içinde hardcoded

**`scripts/skills_gap_analyzer.py`** (426 satır)
- Excel "Missing Skills" sütunundan frequency analizi
- 8 haftalık öğrenme planı
- `LEARNING_RESOURCES` dict hardcoded

**`APPLICATION_TRACKER.md`** (227 satır) — 8 haftalık sprint planı, haftalık hedefler.

**`2_MONTH_ACTION_PLAN.md`** (492 satır) — Günlük breakdown, vize gerektiren adaylar için strateji.

---

**Commit:** `34f18fe` — `✨ Add job tracking system & GitHub integration`

**`JOB_APPLICATIONS.md`** — Markdown tabanlı başvuru takibi.

**`scripts/track_applications.py`** (238 satır) — Excel Notes sütununu parse eder, JOB_APPLICATIONS.md'yi günceller.

**`scripts/sync_to_github.py`** (203 satır) — Excel verilerinden GitHub Issues oluşturur. `REPO_NAME` placeholder bırakıldı.

**`GITHUB_GUIDE.md`** — GitHub setup rehberi.

---

## [0.0.2] — 2026-06-22 — İlk Scan Sonuçları

**Commit:** `47a3698` — `Add Excel reports from first scan`

İlk scan'den elde edilen Excel dosyaları commit edildi (daha sonra `62064940`'ta kaldırıldı — kişisel başvuru verisi git'te yaşamamalı).

---

**Commit:** `8d1b66e` — `Reorganize documentation structure`

README temizlendi, doc dosyaları `docs/` altına taşındı.

---

## [0.0.1] — 2026-06-22 — İlk Commit

**Commit:** `07643ec` — `🎉 Initial commit: Professional Job Discovery System`

Projenin temeli. İçerik:
- `.gitignore`, `.env.example`
- `run_scan.bat` — Windows'ta tam pipeline batch script
- `scripts/filter_jobs.py` (319 satır) — 8 SQL UPDATE filtresi: Senior/Lead/Principal (→4), Standalone Frontend (→4), Freelance/Contract (→3), Intern (→3), Standalone JS (→5), Analytics Engineer (→6), Paris onsite (→6), 4+ yıl deneyim/clearance (→5). Kayıt silmez, sadece `fit_score` düşürür.
- `scripts/export_to_excel.py` (359 satır) — ilk Excel export (daha sonra advanced ile değiştirildi)
- `scripts/export_to_excel_advanced.py` (656 satır) — 6 sayfa Excel: Executive Summary, Perfect Match (8+), Good Match (7), Skills Analysis, By Company, Full Database
- `scripts/run_full_scan.py` (354 satır) — 6 adımlı pipeline: backup → discover → score → filter → Excel → summary. `logs/run_history.json` yazar.
- `scripts/schedule_info.py` (93 satır) — son scan zamanını okur, "ne zaman tara?" önerir
- `scripts/setup_package.py` (199 satır) — kurulum paketi oluşturucu
- `scripts/track_applications.py` (238 satır) — başvuru takibi
- `scripts/extract_requirements.py` (263 satır) — iş ilanlarından gereksinim extraction
- Dokümantasyon: README.md, QUICK_START.md, WINDOWS_SCHEDULER_GUIDE.md, CHANGELOG.md
- `logs/`, `reports/` — `.gitkeep` ile boş klasörler

**İlk scan istatistikleri:**
- 562 iş keşfedildi
- 30 perfect match (8+)
- 121 good match (7)
- Maliyet: ~$0.73
- Süre: ~25-30 dakika

---

## Güvenlik Notu

`config.yaml` dosyasında plaintext OpenRouter API anahtarı bulunuyor (`sk-or-v1-4d7abdbc97...`). Bu anahtar git geçmişine girdi. Henüz temizlenmedi — BFG Repo Cleaner veya `git filter-repo` ile geçmişten silinmeli, anahtar revoke edilmeli.
