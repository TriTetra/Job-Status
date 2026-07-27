"""Test multi-source evidence aggregation backend logic and API endpoint.

Creates overlapping evidence items for resume and github sources,
triggers the GET /api/evidence/skills/aggregated endpoint,
and asserts correct weighted confidence calculation and sources list.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from core.db.connection import db
from core.db.models.evidence_item import EvidenceItem
import urllib.request
import urllib.error

user_id = "user_github_test"  # Re-use our test user

print("Seeding overlapping evidence items for resume and github...")
with db.session_scope() as session:
    # Clear existing evidence items for this user to have a clean slate
    session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id).delete()
    
    # Python - Resume (Confidence: 80%)
    session.add(EvidenceItem(
        user_id=user_id,
        skill_name="Python",
        skill_id=1,
        source="resume",
        confidence_score=0.80,
        evidence_data={"type": "skill"}
    ))
    
    # Python - GitHub (Confidence: 99%)
    session.add(EvidenceItem(
        user_id=user_id,
        skill_name="Python",
        skill_id=1,
        source="github",
        confidence_score=0.99,
        evidence_data={"type": "skill"}
    ))
    
    # Go - GitHub (Confidence: 90%)
    session.add(EvidenceItem(
        user_id=user_id,
        skill_name="Go",
        skill_id=2,
        source="github",
        confidence_score=0.90,
        evidence_data={"type": "skill"}
    ))
    
    # React - Resume (Confidence: 70%)
    session.add(EvidenceItem(
        user_id=user_id,
        skill_name="React",
        skill_id=3,
        source="resume",
        confidence_score=0.70,
        evidence_data={"type": "skill"}
    ))
    
    session.commit()
    print("Seeding complete.")

# Trigger GET /api/evidence/skills/aggregated
print("\nQuerying GET /api/evidence/skills/aggregated...")
req = urllib.request.Request(
    'http://localhost:8000/api/evidence/skills/aggregated',
    headers={'X-User-Id': user_id}
)

try:
    r = urllib.request.urlopen(req)
    res = json.loads(r.read())
    print("API Response:")
    print(json.dumps(res, indent=2))
    
    skills = res.get("skills", [])
    assert len(skills) == 3, f"Expected 3 skills, got {len(skills)}"
    
    # 1. Verify Python aggregation (GitHub + Resume)
    python = next(s for s in skills if s["skill_name"] == "Python")
    print("\nVerifying Python Skill Aggregation:")
    print(f"  Aggregated Confidence: {python['aggregated_confidence']:.1%}")
    print(f"  Total Evidence Count: {python['total_evidence_count']}")
    print(f"  Sources: {python['sources']}")
    
    # Weighted math:
    # weights: github=0.5, resume=0.2
    # sum = (0.99 * 0.5 * 1) + (0.80 * 0.2 * 1) = 0.495 + 0.16 = 0.655
    # total_weight = 0.5 * 1 + 0.2 * 1 = 0.7
    # aggregated = 0.655 / 0.7 = 0.9357 (~93.6%)
    expected_confidence = round(0.655 / 0.7, 3)
    assert python["aggregated_confidence"] == expected_confidence, f"Expected {expected_confidence}, got {python['aggregated_confidence']}"
    assert python["total_evidence_count"] == 2
    assert len(python["sources"]) == 2
    print("  [OK] Python aggregation math correct!")
    
    # 2. Verify Go aggregation (GitHub only)
    go = next(s for s in skills if s["skill_name"] == "Go")
    print("\nVerifying Go Skill Aggregation:")
    print(f"  Aggregated Confidence: {go['aggregated_confidence']:.1%}")
    print(f"  Sources: {go['sources']}")
    assert go["aggregated_confidence"] == 0.90
    assert go["total_evidence_count"] == 1
    assert len(go["sources"]) == 1
    print("  [OK] Go aggregation math correct!")
    
    print("\n[OK] All Multi-Source Aggregation tests passed successfully!")
    
except Exception as e:
    print("[FAIL] Test failed:", e)
    sys.exit(1)
