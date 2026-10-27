"""Small text rules shared by job boards, job extraction and market parsers."""

import re
from typing import Optional


def word_pattern(word: str) -> re.Pattern:
    """Whole-word match. Two letters or fewer ("Go", "AI", "ML") must match case
    too — in lower case they are ordinary words ("go", "ai")."""
    flags = 0 if len(word) <= 2 else re.IGNORECASE
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(word) + r"(?![A-Za-z0-9])", flags)


_NO_SPONSORSHIP = re.compile(
    r"(?:not|unable to|cannot|can't|won't|will not|do not|does not|don't|doesn't|no)\s+"
    r"(?:\w+\s+){0,3}(?:visa\s+)?sponsor",
    re.IGNORECASE,
)
_SPONSORSHIP = re.compile(
    r"visa sponsorship|sponsor(?:ship)? (?:is )?available|will sponsor|\bh-?1b\b|visas? (?:ok|welcome|yes)",
    re.IGNORECASE,
)


def sponsorship_stance(text: str) -> Optional[bool]:
    """False if the text rules visa sponsorship out, True if it offers it, None if silent."""
    if _NO_SPONSORSHIP.search(text or ""):
        return False
    if _SPONSORSHIP.search(text or ""):
        return True
    return None
