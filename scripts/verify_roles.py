"""Verify roles seed — category distribution."""
from sqlalchemy import text, create_engine

from shared.config import get_settings

engine = create_engine(get_settings().database_url)

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
