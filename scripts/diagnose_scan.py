import sqlite3
from pathlib import Path

db_path = Path.home() / ".applypilot/applypilot.db"
conn = sqlite3.connect(str(db_path))

# En son / en eski discovered_at
rows = conn.execute("SELECT MAX(discovered_at), MIN(discovered_at), COUNT(*) FROM jobs").fetchone()
print("Latest discovered_at :", rows[0])
print("Oldest discovered_at :", rows[1])
print("Total jobs            :", rows[2])

# fit_score dagilimi
score_dist = conn.execute(
    "SELECT fit_score, COUNT(*) FROM jobs GROUP BY fit_score ORDER BY fit_score DESC LIMIT 10"
).fetchall()
print("Score distribution    :", score_dist)

# SQLite datetime filtresi calisiyor mu?
t1 = conn.execute("SELECT COUNT(*) FROM jobs WHERE discovered_at >= datetime('now', '-9999 hours')").fetchone()
print("Jobs with 9999h filter:", t1[0])

# String compare
t2 = conn.execute("SELECT COUNT(*) FROM jobs WHERE discovered_at >= '2026-01-01'").fetchone()
print("Jobs since 2026-01-01 :", t2[0])

# scan_and_normalize icin plugin_loader test
print("\n--- plugin scan_and_normalize (hours=0, score=0) ---")
import sys
sys.path.insert(0, ".")
from plugins.plugin_loader import load_job_source_plugin
plugin = load_job_source_plugin("applypilot")

# scan_and_normalize metodu var mi?
print("Has scan_and_normalize:", hasattr(plugin, "scan_and_normalize"))
print("Methods:", [m for m in dir(plugin) if not m.startswith("_")])

conn.close()
