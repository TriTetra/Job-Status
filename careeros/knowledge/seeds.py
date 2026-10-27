"""Reference data seeding — every dataset lives in infra/seeds/v1/*.yaml, not in code.

    career-os seed            # everything, in dependency order
    career-os seed roles      # one dataset

Every seed is idempotent (upsert or insert-if-missing), so re-running is safe.
Order matters: roles before sources (sources write suggested_source_ids into roles).
"""

import json
import logging
from functools import lru_cache
from typing import Callable

import sqlalchemy as sa
import yaml

from careeros.db.connection import db
from careeros.shared.config import ROOT

logger = logging.getLogger(__name__)

SEEDS_DIR = ROOT / "infra" / "seeds" / "v1"


@lru_cache(maxsize=None)
def load_seed(name: str) -> dict:
    """infra/seeds/v1/<name>.yaml (cached)."""
    with (SEEDS_DIR / f"{name}.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── datasets ──────────────────────────────────────────────────────────────

def seed_skills() -> int:
    """Canonical skills taxonomy. Insert-only: existing slugs (and their edits) are kept."""
    from careeros.evidence.models.skill import Skill

    skills = load_seed("skills")["skills"]
    inserted = 0
    with db.session_scope() as session:
        existing = {slug for (slug,) in session.query(Skill.slug).all()}
        for s in skills:
            if s["slug"] in existing:
                continue
            session.add(Skill(
                name=s["name"],
                slug=s["slug"],
                category=s["category"],
                subcategory=s.get("subcategory"),
                aliases=s.get("aliases", []),
                related_skill_ids=[],
                skill_metadata={},
                is_verified=True,
                is_deprecated=False,
            ))
            inserted += 1
    logger.info("Skills: %d inserted, %d already present (%d in seed)", inserted, len(skills) - inserted, len(skills))
    return inserted


def seed_roles() -> int:
    """Canonical roles, upserted by slug. metadata is merged (existing keys not in the seed survive)."""
    roles = load_seed("roles")["roles"]
    upsert = sa.text("""
        INSERT INTO roles (id, slug, title, category, aliases, metadata, version)
        VALUES (gen_random_uuid(), :slug, :title, :category, CAST(:aliases AS jsonb), CAST(:metadata AS jsonb), 1)
        ON CONFLICT (slug) DO UPDATE SET
            title      = EXCLUDED.title,
            category   = EXCLUDED.category,
            aliases    = EXCLUDED.aliases,
            metadata   = COALESCE(roles.metadata, '{}'::jsonb) || EXCLUDED.metadata,
            updated_at = now()
    """)
    with db.engine.begin() as conn:
        conn.execute(upsert, [
            {
                "slug": r["slug"],
                "title": r["title"],
                "category": r["category"],
                "aliases": json.dumps(r.get("aliases", [])),
                "metadata": json.dumps(r.get("metadata", {})),
            }
            for r in roles
        ])
        by_category = conn.execute(
            sa.text("SELECT category, count(*) FROM roles GROUP BY category ORDER BY count(*) DESC")
        ).fetchall()
    logger.info("Roles: %d upserted · by category: %s", len(roles), ", ".join(f"{c}={n}" for c, n in by_category))
    return len(roles)


def seed_goals() -> int:
    goals = load_seed("goals")["goals"]
    upsert = sa.text("""
        INSERT INTO goals (id, label, theme, applicable, priority_for, sort_order)
        VALUES (:id, :label, :theme, CAST(:applicable AS jsonb), CAST(:priority_for AS jsonb), :sort_order)
        ON CONFLICT (id) DO UPDATE SET
            label        = EXCLUDED.label,
            theme        = EXCLUDED.theme,
            applicable   = EXCLUDED.applicable,
            priority_for = EXCLUDED.priority_for,
            sort_order   = EXCLUDED.sort_order
    """)
    with db.engine.begin() as conn:
        conn.execute(upsert, [
            {**g, "applicable": json.dumps(g["applicable"]), "priority_for": json.dumps(g["priority_for"])}
            for g in goals
        ])
    logger.info("Goals: %d upserted", len(goals))
    return len(goals)


def seed_evidence_sources() -> int:
    """Source registry + each canonical role's suggested_source_ids (by its category)."""
    data = load_seed("evidence_sources")
    category_sources, default = data["category_sources"], data["default_sources"]
    upsert = sa.text("""
        INSERT INTO evidence_sources (id, label, icon, category, status, oauth_provider, connect_kind, sort_order)
        VALUES (:id, :label, :icon, :category, :status, :oauth_provider, :connect_kind, :sort_order)
        ON CONFLICT (id) DO UPDATE SET
            label          = EXCLUDED.label,
            icon           = EXCLUDED.icon,
            category       = EXCLUDED.category,
            status         = EXCLUDED.status,
            oauth_provider = EXCLUDED.oauth_provider,
            connect_kind   = EXCLUDED.connect_kind,
            sort_order     = EXCLUDED.sort_order
    """)
    suggest = sa.text("""
        UPDATE roles
        SET metadata = COALESCE(metadata, '{}'::jsonb) || jsonb_build_object('suggested_source_ids', CAST(:ids AS jsonb))
        WHERE id = :id
    """)
    with db.engine.begin() as conn:
        conn.execute(upsert, data["sources"])
        roles = conn.execute(sa.text("SELECT id, category FROM roles")).fetchall()
        if roles:
            conn.execute(suggest, [
                {"id": role_id, "ids": json.dumps(category_sources.get(category, default))}
                for role_id, category in roles
            ])
    logger.info("Evidence sources: %d upserted; suggestions set on %d roles", len(data["sources"]), len(roles))
    return len(data["sources"])


def seed_reference() -> int:
    """Countries, visas, salary ranges (per-file YAML folders)."""
    from careeros.knowledge.reference_seed import seed_countries, seed_salaries, seed_visas

    return seed_countries() + seed_visas() + seed_salaries()


# Dependency order: skills/reference are independent; roles before evidence sources
SEEDS: dict[str, Callable[[], int]] = {
    "reference": seed_reference,
    "skills": seed_skills,
    "roles": seed_roles,
    "goals": seed_goals,
    "sources": seed_evidence_sources,
}


def run(targets: list[str] | None = None) -> dict[str, int]:
    """Run the named seeds (all when empty) in dependency order. Returns {name: rows}."""
    wanted = targets or list(SEEDS)
    unknown = set(wanted) - set(SEEDS)
    if unknown:
        raise ValueError(f"Unknown seed(s): {', '.join(sorted(unknown))}. Choose from: {', '.join(SEEDS)}")
    return {name: SEEDS[name]() for name in SEEDS if name in wanted}
