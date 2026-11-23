"""Portfolio website → evidence items (source="portfolio").

The crawler reads the home page plus up to three linked project/work/about pages on
the same site. Only public internet addresses are fetched (no localhost, private
networks, cloud metadata or the app's own containers), redirects are re-checked,
and responses are size-capped. Technologies are found by whole-word matches
against the skills taxonomy.
"""

import ipaddress
import logging
import re
import socket
from datetime import datetime
from functools import lru_cache
from typing import Optional
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.evidence.skills import find_canonical, load_all_skills
from careeros.identity.models.connected_account import ConnectedAccount
from careeros.knowledge.skill_names import _index as _skill_index

logger = logging.getLogger(__name__)

MAX_PAGES = 4               # home page + 3 linked pages
MAX_BYTES = 2_000_000       # per page
MAX_REDIRECTS = 3
MIN_TEXT_CHARS = 200        # less than this: the site draws its content with JavaScript
MAX_PROJECTS = 8

# Links worth following from the home page
_FOLLOW = re.compile(r"project|work|portfolio|case|about|showcase", re.IGNORECASE)
# class / id tokens that mark a project block ("network" and "framework" don't count)
_PROJECT_TOKENS = {"project", "projects", "portfolio", "work", "works", "case", "casestudy", "showcase"}
# Headings that name a section, not a project
_SECTION_TITLES = {"projects", "my projects", "work", "my work", "selected work", "selected works",
                   "portfolio", "case studies", "featured projects", "recent work", "side projects"}
# Taxonomy names that are also ordinary English words: matched only as written ("Rust", not "rust")
_CASE_SENSITIVE = {"rust", "swift", "express", "spark", "flask", "ruby", "dart", "unity", "excel",
                   "agile", "helm", "rails", "elixir", "transformers", "git"}
# Too short or too common to find reliably in free text (still found via their aliases, e.g. "golang")
_SKIP = {"go", "r", "c", "shell", "embedded", "transformer", "ros", "kanban", "scrum", "case"}


class PortfolioCrawlError(Exception):
    """The portfolio URL could not be crawled (message is safe to show the user)."""


# ── safe fetching ─────────────────────────────────────────────────────────

def _public_addresses_only(host: str, port: int) -> None:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise PortfolioCrawlError("That website's address could not be found.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.version == 6 and ip.ipv4_mapped:  # ::ffff:127.0.0.1 is still localhost
            ip = ip.ipv4_mapped
        if not ip.is_global or ip.is_multicast:
            raise PortfolioCrawlError("Only public websites can be added.")


def check_url(url: str) -> str:
    """The URL if it is a public http(s) website, else PortfolioCrawlError."""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise PortfolioCrawlError("Enter a website address like https://yourname.dev")
    if parsed.username or parsed.password:
        raise PortfolioCrawlError("Enter a website address without a login in it.")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in (80, 443):
        raise PortfolioCrawlError("Only standard web ports (80, 443) are supported.")
    _public_addresses_only(parsed.hostname, port)
    return url


class PortfolioCrawler:
    """Crawl a portfolio website for projects and technologies."""

    def __init__(self, timeout: int = 10, http: Optional[requests.Session] = None,
                 url_check=check_url):
        self.timeout = timeout
        self.http = http or requests.Session()
        self.check = url_check
        self.headers = {"User-Agent": "AplioBot/1.0 (+portfolio reader)", "Accept": "text/html"}

    def fetch(self, url: str) -> tuple[str, str]:
        """(final URL, HTML), following redirects only to public addresses."""
        for _ in range(MAX_REDIRECTS + 1):
            url = self.check(url)
            try:
                resp = self.http.get(url, headers=self.headers, timeout=self.timeout,
                                     allow_redirects=False, stream=True)
            except requests.exceptions.Timeout:
                raise PortfolioCrawlError("The website took too long to answer.")
            except requests.exceptions.RequestException as e:
                logger.info("Portfolio fetch failed for %s: %s", url, e)
                raise PortfolioCrawlError("The website could not be reached.")
            try:
                if resp.is_redirect and resp.headers.get("location"):
                    url = urljoin(url, resp.headers["location"])
                    continue
                if resp.status_code >= 400:
                    raise PortfolioCrawlError(f"The website answered with an error (HTTP {resp.status_code}).")
                if "html" not in resp.headers.get("content-type", "text/html").lower():
                    raise PortfolioCrawlError("That address isn't a web page.")
                body = b""
                for chunk in resp.iter_content(64 * 1024):
                    body += chunk
                    if len(body) > MAX_BYTES:
                        break
                return url, body[:MAX_BYTES].decode(resp.encoding or "utf-8", errors="replace")
            finally:
                resp.close()
        raise PortfolioCrawlError("The website redirects too many times.")

    def crawl(self, url: str) -> dict:
        """{"projects", "technologies", "about", "url", "pages"} or {"error": message}."""
        try:
            home_url, html = self.fetch(url)
            pages = [(home_url, BeautifulSoup(html, "html.parser"))]
            for link in self._follow_links(home_url, pages[0][1]):
                try:
                    pages.append((link, BeautifulSoup(self.fetch(link)[1], "html.parser")))
                except PortfolioCrawlError:
                    continue  # one broken sub-page doesn't spoil the rest

            texts = [_visible_text(soup) for _, soup in pages]
            if sum(len(t) for t in texts) < MIN_TEXT_CHARS:
                return {"error": "This site draws its content with JavaScript, so it can't be read. "
                                 "Try a page that works without JavaScript, such as a static portfolio "
                                 "or a GitHub profile README."}
            projects: list[dict] = []
            for _, soup in pages:
                for p in _extract_projects(soup):
                    if p["name"].lower() not in {x["name"].lower() for x in projects}:
                        projects.append(p)
            return {
                "projects": projects[:MAX_PROJECTS],
                "technologies": find_technologies(" ".join(texts)),
                "about": _extract_about(pages[0][1]),
                "url": home_url,
                "pages": len(pages),
            }
        except PortfolioCrawlError as e:
            return {"error": str(e)}
        except Exception:
            logger.exception("Unexpected error crawling %s", url)
            return {"error": "The website could not be read."}

    @staticmethod
    def _follow_links(base: str, soup: BeautifulSoup) -> list[str]:
        host = urlparse(base).hostname
        seen, out = {urldefrag(base)[0].rstrip("/")}, []
        for a in soup.find_all("a", href=True):
            link = urldefrag(urljoin(base, a["href"]))[0]
            if urlparse(link).hostname != host or link.rstrip("/") in seen:
                continue
            if _FOLLOW.search(urlparse(link).path) or _FOLLOW.search(a.get_text(" ", strip=True)):
                seen.add(link.rstrip("/"))
                out.append(link)
            if len(out) >= MAX_PAGES - 1:
                break
        return out


# ── reading pages ─────────────────────────────────────────────────────────

def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _tokens(tag) -> set[str]:
    raw = " ".join(tag.get("class") or []) + " " + (tag.get("id") or "")
    return {t for t in re.split(r"[^a-z0-9]+", raw.lower()) if t}


def _extract_projects(soup: BeautifulSoup) -> list[dict]:
    projects = []
    for block in soup.find_all(["article", "section", "div", "li"]):
        if not (_tokens(block) & _PROJECT_TOKENS):
            continue
        title_tag = block.find(["h2", "h3", "h4"])
        if not title_tag:
            continue
        name = title_tag.get_text(" ", strip=True)
        if len(name) < 3 or len(name) > 120 or name.lower() in _SECTION_TITLES:
            continue
        desc_tag = block.find("p")
        text = block.get_text(" ", strip=True)
        projects.append({
            "name": name,
            "description": desc_tag.get_text(" ", strip=True)[:300] if desc_tag else "",
            "technologies": find_technologies(text),
        })
    return projects


def _extract_about(soup: BeautifulSoup) -> Optional[str]:
    for block in soup.find_all(["section", "div"]):
        if "about" in _tokens(block):
            return block.get_text(" ", strip=True)[:500]
    return None


@lru_cache(maxsize=1)
def _tech_patterns() -> list[tuple[re.Pattern, str]]:
    """(pattern, canonical name) for every taxonomy name and alias worth searching for."""
    patterns = []
    for alias, name in _skill_index().items():
        if alias in _SKIP or len(alias) < 3:
            continue
        if alias in _CASE_SENSITIVE:
            needle, flags = name, 0          # "Rust" the language, not "rust" the word
        else:
            needle, flags = alias, re.IGNORECASE
        patterns.append((re.compile(rf"(?<![\w.+#-]){re.escape(needle)}(?![\w+#-])", flags), name))
    return patterns


def find_technologies(text: str) -> list[str]:
    """Taxonomy skills named in the text, as whole words ("go" in "google" doesn't count)."""
    found: dict[str, None] = {}
    for pattern, name in _tech_patterns():
        if name not in found and pattern.search(text):
            found[name] = None
    return list(found)


# ── evidence ──────────────────────────────────────────────────────────────

def sync_portfolio_evidence(user_id: str, url: str, session: Session, crawler: Optional[PortfolioCrawler] = None) -> dict:
    """Crawl the portfolio, then remember its URL and replace the user's portfolio evidence.

    Raises PortfolioCrawlError if the site cannot be crawled (nothing is saved then).
    """
    result = (crawler or PortfolioCrawler()).crawl(url)
    if "error" in result:
        raise PortfolioCrawlError(result["error"])
    url = result.get("url") or url

    account = _portfolio_account(session, user_id)
    if account is None:
        account = ConnectedAccount(user_id=user_id, provider="portfolio")
        session.add(account)
    account.provider_username = url
    account.provider_user_id = url
    account.last_synced_at = datetime.utcnow()

    # Idempotent: a re-crawl replaces previous portfolio evidence
    session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id,
        EvidenceItem.source == "portfolio",
    ).delete()

    created = 0
    for project in result.get("projects", []):
        session.add(EvidenceItem(
            user_id=user_id,
            source="portfolio",
            source_url=url,
            skill_name=project["name"],
            confidence_score=0.85,
            evidence_data={
                "type": "project",
                "description": project.get("description", ""),
                "technologies": project.get("technologies", []),
            },
        ))
        created += 1

    canonical_skills = load_all_skills(session)
    seen: set[str] = set()
    for tech in result.get("technologies", []):
        canonical = find_canonical(tech, canonical_skills)
        name = canonical.name if canonical else tech
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        session.add(EvidenceItem(
            user_id=user_id,
            source="portfolio",
            source_url=url,
            skill_id=canonical.id if canonical else None,
            skill_name=name,
            confidence_score=0.80,
            evidence_data={"type": "skill"},
        ))
        created += 1

    from careeros.memory.events import remember

    remember(session, user_id, "EvidenceImported", {
        "source": "portfolio", "url": url, "projects": len(result.get("projects", [])),
        "technologies": len(result.get("technologies", [])), "items": created,
    }, stream="evidence", actor="import:portfolio")
    session.commit()
    return {
        "status": "crawled",
        "pages_read": result.get("pages", 1),
        "projects_found": len(result.get("projects", [])),
        "technologies_found": len(result.get("technologies", [])),
        "evidence_created": created,
    }


def _portfolio_account(session: Session, user_id: str) -> Optional[ConnectedAccount]:
    return session.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == user_id,
        ConnectedAccount.provider == "portfolio",
    ).first()


def portfolio_status(session: Session, user_id: str) -> dict:
    account = _portfolio_account(session, user_id)
    if not account:
        return {"connected": False}
    return {
        "connected": True,
        "url": account.provider_username,
        "last_synced_at": account.last_synced_at.isoformat() if account.last_synced_at else None,
    }


def disconnect_portfolio(session: Session, user_id: str) -> None:
    """Forget the portfolio URL and remove all portfolio evidence."""
    account = _portfolio_account(session, user_id)
    if account:
        session.delete(account)
    session.query(EvidenceItem).filter(
        EvidenceItem.user_id == user_id,
        EvidenceItem.source == "portfolio",
    ).delete()
    from careeros.memory.events import remember

    remember(session, user_id, "EvidenceRemoved", {"source": "portfolio"}, stream="evidence")
    session.commit()
