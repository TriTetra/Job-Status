"""E2E DB verification for all test users."""
from sqlalchemy import text
from careeros.db.connection import db

session = db.get_session()

tests = [
    ("test_e2e_slug_001",   "Slug canonical"),
    ("test_e2e_custom_002", "Custom role"),
    ("test_e2e_origin_003", "Origin=user override"),
]

for uid, label in tests:
    print(f"\n=== {label} ({uid}) ===")
    user = session.execute(text(
        "SELECT current_role_id, current_custom_role_id, years_in_role, "
        "career_level, career_level_origin, onboarding_state "
        "FROM users WHERE clerk_id = :uid"
    ), {"uid": uid}).mappings().fetchone()

    if not user:
        print("  NOT FOUND")
        continue

    for k, v in user.items():
        print(f"  {k}: {v}")

    rows = session.execute(text(
        "SELECT role_id, custom_role_id, is_current, source "
        "FROM user_roles WHERE user_id = :uid ORDER BY started_at DESC"
    ), {"uid": uid}).mappings().fetchall()
    print(f"  user_roles({len(rows)} rows):")
    for r in rows:
        print(f"    role_id={r['role_id']}, custom={r['custom_role_id']}, "
              f"is_current={r['is_current']}, source={r['source']}")

session.close()
