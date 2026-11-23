"""Telegram Bot API client: the few calls Aplio needs.

The bot token comes from TELEGRAM_BOT_TOKEN and is part of every request URL, so
errors are reported without the URL (it would leak the token into logs).
"""

import hashlib
import hmac
import logging
from functools import lru_cache
from typing import Optional

import requests

from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

API = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 15
WEBHOOK_PATH = "/api/telegram/webhook"


class TelegramError(RuntimeError):
    pass


def _token() -> Optional[str]:
    return get_settings().telegram_bot_token


def available() -> bool:
    return bool(_token())


def call(method: str, **payload) -> dict:
    token = _token()
    if not token:
        raise TelegramError("Telegram is not set up on this server")
    try:
        resp = requests.post(API.format(token=token, method=method), json=payload, timeout=TIMEOUT)
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise TelegramError(f"{method}: {type(e).__name__}") from None  # no URL: it holds the token
    if not data.get("ok"):
        raise TelegramError(f"{method}: {data.get('description') or resp.status_code}")
    return data.get("result") or {}


@lru_cache(maxsize=4)
def _username_for(token_fingerprint: str) -> str:
    return call("getMe").get("username") or ""


def bot_username() -> str:
    token = _token() or ""
    return _username_for(hashlib.sha256(token.encode()).hexdigest()[:16]) if token else ""


def send(chat_id: int, html_text: str) -> None:
    call("sendMessage", chat_id=chat_id, text=html_text, parse_mode="HTML", disable_web_page_preview=True)


def webhook_secret() -> str:
    """What Telegram sends back in X-Telegram-Bot-Api-Secret-Token (derived from the bot token)."""
    token = _token() or ""
    return hmac.new(token.encode(), b"careeros-telegram-webhook", hashlib.sha256).hexdigest()[:48]


def secret_ok(header: Optional[str]) -> bool:
    return bool(_token()) and bool(header) and hmac.compare_digest(header, webhook_secret())


def ensure_webhook(base_url: str) -> bool:
    """Point the bot at this site. Only over https (Telegram's rule); local dev skips it."""
    if not available():
        return False
    if not base_url.startswith("https://"):
        logger.info("Telegram webhook not set: WEB_APP_URL is not https (%s)", base_url)
        return False
    try:
        call("setWebhook", url=base_url.rstrip("/") + WEBHOOK_PATH, secret_token=webhook_secret(),
             allowed_updates=["message"])
        logger.info("Telegram webhook set for @%s", bot_username())
        return True
    except TelegramError as e:
        logger.warning("Telegram webhook could not be set: %s", e)
        return False
