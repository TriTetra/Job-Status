"""Encrypt/decrypt OAuth tokens at rest (Fernet, key from TOKEN_ENCRYPTION_KEY)."""

import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)


class TokenCipher:
    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

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
