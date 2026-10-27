"""Password hashing (argon2id) and policy."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

MIN_LENGTH = 12

# argon2-cffi defaults follow the RFC 9106 low-memory recommendation
_hasher = PasswordHasher()

# Verified against when the email is unknown, so a miss costs the same time as a hit
_DUMMY_HASH = _hasher.hash("timing-equalizer-not-a-real-password")


class WeakPassword(ValueError):
    pass


def check_policy(password: str) -> None:
    if len(password) < MIN_LENGTH:
        raise WeakPassword(f"Password must be at least {MIN_LENGTH} characters")
    if password.strip() != password:
        raise WeakPassword("Password must not start or end with whitespace")


def hash_password(password: str) -> str:
    check_policy(password)
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """True if it matches. A missing hash still burns a full verification (no timing oracle)."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True when the stored hash used older parameters — re-hash on the next successful login."""
    return _hasher.check_needs_rehash(password_hash)
