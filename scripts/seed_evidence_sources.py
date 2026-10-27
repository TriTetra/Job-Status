"""Seed evidence_sources + role suggested_source_ids (metadata-driven, multi-profession).

Every profession gets its own proof sources. Custom roles are mapped at query
time (see get_evidence_sources) via title keywords → inferred category.
"""
import json
from sqlalchemy import text
from core.db.connection import db

# ─── All platforms (new platform = one row here; no code change) ──────────────
# (id, label, icon, category, status, oauth_provider, connect_kind, sort_order)
SOURCES = [
    # available today
    ("github",        "GitHub",          "github",       "code",         "available",   "github",    "oauth", 10),
    ("portfolio",     "Portfolio",       "globe",        "generic",      "available",   "portfolio", "url",   20),
    # code
    ("gitlab",        "GitLab",          "gitlab",       "code",         "coming_soon", None,        "oauth", 30),
    ("stackoverflow", "Stack Overflow",  "code",         "code",         "coming_soon", None,        "oauth", 40),
    # design / visual
    ("dribbble",      "Dribbble",        "dribbble",     "visual_art",   "coming_soon", None,        "oauth", 50),
    ("behance",       "Behance",         "behance",      "visual_art",   "coming_soon", None,        "oauth", 60),
    ("figma",         "Figma",           "figma",        "visual_art",   "coming_soon", None,        "oauth", 70),
    ("artstation",    "ArtStation",      "palette",      "visual_art",   "coming_soon", None,        "url",   75),
    # data
    ("kaggle",        "Kaggle",          "database",     "data",         "coming_soon", None,        "oauth", 80),
    # academic / research
    ("scholar",       "Google Scholar",  "graduation",   "academic",     "coming_soon", None,        "url",   90),
    ("researchgate",  "ResearchGate",    "flask",        "academic",     "coming_soon", None,        "url",   100),
    ("orcid",         "ORCID",           "fingerprint",  "academic",     "coming_soon", None,        "url",   110),
    ("pubmed",        "PubMed",          "book",         "medical",      "coming_soon", None,        "url",   120),
    # medical / clinical
    ("doximity",      "Doximity",        "stethoscope",  "medical",      "coming_soon", None,        "url",   130),
    # architecture / built environment
    ("archinect",     "Archinect",       "building",     "architecture", "coming_soon", None,        "url",   140),
    ("houzz",         "Houzz",           "home",         "architecture", "coming_soon", None,        "url",   150),
    # writing / content
    ("medium",        "Medium",          "pen",          "writing",      "coming_soon", None,        "url",   160),
    ("substack",      "Substack",        "layers",       "writing",      "coming_soon", None,        "url",   170),
    # generic professional
    ("linkedin",      "LinkedIn",        "linkedin",     "generic",      "coming_soon", None,        "oauth", 180),
]

# ─── Category → suggested sources (covers real role categories AND inferred ones) ─
CATEGORY_SOURCES = {
    # canonical role categories (from roles table)
    "Engineering":   ["github", "portfolio", "stackoverflow"],
    "AI/ML":         ["github", "kaggle", "portfolio"],
    "Data":          ["kaggle", "github", "portfolio"],
    "Design":        ["dribbble", "behance", "portfolio"],
    "Product":       ["linkedin", "portfolio"],
    "Management":    ["linkedin", "portfolio"],
    "DevOps":        ["github", "portfolio"],
    "Security":      ["github", "portfolio"],
    "Research":      ["scholar", "researchgate", "github"],
    "QA":            ["github", "portfolio"],
    # inferred categories (custom roles, mapped by title keywords in P0-c)
    "medical":       ["pubmed", "orcid", "scholar", "doximity"],
    "academic":      ["scholar", "researchgate", "orcid", "portfolio"],
    "architecture":  ["archinect", "houzz", "behance", "portfolio"],
    "visual_art":    ["artstation", "behance", "dribbble", "portfolio"],
    "writing":       ["medium", "substack", "portfolio"],
    "education":     ["linkedin", "scholar", "portfolio"],
    "legal":         ["linkedin", "portfolio"],
}
DEFAULT_SOURCES = ["portfolio", "linkedin"]


def seed():
    engine = db.engine
    with engine.begin() as conn:
        # 1) evidence_sources — upsert ALL mutable columns so re-seeds heal drift
        for s in SOURCES:
            conn.execute(text("""
                INSERT INTO evidence_sources
                  (id, label, icon, category, status, oauth_provider, connect_kind, sort_order)
                VALUES (:id, :label, :icon, :cat, :status, :oauth, :kind, :ord)
                ON CONFLICT (id) DO UPDATE SET
                  label          = EXCLUDED.label,
                  icon           = EXCLUDED.icon,
                  category       = EXCLUDED.category,
                  status         = EXCLUDED.status,
                  oauth_provider = EXCLUDED.oauth_provider,
                  connect_kind   = EXCLUDED.connect_kind,
                  sort_order     = EXCLUDED.sort_order
            """), {"id": s[0], "label": s[1], "icon": s[2], "cat": s[3],
                   "status": s[4], "oauth": s[5], "kind": s[6], "ord": s[7]})

        # 2) roles.metadata.suggested_source_ids (canonical roles, by category)
        rows = conn.execute(text("SELECT id, category FROM roles")).fetchall()
        for role_id, category in rows:
            suggested = CATEGORY_SOURCES.get(category, DEFAULT_SOURCES)
            conn.execute(text("""
                UPDATE roles
                SET metadata = COALESCE(metadata, CAST('{}' AS JSONB))
                             || jsonb_build_object('suggested_source_ids', CAST(:sug AS JSONB))
                WHERE id = :id
            """), {"sug": json.dumps(suggested), "id": role_id})

    print(f"Seeded {len(SOURCES)} sources across {len(CATEGORY_SOURCES)} categories; "
          f"updated {len(rows)} canonical roles")


if __name__ == "__main__":
    seed()
