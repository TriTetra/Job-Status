"""Which company boards to read and which postings on them are worth keeping."""

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, Optional

import yaml

from careeros.jobs.sources.ats import FETCHERS, Board
from careeros.shared.config import ROOT
from careeros.shared.text import word_pattern

COMPANIES_FILE = ROOT / "infra" / "config" / "companies.yaml"
_WORKDAY_FIELDS = ("host", "tenant", "site")


class BoardConfigError(ValueError):
    pass


@dataclass(frozen=True)
class TitleFilter:
    """A title is kept when it contains every word of some include term (any order)
    and no exclude phrase: "Backend Engineer" keeps "Software Engineer, Backend"."""

    include: tuple[str, ...]
    exclude: tuple[str, ...]

    def __post_init__(self):
        object.__setattr__(self, "_inc", [[word_pattern(w) for w in _words(t)] for t in self.include if _words(t)])
        object.__setattr__(self, "_exc", _phrases_regex(self.exclude))

    def with_terms(self, extra: Iterable[str]) -> "TitleFilter":
        return TitleFilter(tuple(dict.fromkeys([*self.include, *(t for t in extra if t)])), self.exclude)

    def keeps(self, title: str) -> bool:
        if self._exc and self._exc.search(title):
            return False
        return any(all(rx.search(title) for rx in words) for words in self._inc)


def _words(term: str) -> list[str]:
    return [w for w in re.split(r"[\s\-/,]+", term.strip()) if w]


def _phrases_regex(terms: Iterable[str]) -> Optional[re.Pattern]:
    parts = [re.escape(t.strip()).replace(r"\ ", r"[\s\-]?") for t in terms if t.strip()]
    if not parts:
        return None
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(parts) + r")(?![A-Za-z0-9])", re.IGNORECASE)


@dataclass(frozen=True)
class BoardConfig:
    boards: tuple[Board, ...]
    titles: TitleFilter

    def select(self, keys: Optional[Iterable[str]]) -> list[Board]:
        if not keys:
            return list(self.boards)
        wanted = set(keys)
        unknown = wanted - {b.key for b in self.boards}
        if unknown:
            raise BoardConfigError(f"Unknown company key(s): {', '.join(sorted(unknown))}")
        return [b for b in self.boards if b.key in wanted]


def parse(data: dict) -> BoardConfig:
    titles = data.get("titles") or {}
    search = tuple(data.get("workday_search") or ())
    boards, seen = [], set()
    for entry in data.get("companies") or []:
        key, ats = entry.get("key"), entry.get("ats")
        if not key or not entry.get("name"):
            raise BoardConfigError(f"Company entry needs key and name: {entry}")
        if key in seen:
            raise BoardConfigError(f"Duplicate company key: {key}")
        if ats not in FETCHERS:
            raise BoardConfigError(f"{key}: unknown ats '{ats}' (use {', '.join(FETCHERS)})")
        if ats == "workday":
            missing = [f for f in _WORKDAY_FIELDS if not entry.get(f)]
            if missing:
                raise BoardConfigError(f"{key}: workday needs {', '.join(missing)}")
        elif not entry.get("board"):
            raise BoardConfigError(f"{key}: {ats} needs board")
        seen.add(key)
        boards.append(Board(
            key=key, name=entry["name"], ats=ats, board=entry.get("board", ""),
            host=entry.get("host", ""), tenant=entry.get("tenant", ""), site=entry.get("site", ""),
            search=tuple(entry.get("search") or (search if ats == "workday" else ())),
        ))
    return BoardConfig(
        boards=tuple(boards),
        titles=TitleFilter(tuple(titles.get("include") or ()), tuple(titles.get("exclude") or ())),
    )


@lru_cache(maxsize=1)
def load_boards() -> BoardConfig:
    with open(COMPANIES_FILE, encoding="utf-8") as f:
        return parse(yaml.safe_load(f) or {})
