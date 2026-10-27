"""Structured fields from posting text: skills, seniority, remote, salary, visa.

Deterministic and config-driven (`extraction:` in infra/config/plugins.yaml).
Used by every job source so a Greenhouse posting and an ApplyPilot row are read
the same way.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from careeros.shared.config import load_plugin_config
from careeros.shared.text import sponsorship_stance, word_pattern

_REQUIREMENTS_HEADING = re.compile(
    r"(requirements?|qualifications?|what you.?ll need"
    r"|skills?(?: required)?|tech stack|you have|must have)\s*:?\s*\n",
    re.IGNORECASE,
)
_REMOTE_REGION = re.compile(
    r"remote[^\n]{0,25}?[\(\-–:]?\s*"
    r"(united states|usa|us\b|canada|united kingdom|uk\b|germany|france|"
    r"netherlands|spain|poland|turkey|india|brazil|australia|japan|"
    r"europe|emea|apac|americas|eu\b|worldwide|global|anywhere)",
    re.IGNORECASE,
)
_REMOTE_WORDS = ("remote", "anywhere", "work from home", "wfh")

# "$120,000 - $160,000", "$120k–$160k", "USD 120,000 to 160,000"
_AMOUNT = r"(\d{2,3}(?:,\d{3})+|\d{2,3}(?:\.\d)?\s?[kK])"
_SALARY_RANGE = re.compile(
    r"(?:\$|USD\s?|US\$)\s?" + _AMOUNT + r"\s*(?:-|–|—|to)\s*(?:\$|USD\s?|US\$)?\s?" + _AMOUNT
)

def _amount(text: str) -> int:
    text = text.replace(",", "").strip()
    if text[-1] in "kK":
        return int(float(text[:-1].strip()) * 1000)
    return int(text)


class TextExtractor:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg = config or load_plugin_config()["extraction"]
        self._skills = cfg["skill_extraction"]
        self._sizes = cfg["company_sizes"]
        self._seniority = cfg["seniority"]
        self._skill_patterns = [(skill, word_pattern(skill)) for skill in self._skills["keywords"]]

    def skills(self, description: str, title: str) -> List[str]:
        """Known skill keywords, from the requirements section when there is one."""
        text = description
        heading = _REQUIREMENTS_HEADING.search(description)
        if heading and self._skills["prefer_requirements_section"]:
            section = description[heading.end(): heading.end() + self._skills["max_section_chars"]]
            next_heading = re.search(r"\n[A-Z][^\n]{0,40}:?\s*\n", section)
            text = section[: next_heading.start()] if next_heading else section
        haystack = text + " " + title
        return [skill for skill, rx in self._skill_patterns if rx.search(haystack)]

    def required_years(self, title: str, description: str) -> float:
        lowered = title.lower()
        for p in self._seniority["title_patterns"]:
            if re.search(p["pattern"], lowered):
                return p["years"]
        m = re.search(self._seniority["description_pattern"], (title + " " + description).lower())
        if m:
            return float(m.group(1))
        return self._seniority["default_years"]

    def company_size(self, company: str) -> str:
        lowered = (company or "").lower()
        if not lowered or lowered == "unknown":
            return "unknown"
        for size, names in self._sizes.items():
            if any(n in lowered for n in names):
                return size
        return "unknown"

    @staticmethod
    def is_remote(location: str, description: str) -> bool:
        text = (location + " " + description[:500]).lower()
        return any(w in text for w in _REMOTE_WORDS)

    @staticmethod
    def remote_region(location: str, description: str) -> Optional[str]:
        m = _REMOTE_REGION.search(location + " " + (description or "")[:800])
        if not m:
            return None
        region = m.group(1).strip()
        return region.upper() if len(region) <= 3 else region.title()

    @staticmethod
    def salary(text: str) -> Tuple[Optional[int], Optional[int]]:
        """A dollar range written in the posting, e.g. pay-transparency lines."""
        m = _SALARY_RANGE.search(text or "")
        if not m:
            return None, None
        low, high = _amount(m.group(1)), _amount(m.group(2))
        if not (10_000 <= low <= high <= 2_000_000):
            return None, None
        return low, high

    @staticmethod
    def sponsors_visa(text: str) -> Optional[bool]:
        """False if the posting rules sponsorship out, True if it offers it, None if silent."""
        return sponsorship_stance(text)
