"""A company card from public sources, each fact with where it comes from:

- Wikidata (CC0): founded, size, headquarters, industry, listed or not, dissolved. Found by
  name and accepted only when the entity's official website matches the company's domain,
  so a namesake is never shown. Requests carry a User-Agent with a contact link (Wikimedia
  policy) and run one at a time.
- Companies House (UK register, free API key COMPANIES_HOUSE_API_KEY): status, incorporation
  date, type. Only for companies with jobs in the UK, and only when exactly one active
  company has the same name. Off without a key.
- News Aplio already reads (careeros/market: TechCrunch, Hacker News): layoffs, funding,
  acquisitions naming the company in the last year.
- What people on Hacker News say: comments that name the company and talk about working
  there, summarised by the LLM point by point, every point linked to the comments it rests
  on (on request: it costs an LLM call). Aplio doesn't collect reviews from review sites.

Cached in company_facts; Wikidata and Companies House re-read after 30 days, Hacker News
after 14. Facts that matter for trust (dissolved, liquidation, recent layoffs) feed the
trust check (careeros/jobs/trust.py).
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.companies.models.company_facts import CompanyFacts

logger = logging.getLogger(__name__)

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
CH_API = "https://api.company-information.service.gov.uk"
CH_PAGE = "https://find-and-update.company-information.service.gov.uk/company/{number}"
HN_API = "https://hn.algolia.com/api/v1/search"
HN_ITEM = "https://news.ycombinator.com/item?id={id}"
TIMEOUT = 10
TTL = {"wikidata": timedelta(days=30), "companies_house": timedelta(days=30), "people": timedelta(days=14)}
NEWS_DAYS = 365
LAYOFF_RECENT_DAYS = 120
MIN_COMMENTS = 3
MAX_COMMENTS = 20

_SUFFIX = re.compile(r"\b(inc|inc\.|gmbh|ltd|limited|llc|plc|b\.?v\.?|ag|s\.?a\.?|se|corp(oration)?|co\.?|"
                     r"a\.ş\.|as|oy|ab|srl|sas|holding|group)\b\.?", re.I)
_WORK = re.compile(r"\b(i (used to )?work(ed)? (at|for)|worked (at|for|there)|working (at|for|there)|"
                   r"(ex|former|current)[- ](employee|engineer|colleague)s?|employees|work culture|company culture|"
                   r"culture (is|was|there)|management (is|was)|my manager|interview(ed|s)? (at|with|process)|"
                   r"layoffs?|laid off|salar(y|ies)|total comp|\btc\b|rsus?|on-?call|burn ?out|work-life|\bwlb\b|"
                   r"toxic|great place to work|promotion|\bpip\b|recruiter)", re.I)
# Searches for talk about working somewhere (Hacker News search is by relevance)
HN_TOPICS = ("worked at", "culture", "interview", "layoffs", "salary", "management")


def key_of(name: str) -> str:
    """"Acme GmbH" and "ACME" share one card."""
    return " ".join(_SUFFIX.sub(" ", (name or "").lower()).replace(",", " ").split())[:200]


def _base(host: str) -> str:
    """careers.acme.co.uk → acme.co.uk; jobs.acme.com → acme.com"""
    h = (host or "").lower().removeprefix("www.").strip(".")
    parts = h.split(".")
    if len(parts) >= 3 and len(parts[-1]) == 2 and len(parts[-2]) <= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _agent() -> str:
    from careeros.shared.config import get_settings

    return f"AplioBot/1.0 (+{get_settings().web_app_url}; company facts for job seekers)"


def _http() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _agent(), "Accept": "application/json"})
    return s


# ── Wikidata ─────────────────────────────────────────────────────────────

def _claims(entity: dict, prop: str) -> list[dict]:
    return [c for c in (entity.get("claims") or {}).get(prop, []) if c.get("rank") != "deprecated"]


def _value(claim: dict):
    return ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")


def _year(claim: dict) -> Optional[int]:
    v = _value(claim)
    m = re.match(r"[+-]?(\d{4})", (v or {}).get("time", "")) if isinstance(v, dict) else None
    return int(m.group(1)) if m else None


def _employees(entity: dict) -> Optional[dict]:
    best = None
    for c in _claims(entity, "P1128"):
        v = _value(c)
        if not isinstance(v, dict) or "amount" not in v:
            continue
        when = None
        for q in (c.get("qualifiers") or {}).get("P585", []):
            m = re.match(r"[+-]?(\d{4})", ((q.get("datavalue") or {}).get("value") or {}).get("time", ""))
            when = int(m.group(1)) if m else when
        row = {"count": int(float(v["amount"])), "year": when, "preferred": c.get("rank") == "preferred"}
        if best is None or (row["preferred"], row["year"] or 0) > (best["preferred"], best["year"] or 0):
            best = row
    return {"count": best["count"], "year": best["year"]} if best else None


def _ids(entity: dict, prop: str) -> list[str]:
    return [v["id"] for v in (_value(c) for c in _claims(entity, prop)) if isinstance(v, dict) and v.get("id")]


def wikidata(name: str, domain: Optional[str], http: Optional[requests.Session] = None) -> dict:
    """{} when nothing matches the company's website (never a namesake)."""
    if not domain:
        return {}
    http = http or _http()
    want = _base(domain)
    found = http.get(WIKIDATA_API, timeout=TIMEOUT, params={
        "action": "wbsearchentities", "search": name, "language": "en", "type": "item", "limit": 7,
        "format": "json", "maxlag": 5}).json().get("search") or []
    ids = [f["id"] for f in found if f.get("id")]
    if not ids:
        return {}
    entities = http.get(WIKIDATA_API, timeout=TIMEOUT, params={
        "action": "wbgetentities", "ids": "|".join(ids), "props": "claims|labels|descriptions", "languages": "en",
        "format": "json", "maxlag": 5}).json().get("entities") or {}
    pick = None
    for qid in ids:
        e = entities.get(qid) or {}
        sites = [_value(c) for c in _claims(e, "P856")]
        if any(isinstance(s, str) and _base(urlparse(s).hostname or "") == want for s in sites):
            pick = e
            break
    if pick is None:
        return {}
    refs = {p: _ids(pick, p)[:2] for p in ("P17", "P159", "P452", "P414", "P749")}
    labels = {}
    wanted = sorted({i for v in refs.values() for i in v})
    if wanted:
        got = http.get(WIKIDATA_API, timeout=TIMEOUT, params={
            "action": "wbgetentities", "ids": "|".join(wanted), "props": "labels", "languages": "en",
            "format": "json", "maxlag": 5}).json().get("entities") or {}
        labels = {k: ((v.get("labels") or {}).get("en") or {}).get("value") for k, v in got.items()}
    names = {p: [labels[i] for i in ids_ if labels.get(i)] for p, ids_ in refs.items()}
    founded = next((y for y in map(_year, _claims(pick, "P571")) if y), None)
    dissolved = next((y for y in map(_year, _claims(pick, "P576")) if y), None)
    qid = pick.get("id")
    return {
        "id": qid,
        "label": ((pick.get("labels") or {}).get("en") or {}).get("value") or name,
        "description": ((pick.get("descriptions") or {}).get("en") or {}).get("value"),
        "founded": founded, "dissolved": dissolved, "employees": _employees(pick),
        "country": (names["P17"] or [None])[0], "headquarters": (names["P159"] or [None])[0],
        "industry": names["P452"][:2], "listed_on": names["P414"][:2], "parent": (names["P749"] or [None])[0],
        "url": f"https://www.wikidata.org/wiki/{qid}", "source": "Wikidata (CC0)",
    }


# ── Companies House ──────────────────────────────────────────────────────

def companies_house(name: str, api_key: Optional[str], http: Optional[requests.Session] = None) -> dict:
    """The one active UK company with this exact name, or {} (several or none: not guessed)."""
    if not api_key:
        return {}
    http = http or _http()
    resp = http.get(f"{CH_API}/search/companies", timeout=TIMEOUT, auth=(api_key, ""),
                    params={"q": name, "items_per_page": 10})
    if resp.status_code != 200:
        return {}
    want = key_of(name)
    same = [i for i in resp.json().get("items") or [] if key_of(i.get("title", "")) == want]
    active = [i for i in same if (i.get("company_status") or "") == "active"]
    pick = active[0] if len(active) == 1 else (same[0] if len(same) == 1 else None)
    if pick is None:
        return {}
    number = pick.get("company_number")
    return {
        "number": number, "name": pick.get("title"), "status": pick.get("company_status"),
        "incorporated": pick.get("date_of_creation"), "type": pick.get("company_type"),
        "locality": (pick.get("address") or {}).get("locality"),
        "url": CH_PAGE.format(number=number), "source": "Companies House (UK register)",
    }


# ── news Aplio already reads ─────────────────────────────────────────────

def news(session: Session, name: str, now: Optional[datetime] = None) -> list[dict]:
    from careeros.market.models.market_signal import MarketSignal

    now = now or datetime.now(timezone.utc)
    want = key_of(name)
    if len(want) < 3:
        return []
    rows = (session.query(MarketSignal)
            .filter(MarketSignal.signal_type.in_(("layoff", "funding", "acquisition")),
                    MarketSignal.occurred_at >= (now - timedelta(days=NEWS_DAYS)).replace(tzinfo=None))
            .order_by(MarketSignal.occurred_at.desc()).limit(500).all())
    out = []
    for r in rows:
        if any(key_of(c) == want for c in r.companies_affected or []):
            out.append({"type": r.signal_type, "title": r.title, "url": r.url, "source": r.source,
                        "date": r.occurred_at.date().isoformat() if r.occurred_at else None,
                        "count": (r.metadata_json or {}).get("layoff_count")})
    return out[:8]


# ── what people on Hacker News say ───────────────────────────────────────

class _Point(BaseModel):
    text: str
    refs: list[str] = Field(default_factory=list)


class _People(BaseModel):
    points: list[_Point] = Field(default_factory=list)


PEOPLE_RULES = (
    "You summarise what Hacker News commenters say about working at one company, for a job seeker. "
    "Use only the comments given. Up to 4 points, each one plain sentence of at most 30 words, saying who says it "
    "(\"several commenters\", \"one former engineer\"). Cover pay, culture, management, interviews or stability "
    "where the comments do; include criticism and praise as they appear. End each point with the ids of the "
    "comments it rests on, as refs. If the comments say nothing about working there, return no points. "
    "Return JSON: {\"points\": [{\"text\": \"...\", \"refs\": [\"c1\", \"c4\"]}]}"
)


def hn_comments(name: str, http: Optional[requests.Session] = None, now: Optional[datetime] = None) -> list[dict]:
    """Comments from the last three years that name the company and talk about working there."""
    http = http or _http()
    now = now or datetime.now(timezone.utc)
    since = int((now - timedelta(days=3 * 365)).timestamp())
    rx = re.compile(r"(?<!\w)" + re.escape(name) + r"(?!\w)", re.I)
    out, seen = [], set()
    for topic in HN_TOPICS:
        hits = http.get(HN_API, timeout=TIMEOUT, params={
            "query": f"{name} {topic}", "tags": "comment", "hitsPerPage": 20,
            "numericFilters": f"created_at_i>{since}"}).json().get("hits") or []
        for h in hits:
            cid = h.get("objectID")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            text = re.sub(r"<[^>]+>", " ", h.get("comment_text") or "")
            text = text.replace("&#x27;", "'").replace("&quot;", '"').replace("&#x2F;", "/").replace("&amp;", "&")
            text = " ".join(text.split())
            if rx.search(text) and _WORK.search(text):
                out.append({"id": cid, "text": text[:700], "at": (h.get("created_at") or "")[:10],
                            "url": HN_ITEM.format(id=cid)})
        if len(out) >= MAX_COMMENTS:
            break
    return out[:MAX_COMMENTS]


def people(name: str, http: Optional[requests.Session] = None, now: Optional[datetime] = None) -> dict:
    """{points: [{text, sources: [url]}], comments: n, search: url} or {comments: n} when too few."""
    from careeros.shared.llm import get_llm_client

    comments = hn_comments(name, http, now)
    search = f"https://hn.algolia.com/?query={requests.utils.quote(name)}&type=comment"
    base = {"comments": len(comments), "search": search, "source": "Hacker News comments"}
    if len(comments) < MIN_COMMENTS:
        return base
    ids = {f"c{i}": c for i, c in enumerate(comments, 1)}
    listed = "\n".join(f"[{k}] ({c['at']}) {c['text']}" for k, c in ids.items())
    try:
        got = get_llm_client().complete_model(f"COMPANY: {name}\nCOMMENTS\n{listed}", _People, system=PEOPLE_RULES,
                                              task="general", temperature=0.2, max_tokens=600, timeout=60)
    except Exception as e:
        logger.info("Hacker News summary for %s unavailable: %s", name, type(e).__name__)
        return {**base, "links": [{"url": c["url"], "at": c["at"]} for c in comments[:5]]}
    points = []
    for p in got.points[:4]:
        refs = [ids[r] for r in p.refs if r in ids]
        if refs and p.text.strip():
            points.append({"text": " ".join(p.text.split())[:240], "sources": [r["url"] for r in refs][:4]})
    return {**base, "points": points}


# ── the card ─────────────────────────────────────────────────────────────

def _fresh(row: CompanyFacts, section: str, now: datetime) -> bool:
    at = (row.read_at or {}).get(section)
    return bool(at) and now - datetime.fromisoformat(at) < TTL[section]


def card(session: Session, name: str, domain: Optional[str] = None, *, uk: bool = False, with_people: bool = False,
         now: Optional[datetime] = None, http: Optional[requests.Session] = None) -> dict:
    """The company's card, reading only what is missing or stale. Never raises for a source failing."""
    from careeros.shared.config import get_settings

    now = now or datetime.now(timezone.utc)
    key = key_of(name)
    if not key:
        return {}
    row = session.get(CompanyFacts, key) or CompanyFacts(key=key, name=name[:200], read_at={})
    if domain and not row.domain:
        row.domain = _base(domain)[:255]
    read = dict(row.read_at or {})
    http = http or _http()

    def refresh(section: str, fn) -> None:
        if _fresh(row, section, now):
            return
        try:
            setattr(row, section, fn())
            read[section] = now.isoformat()
        except Exception as e:   # a source down: try again next time, keep what we had
            logger.info("Company facts %s for %s failed: %s", section, name, type(e).__name__)

    refresh("wikidata", lambda: wikidata(name, row.domain, http))
    ch_key = getattr(get_settings(), "companies_house_api_key", None)
    if uk and ch_key:
        refresh("companies_house", lambda: companies_house(name, ch_key, http))
    if with_people:
        refresh("people", lambda: people(name, http, now))
    row.read_at, row.last_used_at = read, now
    session.add(row)
    session.flush()
    return to_dict(row, news(session, name, now), companies_house_on=bool(ch_key))


def to_dict(row: CompanyFacts, news_items: list[dict], companies_house_on: bool = False) -> dict:
    good, concerns = trust_notes(row.wikidata, row.companies_house, news_items)
    return {
        "name": row.name, "domain": row.domain,
        "wikidata": row.wikidata or None, "companies_house": row.companies_house or None,
        "companies_house_on": companies_house_on,
        "people": row.people, "news": news_items, "read_at": row.read_at or {},
        "good": good, "concerns": concerns,
    }


def trust_notes(wd: Optional[dict], ch: Optional[dict], news_items: list[dict],
                now: Optional[datetime] = None) -> tuple[list[str], list[str]]:
    """What the public record adds to trust: (good, concerns)."""
    now = now or datetime.now(timezone.utc)
    good, concerns = [], []
    if wd:
        if wd.get("dissolved"):
            concerns.append(f"Dissolved in {wd['dissolved']} (Wikidata)")
        elif wd.get("founded"):
            good.append(f"Founded in {wd['founded']} (Wikidata)")
    if ch:
        status = (ch.get("status") or "").replace("-", " ")
        if status and status != "active":
            concerns.append(f"UK register status: {status} (Companies House)")
        elif ch.get("incorporated"):
            good.append(f"Registered in the UK since {ch['incorporated'][:4]} (Companies House)")
    for n in news_items:
        if n.get("type") == "layoff" and n.get("date"):
            days = (now.date() - datetime.fromisoformat(n["date"]).date()).days
            if days <= LAYOFF_RECENT_DAYS:
                concerns.append(f"Layoffs reported {n['date']} ({n.get('source') or 'news'})")
                break
    return good, concerns


def cached(session: Session, names: list[str]) -> dict[str, dict]:
    """key → {good, concerns} for companies already on file (no network): for the trust check."""
    keys = {key_of(n) for n in names if n}
    if not keys:
        return {}
    rows = session.query(CompanyFacts).filter(CompanyFacts.key.in_(list(keys))).all()
    out = {}
    for r in rows:
        good, concerns = trust_notes(r.wikidata, r.companies_house, [])
        if good or concerns:
            out[r.key] = {"good": good, "concerns": concerns}
    return out
