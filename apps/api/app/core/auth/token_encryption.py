"""Encrypt/decrypt OAuth tokens at rest."""

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
import logging

from shared.config import get_settings

logger = logging.getLogger(__name__)


class TokenEncryption:
    """Fernet-based symmetric encryption for OAuth tokens."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            key = get_settings().token_encryption_key
            if not key:
                raise ValueError("TOKEN_ENCRYPTION_KEY not set in environment")
            cls._instance._fernet = Fernet(key.encode())
        return cls._instance
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string, return base64-encoded ciphertext."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext, return plaintext."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt token - invalid key or corrupted data")
            raise


# Singleton
token_encryption = TokenEncryption()
