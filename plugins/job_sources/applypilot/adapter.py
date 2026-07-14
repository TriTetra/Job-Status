"""
ApplyPilot adapter — normalizes raw DB rows to canonical Job schema.

All extraction logic is config-driven from config/plugins.yaml:
  - Company name (from URL, title, application_url, description)
  - Skills (keyword matching with optional requirements-section scoping)
  - Salary parsing (configurable regex patterns)
  - Company size classification
  - Seniority / required-years detection
  - Remote detection
"""

import re
from typing import Any, Dict, List, Optional, Tuple


class ApplyPilotAdapter:
    """Normalizes ApplyPilot raw rows to canonical Job schema."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._col = config["columns"]
        self._company_cfg = config["company_extraction"]
        self._skill_cfg = config["skill_extraction"]
        self._salary_patterns = config["salary_patterns"]
        self._sizes = config["company_sizes"]
        self._seniority_cfg = config["seniority"]

        # Compile requirements-heading regex once
        self._req_heading_re = re.compile(
            r"(requirements?|qualifications?|what you.?ll need"
            r"|skills?(?: required)?|tech stack|you have|must have)\s*:?\s*\n",
            re.IGNORECASE,
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        url = row.get(self._col["url"], "") or ""
        title = row.get(self._col["title"]) or "Unknown"
        location = row.get(self._col["location"]) or "Unknown"

        description = (
            row.get(self._col["full_description"])
            or row.get(self._col["description"])
            or ""
        )

        company = self._extract_company(
            title,
            url,
            row.get(self._col["application_url"]),
            description,
        )

        remote = self._is_remote(location, description)
        salary_min, salary_max = self._parse_salary(row.get(self._col["salary"]))
        company_size = self._classify_size(company)
        required_skills = self._extract_skills(description, title)
        required_years = self._extract_years(title, description)
        posted_date = self._parse_date(row.get(self._col["discovered_at"]))

        raw_score = row.get(self._col["fit_score"])

        return {
            "url": url,
            "title": title,
            "company": company,
            "description": description,
            "location": location,
            "remote": remote,
            "required_skills": required_skills,
            "preferred_skills": [],
            "required_years": required_years,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "company_size": company_size,
            "sponsors_visa": remote,  # heuristic
            "posted_date": posted_date,
            "source": row.get(self._col["site"], "unknown") or "unknown",
            "fit_score": float(raw_score) if raw_score is not None else None,
            "application_url": row.get(self._col["application_url"]),
            "score_reasoning": row.get(self._col["score_reasoning"]),
        }

    # ------------------------------------------------------------------
    # Company extraction
    # ------------------------------------------------------------------

    def _extract_company(
        self,
        title: str,
        url: str,
        application_url: Optional[str],
        description: str,
    ) -> str:
        blocklist = self._company_cfg["blocklist"]

        # 1. LinkedIn company slug
        if "linkedin.com" in url:
            m = re.search(r"/company/([^/?#]+)", url)
            if m:
                return m.group(1).replace("-", " ").title()

        # 2. "Title - Company" pattern
        if " - " in title:
            candidate = title.split(" - ")[-1].strip()
            if candidate.lower() not in blocklist:
                return candidate

        # 3. "Title at Company" pattern
        if " at " in title:
            candidate = title.split(" at ")[-1].strip()
            if candidate.lower() not in blocklist:
                return candidate

        # 4. Application URL domain (non-ATS)
        if application_url:
            m = re.search(
                r"https?://(?:www\.)?([a-z0-9\-]+)\.[a-z.]+",
                application_url,
                re.IGNORECASE,
            )
            if m:
                full_url = m.group(0).lower()
                if not any(
                    ats in full_url
                    for ats in self._company_cfg["ats_domains"]
                ):
                    return m.group(1).replace("-", " ").title()

        # 5. Description patterns ("At X, we..." / "Join X!")
        if description:
            for pattern in [
                r"^At ([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,4}),\s+we",
                r"\bJoin ([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,4})[\s,!.]",
            ]:
                m = re.search(pattern, description[:600])
                if m:
                    candidate = m.group(1).strip().rstrip(".,")
                    if candidate.lower() not in blocklist and len(candidate) > 1:
                        return candidate

        return "Unknown"

    # ------------------------------------------------------------------
    # Skill extraction
    # ------------------------------------------------------------------

    def _extract_skills(self, description: str, title: str) -> List[str]:
        heading_match = self._req_heading_re.search(description)

        if heading_match and self._skill_cfg["prefer_requirements_section"]:
            start = heading_match.end()
            max_chars = self._skill_cfg["max_section_chars"]
            section = description[start : start + max_chars]
            next_h = re.search(r"\n[A-Z][^\n]{0,40}:?\s*\n", section)
            if next_h:
                section = section[: next_h.start()]
            text = (section + " " + title).lower()
        else:
            text = (description + " " + title).lower()

        found: List[str] = []
        for skill in self._skill_cfg["keywords"]:
            pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
            if re.search(pattern, text):
                found.append(skill)
        return found

    # ------------------------------------------------------------------
    # Salary parsing
    # ------------------------------------------------------------------

    def _parse_salary(
        self, salary_str: Optional[str]
    ) -> Tuple[Optional[int], Optional[int]]:
        if not salary_str:
            return None, None
        clean = salary_str.replace(",", "")
        for cfg in self._salary_patterns:
            m = re.search(cfg["pattern"], clean)
            if m:
                try:
                    mult = cfg["multiplier"]
                    return int(m.group(1)) * mult, int(m.group(2)) * mult
                except (ValueError, IndexError):
                    continue
        return None, None

    # ------------------------------------------------------------------
    # Company size
    # ------------------------------------------------------------------

    def _classify_size(self, company: str) -> str:
        if not company or company == "Unknown":
            return "unknown"
        lo = company.lower()
        for size, keywords in self._sizes.items():
            if any(kw in lo for kw in keywords):
                return size
        return "unknown"

    # ------------------------------------------------------------------
    # Seniority
    # ------------------------------------------------------------------

    def _extract_years(self, title: str, description: str) -> float:
        lo = title.lower()
        for p in self._seniority_cfg["title_patterns"]:
            if re.search(p["pattern"], lo):
                return p["years"]
        text = (title + " " + description).lower()
        m = re.search(self._seniority_cfg["description_pattern"], text)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
        return self._seniority_cfg["default_years"]

    # ------------------------------------------------------------------
    # Remote detection
    # ------------------------------------------------------------------

    def _is_remote(self, location: str, description: str) -> bool:
        text = (location + " " + description[:500]).lower()
        return any(kw in text for kw in ["remote", "anywhere", "work from home", "wfh"])

    # ------------------------------------------------------------------
    # Date parsing
    # ------------------------------------------------------------------

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        try:
            from datetime import datetime
            return datetime.fromisoformat(date_str).isoformat()
        except (ValueError, TypeError):
            return date_str
