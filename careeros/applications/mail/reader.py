"""Reading a mailbox without touching it: headers first, a body only for a message that is
about one of the person's applications.

The INBOX is opened read-only (EXAMINE) and fetched with BODY.PEEK, so nothing is marked
read, moved or deleted.
"""

import email
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.header import decode_header, make_header
from email.policy import default as default_policy
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_MESSAGES = 600          # newest first, per check
BATCH = 100
BODY_BYTES = 80_000
MAX_TEXT = 6_000
_UID = re.compile(rb"UID (\d+)")


@dataclass
class Header:
    uid: str
    message_id: str
    from_addr: str
    from_name: str
    subject: str
    date: Optional[datetime]

    @property
    def from_domain(self) -> str:
        return self.from_addr.rsplit("@", 1)[-1].lower() if "@" in self.from_addr else ""

    @property
    def key(self) -> str:
        """Stable id for "seen already": the Message-ID, else what identifies the message."""
        raw = self.message_id or f"{self.date}|{self.from_addr}|{self.subject}"
        return hashlib.sha256(raw.encode()).hexdigest()


def _text(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return " ".join(str(make_header(decode_header(value))).split())
    except Exception:
        return " ".join(value.split())


def parse_header(uid: str, raw: bytes) -> Header:
    msg = email.message_from_bytes(raw)
    name, addr = parseaddr(_text(msg.get("From")))
    try:
        date = parsedate_to_datetime(msg.get("Date")) if msg.get("Date") else None
        if date is not None and date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        date = None
    return Header(uid=uid, message_id=(msg.get("Message-ID") or "").strip()[:300], from_addr=addr.lower(),
                  from_name=name, subject=_text(msg.get("Subject"))[:300], date=date)


def _pairs(data) -> list[tuple[str, bytes]]:
    out = []
    for item in data or []:
        if isinstance(item, tuple) and len(item) >= 2:
            m = _UID.search(item[0])
            if m:
                out.append((m.group(1).decode(), item[1]))
    return out


def headers_since(conn, since: datetime) -> list[Header]:
    """Headers of INBOX messages since `since`, newest first (at most MAX_MESSAGES)."""
    conn.select("INBOX", readonly=True)
    typ, data = conn.uid("search", None, f"(SINCE {since:%d-%b-%Y})")
    if typ != "OK" or not data or not data[0]:
        return []
    uids = data[0].split()[-MAX_MESSAGES:][::-1]
    out: list[Header] = []
    for i in range(0, len(uids), BATCH):
        batch = b",".join(uids[i:i + BATCH]).decode()
        typ, rows = conn.uid("fetch", batch, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE MESSAGE-ID)])")
        if typ != "OK":
            continue
        out += [parse_header(uid, raw) for uid, raw in _pairs(rows)]
    return out


def body_text(raw: bytes) -> str:
    """Readable text of a message (plain part first, else HTML), quoted history dropped."""
    msg = email.message_from_bytes(raw, policy=default_policy)
    text = ""
    try:
        part = msg.get_body(preferencelist=("plain", "html"))
        if part is not None:
            content = part.get_content()
            text = BeautifulSoup(content, "html.parser").get_text("\n") if part.get_content_subtype() == "html" \
                else content
    except Exception:  # a truncated or odd message: whatever text there is
        text = raw.decode("utf-8", errors="replace")
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith(">") or re.match(r"^\s*On .{5,120} wrote:\s*$", line):
            break
        lines.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()[:MAX_TEXT]


def fetch_body(conn, uid: str) -> str:
    typ, rows = conn.uid("fetch", uid, f"(BODY.PEEK[]<0.{BODY_BYTES}>)")
    pairs = _pairs(rows) if typ == "OK" else []
    return body_text(pairs[0][1]) if pairs else ""
