# Memory Architecture for a Git-Style "Person Memory" (Career Assistant, Postgres-only)

Scope note: research done 2026-11-23. Sources marked **[fetched]** were read in this session; sources marked **[background, not re-fetched]** are well-known primary references cited from prior knowledge and should be spot-checked by the writer before being quoted verbatim. Weak or vendor claims are flagged inline.

---

## 1. Event sourcing + CQRS for user data (append-only log + projections; when it helps; pitfalls; Postgres implementations)

### Takeaway
Event sourcing gives exactly the "every change kept, replayable, auditable" property the product wants, but Microsoft's own pattern guide warns it is costly and recommends applying it selectively (it even names "user profile management" as a typical CRUD candidate). For a small team on one Postgres, the practical form is a plain `events` table (JSONB payload, per-stream version, optimistic concurrency) plus synchronously-updated projection tables in the same transaction, with upcasters for schema evolution, snapshots only when streams get long, and personal data kept out of the immutable payload (reference-by-id or crypto-shredding).

### Cited Findings
- Definition: store "the full series of actions taken on an object in an append-only store" which acts as the system of record; state is derived by replaying the stream ("rehydration"); materialized views/projections are used because replay is costly. — [Azure Architecture Center, Event Sourcing pattern (updated 2026)](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Explicit warning: "Event sourcing is a complex pattern that introduces significant trade-offs… costly to migrate to or from… For most systems and most parts of a system, traditional data management is sufficient." It suggests applying it selectively, e.g. to a ledger, and using CRUD for parts like "user profile management or application configuration." — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Not suitable for: plain CRUD with no audit/replay need; prototypes/MVPs/short-lived systems; systems needing real-time consistent views (projections are eventually consistent); mostly static data; teams without event-driven experience. — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Use when: you want to capture intent/reason (e.g. "Moved home", "Closed account"), need history/audit/rollback, want to rebuild read models in new shapes later. Design events around business intent ("two seats reserved") rather than resulting state ("remaining seats = 42"); state-focused events reduce the store "to a change log that has no business meaning." — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Schema evolution strategies, in order of preference: tolerant deserialization (ignore unknown fields, default missing); explicit event version in envelope or type name; **upcasting** (chained transform functions old→new at read time, stored events unchanged); in-place migration only as "last resort because it undermines the audit trail." Bugs that wrote wrong events need compensating events or upcasters. — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Concurrency: event stores use optimistic concurrency and "reject an append if the stream changed since it was read"; a per-stream incremental id lets the store reject a duplicate (entity id, event id). — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Snapshots every N events reduce replay cost; "Snapshots are an optimization, not a replacement for the eventstream" and can be regenerated. — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Consumers get at-least-once delivery, so handlers must be idempotent; track last processed sequence number per consumer. Watch for circular event→event loops. Test with given-when-then (past events, command, expected new events). — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Event store can be "a general-purpose relational or document database with an append-only table"; relational DBs "require you to build those behaviors yourself" (stream reads, optimistic concurrency, snapshots). Don't use Kafka as the event store (no per-entity stream queries / optimistic concurrency). — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- GDPR tension is called out in the pattern itself: store personal data outside the event store and reference by id; if not separable, use crypto-shredding with a per-subject key (adds encryption overhead on every read/write, needs robust key management). — [Azure, Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Classic definition: "Capture all changes to an application state as a sequence of events"; enables complete rebuild, temporal query, event replay. — [Martin Fowler, Event Sourcing (2005)](https://martinfowler.com/eaaDev/EventSourcing.html) **[background, not re-fetched]**
- Marten (.NET) is the best-known "Postgres as event store" library: events in an `mt_events` table with JSONB bodies, `mt_streams` with version, inline/async projections, snapshots. — [Marten docs: Event Store](https://martendb.io/events/) **[background, not re-fetched]** (No equivalent mature Python library was verified in this session; Python options like `eventsourcing` (johnbywater) exist with a Postgres backend — **unverified maturity**.)

### Inferences
- Recommended hybrid for Aplio (small team): **"event log + current-state tables written in the same transaction"** (sometimes called "event-sourcing-lite" / audit-log-as-source). Every write path (`profile.update_skill`, `cv.commit`, `application.status_changed`, `learning.module_completed`, `decision.recorded`) appends one row to `person_events` AND updates projection tables in one Postgres transaction → no eventual-consistency problem, projections can still be rebuilt by replay. Async projections (embeddings, LLM summaries, briefing digests) run off a cursor on the same table (`LISTEN/NOTIFY` or a polling worker with `last_seq`).
- Minimal schema sketch:
  ```sql
  CREATE TABLE person_events (
    seq           bigserial PRIMARY KEY,          -- global order (transaction time order)
    person_id     uuid NOT NULL,
    stream        text NOT NULL,                  -- 'profile', 'cv:<id>', 'application:<id>', 'learning'
    stream_version int  NOT NULL,                 -- optimistic concurrency
    type          text NOT NULL,                  -- 'SkillAdded', 'CvCommitted', 'ApplicationSubmitted', ...
    schema_ver    smallint NOT NULL DEFAULT 1,    -- for upcasters
    payload       jsonb NOT NULL,                 -- NO raw PII here; ids/refs or ciphertext
    actor         text NOT NULL,                  -- 'user' | 'agent:matcher' | 'agent:briefing' | 'import:linkedin'
    source_ref    jsonb,                          -- provenance: chat msg id, doc id, URL
    valid_from    timestamptz,                    -- valid time (when it became true in the world)
    recorded_at   timestamptz NOT NULL DEFAULT now(), -- transaction time
    causation_id  bigint, correlation_id uuid,
    UNIQUE (person_id, stream, stream_version)
  );
  CREATE INDEX ON person_events (person_id, stream, stream_version);
  CREATE INDEX ON person_events USING gin (payload jsonb_path_ops);
  ```
- Transactional outbox: since notifications/briefing are side effects, the same `person_events` table can double as the outbox (consumer table `projection_checkpoints(consumer, last_seq)`), avoiding dual-write bugs. (Outbox pattern itself not fetched this session — see Gaps.)
- Pitfall specific to LLM writers: agent-generated events (e.g. "inferred skill: Kubernetes") must be distinguishable from user-asserted facts (`actor`, `confidence`), otherwise replay re-imports hallucinations as truth.

### Gaps
- Did not fetch Greg Young's "Versioning in an Event Sourced System" (Leanpub) for upcasting details; Azure covers the same strategies.
- Did not verify a production-grade Python/SQLAlchemy event-store library; recommendation is to hand-roll the ~1 table + checkpoint table.
- Transactional outbox pattern doc (microservices.io / Azure) not fetched this session.

---

## 2. Temporal / bitemporal data ("what did we know on date X" vs "what was true then")

### Takeaway
Two clocks are needed: **valid time** (when a fact was true about the person, e.g. "worked at X 2021–2023", "knew Python since 2019") and **transaction time** (when Aplio learned/recorded it). PostgreSQL 18+ natively supports application-time keys (`WITHOUT OVERLAPS`) and temporal foreign keys (`PERIOD`), but still does **not** support system-versioned (transaction-time) tables — emulate with triggers/history tables or simply derive transaction time from the append-only event log. Zep/Graphiti is a concrete LLM-memory precedent that uses exactly this bitemporal model.

### Cited Findings
- PostgreSQL "Current" docs (v19.0 docs at time of fetch): application time supported via range/multirange column with `PRIMARY KEY (product_no, valid_at WITHOUT OVERLAPS)`; backed by GiST, requires `btree_gist`; empty ranges forbidden; temporal FKs `FOREIGN KEY (product_no, PERIOD valid_at) REFERENCES products (product_no, PERIOD valid_at)` — referenced history must cover the referencing row's history, possibly via multiple referenced rows; only `NO ACTION` supported. — [PostgreSQL docs: Temporal Tables](https://www.postgresql.org/docs/current/ddl-temporal-tables.html) **[fetched]**
- Same page: "PostgreSQL does not currently support system time, but it could be emulated using triggers, and there are external extensions that provide such functionality." — [PostgreSQL docs: Temporal Tables](https://www.postgresql.org/docs/current/ddl-temporal-tables.html) **[fetched]**
- The `WITHOUT OVERLAPS` / `PERIOD` features first shipped in PostgreSQL 18 (an earlier attempt for v17 was reverted during development). — [PostgreSQL feature matrix: temporal constraints](https://www.postgresql.org/about/featurematrix/detail/temporal-constraints); [Neon PG18 guide](https://neon.com/postgresql/18/temporal-constraints); [revert patch on pgsql-hackers](https://postgresql.org/message-id/attachment/160256/0004-Revert-Add-temporal-FOREIGN-KEY-contraints.patch) **[search results]**
- Tooling: Atlas supports PG18 temporal keys; Django ticket #36627 tracks support; Npgsql/EF Core documents it. (SQLAlchemy support not found.) — [Atlas changelog](https://atlasgo.io/changelog/postgres-temporal-constraints); [Django ticket 36627](https://code.djangoproject.com/ticket/36627?format=tab); [Npgsql docs](https://www.npgsql.org/efcore/misc/temporal-constraints.html) **[search results]**
- `UPDATE/DELETE … FOR PORTION OF` was not mentioned on the temporal-tables docs page — availability unconfirmed. — [PostgreSQL docs](https://www.postgresql.org/docs/current/ddl-temporal-tables.html) **[fetched]**
- SQL:2011 introduced application-time period tables, system-versioned tables (`FOR SYSTEM_TIME AS OF`), and bitemporal tables combining both. — [Kulkarni & Michels, "Temporal features in SQL:2011", SIGMOD Record 41(3), 2012](https://sigmodrecord.org/publications/sigmodRecord/1209/pdfs/07.industry.kulkarni.pdf) **[background, not re-fetched]**; Snodgrass, *Developing Time-Oriented Database Applications in SQL* (1999) is the canonical bitemporal design text **[background]**.
- LLM-memory precedent — Zep's Graphiti uses a bi-temporal model: timeline T (valid time: `t_valid`, `t_invalid`) and T′ (transaction time: `t'_created`, `t'_expired`) "for traditional database auditing." On a contradicting new fact, an LLM compares against related edges and sets the old edge's `t_invalid` to the new edge's `t_valid` (invalidate, don't delete). — [Rasmussen et al., "Zep: A Temporal Knowledge Graph Architecture for Agent Memory", arXiv 2501.13956](https://arxiv.org/html/2501.13956) **[fetched]**
- Mem0's graph variant likewise "marks obsolete relations as invalid rather than deleting them," preserving history for temporal reasoning. — [Chhikara et al., Mem0, arXiv 2504.19413](https://arxiv.org/html/2504.19413) **[fetched]**
- Temporal reasoning is where memory matters most: on LongMemEval, Zep vs full-context improved temporal-reasoning questions 36.5%→54.1% (gpt-4o-mini) and 45.1%→62.4% (gpt-4o). — [Zep paper, Table 3](https://arxiv.org/html/2501.13956) **[fetched]**

### Inferences
- Practical Aplio model: a `person_facts` projection with both clocks:
  ```sql
  CREATE EXTENSION IF NOT EXISTS btree_gist;
  CREATE TABLE person_facts (
    person_id   uuid,
    fact_key    text,              -- 'skill:python', 'employment:acme', 'pref:remote', 'goal:target_role'
    value       jsonb,             -- {"level":"advanced","evidence":[...]}
    valid_at    tstzrange,         -- valid time: when true in the person's life
    sys_period  tstzrange NOT NULL DEFAULT tstzrange(now(), NULL), -- transaction time
    confidence  real, source_event bigint REFERENCES person_events(seq),
    PRIMARY KEY (person_id, fact_key, valid_at WITHOUT OVERLAPS)  -- PG18+
  );
  -- history table + trigger moves superseded rows (sets upper(sys_period)=now())
  ```
  "What was true on 2024-03-01": `WHERE valid_at @> '2024-03-01'` on current rows. "What did Aplio believe on 2024-03-01": query history ∪ current `WHERE sys_period @> '2024-03-01'`. Note: the PK constraint above applies only to current rows; history rows go to a separate table without the constraint.
- Simpler alternative if PG < 18 or SQLAlchemy friction: keep `valid_from/valid_to` columns + an `EXCLUDE USING gist` constraint (available long before PG18); derive transaction time from `person_events.recorded_at`.
- Since the event log already stores `recorded_at` (transaction time) and `valid_from` (valid time), "as-known-at" queries can always be answered by replaying events with `recorded_at <= X` — the temporal projection is an optimization.

### Gaps
- Did not verify current state of community system-versioning extensions (`temporal_tables`, `periods` by Vik Fearing) for PG 18/19 or managed-Postgres availability.
- `FOR PORTION OF` support in PG19 unverified.

---

## 3. Git-like versioning of documents and structured data (CV variants as branches)

### Takeaway
Git's model — immutable content-addressed snapshots, commits with parent pointers, branches as movable named refs, diffs computed between snapshots, 3-way merge from a common ancestor — maps cleanly onto CV variants and profile versions, and can be implemented in ~3 Postgres tables (`blobs`, `commits`, `refs`) plus RFC 6902 JSON Patch for diffs. Purpose-built versioned DBs (Dolt, TerminusDB, lakeFS) prove the model but would mean a second database; Dolt is MySQL-compatible (Doltgres is the Postgres flavour, maturity unverified here).

### Cited Findings
- Dolt: a commit stores the root hash of the whole database linked into a commit graph; commit hashes are SHA-256 over the entire database; each commit links to its parent, merge commits have multiple parents; commits support diffs between commits, finding common ancestors, restoring to a past commit, history/authorship; Dolt commits are distinct from SQL transaction commits; available via CLI or SQL (`dolt_commit`). — [Dolt docs: Commits](https://www.dolthub.com/docs/concepts/dolt/git/commits) **[fetched]**
- Dolt's storage uses prolly trees (content-addressed B-trees) enabling structural sharing and cell-level diff/merge; Dolt is MySQL-wire-compatible; DoltgreSQL is the Postgres-compatible variant. — [DoltHub docs](https://www.dolthub.com/docs/) **[background, not re-fetched — Doltgres maturity unverified]**
- TerminusDB: graph/document DB with git-like branch, commit, diff, merge on JSON documents; lakeFS: git-like branching over object storage (data lakes). — [TerminusDB docs](https://terminusdb.com/docs/) ; [lakeFS docs](https://docs.lakefs.io/) **[background, not re-fetched]**
- RFC 6902 JSON Patch: ordered list of operations `add`, `remove`, `replace`, `move`, `copy`, `test` addressed by JSON Pointer (RFC 6901); `test` enables optimistic precondition checks. — [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902) **[background, not re-fetched]**
- RFC 7386 JSON Merge Patch (obsoleted by RFC 7396): a partial document where `null` means delete; cannot express array element edits or set a value to null — simpler but lossy. — [RFC 7396](https://www.rfc-editor.org/rfc/rfc7396) **[background, not re-fetched]**
- Precedent of "never delete, invalidate" in memory systems (Graphiti `t_invalid`, Mem0g invalid relations) — see §2. — [Zep](https://arxiv.org/html/2501.13956); [Mem0](https://arxiv.org/html/2504.19413) **[fetched]**

### Inferences
- Recommended Postgres "mini-git" for CVs and profile documents:
  ```sql
  CREATE TABLE doc_blobs (            -- content-addressed, immutable, deduplicated
    hash bytea PRIMARY KEY,           -- sha256 of canonical JSON (sorted keys, RFC 8785 JCS)
    person_id uuid NOT NULL,          -- needed for per-user erasure
    body jsonb NOT NULL               -- structured CV: sections, bullets with stable ids
  );
  CREATE TABLE doc_commits (
    id bytea PRIMARY KEY,             -- sha256(tree_hash || parents || author || msg || ts)
    person_id uuid NOT NULL, doc_kind text NOT NULL,  -- 'cv' | 'profile'
    tree_hash bytea REFERENCES doc_blobs(hash),
    parents bytea[] NOT NULL,         -- 0 = root, 1 = normal, 2 = merge
    author text NOT NULL,             -- 'user' | 'agent:tailor'
    message text, created_at timestamptz DEFAULT now(),
    patch_from_parent jsonb           -- cached RFC 6902 diff for UI ("what changed")
  );
  CREATE TABLE doc_refs (             -- branches & tags = mutable pointers
    person_id uuid, doc_kind text, name text,  -- 'main', 'target/data-engineer', 'tag/sent-to-acme-2026-05'
    commit_id bytea REFERENCES doc_commits(id),
    PRIMARY KEY (person_id, doc_kind, name)
  );
  ```
  - `main` = master CV (the "truth"); each target role is a branch (`target/backend`, `target/ml-eng`); every submitted application **tags** the exact commit sent (immutable evidence of "which CV did I send to X").
  - Branch moves use compare-and-swap: `UPDATE doc_refs SET commit_id=$new WHERE … AND commit_id=$expected` (same optimistic concurrency idea as events).
  - Give every CV bullet/section a stable UUID inside the JSON; then diffs/merges are per-item (like Dolt's cell-level) instead of array-index based, which RFC 6902 handles poorly (index shifts).
  - Merge ("pull the new certification from main into all role branches"): 3-way merge = diff(base→main) applied to branch, conflicts only when the same item id was edited on both sides; let the LLM propose a resolution but require user confirmation.
- Store full snapshots (blobs) rather than patch chains: CVs are a few KB, dedup by hash makes storage trivial, and it avoids replay to read a version; keep RFC 6902 patches only as derived/cached data for the "diff" UI.
- Each commit also emits a `CvCommitted` event into `person_events`, so the global timeline and the doc graph stay linked.
- Don't adopt Dolt/TerminusDB for this: it doubles the operational surface for a feature implementable in Postgres; their value is as design references.

### Gaps
- Did not fetch Dolt merge/conflict docs, Doltgres status, TerminusDB, or lakeFS pages this session.
- No primary source found specifically on CV versioning as branches — this is a design inference.

---

## 4. LLM agent memory research (types, architectures, retrieval, benchmarks with numbers)

### Takeaway
The literature converges on: (a) keep raw episodes losslessly, (b) extract/consolidate atomic facts with ADD/UPDATE/DELETE(invalidate)/NOOP decisions, (c) retrieve a small, relevant, time-annotated slice (hybrid semantic + lexical + graph/recency + importance) rather than stuffing full history, and (d) periodically "reflect" into higher-level summaries that cite their sources. Benchmarks show selective memory beats or matches full-context at ~1–2k tokens and ~90% lower latency, with temporal and preference questions benefiting most; but vendor benchmark numbers are self-reported and contested.

### Cited Findings
**Generative Agents (Park et al., UIST 2023)**
- Memory stream stores "a complete record of the agent's experiences" in natural language; retrieval score = recency + importance + relevance, each min-max normalized to [0,1], all weights α = 1. Recency = exponential decay over game hours since last retrieval, decay factor **0.995**; importance = LLM-rated integer **1–10** at creation time (e.g. 2 for cleaning room, 8 for asking crush out); relevance = cosine similarity of embeddings. — [Park et al., arXiv 2304.03442 (ar5iv HTML)](https://ar5iv.labs.arxiv.org/html/2304.03442) **[fetched]**
- Reflection triggers when the sum of importance of recent events exceeds **150** (~2–3 times per simulated day); LLM gets the 100 most recent memories → generates 3 salient questions → retrieves for each → produces 5 insights each citing evidence ("insight (because of 1, 5, 3)"); reflections can cite reflections, forming trees. — [Park et al.](https://ar5iv.labs.arxiv.org/html/2304.03442) **[fetched]**
- Ablation (TrueSkill μ): full 29.89; no reflection 26.88; no reflection+planning 25.64; human crowdworkers 22.95; no observation/reflection/planning 21.21. — [Park et al.](https://ar5iv.labs.arxiv.org/html/2304.03442) **[fetched]**

**MemGPT / Letta (Packer et al., 2023)**
- "Virtual context management" inspired by OS hierarchical memory: moves data between fast (in-context) and slow (external) tiers, uses interrupts/function calls; evaluated on long-document analysis and multi-session chat. — [Packer et al., arXiv 2310.08560](https://arxiv.org/abs/2310.08560) **[fetched abstract]**
- (Details: core memory blocks the agent self-edits, recall storage = searchable message history, archival storage = vector store; productised as Letta.) — [MemGPT paper](https://arxiv.org/abs/2310.08560) **[background, not verified from full text]**

**Mem0 (Chhikara et al., 2025)**
- Pipeline: extract candidate facts from new exchange → for each, retrieve top-s similar memories → LLM chooses via tool call **ADD / UPDATE / DELETE / NOOP**. Graph variant Mem0g stores entities (type, embedding, timestamp) and (source, relation, destination) triplets; conflicts resolved by marking obsolete relations invalid. — [Mem0, arXiv 2504.19413](https://arxiv.org/html/2504.19413) **[fetched]**
- LoCoMo LLM-as-judge overall J: Full-context **72.90**, Mem0g **68.44**, Mem0 **66.88**, Zep **65.99**, best RAG (k=2, 256-tok chunks) **60.97**, LangMem **58.10**, OpenAI memory **52.90**, A-Mem **48.38**. — [Mem0 Table 2](https://arxiv.org/html/2504.19413) **[fetched]**
- p95 total latency (s): Mem0 1.44, Mem0g 2.59, Zep 2.93, RAG 1.91, A-Mem 4.37, LangMem 60.40, full-context 17.12. Retrieved context per query: Mem0 1,764 tokens, Mem0g 3,616, Zep 3,911, full-context 26,031. Stored memory per conversation: Mem0 ~7k tokens, Mem0g ~14k, Zep >600k (vs ~26k raw). Abstract: 91% lower p95 latency and >90% token savings vs full-context; 26% relative improvement over OpenAI. — [Mem0](https://arxiv.org/html/2504.19413) **[fetched]**
- Caveat: these are Mem0's self-reported comparisons; note full-context still scores highest on LoCoMo (conversations ~26k tokens fit in context). Zep publicly disputed Mem0's Zep configuration **[weak — recalled, not fetched]**.

**Zep / Graphiti (Rasmussen et al., 2025)**
- Three subgraphs: episode subgraph (raw messages/text/JSON stored losslessly), semantic entity subgraph (resolved entities + fact edges), community subgraph (label-propagation clusters with summaries). Retrieval runs cosine, BM25 and BFS in parallel, then reranks (RRF, MMR, episode-mentions, node-distance, cross-encoder); context string includes facts with validity dates. — [Zep, arXiv 2501.13956](https://arxiv.org/html/2501.13956) **[fetched]**
- DMR: Zep 94.8% vs MemGPT 93.4%. LongMemEval_s: gpt-4o-mini full-context 55.4% (31.3 s, 115k tokens) vs Zep 63.8% (3.20 s, 1.6k tokens); gpt-4o full-context 60.2% (28.9 s) vs Zep 71.2% (2.58 s). Gains largest for single-session-preference (gpt-4o 20.0%→56.7%) and temporal reasoning; Zep is *worse* on single-session-assistant (94.6%→80.4%, gpt-4o). — [Zep Tables 2–3](https://arxiv.org/html/2501.13956) **[fetched]** (self-reported by vendor)

**A-MEM (Xu et al., 2025)**
- Zettelkasten-style notes with contextual description, keywords, tags; automatic link generation to similar past memories; "memory evolution" — new memories can update attributes of existing ones. — [A-MEM, arXiv 2502.12110](https://arxiv.org/abs/2502.12110) **[fetched abstract]** (A-Mem scored lowest (48.38) in Mem0's LoCoMo comparison — third-party run, see above.)

**LongMemEval (Wu et al., ICLR 2025)**
- 500 curated questions testing five abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention; commercial assistants and long-context LLMs show ~30% accuracy drop over sustained interactions. Proposed optimizations: session decomposition (value granularity), fact-augmented key expansion (indexing), time-aware query expansion (narrow search by time). — [LongMemEval, arXiv 2410.10813](https://arxiv.org/abs/2410.10813) **[fetched abstract]**

**Memory types**
- Episodic (what happened, raw events), semantic (distilled facts/beliefs), procedural (how to act — prompts/rules/skills) is the CoALA taxonomy also used by LangMem. — [Sumers et al., "Cognitive Architectures for Language Agents" (CoALA), arXiv 2309.02427](https://arxiv.org/abs/2309.02427); [LangMem conceptual guide](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/) **[background, not re-fetched]**

### Inferences
- Mapping to Aplio:
  - **Episodic** = `person_events` + raw chat/document episodes (lossless, like Graphiti's episode subgraph).
  - **Semantic** = `person_facts` (bitemporal), CV commits, skill graph; produced by a Mem0-style extractor that outputs ADD/UPDATE/INVALIDATE/NOOP against existing facts — never physical DELETE (set `valid_to`/`t_invalid`), matching Graphiti/Mem0g.
  - **Procedural** = per-user preferences for how Aplio behaves (tone, notification cadence, "never suggest relocation"), stored as versioned rules the agents load into system prompts.
  - **Reflections** = periodic LLM "insights" (e.g. "rejections cluster at final interview for senior roles") stored as facts with `kind='reflection'` and `evidence_event_ids[]`, triggered by an importance-sum threshold à la Park (150) or weekly; must cite sources so the UI can show "why Aplio thinks this".
- Retrieval for a prompt (single Postgres): pgvector embeddings on facts/episodes + Postgres full-text (`tsvector`, BM25-like) + structured filters (module, time window, `valid_at @> now()`), fused with RRF, then scored with recency decay and importance; inject ~1–2k tokens of facts **with their validity dates** (Zep finding: dated facts help temporal questions). Always include a small "core profile" block (MemGPT core memory analog) — current target roles, top skills, constraints — regardless of query.
- Each module reads a projection tailored to it (job-matching reads current skills/preferences; briefing reads last-N-days events; learning reads skill gaps) and writes back only via events — the CQRS split.
- Evidence suggests full-context is still competitive when the whole history fits (LoCoMo 72.9 vs 66.9); for a single user's career data, a hybrid "core profile always + retrieved episodes" is safer than pure retrieval.

### Gaps
- LoCoMo original paper (Maharana et al., ACL 2024, arXiv 2402.17753) not fetched; dataset stats not verified here.
- LongMemEval per-system leaderboard numbers beyond Zep's report not collected; no 2026 SOTA numbers verified (Letta, Mem0 v2, OpenAI/Anthropic memory features). Letta has claimed strong LoCoMo results with a simple filesystem agent **[weak — recalled, not verified]**.
- MemGPT full-text details (core/recall/archival) not verified this session.
- Benchmark numbers are largely vendor-self-reported; no independent replication was found in this session.

---

## 5. Personal knowledge graphs and combining them with event logs

### Takeaway
Balog & Kenter define a PKG as structured information about entities that matter to one user (even if not globally notable), linked to general KGs. In practice the PKG should be a **projection** of the event log (entities = person, skills, companies, roles, courses, applications; edges = has_skill, applied_to, worked_at, completed, targets), with bitemporal edges and provenance back to events — the architecture Zep/Graphiti demonstrates.

### Cited Findings
- Balog & Kenter, "Personal Knowledge Graphs: A Research Agenda," ICTIR 2019, pp. 217–220, DOI 10.1145/3341981.3344241 (Google, London). PKG = structured information about entities personally related to the user, including ones not globally important; the paper contrasts PKGs with general KGs and sets out challenges/research agenda (population, representation, management, access/use). — [Google Research listing](https://research.google/pubs/personal-knowledge-graphs-a-research-agenda/); [dblp](https://dblp.org/rec/conf/ictir/BalogK19) **[search results; full text not extracted]**
- Graphiti: episodes (raw input) linked via episodic edges to the entities they mention; semantic entity subgraph built by extraction + entity resolution; facts as edges with bitemporal validity; communities summarised. — [Zep](https://arxiv.org/html/2501.13956) **[fetched]**
- Mem0g: entities with type, embedding, creation timestamp; relations as triplets; similarity-threshold entity resolution; ~2% better than flat Mem0 on LoCoMo at ~2× latency and tokens. — [Mem0](https://arxiv.org/html/2504.19413) **[fetched]**

### Inferences
- In one Postgres: `pkg_nodes(id, person_id, type, canonical_name, external_ref /* ESCO/O*NET skill id, company domain */, embedding vector)` and `pkg_edges(id, person_id, src, rel, dst, props jsonb, valid_at tstzrange, sys_period tstzrange, source_event bigint)`. Recursive CTEs handle 1–3 hop traversals fine at single-user scale; no graph DB needed.
- Linking to external KGs (ESCO/O*NET skill taxonomies, company identifiers) is the PKG "linking to general KG" idea and lets job-matching compare person skills with job skills on canonical ids.
- Because the graph is a projection, it can be rebuilt when extraction prompts/models improve — a key reason to keep episodes lossless.

### Gaps
- Could not extract Balog & Kenter full text (PDF binary); research-agenda sub-areas listed above are from abstract-level summaries and should be verified.
- No evidence found comparing PKG vs flat-fact memory specifically for career assistants.

---

## 6. Privacy: GDPR erasure with append-only logs; user-visible memory controls and trust

### Takeaway
Append-only does not exempt you from Art. 17: regulators expect erasure "by design." The safe pattern is to keep personal data out of immutable records (reference by id into a deletable store = "forgettable payloads"), and where it must be inside, encrypt per subject and delete the key (crypto-shredding) — but the EDPB treats encrypted/hashed data as still personal and key deletion as risk-reducing, not a guaranteed equivalent to deletion. For a single Postgres app, the simplest compliant approach is **hard delete per person** (all tables are `person_id`-partitioned) plus crypto-shredding only for backups/derived copies. Users strongly want to see/edit/delete memories; evidence on trust is mostly qualitative or small prototype studies.

### Cited Findings
- EDPB Guidelines 02/2025 on blockchain (final v2.0, dated 7 July 2026): erasure/objection must be "complied with by design" (para. 102); registering clear-text, encrypted or hashed personal data on-chain is "not advisable" because it is hard to rectify/erase (para. 104); rectification via a later cancelling transaction while the original remains (para. 106). — [EDPB Guidelines 02/2025 page](https://edpb.europa.eu/documents/guideline/guidelines-022025-on-processing-of-personal-data-through-blockchain_en); [v2 PDF](https://www.edpb.europa.eu/system/files/2026-07/edpb_guidelines_202502_blockchain_v2_en.pdf) **[fetched via summary tool]**
- Same guidelines: salted/keyed hashes remain personal data; after deleting the key/salt the hash "should not be linkable" unless algorithm broken or key leaked; unsalted hashes insufficient (para. 52). Encryption + key deletion makes data unintelligible only until algorithms are broken or keys compromised; encryption does not remove GDPR obligations (para. 51); consider encryption lifespan incl. quantum risk (para. 96). Measures "can be helpful for reducing risks" but must be "carefully tested, validated" and combined (para. 56). Preference: only proof-of-existence on the immutable ledger, personal data off-chain (para. 54). — [EDPB Guidelines 02/2025](https://edpb.europa.eu/documents/guideline/guidelines-022025-on-processing-of-personal-data-through-blockchain_en) **[fetched; paragraph numbers via summarising tool — verify before quoting]**
- Crypto-shredding (Verraes): per-resource encryption key; deleting the key makes all copies and backups unreadable; caveats: only as strong as the crypto/key management; doesn't stop consumers deriving new sensitive values from data; legal view that encrypted data is still personal data. Recommends **Forgettable Payloads** (sensitive payload stored in a separate, deletable store referenced from the event) as more appropriate for personal data. — [Mathias Verraes, "Eventsourcing Patterns: Crypto-Shredding" (2019)](https://verraes.net/2019/05/eventsourcing-patterns-throw-away-the-key/) **[fetched]**
- Azure pattern guide recommends the same two options (store PII outside the event store by id; else per-subject key crypto-shredding with encryption overhead and key management cost). — [Azure Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) **[fetched]**
- Key granularity trade-off: per-user key = max isolation, highest key-management overhead; envelope pattern with per-record DEK wrapped by per-user KEK described as practical; if a key copy survives (backups), data is recoverable. — [OneUptime crypto-shredding guide (vendor blog, 2026)](https://oneuptime.com/blog/post/2026-02-17-how-to-set-up-crypto-shredding-for-gdpr-right-to-erasure-compliance-in-google-cloud/view); [DEV: "You can't delete an event…"](https://dev.to/norbertrosenwinkel/you-cant-delete-an-event-gdpr-says-you-must-crypto-shredding-is-the-truce-26ak) **[search results; weak/vendor sources]**
- User needs: interview study of ChatGPT memory users — users want granular control over memory generation, management, use and updating (review, edit, delete, categorise) and transparency into how memories and inferences are used; opacity undermines sense of control. — [Understanding Users' Privacy Perceptions Towards LLM's RAG-based Memory, arXiv 2508.07664](https://arxiv.org/html/2508.07664v1) **[search result summary]**
- MemoAnalyzer prototype (n=36): proactive memory-privacy UI preferred over default GPT memory and manual management for perceived control, transparency, trust, with comparable time. — ["Ghost of the past", arXiv 2410.14931](https://arxiv.org/html/2410.14931v1) **[search result summary; small prototype study]**
- Reporting on a study at ACM Web Conference: users have less control over what is stored than vendors promise. — [CJR](https://www.cjr.org/?p=119732) **[search result; secondary source]**
- Transparency vs cognitive load: "Too much visibility into memory may overwhelm users. But too little undermines trust." — [IBM Think](https://ibm.com/think/news/when-ai-remembers) **[expert opinion]**

### Inferences
- Aplio erasure design (single Postgres, not a public ledger — so true deletion IS possible, unlike blockchain):
  1. Every row in every memory table carries `person_id` → "forget me" = transactional `DELETE … WHERE person_id = $1` across events, facts, blobs, commits, embeddings, LLM caches.
  2. Selective forget ("forget my salary expectation"): append a `FactForgotten` tombstone event AND physically purge/redact the earlier payloads and derived rows (event payload rewrite is acceptable here — it's the Azure "last resort" in-place migration, justified by law); keep only a non-PII tombstone (`type`, `seq`, `forgotten_at`) so replay stays consistent.
  3. Crypto-shredding for what you can't easily rewrite: backups, exports, object storage (CV PDFs). Per-user DEK wrapped by a KMS KEK; delete the wrapped DEK on erasure. Treat as risk reduction, per EDPB.
  4. Data minimisation: don't log raw chat in events; store episodes in a separate `episodes` table with retention policy; embeddings are derived personal data and must be deleted with source.
- "What Aplio knows about you" page: render `person_facts` grouped by kind (skills, experience, preferences, goals, inferred insights), each with source ("from CV v12", "you said on 3 May", "inferred from 4 rejections"), confidence, validity dates, and actions **Correct / Forget / Don't use for X**. User corrections are events with `actor='user'` that outrank agent inferences. Show the CV branch graph and per-commit diffs as the git-style "history" view.
- Separate "inferred" from "stated" memory in the UI — the research points to discomfort mainly around opaque inferences.

### Gaps
- No EDPB/ICO guidance specific to event-sourced application databases (as opposed to blockchain) was found; the blockchain guidance is the closest primary source.
- ICO guidance on right to erasure / backups not fetched this session.
- No large quantitative study linking memory-control UI to retention/trust in production assistants was found.
