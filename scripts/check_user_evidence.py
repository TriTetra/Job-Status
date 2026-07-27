"""Query database directly for evidence items for a test user."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine

# Read DATABASE_URL
env_path = Path(__file__).parent.parent / ".env"
db_url = [l.split("=", 1)[1].strip().strip('"') for l in open(env_path) if l.startswith("DATABASE_URL=")][0]
engine = create_engine(db_url)

user_id = 'user_4a7c13b3'

with engine.connect() as conn:
    rows = conn.execute(
        text("SELECT id, skill_name, source, confidence_score, evidence_data FROM evidence_items WHERE user_id = :uid"),
        {"uid": user_id}
    ).fetchall()
    
    print(f"Total evidence items found for {user_id}: {len(rows)}")
    for r in rows:
        print(f"ID: {r[0]} | Skill: {r[1]} | Source: {r[2]} | Confidence: {r[3]:.0%} | Data: {r[4]}")

engine.dispose()
