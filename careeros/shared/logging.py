"""Process-wide logging setup.

Library code only does `logger = logging.getLogger(__name__)` and logs.
Entry points (API app, CLI, scripts) call configure_logging() once.
"""

import logging

from careeros.shared.config import get_settings

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_configured = False


def configure_logging(level: str | None = None) -> None:
    """Idempotent. Level: argument > LOG_LEVEL env > INFO."""
    global _configured
    if _configured:
        return
    logging.basicConfig(level=(level or get_settings().log_level), format=_FORMAT, datefmt="%H:%M:%S")
    # Third-party chatter that drowns out our own logs at INFO
    for noisy in ("httpx", "urllib3", "sentence_transformers", "github"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True
