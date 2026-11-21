"""Account flows end to end: setup, invites, password change. Run against a FRESH stack:
    docker compose -f docker-compose.prod.yml up -d   (empty database)
    CAREEROS_URL=http://localhost:13000 python tests/manual/account_flows.py
"""
import os
import secrets

import requests

BASE = os.environ.get("CAREEROS_URL", "http://localhost:13000")
H = {"X-CareerOS-CSRF": "1"}
results = []


def check(label, cond, extra=""):
    results.append(cond)
    print(("PASS " if cond else "FAIL ") + label + (f"  [{extra}]" if extra else ""))


admin, friend, other = requests.Session(), requests.Session(), requests.Session()
for s in (admin, friend, other):
    s.headers.update(H)

pw_admin = "admin-" + secrets.token_urlsafe(12)
pw_friend = "friend-" + secrets.token_urlsafe(12)

r = requests.get(f"{BASE}/api/auth/setup")
check("fresh site needs setup", r.status_code == 200 and r.json()["needed"] is True, r.text)

r = requests.post(f"{BASE}/api/auth/setup", headers=H, json={"email": "owner@example.com", "password": "short"})
check("setup refuses a weak password", r.status_code == 400, r.text[:80])

r = admin.post(f"{BASE}/api/auth/setup", json={"email": "Owner@Example.com", "password": pw_admin, "first_name": "Ada"})
check("setup creates the first account and signs in", r.status_code == 204 and "careeros_session" in admin.cookies)
me = admin.get(f"{BASE}/api/auth/me").json()
check("first account is admin", me.get("is_admin") is True and me["email"] == "owner@example.com", str(me))

r = requests.get(f"{BASE}/api/auth/setup")
check("setup is closed afterwards", r.json()["needed"] is False)
r = other.post(f"{BASE}/api/auth/setup", json={"email": "intruder@example.com", "password": "x" * 20})
check("second setup attempt is refused", r.status_code == 409, r.text[:80])

r = admin.post(f"{BASE}/api/auth/invites", json={"email": "friend@example.com"})
check("admin creates an invite", r.status_code == 201 and "/invite/" in r.json()["url"], r.text[:120])
token = r.json()["url"].rsplit("/", 1)[1]
r = admin.post(f"{BASE}/api/auth/invites", json={"email": "owner@example.com"})
check("no invite for an existing account", r.status_code == 409)

r = requests.post(f"{BASE}/api/auth/invites/check", headers=H, json={"token": token})
check("invite check shows the bound email", r.json() == {"valid": True, "email": "friend@example.com"}, r.text)
r = requests.post(f"{BASE}/api/auth/invites/check", headers=H, json={"token": "x" * 40})
check("forged token is invalid", r.json()["valid"] is False)

r = other.post(f"{BASE}/api/auth/invites/accept", json={"token": token, "email": "someone@else.com", "password": pw_friend})
check("invite bound to another email is refused", r.status_code == 410, r.text[:80])
r = friend.post(f"{BASE}/api/auth/invites/accept", json={"token": token, "email": "friend@example.com", "password": pw_friend, "first_name": "Bo"})
check("friend signs up with the invite", r.status_code == 204 and "careeros_session" in friend.cookies, r.text[:80])
r = other.post(f"{BASE}/api/auth/invites/accept", json={"token": token, "email": "friend@example.com", "password": pw_friend})
check("invite can't be used twice", r.status_code == 410)

fme = friend.get(f"{BASE}/api/auth/me").json()
check("friend is not admin", fme.get("is_admin") is False)
check("friend can't create invites", friend.post(f"{BASE}/api/auth/invites", json={}).status_code == 403)
check("friend can't list invites", friend.get(f"{BASE}/api/auth/invites").status_code == 403)

inv = admin.get(f"{BASE}/api/auth/invites").json()
check("admin sees the used invite", any(i["used_by_email"] == "friend@example.com" for i in inv), str(inv)[:120])
r = admin.post(f"{BASE}/api/auth/invites", json={})
open_id = r.json()["id"]
check("admin revokes a pending invite", admin.delete(f"{BASE}/api/auth/invites/{open_id}").status_code == 204)
check("revoked invite is gone", all(i["id"] != open_id for i in admin.get(f"{BASE}/api/auth/invites").json()))

# password change: a second browser of the friend gets signed out, this one stays
second = requests.Session(); second.headers.update(H)
second.post(f"{BASE}/api/auth/login", json={"email": "friend@example.com", "password": pw_friend})
check("friend signed in on a second device", second.get(f"{BASE}/api/auth/me").status_code == 200)
r = friend.post(f"{BASE}/api/auth/password", json={"current_password": "wrong-password-123", "new_password": "n" * 16})
check("wrong current password is refused", r.status_code == 400, r.text[:80])
new_pw = "new-" + secrets.token_urlsafe(14)
r = friend.post(f"{BASE}/api/auth/password", json={"current_password": pw_friend, "new_password": new_pw})
check("password changed", r.status_code == 204, r.text[:80])
check("this browser stays signed in", friend.get(f"{BASE}/api/auth/me").status_code == 200)
check("other device is signed out", second.get(f"{BASE}/api/auth/me").status_code == 401)
check("old password no longer works",
      requests.post(f"{BASE}/api/auth/login", headers=H, json={"email": "friend@example.com", "password": pw_friend}).status_code == 401)
check("new password works",
      requests.post(f"{BASE}/api/auth/login", headers=H, json={"email": "friend@example.com", "password": new_pw}).status_code == 204)

for path in ("/invite/" + token, "/invite/whatever"):
    r = requests.get(BASE + path, allow_redirects=False)
    check(f"{path[:20]}… page is public", r.status_code == 200, str(r.status_code))

print(f"\n{sum(results)}/{len(results)} passed")
