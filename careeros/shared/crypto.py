"""Encrypt/decrypt OAuth tokens at rest (Fernet, key from TOKEN_ENCRYPTION_KEY).

TOKEN_ENCRYPTION_KEY may be a Fernet key or any long random secret (e.g. one
Coolify generates): a secret that isn't a Fernet key is turned into one with SHA-256.
"""

import base64
import binascii
import hashlib
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)


MIN_SECRET_LENGTH = 32


def fernet_key(secret: str) -> bytes:
    """The secret itself if it is a Fernet key, else a key derived from it."""
    try:
        if len(base64.urlsafe_b64decode(secret.encode())) == 32:
            return secret.encode()
    except (binascii.Error, ValueError):
        pass
    if len(secret) < MIN_SECRET_LENGTH:
        raise ValueError(f"TOKEN_ENCRYPTION_KEY must be a Fernet key or a secret of {MIN_SECRET_LENGTH}+ characters")
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())


class TokenCipher:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(fernet_key(key))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string, return base64-encoded ciphertext ('' stays '')."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext ('' stays ''). Raises InvalidToken on a wrong key."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt token - invalid key or corrupted data")
            raise


@lru_cache(maxsize=1)
def get_token_cipher() -> TokenCipher:
    """Process-wide cipher. Created on first use, so importing this module never needs the key."""
    key = get_settings().token_encryption_key
    if not key:
        raise ValueError("TOKEN_ENCRYPTION_KEY not set in environment")
    return TokenCipher(key)
