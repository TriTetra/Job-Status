"""Own authentication — private, invite-only.

There is no sign-up: accounts are created from the CLI (`career-os user add`).

    passwords.py  argon2id hashing + the password policy
    sessions.py   server-side sessions behind an httpOnly cookie (only a hash is stored)
    throttle.py   login attempt limits (per email and per client IP)
    accounts.py   create users, set passwords, authenticate, deactivate
"""
