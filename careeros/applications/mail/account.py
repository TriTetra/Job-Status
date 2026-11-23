"""A person's mailbox connection: IMAP over SSL with an app password, stored encrypted.

An app password (Gmail, Yahoo, iCloud, Yandex… with two-step sign-in) opens only the mailbox
and can be revoked from the provider at any time without changing the real password. It is
encrypted at rest (careeros/shared/crypto.py) and only used to read: the mailbox is opened
read-only, messages are never marked read, moved or deleted.

Disconnecting forgets everything: the connection and every signal found in the mailbox.
"""

import imaplib
import logging
import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from careeros.applications.models.mail_signal import MailSignal
from careeros.identity.models.connected_account import ConnectedAccount

logger = logging.getLogger(__name__)

PROVIDER = "imap"
PORT = 993
TIMEOUT = 20

# Mail domain → IMAP host. Others: the person gives their provider's IMAP host.
HOSTS = {
    "gmail.com": "imap.gmail.com", "googlemail.com": "imap.gmail.com",
    "yahoo.com": "imap.mail.yahoo.com", "ymail.com": "imap.mail.yahoo.com",
    "icloud.com": "imap.mail.me.com", "me.com": "imap.mail.me.com", "mac.com": "imap.mail.me.com",
    "outlook.com": "outlook.office365.com", "hotmail.com": "outlook.office365.com",
    "live.com": "outlook.office365.com", "msn.com": "outlook.office365.com",
    "yandex.com": "imap.yandex.com", "yandex.ru": "imap.yandex.com", "yandex.com.tr": "imap.yandex.com",
    "mail.ru": "imap.mail.ru", "gmx.com": "imap.gmx.com", "gmx.de": "imap.gmx.net", "gmx.net": "imap.gmx.net",
    "web.de": "imap.web.de", "zoho.com": "imap.zoho.com", "fastmail.com": "imap.fastmail.com",
    "aol.com": "imap.aol.com", "proton.me": "", "protonmail.com": "",
}
_EMAIL = re.compile(r"^[^@\s]{1,64}@([a-z0-9-]+(?:\.[a-z0-9-]+)+)$", re.I)
_HOST = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)+$", re.I)


class MailError(Exception):
    """A connection problem (message safe to show the person)."""


def host_for(email: str, host: Optional[str] = None) -> str:
    m = _EMAIL.match((email or "").strip())
    if not m:
        raise MailError("Enter your e-mail address.")
    if host and host.strip():
        h = host.strip().lower()
        if not _HOST.match(h):
            raise MailError("Enter the IMAP server's name, like imap.example.com.")
        return h
    known = HOSTS.get(m.group(1).lower())
    if known == "":
        raise MailError("Proton Mail can't be read over IMAP without its desktop Bridge, so it isn't supported.")
    if known is None:
        raise MailError("Aplio doesn't know this provider's IMAP server: enter it (your provider's help pages list it).")
    return known


def _public(host: str) -> None:
    """Only public servers: never the app's own network (same rule as reading web pages)."""
    from careeros.evidence.portfolio import PortfolioCrawlError, _public_addresses_only

    try:
        _public_addresses_only(host, PORT)
    except PortfolioCrawlError:
        raise MailError("That mail server can't be reached from Aplio.") from None


def clean_password(password: str) -> str:
    """App passwords are shown in groups ("abcd efgh ijkl mnop"): the spaces aren't part of them."""
    p = (password or "").strip()
    squeezed = p.replace(" ", "")
    return squeezed if len(squeezed) == 16 and squeezed.isalnum() else p


def open_mailbox(host: str, email: str, password: str) -> imaplib.IMAP4_SSL:
    """Logged-in IMAP connection (the caller logs out), or MailError."""
    _public(host)
    try:
        conn = imaplib.IMAP4_SSL(host, PORT, ssl_context=ssl.create_default_context(), timeout=TIMEOUT)
    except (OSError, socket.timeout, ssl.SSLError) as e:
        logger.info("IMAP connect to %s failed: %s", host, type(e).__name__)
        raise MailError("The mail server didn't answer. Check the server name.") from None
    try:
        conn.login(email, password)
    except imaplib.IMAP4.error:
        try:
            conn.logout()
        except Exception:
            pass
        raise MailError("The mail server refused the sign-in. Use an app password (not your normal "
                        "password), and check IMAP is turned on in your mail settings.") from None
    return conn


def _account(session: Session, user_id: str) -> Optional[ConnectedAccount]:
    return (session.query(ConnectedAccount)
            .filter(ConnectedAccount.user_id == user_id, ConnectedAccount.provider == PROVIDER).first())


def credentials(session: Session, user_id: str) -> Optional[tuple[str, str, str]]:
    """(host, email, password) of an active connection, or None."""
    from careeros.shared.crypto import get_token_cipher

    acc = _account(session, user_id)
    if acc is None or not acc.is_active or not acc.access_token:
        return None
    return (acc.account_metadata or {}).get("host", ""), acc.provider_username or "", \
        get_token_cipher().decrypt(acc.access_token)


def connect(session: Session, user_id: str, email: str, password: str, host: Optional[str] = None,
            opener=open_mailbox) -> dict:
    """Test the sign-in, then keep the connection (password encrypted)."""
    from careeros.shared.crypto import get_token_cipher

    email = (email or "").strip()
    h = host_for(email, host)
    password = clean_password(password)
    if not password:
        raise MailError("Enter the app password.")
    try:
        cipher = get_token_cipher()
    except ValueError:
        raise MailError("This server can't store passwords safely yet (the admin sets TOKEN_ENCRYPTION_KEY).") from None
    conn = opener(h, email, password)
    try:
        conn.logout()
    except Exception:
        pass
    acc = _account(session, user_id) or ConnectedAccount(user_id=user_id, provider=PROVIDER)
    acc.provider_username = email
    acc.access_token = cipher.encrypt(password)
    acc.account_metadata = {"host": h, "connected_at": datetime.now(timezone.utc).isoformat()}
    acc.is_active, acc.sync_status, acc.last_synced_at = True, "connected", None
    session.add(acc)
    session.flush()
    return status(session, user_id)


def disconnect(session: Session, user_id: str) -> None:
    """Forget the mailbox: the connection and everything found in it."""
    acc = _account(session, user_id)
    if acc is not None:
        session.delete(acc)
    session.query(MailSignal).filter(MailSignal.user_id == user_id).delete(synchronize_session=False)
    session.flush()


def signal_dict(s: MailSignal) -> dict:
    return {
        "id": s.id, "url": s.url, "company": s.company, "title": s.title,
        "received_at": s.received_at.isoformat() if s.received_at else None,
        "from_domain": s.from_domain, "subject": s.subject, "kind": s.kind,
        "confidence": round(s.confidence or 0, 2), "evidence": s.evidence, "state": s.state,
        "status_before": s.status_before, "status_after": s.status_after,
    }


def status(session: Session, user_id: str) -> dict:
    acc = _account(session, user_id)
    rows = (session.query(MailSignal).filter(MailSignal.user_id == user_id, MailSignal.state != "noted")
            .order_by(MailSignal.received_at.desc().nullslast(), MailSignal.id.desc()).limit(30).all())
    return {
        "connected": bool(acc and acc.is_active),
        "email": acc.provider_username if acc else None,
        "host": (acc.account_metadata or {}).get("host") if acc else None,
        "last_checked": acc.last_synced_at.isoformat() if acc and acc.last_synced_at else None,
        "problem": acc.sync_status if acc and acc.sync_status not in ("connected", "ok", "pending") else None,
        "pending": sum(1 for r in rows if r.state == "pending"),
        "signals": [signal_dict(r) for r in rows],
    }
