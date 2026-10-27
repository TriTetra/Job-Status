"""The job brain's reading step: the LLM turns a posting into structured facts, once.

Facts are cached on the job (`llm_facts`, keyed by the posting's content_hash)
and only re-extracted when the posting changes. Scoring stays deterministic —
it reads these facts instead of keyword guesses when they exist. Only jobs that
match some user's target roles are extracted, newest first, within the bulk
share of the daily LLM budget.
"""

import logging
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, update

from careeros.db.connection import db
from careeros.jobs.models.job import Job
from careeros.knowledge.skill_names import canonical_list, known_names
from careeros.shared.config import get_settings
from careeros.shared.llm import LLMBudgetExceeded, LLMNotConfiguredError, get_llm_client

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_CHARS = 7000
MAX_SKILLS = 20
MAX_REQUIRED = 12
SENIORITY_YEARS = {"intern": 0.0, "junior": 1.0, "mid": 3.0, "senior": 5.0, "staff": 8.0,
                   "principal": 10.0, "manager": 6.0}


class JobFacts(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    min_years: Optional[float] = Field(default=None, ge=0, le=40)
    seniority: Literal["intern", "junior", "mid", "senior", "staff", "principal", "manager", "unknown"] = "unknown"
    workplace: Literal["remote", "hybrid", "onsite", "unknown"] = "unknown"
    remote_regions: list[str] = Field(default_factory=list)
    visa_sponsorship: Literal["yes", "no", "unknown"] = "unknown"
    salary_min: Optional[int] = Field(default=None, ge=0)
    salary_max: Optional[int] = Field(default=None, ge=0)
    salary_currency: Optional[str] = None
    salary_period: Literal["year", "month", "hour", "unknown"] = "unknown"
    summary: str = ""

    @field_validator("required_skills")
    @classmethod
    def _required(cls, v: list[str]) -> list[str]:
        return canonical_list(s for s in v if isinstance(s, str) and len(s) <= 60)[:MAX_REQUIRED]

    @field_validator("nice_to_have_skills")
    @classmethod
    def _nice(cls, v: list[str]) -> list[str]:
        return canonical_list(s for s in v if isinstance(s, str) and len(s) <= 60)[:MAX_SKILLS]

    @field_validator("remote_regions")
    @classmethod
    def _regions(cls, v: list[str]) -> list[str]:
        return [r.strip()[:40] for r in v if isinstance(r, str) and r.strip()][:5]

    @field_validator("summary")
    @classmethod
    def _summary(cls, v: str) -> str:
        return v.strip()[:300]

    @field_validator("salary_currency")
    @classmethod
    def _currency(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper()[:8] if v and v.strip() else None


SYSTEM_PROMPT = (
    "You extract facts from job postings for a job-matching engine. State only what the posting "
    "says; when it doesn't say, use \"unknown\", null or an empty list. Return one JSON object."
)

PROMPT = """Posting
Title: {title}
Company: {company}
Location: {location}

{description}

Return JSON with exactly these keys:
- required_skills: the must-have technologies, languages, tools and platforms, most important first (max 10). Concrete names only: no soft skills, degrees or generic categories like "databases".
- nice_to_have_skills: the same kind of items marked preferred / bonus / nice to have.
- min_years: the smallest number of years of experience the posting asks for, or null.
- seniority: intern | junior | mid | senior | staff | principal | manager | unknown.
- workplace: remote | hybrid | onsite | unknown.
- remote_regions: where a remote hire may live (e.g. "US", "Europe"), or [].
- visa_sponsorship: "yes" only if the posting offers sponsorship; "no" if it says it won't sponsor or requires existing work authorization without sponsorship; otherwise "unknown".
- salary_min, salary_max, salary_currency (ISO code), salary_period (year | month | hour | unknown): only if stated.
- summary: one plain sentence on what the role does (max 25 words).

Prefer these canonical skill names when they apply: {skill_names}"""


def extract_facts(title: str, company: str, location: str, description: str) -> JobFacts:
    prompt = PROMPT.format(
        title=title, company=company, location=location or "not stated",
        description=(description or "")[:MAX_DESCRIPTION_CHARS],
        skill_names=", ".join(known_names()),
    )
    return get_llm_client().complete_model(
        prompt, JobFacts, system=SYSTEM_PROMPT, task="job_extract", temperature=0.0, max_tokens=700, timeout=90,
    )


@dataclass
class EnrichSummary:
    candidates: int = 0
    extracted: int = 0
    failed: int = 0
    stopped: Optional[str] = None   # why the run ended early (budget, not configured)

    def to_dict(self) -> dict:
        return vars(self).copy()


def _pending(limit: int) -> list[tuple[str, str, str, str, str, Optional[str]]]:
    """Open jobs without facts for their current content, matching someone's roles, newest first."""
    from careeros.jobs.boards import TitleFilter, load_boards
    from careeros.jobs.targeting import role_terms

    with db.session_scope() as s:
        terms = role_terms(s)
        titles = TitleFilter(tuple(terms), load_boards().titles.exclude) if terms else load_boards().titles
        rows = (
            s.query(Job.url, Job.title, Job.company, Job.location, Job.description, Job.content_hash)
            .filter(Job.closed_at.is_(None))
            .filter(or_(Job.llm_facts_hash.is_(None), Job.llm_facts_hash != Job.content_hash))
            .order_by(Job.discovered_at.desc().nullslast())
            .all()
        )
    picked = [tuple(r) for r in rows if titles.keeps(r.title or "")]
    return picked[:limit] if limit else picked


def _save(url: str, content_hash: Optional[str], facts: JobFacts, model: str) -> None:
    with db.session_scope() as s:
        s.execute(update(Job).where(Job.url == url).values(
            llm_facts=facts.model_dump(), llm_facts_hash=content_hash, llm_model=model[:128],
        ))


def enrich_jobs(limit: int = 300) -> EnrichSummary:
    """Extract facts for up to `limit` pending jobs. Stops cleanly when the budget runs out."""
    summary = EnrichSummary()
    try:
        client = get_llm_client()
    except LLMNotConfiguredError as e:
        summary.stopped = str(e)
        return summary
    pending = _pending(limit)
    summary.candidates = len(pending)
    model = client.model_for("job_extract")

    def work(row):
        url, title, company, location, description, content_hash = row
        _save(url, content_hash, extract_facts(title, company, location, description), model)

    with ThreadPoolExecutor(max_workers=max(1, get_settings().llm_max_concurrency)) as pool:
        futures = [pool.submit(work, row) for row in pending]
        for future in as_completed(futures):
            try:
                future.result()
                summary.extracted += 1
            except LLMBudgetExceeded as e:
                if not summary.stopped:
                    summary.stopped = str(e)
                    for f in futures:
                        f.cancel()
            except CancelledError:
                continue
            except Exception as e:  # one bad posting (LLM or DB) doesn't stop the run
                summary.failed += 1
                logger.info("Job extraction failed: %s", e)
    logger.info("Job extraction: %s", summary.to_dict())
    return summary
