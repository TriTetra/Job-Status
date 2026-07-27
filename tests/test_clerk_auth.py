"""Integration tests for Clerk JWT Authentication and E2E bypass rules."""

import requests
import uuid

API_BASE = "http://127.0.0.1:8000"

def test_unauthenticated_request():
    """Request without any auth headers should fall back to default user and succeed."""
    r = requests.get(f"{API_BASE}/api/onboarding/state")
    assert r.status_code == 200
    data = r.json()
    assert "state" in data
    print("[OK] Unauthenticated request fell back to default user")


def test_valid_e2e_bypass():
    """Request with X-User-Id starting with user_e2e_ should bypass auth and succeed."""
    test_user_id = f"user_e2e_{uuid.uuid4().hex[:8]}"
    r = requests.get(
        f"{API_BASE}/api/onboarding/state",
        headers={"X-User-Id": test_user_id}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["state"] == "NOT_STARTED"
    print(f"[OK] Valid E2E test bypass allowed: {test_user_id}")


def test_invalid_bypass_id():
    """Request with X-User-Id NOT starting with user_e2e_ should be rejected with 401."""
    fake_user_id = "user_fake_12345"
    r = requests.get(
        f"{API_BASE}/api/onboarding/state",
        headers={"X-User-Id": fake_user_id}
    )
    assert r.status_code == 401
    assert "Authentication required" in r.text
    print(f"[OK] Invalid bypass ID rejected: {fake_user_id}")


def test_invalid_jwt_bearer():
    """Request with an invalid Bearer token should be rejected with 401."""
    r = requests.get(
        f"{API_BASE}/api/onboarding/state",
        headers={"Authorization": "Bearer invalid_mock_token"}
    )
    assert r.status_code == 401
    assert "Invalid authentication token" in r.text
    print("[OK] Invalid JWT Bearer token rejected")


def main():
    print("=" * 60)
    print("CLERK JWT AUTH INTEGRATION TESTS")
    print("=" * 60)
    try:
        test_unauthenticated_request()
        test_valid_e2e_bypass()
        test_invalid_bypass_id()
        test_invalid_jwt_bearer()
        print("=" * 60)
        print("[OK] ALL CLERK AUTH TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"[FAIL] Assertion failed: {e}")
        exit(1)
    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
