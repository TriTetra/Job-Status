"""Verify role history for back-to-back role changes."""
from sqlalchemy import text
from core.db.connection import db

session = db.get_session()
rows = session.execute(text(
    "SELECT role_id, custom_role_id, is_current, source, ended_at "
    "FROM user_roles WHERE user_id = 'test_e2e_slug_001' ORDER BY started_at DESC"
)).mappings().fetchall()

print(f"user_roles history ({len(rows)} rows):")
for r in rows:
    print(f"  current={r['is_current']}, source={r['source']}, "
          f"role={r['role_id']}, custom={r['custom_role_id']}, ended={r['ended_at']}")
session.close()
