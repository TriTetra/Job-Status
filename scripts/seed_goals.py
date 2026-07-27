"""Seed the goals registry — profession-aware motivation catalog."""
import json
from sqlalchemy import text
from core.db.connection import db

ALL = {
    "Engineering", "AI/ML", "Data", "Design", "Product", "Management",
    "DevOps", "Security", "Research", "QA",
    "medical", "academic", "architecture", "visual_art", "writing", "education", "legal",
}
TECH = {"Engineering", "AI/ML", "Data", "DevOps", "Security", "QA"}
OFFICE = TECH | {"Design", "Product", "Management"}
CREATIVE = {"Design", "visual_art", "writing", "architecture"}
SCHOLARLY = {"Research", "academic"}
CLINICAL = {"medical"}
CIVIC = {"education", "legal", "medical"}

# (id, label, theme, applicable, priority_for, sort_order)
GOALS = [
    # growth
    ("technical_depth",    "Technical depth",         "growth",       TECH | {"Research"},                        TECH,                                                    10),
    ("leadership",         "Leadership",              "growth",       ALL,                                        {"Management", "Product", "education", "legal", "medical"}, 20),
    ("management",         "People management",       "growth",       ALL,                                        {"Management"},                                          30),
    ("continuous_learning","Continuous learning",     "growth",       ALL,                                        SCHOLARLY | CLINICAL | {"Engineering", "AI/ML"},         40),
    ("research",           "Research & discovery",    "growth",       SCHOLARLY | CLINICAL | {"AI/ML", "Data"},   SCHOLARLY | CLINICAL,                                    50),
    # lifestyle
    ("remote_first",       "Remote-first",            "lifestyle",    OFFICE | CREATIVE | {"legal", "academic"},  {"writing", "visual_art", "legal", "academic", "Engineering"}, 60),
    ("flexibility",        "Schedule flexibility",    "lifestyle",    ALL,                                        set(),                                                   70),
    ("balance",            "Work-life balance",       "lifestyle",    ALL,                                        CIVIC,                                                   80),
    ("stability",          "Stability & security",    "lifestyle",    ALL,                                        CIVIC,                                                   90),
    ("autonomy",           "Autonomy",                "lifestyle",    ALL,                                        {"writing", "visual_art", "legal"},                      100),
    # compensation
    ("high_compensation",  "High compensation",       "compensation", ALL,                                        set(),                                                   110),
    ("equity",             "Equity / upside",         "compensation", OFFICE,                                     {"Product", "Management", "Engineering"},                120),
    ("benefits",           "Strong benefits",         "compensation", ALL,                                        CIVIC,                                                   130),
    # impact
    ("mission",            "Mission-driven work",     "impact",       ALL,                                        CIVIC | SCHOLARLY,                                       140),
    ("social_impact",      "Social impact",           "impact",       ALL,                                        CIVIC,                                                   150),
    ("open_source",        "Open source",             "impact",       TECH,                                       {"Engineering", "DevOps"},                               160),
    ("innovation",         "Innovation",              "impact",       TECH | CREATIVE | SCHOLARLY,                CREATIVE | SCHOLARLY | {"AI/ML"},                        170),
    ("creativity",         "Creative freedom",        "impact",       CREATIVE,                                   CREATIVE,                                                180),
    ("recognition",        "Recognition & prestige",  "impact",       SCHOLARLY | CLINICAL | CREATIVE | {"legal"}, SCHOLARLY | CLINICAL | CREATIVE | {"legal"},           190),
    # environment
    ("startup_pace",       "Startup / fast pace",     "environment",  OFFICE | CREATIVE,                          CREATIVE | {"Engineering"},                              200),
    ("established_org",    "Established organization","environment",  ALL,                                        CIVIC,                                                   210),
]


def seed():
    engine = db.engine
    with engine.begin() as conn:
        for g in GOALS:
            conn.execute(text("""
                INSERT INTO goals (id, label, theme, applicable, priority_for, sort_order)
                VALUES (:id, :label, :theme, CAST(:app AS JSONB), CAST(:prio AS JSONB), :ord)
                ON CONFLICT (id) DO UPDATE SET
                  label        = EXCLUDED.label,
                  theme        = EXCLUDED.theme,
                  applicable   = EXCLUDED.applicable,
                  priority_for = EXCLUDED.priority_for,
                  sort_order   = EXCLUDED.sort_order
            """), {
                "id": g[0], "label": g[1], "theme": g[2],
                "app": json.dumps(sorted(g[3])),
                "prio": json.dumps(sorted(g[4])),
                "ord": g[5],
            })
    print(f"Seeded {len(GOALS)} goals across {len(ALL)} role categories")


if __name__ == "__main__":
    seed()
