"""
ApplyPilot adapter — normalizes raw DB rows to canonical Job schema.

Config-driven from infra/config/plugins.yaml (column map, company and salary
rules); skills, seniority, remote and size come from careeros.jobs.extraction:
  - Company name (from URL, title, application_url, description)
  - Skills (keyword matching with optional requirements-section scoping)
  - Salary parsing (configurable regex patterns)
  - Company size classification
  - Seniority / required-years detection
  - Remote detection
"""

import re
from typing import Any, Dict, Optional, Tuple

from careeros.jobs.extraction import TextExtractor


class ApplyPilotAdapter:
    """Normalizes ApplyPilot raw rows to canonical Job schema."""

    _ATS_PATH_RE = re.compile(
        r"(?:greenhouse\.io|lever\.co|ashbyhq\.com|teamtailor\.com|smartrecruiters\.com)"
        r"/(?:jobs/|careers/)?([a-z0-9\-]{2,40})(?:[/?#]|$)",
        re.IGNORECASE,
    )
    _ATS_SUBDOMAIN_RE = re.compile(
        r"https?://(?:www\.)?([a-z0-9\-]{2,40})\."
        r"(?:wd\d+\.myworkdayjobs\.com|myworkdaysite\.com|workday\.com|"
        r"greenhouse\.io|lever\.co|ashbyhq\.com|smartrecruiters\.com|bamboohr\.com)",
        re.IGNORECASE,
    )
    _SKIP_SLUGS = {"jobs", "boards", "www", "careers", "login", "apply", "jobsheet"}

    _LOCATION_HEADING_RE = re.compile(
        r"(?:location|based in|headquarters|hq|work location|office|located in)\s*[:\-–]?\s*([^\n.;]{3,60})",
        re.IGNORECASE,
    )
    _COUNTRIES = [
        "United States", "Canada", "Germany", "United Kingdom", "France", "Netherlands",
        "Japan", "Singapore", "Australia", "Switzerland", "Sweden", "Poland", "Turkey",
        "India", "Brazil", "Spain", "Portugal", "Italy", "Austria", "Belgium", "Ireland",
        "Uzbekistan", "Kazakhstan", "Azerbaijan", "Georgia", "New Zealand", "Vietnam",
        "Indonesia", "Thailand", "Malaysia", "Philippines", "Ukraine", "United Arab Emirates",
    ]

    def _prettify_slug(self, slug: str) -> str:
        slug = slug.replace("-", " ").replace("_", " ")
        slug = re.sub(r"([a-z])([A-Z])", r"\1 \2", slug)
        return slug.strip().title()

    def _extract_location(self, description: str, title: str = "") -> str:
        if not description:
            description = ""
        m = self._LOCATION_HEADING_RE.search(description[:2000])
        if m:
            return m.group(1).strip()

        # Fallback: search title then description for country name keywords
        search_text = (title + " " + description[:1000]).lower()
        for c in self._COUNTRIES:
            if c.lower() in search_text:
                return c
        return ""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._col = config["columns"]
        self._company_cfg = config["company_extraction"]
        self._salary_patterns = config["salary_patterns"]
        self._text = TextExtractor()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        url = row.get(self._col["url"], "") or ""
        title = row.get(self._col["title"]) or "Unknown"
        description = (
            row.get(self._col["full_description"])
            or row.get(self._col["description"])
            or ""
        )
        company = (row.get(self._col["company"]) or "").strip()
        if not company or company.lower() == "unknown":
            company = self._extract_company(
                title,
                url,
                row.get(self._col["application_url"]),
                description,
            )

        location = (row.get(self._col["location"]) or "").strip()
        if not location or location.lower() == "unknown":
            location = self._extract_location(description, title) or "Unknown"

        remote = self._text.is_remote(location, description)
        remote_region = self._text.remote_region(location, description) if remote else None
        salary_min, salary_max = self._parse_salary(row.get(self._col["salary"]))
        company_size = self._text.company_size(company)
        required_skills = self._text.skills(description, title)
        required_years = self._text.required_years(title, description)
        posted_date = self._parse_date(row.get(self._col["discovered_at"]))

        raw_score = row.get(self._col["fit_score"])

        return {
            "url": url,
            "title": title,
            "company": company,
            "description": description,
            "location": location,
            "remote": remote,
            "remote_region": remote_region,
            "required_skills": required_skills,
            "preferred_skills": [],
            "required_years": required_years,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "company_size": company_size,
            "sponsors_visa": self._text.sponsors_visa(description),
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

        # 4a. ATS URL → company slug (subdomain veya path)
        for target_url in [application_url, url]:
            if target_url:
                for rx in (self._ATS_PATH_RE, self._ATS_SUBDOMAIN_RE):
                    m = rx.search(target_url)
                    if m and m.group(1).lower() not in self._SKIP_SLUGS:
                        return self._prettify_slug(m.group(1))

        # 4. Application URL domain (non-ATS)
        for target_url in [application_url, url]:
            if target_url:
                m = re.search(
                    r"https?://(?:www\.)?([a-z0-9\-]+)\.[a-z.]+",
                    target_url,
                    re.IGNORECASE,
                )
                if m:
                    full_url = m.group(0).lower()
                    if not any(
                        ats in full_url
                        for ats in self._company_cfg["ats_domains"]
                    ):
                        return m.group(1).replace("-", " ").title()

        # 5. Description patterns
        if description:
            # Clean formatting for matching
            clean_desc = description.replace("**", "").replace("*", "").strip()

            # Pattern A: "About [Company]" or "Who We Are: [Company]"
            m = re.search(
                r"(?:^|\n)(?:About|Who We Are|Who is)\s+([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,3})",
                clean_desc[:1000],
                re.IGNORECASE,
            )
            if m:
                candidate = m.group(1).strip().rstrip(".,:")
                if candidate.lower() not in blocklist and len(candidate) > 1:
                    return candidate

            # Pattern B: Start of description "[Company] is a / was born / was founded"
            m = re.search(
                r"^([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,3})\s+(?:is\s+(?:a|pioneer|on\s+a|looking|dedicated)|was\s+(?:born|founded))",
                clean_desc[:300],
            )
            if m:
                candidate = m.group(1).strip().rstrip(".,")
                if candidate.lower() not in blocklist and len(candidate) > 1:
                    return candidate

            # Pattern C: "At [Company], we..." or "Join [Company]!"
            for pattern in [
                r"\bAt ([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,4}),\s+we",
                r"\bJoin ([A-Z][\w&.,'\-]*(?:\s+[A-Z][\w&.,'\-]*){0,4})[\s,!.]",
            ]:
                m = re.search(pattern, clean_desc[:600])
                if m:
                    candidate = m.group(1).strip().rstrip(".,")
                    if candidate.lower() not in blocklist and len(candidate) > 1:
                        return candidate

        return "Unknown"

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
