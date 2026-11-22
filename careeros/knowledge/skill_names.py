"""Canonical skill names from the skills taxonomy (infra/seeds/v1/skills.yaml).

"postgres", "Postgres", "postgresql" → "PostgreSQL"; unknown names pass through
trimmed. Scoring compares skills by canonical key, so a CV saying "golang" and a
posting saying "Go" match.
"""

import re
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


def compact(name: str) -> str:
    """Spelling-insensitive form: "Hugging Face", "huggingface", "Node.js" ≈ "nodejs".
    Keeps + and # so C, C++ and C# stay apart."""
    return re.sub(r"[\s.\-_]", "", str(name).lower())


@lru_cache(maxsize=1)
def _compact_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for alias, name in _index().items():
        index.setdefault(compact(alias), name)
    return index


def canonical(name: str) -> str:
    cleaned = " ".join(str(name).split())
    lowered = cleaned.lower()
    return _index().get(lowered) or _compact_index().get(compact(lowered)) or cleaned


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


# "React 19", "Tailwind CSS v4", "Python 3.11" → the base name (versions never match a posting)
_VERSION = re.compile(r"^(?P<base>.+?)\s+v?\d+(?:\.\d+)*[a-z]?$", re.IGNORECASE)
# "Redis (Asynq)", "eBPF (Tetragon)" → base + the tools named inside
_PAREN = re.compile(r"^(?P<base>[^()]+?)\s*\((?P<inner>[^()]*)\)$")
# "LangChain / CrewAI", "Git, GitHub Actions" → separate skills ("CI/CD" without spaces stays whole)
_SPLIT = re.compile(r"\s+/\s+|\s*,\s*|\s+&\s+")
# Parenthesised words that describe a level, not a tool: "Python (advanced)"
_NOT_A_TOOL = {"basic", "beginner", "intermediate", "advanced", "expert", "native", "fluent",
               "proficient", "familiar", "working knowledge", "learning"}


def _strip_version(name: str) -> str:
    if canonical(name) != " ".join(name.split()):  # a catalog name that ends in a number: "OAuth 2.0"
        return name
    m = _VERSION.match(name)
    return m["base"] if m and len(m["base"]) >= 2 else name


def split_skill_names(raw: str) -> list[str]:
    """One skill as a CV wrote it → clean canonical names (de-duplicated, order kept).

    Strips versions, splits "A / B" and "A, B", and keeps tools named in parentheses
    when they look like tools (known names, or capitalised like "Asynq", "gRPC").
    """
    text = " ".join(str(raw or "").split()).strip(" .;:")
    if not text:
        return []
    parts: list[str] = []
    m = _PAREN.match(text)
    if m:
        parts.extend(_SPLIT.split(m["base"]))
        for inner in _SPLIT.split(m["inner"]):
            inner = inner.strip()
            if not inner or inner.lower() in _NOT_A_TOOL or "year" in inner.lower():
                continue
            if canonical(inner) != inner or any(c.isupper() for c in inner):
                parts.append(inner)
    else:
        parts.extend(_SPLIT.split(text))
    return canonical_list(_strip_version(p.strip(" .;:")) for p in parts if p.strip(" .;:"))
