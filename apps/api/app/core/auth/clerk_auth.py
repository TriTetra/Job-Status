"""Clerk JWT token verification helper using JWKS."""

import logging
import requests
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

logger = logging.getLogger(__name__)

from shared.config import get_settings

class ClerkAuthenticator:
    _jwks_keys = {}

    @classmethod
    def fetch_jwks(cls):
        """Fetch and cache Clerk public keys."""
        try:
            response = requests.get(get_settings().clerk_jwks_url, timeout=5)
            response.raise_for_status()
            jwks = response.json()
            cls._jwks_keys = {key["kid"]: key for key in jwks.get("keys", [])}
            logger.info("Successfully fetched and cached Clerk JWKS.")
        except Exception as e:
            logger.error(f"Failed to fetch Clerk JWKS: {e}")

    @classmethod
    def get_public_key(cls, kid: str):
        """Get the public key for the given kid, refetching if not found."""
        if kid not in cls._jwks_keys:
            logger.info(f"Key ID {kid} not found in cache. Refetching JWKS...")
            cls.fetch_jwks()
        
        jwk = cls._jwks_keys.get(kid)
        if not jwk:
            raise InvalidTokenError("Key ID not found in Clerk JWKS")
        
        # Convert JWK to PEM public key using PyJWT
        from jwt.algorithms import RSAAlgorithm
        return RSAAlgorithm.from_jwk(jwk)

    @classmethod
    def verify_token(cls, token: str) -> str:
        """Verify the Clerk JWT token and return the user ID (sub claim)."""
        try:
            # Unverified decode to extract header for Key ID (kid)
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            if not kid:
                raise InvalidTokenError("JWT missing 'kid' header")

            public_key = cls.get_public_key(kid)

            # Decode and verify token signature, expiration (exp), etc.
            # Clerk tokens normally use RS256
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},  # Clerk token audience is application-specific
                leeway=60
            )
            
            # The 'sub' claim is the Clerk User ID (e.g. user_2...)
            clerk_user_id = decoded.get("sub")
            if not clerk_user_id:
                raise InvalidTokenError("JWT missing 'sub' claim")

            return clerk_user_id

        except ExpiredSignatureError as e:
            logger.warning("Clerk token signature has expired")
            raise e
        except InvalidTokenError as e:
            logger.warning(f"Invalid Clerk token: {e}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error during Clerk token verification: {e}")
            raise InvalidTokenError(str(e))
