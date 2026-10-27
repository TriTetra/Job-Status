"""Verify roles seed — category distribution."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from sqlalchemy import text, create_engine

env_path = Path(__file__).parent.parent / ".env"
db_url = [l.split("=", 1)[1].strip().strip('"') for l in open(env_path) if l.startswith("DATABASE_URL=")][0]
engine = create_engine(db_url)

with engine.connect() as conn:
    rows = conn.execute(text("SELECT category, count(*) as cnt FROM roles GROUP BY category ORDER BY cnt DESC")).fetchall()
    print("Category Distribution:")
    print("-" * 45)
    for r in rows:
        print(f"  {r[0]:35s} {r[1]:3d}")
    
    total = conn.execute(text("SELECT count(*) FROM roles")).scalar()
    print(f"\nTotal: {total} roles")
    
    # Sample 5 roles
    samples = conn.execute(text("SELECT slug, title, category FROM roles ORDER BY random() LIMIT 5")).fetchall()
    print("\nSample roles:")
    for s in samples:
        print(f"  [{s[2]}] {s[1]} ({s[0]})")

engine.dispose()
