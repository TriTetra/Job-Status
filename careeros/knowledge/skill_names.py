"""Canonical skill names from the skills taxonomy (infra/seeds/v1/skills.yaml).

"postgres", "Postgres", "postgresql" → "PostgreSQL"; unknown names pass through
trimmed. Scoring compares skills by canonical key, so a CV saying "golang" and a
posting saying "Go" match.
"""

from functools import lru_cache
from typing import Iterable

import yaml

from careeros.shared.config import ROOT

SKILLS_FILE = ROOT / "infra" / "seeds" / "v1" / "skills.yaml"

# Common spellings the taxonomy doesn't list as aliases
_EXTRA_ALIASES = {
    "postgres": "postgresql", "k8s": "kubernetes", "node": "node.js", "nodejs": "node.js",
    "react.js": "react", "reactjs": "react", "vue.js": "vue", "next": "next.js", "nextjs": "next.js",
    "amazon web services": "aws", "google cloud": "gcp", "google cloud platform": "gcp",
    "ml": "machine learning", "dl": "deep learning", "large language models": "llm", "llms": "llm",
}


@lru_cache(maxsize=1)
def _index() -> dict[str, str]:
    with open(SKILLS_FILE, encoding="utf-8") as f:
        skills = (yaml.safe_load(f) or {}).get("skills") or []
    index: dict[str, str] = {}
    for skill in skills:
        name = skill["name"]
        for key in [name, skill.get("slug", ""), *(skill.get("aliases") or [])]:
            if key:
                index.setdefault(str(key).strip().lower(), name)
    for alias, target in _EXTRA_ALIASES.items():
        if target in index:
            index.setdefault(alias, index[target])
    return index


def canonical(name: str) -> str:
    cleaned = " ".join(str(name).split())
    return _index().get(cleaned.lower(), cleaned)


def key(name: str) -> str:
    """Comparison key: canonical name, lower case."""
    return canonical(name).lower()


def canonical_list(names: Iterable[str]) -> list[str]:
    """Canonical, de-duplicated, order kept."""
    out: dict[str, str] = {}
    for n in names:
        if n and str(n).strip():
            c = canonical(n)
            out.setdefault(c.lower(), c)
    return list(out.values())


def known_names() -> list[str]:
    return sorted(set(_index().values()))
