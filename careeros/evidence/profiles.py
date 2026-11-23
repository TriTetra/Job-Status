"""Public profiles → evidence: GitHub, GitLab, Stack Overflow, ORCID, Medium, Substack.

No OAuth app, no API keys: the user gives a username / profile link, and the
public API (or RSS feed) is read. Ownership isn't proven, so confidences sit a
little below OAuth-backed evidence. Every reader returns a `Profile`; one writer
turns it into evidence items (replacing that source's previous items) and a
`ConnectedAccount` row (provider = source id).

Optional `GITHUB_TOKEN` raises GitHub's anonymous limit (60 requests/hour per
server IP) to 5 000; a GitHub connect costs 2 requests.
"""

import logging
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
from urllib.parse import urljoin, urlparse

import requests
from sqlalchemy.orm import Session

from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.evidence.portfolio import PortfolioCrawlError, check_url, find_technologies
from careeros.evidence.skills import find_canonical, load_all_skills
from careeros.identity.models.connected_account import ConnectedAccount
from careeros.knowledge.skill_names import canonical, known_names, split_skill_names
from careeros.shared.config import get_settings

logger = logging.getLogger(__name__)

TIMEOUT = 15
USER_AGENT = "AplioBot/1.0 (+career evidence reader)"
MAX_FEED_BYTES = 3_000_000


class ProfileError(Exception):
    """The profile couldn't be read (message is safe to show the user)."""


class _Unauthorized(ProfileError):
    """HTTP 401 — our own credentials were rejected."""


@dataclass
class Profile:
    handle: str                    # normalised username / id, stored on the account
    url: str                       # public profile page
    summary: str                   # one sentence for the UI
    skills: list[tuple[str, float, str]] = field(default_factory=list)   # (name, confidence, evidence)
    items: list[dict] = field(default_factory=list)  # {"name", "type", "confidence", "url", "data"}
    metadata: dict = field(default_factory=dict)


# ── HTTP ──────────────────────────────────────────────────────────────────

def _get(http, url: str, label: str, *, params=None, headers=None, json_body=True) -> Any:
    try:
        resp = http.get(url, params=params, timeout=TIMEOUT,
                        headers={"User-Agent": USER_AGENT, **(headers or {})})
    except requests.exceptions.Timeout:
        raise ProfileError(f"{label} took too long to answer. Try again.")
    except requests.exceptions.RequestException as e:
        logger.info("%s request failed: %s", label, e)
        raise ProfileError(f"{label} couldn't be reached. Try again.")
    if resp.status_code == 401:
        raise _Unauthorized(f"{label} rejected the request (HTTP 401).")
    if resp.status_code == 404:
        raise ProfileError(f"No {label} profile found with that name.")
    if resp.status_code in (403, 429):
        raise ProfileError(f"{label} is limiting requests right now. Try again in a few minutes.")
    if resp.status_code >= 400:
        logger.info("%s HTTP %s: %s", label, resp.status_code, resp.text[:200])
        raise ProfileError(f"{label} answered with an error (HTTP {resp.status_code}).")
    if not json_body:
        return resp
    try:
        return resp.json()
    except ValueError:
        raise ProfileError(f"{label} sent an unexpected answer.")


def _dig(d: Any, *keys: str) -> Any:
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _known(name: str) -> Optional[str]:
    """The taxonomy name for a tag/topic, or None if it isn't a known skill."""
    names = split_skill_names(name.replace("-", " ").replace("_", " "))
    if not names:
        return None
    hit = canonical(names[0])
    return hit if hit in _known_set() else None


_KNOWN: set[str] = set()


def _known_set() -> set[str]:
    if not _KNOWN:
        _KNOWN.update(known_names())
    return _KNOWN


def _handle_from(value: str, hosts: tuple[str, ...], pattern: str, label: str, example: str) -> str:
    """Username from "name", "@name" or a profile URL on one of `hosts`."""
    v = value.strip().strip("/")
    if "://" in v or "/" in v:  # a link (usernames never contain "/")
        parsed = urlparse(v if "://" in v else "https://" + v)
        host = (parsed.hostname or "").lower().removeprefix("www.")
        if host not in hosts:
            raise ProfileError(f"That isn't a {label} link. Example: {example}")
        parts = [p for p in parsed.path.split("/") if p]
        v = parts[0] if parts else ""
    v = v.lstrip("@")
    if not re.fullmatch(pattern, v):
        raise ProfileError(f"Enter a {label} username or profile link, like {example}")
    return v


def _lang_confidence(repo_count: int) -> float:
    return round(min(0.85, 0.62 + 0.05 * repo_count), 3)


# ── GitHub ────────────────────────────────────────────────────────────────

def _github(value: str, http) -> Profile:
    handle = _handle_from(value, ("github.com",), r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})",
                          "GitHub", "github.com/octocat")
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = get_settings().github_token
    try:
        user = _get(http, f"https://api.github.com/users/{handle}", "GitHub",
                    headers={**headers, "Authorization": f"Bearer {token}"} if token else headers)
        if token:
            headers["Authorization"] = f"Bearer {token}"
    except _Unauthorized:
        # An expired GITHUB_TOKEN must not break every connect: fall back to anonymous
        logger.warning("GITHUB_TOKEN was rejected by GitHub; reading public profiles anonymously")
        user = _get(http, f"https://api.github.com/users/{handle}", "GitHub", headers=headers)
    repos = _get(http, f"https://api.github.com/users/{handle}/repos", "GitHub", headers=headers,
                 params={"type": "owner", "sort": "pushed", "per_page": 100})
    own = [r for r in repos if isinstance(r, dict) and not r.get("fork") and not r.get("archived")]

    langs: dict[str, int] = {}
    topics: dict[str, int] = {}
    for r in own:
        if r.get("language"):
            langs[r["language"]] = langs.get(r["language"], 0) + 1
        for t in r.get("topics") or []:
            topics[t] = topics.get(t, 0) + 1
    skills = [(lang, _lang_confidence(n), f"Main language of {n} public repositor{'y' if n == 1 else 'ies'}")
              for lang, n in langs.items()]
    skills += [(k, 0.6, f"Topic on {n} repositor{'y' if n == 1 else 'ies'}")
               for t, n in topics.items() if (k := _known(t))]

    top = sorted(own, key=lambda r: (r.get("stargazers_count", 0), r.get("pushed_at") or ""), reverse=True)[:10]
    items = [{
        "name": r["name"], "type": "project", "confidence": 0.75, "url": r.get("html_url"),
        "data": {"description": r.get("description") or "", "technologies": [r["language"]] if r.get("language") else [],
                 "language": r.get("language"), "topics": r.get("topics") or [], "stars": r.get("stargazers_count", 0),
                 "last_push": r.get("pushed_at"), "url": r.get("html_url")},
    } for r in top if r.get("name")]
    return Profile(
        handle=user.get("login") or handle, url=user.get("html_url") or f"https://github.com/{handle}",
        summary=f"Read {len(own)} public repositor{'y' if len(own) == 1 else 'ies'}: "
                f"{len(langs)} language{'s' if len(langs) != 1 else ''}, {len(items)} project{'s' if len(items) != 1 else ''}.",
        skills=skills, items=items,
        metadata={"name": user.get("name"), "avatar_url": user.get("avatar_url"), "public_repos": user.get("public_repos"),
                  "followers": user.get("followers"), "bio": user.get("bio")},
    )


# ── GitLab ────────────────────────────────────────────────────────────────

GITLAB_API = "https://gitlab.com/api/v4"


def _gitlab(value: str, http) -> Profile:
    handle = _handle_from(value, ("gitlab.com",), r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,254}", "GitLab", "gitlab.com/username")
    users = _get(http, f"{GITLAB_API}/users", "GitLab", params={"username": handle})
    if not users:
        raise ProfileError("No GitLab profile found with that name.")
    user = users[0]
    projects = _get(http, f"{GITLAB_API}/users/{user['id']}/projects", "GitLab",
                    params={"per_page": 30, "order_by": "last_activity_at"})
    own = [p for p in projects if isinstance(p, dict) and "forked_from_project" not in p and not p.get("archived")]
    top = sorted(own, key=lambda p: (p.get("star_count", 0), p.get("last_activity_at") or ""), reverse=True)[:8]

    langs: dict[str, int] = {}
    items = []
    for p in top:
        try:
            shares = _get(http, f"{GITLAB_API}/projects/{p['id']}/languages", "GitLab") or {}
        except ProfileError:
            shares = {}
        main = [lang for lang, pct in shares.items() if pct >= 15] or list(shares)[:1]
        for lang in main:
            langs[lang] = langs.get(lang, 0) + 1
        items.append({
            "name": p.get("name") or p.get("path"), "type": "project", "confidence": 0.75, "url": p.get("web_url"),
            "data": {"description": p.get("description") or "", "technologies": main, "topics": p.get("topics") or [],
                     "stars": p.get("star_count", 0), "last_push": p.get("last_activity_at"), "url": p.get("web_url")},
        })
    skills = [(lang, _lang_confidence(n), f"Main language of {n} public project{'s' if n != 1 else ''}")
              for lang, n in langs.items()]
    return Profile(
        handle=user.get("username") or handle, url=user.get("web_url") or f"https://gitlab.com/{handle}",
        summary=f"Read {len(own)} public project{'s' if len(own) != 1 else ''}: {len(langs)} language{'s' if len(langs) != 1 else ''}.",
        skills=skills, items=items,
        metadata={"name": user.get("name"), "avatar_url": user.get("avatar_url")},
    )


# ── Stack Overflow ────────────────────────────────────────────────────────

SE_API = "https://api.stackexchange.com/2.3"


def _stackoverflow(value: str, http) -> Profile:
    v = value.strip()
    m = re.search(r"stackoverflow\.com/users/(\d+)", v) or re.fullmatch(r"(\d{1,12})", v)
    if not m:
        raise ProfileError("Enter your Stack Overflow profile link, like stackoverflow.com/users/22656/your-name")
    uid = m.group(1)
    users = _get(http, f"{SE_API}/users/{uid}", "Stack Overflow", params={"site": "stackoverflow"}).get("items") or []
    if not users:
        raise ProfileError("No Stack Overflow profile found with that id.")
    user = users[0]
    tags = _get(http, f"{SE_API}/users/{uid}/top-tags", "Stack Overflow",
                params={"site": "stackoverflow", "pagesize": 30}).get("items") or []

    skills: list[tuple[str, float, str]] = []
    seen: set[str] = set()
    for t in tags:
        tag = re.sub(r"-\d+(?:\.\w+)*$", "", t.get("tag_name", ""))  # python-3.x → python
        name = _known(tag)
        answers, score = t.get("answer_count", 0), t.get("answer_score", 0)
        if not name or name in seen or (answers < 1 and t.get("question_count", 0) < 3):
            continue  # top tags come best first, so a later "c#-4.0" adds nothing to "c#"
        seen.add(name)
        confidence = round(min(0.9, 0.6 + 0.04 * math.log2(1 + max(score, 0))), 3)
        skills.append((name, confidence, f"{answers} answers (score {score}) on Stack Overflow"))
    rep = user.get("reputation", 0)
    return Profile(
        handle=str(uid), url=user.get("link") or f"https://stackoverflow.com/users/{uid}",
        summary=f"{rep:,} reputation; {len(skills)} skill{'s' if len(skills) != 1 else ''} from your top tags.",
        skills=skills,
        metadata={"name": user.get("display_name"), "reputation": rep, "badges": user.get("badge_counts")},
    )


# ── ORCID ─────────────────────────────────────────────────────────────────

def _orcid(value: str, http) -> Profile:
    m = re.search(r"(\d{4}-\d{4}-\d{4}-\d{3}[\dX])", value.strip().upper())
    if not m:
        raise ProfileError("Enter your ORCID iD, like 0000-0002-1825-0097")
    oid = m.group(1)
    record = _get(http, f"https://pub.orcid.org/v3.0/{oid}/record", "ORCID", headers={"Accept": "application/json"})
    activities = record.get("activities-summary") or {}

    items = []
    for group in (_dig(activities, "works", "group") or [])[:30]:
        w = (group.get("work-summary") or [{}])[0]
        title = _dig(w, "title", "title", "value")
        if not title:
            continue
        doi = next((e.get("external-id-value") for e in (_dig(w, "external-ids", "external-id") or [])
                    if e.get("external-id-type") == "doi"), None)
        items.append({
            "name": title, "type": "publication", "confidence": 0.93,
            "url": f"https://doi.org/{doi}" if doi else _dig(w, "url", "value"),
            "data": {"title": title, "detail": _dig(w, "journal-title", "value") or "", "work_type": w.get("type"),
                     "year": _dig(w, "publication-date", "year", "value"), "doi": doi, "status": "completed"},
        })
    for group in (_dig(activities, "fundings", "group") or [])[:15]:
        f = (group.get("funding-summary") or [{}])[0]
        title = _dig(f, "title", "title", "value")
        if title:
            items.append({
                "name": title, "type": "grant", "confidence": 0.93, "url": _dig(f, "url", "value"),
                "data": {"title": title, "detail": _dig(f, "organization", "name") or "",
                         "year": _dig(f, "start-date", "year", "value"), "status": "completed"},
            })
    keywords = [k.get("content", "") for k in (_dig(record, "person", "keywords", "keyword") or [])]
    skills = [(k, 0.6, "Keyword on your ORCID record") for kw in keywords for k in [_known(kw)] if k]
    given = _dig(record, "person", "name", "given-names", "value")
    family = _dig(record, "person", "name", "family-name", "value")
    pubs = sum(1 for i in items if i["type"] == "publication")
    grants = len(items) - pubs
    return Profile(
        handle=oid, url=f"https://orcid.org/{oid}",
        summary=f"{pubs} publication{'s' if pubs != 1 else ''}"
                + (f" and {grants} grant{'s' if grants != 1 else ''}" if grants else "") + " from your ORCID record.",
        skills=skills, items=items,
        metadata={"name": " ".join(x for x in (given, family) if x) or None},
    )


# ── Medium / Substack (RSS) ───────────────────────────────────────────────

def _read_feed(text: str, label: str) -> list[dict]:
    try:
        root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
    except ET.ParseError:
        raise ProfileError(f"{label} sent a feed that couldn't be read.")
    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        if title:
            posts.append({"title": title, "link": (item.findtext("link") or "").strip(),
                          "published": (item.findtext("pubDate") or "").strip(),
                          "categories": [c.text.strip() for c in item.findall("category") if c.text]})
    return posts


def _writing_profile(handle: str, url: str, label: str, posts: list[dict]) -> Profile:
    counts: dict[str, int] = {}
    for p in posts:
        text = " ".join([p["title"], *(c.replace("-", " ") for c in p["categories"])])
        for name in set(find_technologies(text)) | {k for c in p["categories"] if (k := _known(c))}:
            counts[name] = counts.get(name, 0) + 1
    skills = [(name, round(min(0.75, 0.55 + 0.05 * n), 3), f"Wrote {n} {label} post{'s' if n != 1 else ''} about it")
              for name, n in counts.items()]
    items = [{
        "name": p["title"], "type": "article", "confidence": 0.7, "url": p["link"] or None,
        "data": {"platform": label, "published": p["published"], "categories": p["categories"]},
    } for p in posts[:20]]
    return Profile(
        handle=handle, url=url,
        summary=f"Read {len(posts)} recent post{'s' if len(posts) != 1 else ''}; "
                f"{len(skills)} topic{'s' if len(skills) != 1 else ''} match known skills.",
        skills=skills, items=items, metadata={"posts": len(posts)},
    )


def _medium(value: str, http) -> Profile:
    handle = _handle_from(value, ("medium.com",), r"[A-Za-z0-9_.-]{1,60}", "Medium", "medium.com/@username")
    resp = _get(http, f"https://medium.com/feed/@{handle}", "Medium", json_body=False)
    posts = _read_feed(resp.text, "Medium")
    return _writing_profile(handle, f"https://medium.com/@{handle}", "Medium", posts)


def _safe_feed(http, url: str, label: str) -> str:
    """Fetch a feed on a user-chosen host, re-checking every redirect (public addresses only)."""
    for _ in range(4):
        try:
            url = check_url(url)
        except PortfolioCrawlError as e:
            raise ProfileError(str(e))
        resp = _get(http, url, label, json_body=False, headers={"Accept": "application/rss+xml, application/xml"})
        if resp.status_code in (301, 302, 303, 307, 308) and resp.headers.get("location"):
            url = urljoin(url, resp.headers["location"])
            continue
        return resp.content[:MAX_FEED_BYTES].decode(resp.encoding or "utf-8", errors="replace")
    raise ProfileError(f"{label} redirected too many times.")


class _NoRedirect:
    """requests session wrapper that never follows redirects (they're checked by hand)."""

    def __init__(self, http):
        self.http = http

    def get(self, url, **kwargs):
        return self.http.get(url, allow_redirects=False, **kwargs)


def _substack(value: str, http) -> Profile:
    v = value.strip().strip("/")
    parsed = urlparse(v if "://" in v else "https://" + v)
    host = (parsed.hostname or "").lower()
    if host.endswith(".substack.com"):
        name = host.removesuffix(".substack.com")
        if not re.fullmatch(r"[a-z0-9-]{1,63}", name):
            raise ProfileError("Enter your Substack address, like yourname.substack.com")
        handle, base = name, f"https://{name}.substack.com"
    elif "." in host:                                    # a Substack on its own domain
        handle, base = host.removeprefix("www."), f"https://{host}"
    elif re.fullmatch(r"[a-z0-9-]{1,63}", v.lower()):
        handle, base = v.lower(), f"https://{v.lower()}.substack.com"
    else:
        raise ProfileError("Enter your Substack address, like yourname.substack.com")
    text = _safe_feed(_NoRedirect(http), f"{base}/feed", "Substack")
    posts = _read_feed(text, "Substack")
    if not posts and "<rss" not in text[:500]:
        raise ProfileError("No Substack feed found at that address.")
    return _writing_profile(handle, base, "Substack", posts)


READERS: dict[str, Callable[[str, Any], Profile]] = {
    "github": _github,
    "gitlab": _gitlab,
    "stackoverflow": _stackoverflow,
    "orcid": _orcid,
    "medium": _medium,
    "substack": _substack,
}


# ── evidence ──────────────────────────────────────────────────────────────

def read_profile(source_id: str, value: str, http=None) -> Profile:
    reader = READERS.get(source_id)
    if reader is None:
        raise ProfileError("This source can't be connected yet.")
    if not value or len(value) > 300:
        raise ProfileError("Enter a username or profile link.")
    return reader(value, http or requests.Session())


def save_profile(session: Session, user_id: str, source_id: str, profile: Profile) -> dict:
    """Replace this source's evidence with the profile's, and remember the account."""
    session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id, EvidenceItem.source == source_id).delete()

    # Same skill twice (e.g. "TypeScript" as language and topic) → keep the higher confidence
    best: dict[str, tuple[str, float, str]] = {}
    for name, confidence, evidence in profile.skills:
        for clean in split_skill_names(name):
            key = clean.lower()
            if key not in best or confidence > best[key][1]:
                best[key] = (clean, confidence, evidence)

    taxonomy = load_all_skills(session)
    for name, confidence, evidence in best.values():
        match = find_canonical(name, taxonomy)
        session.add(EvidenceItem(
            user_id=user_id, source=source_id, source_url=profile.url,
            skill_name=(match.name if match else name)[:200], skill_id=match.id if match else None,
            confidence_score=confidence, evidence_text=evidence[:500],
            evidence_data={"type": "skill", "matched_canonical": match.name if match else None},
        ))
    for item in profile.items:
        session.add(EvidenceItem(
            user_id=user_id, source=source_id, source_url=item.get("url"),
            skill_name=str(item["name"])[:200], confidence_score=item["confidence"],
            evidence_data={"type": item["type"], **item.get("data", {})},
        ))

    account = session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id, ConnectedAccount.provider == source_id,
    ).first()
    if account is None:
        account = ConnectedAccount(user_id=user_id, provider=source_id)
        session.add(account)
    account.provider_username = profile.handle
    account.provider_user_id = profile.handle
    account.account_metadata = {**profile.metadata, "url": profile.url, "summary": profile.summary}
    account.is_active = True
    account.sync_status = "synced"
    account.last_synced_at = datetime.utcnow()
    from careeros.memory.events import remember

    remember(session, user_id, "EvidenceImported", {
        "source": source_id, "handle": profile.handle, "skills": sorted(v[0] for v in best.values())[:40],
        "items": len(profile.items),
    }, stream="evidence", actor=f"import:{source_id}")
    session.commit()
    return {"status": "connected", "source": source_id, "handle": profile.handle, "url": profile.url,
            "summary": profile.summary, "skills_found": len(best), "items_found": len(profile.items)}


def connect_profile(session: Session, user_id: str, source_id: str, value: str, http=None) -> dict:
    """Read the public profile, then save it. ProfileError → nothing is saved."""
    return save_profile(session, user_id, source_id, read_profile(source_id, value, http))


def disconnect_profile(session: Session, user_id: str, source_id: str) -> None:
    """Forget the account and remove its evidence."""
    session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id, ConnectedAccount.provider == source_id,
    ).delete()
    session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id, EvidenceItem.source == source_id).delete()
    from careeros.memory.events import remember

    remember(session, user_id, "EvidenceRemoved", {"source": source_id}, stream="evidence")
    session.commit()
