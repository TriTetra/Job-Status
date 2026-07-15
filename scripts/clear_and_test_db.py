"""Clear idle DB transactions and then seed roles."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.db.connection import db

# Step 1: Clear idle transactions
print("Clearing idle transactions...")
with db.engine.connect() as conn:
    r = conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND pid != pg_backend_pid()"))
    print(f"Terminated {r.rowcount} idle transactions")
    conn.commit()

# Step 2: Quick count test
with db.engine.connect() as conn:
    r = conn.execute(text("SELECT count(*) FROM roles"))
    print(f"Current roles count: {r.scalar()}")
    conn.commit()

print("DB is clean. Now running seed...")
