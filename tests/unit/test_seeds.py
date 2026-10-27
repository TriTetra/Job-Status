"""Reference data in infra/seeds/v1/*.yaml + the seeding entry point (no database)."""

import pytest

from careeros.evidence import sources as runtime_sources
from careeros.knowledge import seeds
from careeros.knowledge.seeds import load_seed


# ── data integrity ────────────────────────────────────────────────────────

def test_roles_are_unique_and_complete():
    roles = load_seed("roles")["roles"]
    slugs = [r["slug"] for r in roles]
    assert len(roles) == 180
    assert len(set(slugs)) == len(slugs)
    for r in roles:
        assert r["title"] and r["category"] and isinstance(r.get("aliases", []), list)
        assert "_" not in r["title"], f"slug-like title: {r['title']}"


def test_role_categories_have_source_recommendations_or_fall_back():
    categories = {r["category"] for r in load_seed("roles")["roles"]}
    mapped = set(load_seed("evidence_sources")["category_sources"])
    # every category either has its own list or uses default_sources — none should be a typo of a mapped one
    unmapped = {c for c in categories - mapped if c.lower() in {m.lower() for m in mapped}}
    assert not unmapped, f"category spelled differently from evidence_sources.yaml: {unmapped}"


def test_skills_have_unique_slugs():
    skills = load_seed("skills")["skills"]
    slugs = [s["slug"] for s in skills]
    assert len(set(slugs)) == len(slugs)
    assert all(s["name"] and s["category"] for s in skills)


def test_goals_only_reference_known_categories():
    data = load_seed("goals")
    known = set(data["categories"])
    ids = [g["id"] for g in data["goals"]]
    assert len(set(ids)) == len(ids)
    for g in data["goals"]:
        assert set(g["applicable"]) <= known, g["id"]
        assert set(g["priority_for"]) <= set(g["applicable"]), f"{g['id']}: suggested where it is hidden"


def test_evidence_sources_recommend_only_registered_sources():
    data = load_seed("evidence_sources")
    registered = {s["id"] for s in data["sources"]}
    for category, ids in data["category_sources"].items():
        assert set(ids) <= registered, f"{category}: unknown source in {ids}"
    assert set(data["default_sources"]) <= registered


def test_runtime_recommendations_come_from_the_seed_file():
    data = load_seed("evidence_sources")
    assert runtime_sources.CATEGORY_SOURCES == data["category_sources"]
    assert runtime_sources.DEFAULT_SOURCES == data["default_sources"]


# ── runner ────────────────────────────────────────────────────────────────

def test_run_executes_in_dependency_order(monkeypatch):
    called = []
    fake = {name: (lambda n=name: called.append(n) or 1) for name in seeds.SEEDS}
    monkeypatch.setattr(seeds, "SEEDS", fake)

    assert seeds.run(["sources", "roles"]) == {"roles": 1, "sources": 1}
    assert called == ["roles", "sources"]  # roles first: sources write into roles.metadata

    called.clear()
    seeds.run()
    assert called == list(fake)


def test_run_rejects_unknown_targets():
    with pytest.raises(ValueError, match="Unknown seed"):
        seeds.run(["rolez"])


def test_roles_upsert_merges_metadata(monkeypatch):
    """Re-seeding roles must not wipe keys other seeds added (suggested_source_ids)."""
    captured = {}

    class Conn:
        def execute(self, stmt, params=None):
            captured.setdefault("sql", str(stmt))
            captured.setdefault("rows", params)

            class R:
                def fetchall(self):
                    return []
            return R()

    class Begin:
        def __enter__(self):
            return Conn()

        def __exit__(self, *a):
            return False

    from types import SimpleNamespace
    monkeypatch.setattr(seeds, "db", SimpleNamespace(engine=SimpleNamespace(begin=lambda: Begin())))

    assert seeds.seed_roles() == 180
    assert "COALESCE(roles.metadata, '{}'::jsonb) || EXCLUDED.metadata" in captured["sql"]
    assert len(captured["rows"]) == 180  # one batched executemany, not 180 round-trips
