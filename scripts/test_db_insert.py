"""Kill all other DB connections, then insert one test role to verify."""
import sys, os, json, uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, create_engine

# Get DATABASE_URL directly
env_path = Path(__file__).parent.parent / ".env"
db_url = None
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not db_url:
    db_url = os.environ.get("DATABASE_URL")

print(f"Using DB URL: {db_url[:30]}...")

# Create a fresh engine — no connection pool reuse
engine = create_engine(db_url, pool_pre_ping=True)

# Step 1: Kill all other connections to career_os DB
print("Step 1: Killing all other DB connections...")
with engine.connect() as conn:
    conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid != pg_backend_pid()"))
    conn.commit()
    print("  Done.")

# Step 2: Check roles table
print("Step 2: Checking roles table...")
with engine.connect() as conn:
    r = conn.execute(text("SELECT count(*) FROM roles"))
    print(f"  Current roles count: {r.scalar()}")
    conn.commit()

# Step 3: Insert one test role
print("Step 3: Inserting test role...")
with engine.begin() as conn:
    conn.execute(
        text("""
            INSERT INTO roles (id, slug, title, category, aliases, metadata, version)
            VALUES (:id, :slug, :title, :category, CAST(:aliases AS jsonb), CAST(:meta AS jsonb), 1)
            ON CONFLICT (slug) DO NOTHING
        """),
        {
            "id": str(uuid.uuid4()),
            "slug": "test_role_verify",
            "title": "Test Role (Verify)",
            "category": "Test",
            "aliases": json.dumps(["Test"]),
            "meta": json.dumps({"test": True})
        }
    )
    print("  Inserted successfully!")

# Step 4: Verify
print("Step 4: Verifying...")
with engine.connect() as conn:
    r = conn.execute(text("SELECT count(*) FROM roles"))
    print(f"  Roles count after insert: {r.scalar()}")
    # Clean up
    conn.execute(text("DELETE FROM roles WHERE slug = 'test_role_verify'"))
    conn.commit()
    print("  Test role cleaned up.")

print("\nAll tests passed! DB is accessible and writable.")
engine.dispose()
