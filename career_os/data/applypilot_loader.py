"""
Load data from ApplyPilot database and convert to Career OS models.
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..models import Job, UserProfile, Skill, SkillLevel


class ApplyPilotLoader:
    """
    Load jobs from ApplyPilot SQLite database.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            db_path: Path to applypilot.db. If None, uses default location.
        """
        if db_path is None:
            # Default ApplyPilot location
            home = Path.home()
            db_path = home / ".applypilot" / "applypilot.db"

        self.db_path = db_path

        if not db_path.exists():
            raise FileNotFoundError(f"ApplyPilot database not found at {db_path}")

        print(f"Connected to ApplyPilot DB: {db_path}")

    def load_jobs(self, min_score: int = 7, limit: Optional[int] = None) -> List[Job]:
        """
        Load jobs from ApplyPilot database.

        Args:
            min_score: Minimum fit score to load
            limit: Maximum number of jobs to load

        Returns:
            List of Job objects
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name

        query = """
            SELECT
                url,
                title,
                location,
                COALESCE(full_description, description) AS description,
                fit_score,
                score_reasoning,
                site,
                salary,
                discovered_at,
                application_url
            FROM jobs
            WHERE fit_score >= ?
            ORDER BY fit_score DESC, discovered_at DESC
        """

        params = [min_score]

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

        jobs = []

        for row in rows:
            # Parse job data
            job = self._row_to_job(row)
            if job:
                jobs.append(job)

        conn.close()

        print(f"Loaded {len(jobs)} jobs from ApplyPilot (score >= {min_score})")

        return jobs

    def _row_to_job(self, row: sqlite3.Row) -> Optional[Job]:
        """
        Convert database row to Job object.

        Args:
            row: SQLite row

        Returns:
            Job object or None if parsing fails
        """
        try:
            # Extract basic info
            url = row['url']
            title = row['title'] or "Unknown"
            location = row['location'] or "Unknown"
            description = row['description'] or ""

            # Extract company from title, URL, application URL, or description
            company = self._extract_company(title, url, row['application_url'], description)

            # Date
            date_posted = None
            if row['discovered_at']:
                try:
                    date_posted = datetime.fromisoformat(row['discovered_at'])
                except ValueError:
                    pass

            # ApplyPilot fit score
            applypilot_score = row['fit_score']

            # Site/source
            source = row['site'] or "unknown"

            # Remote
            remote = self._is_remote(location, description)

            # Salary
            salary_min, salary_max = self._parse_salary(row['salary'])

            # Company size (heuristic from company name)
            company_size = self._guess_company_size(company)

            # Required skills (extract from description)
            required_skills = self._extract_skills(description, title)

            # Required years (heuristic from title/description)
            required_years = self._extract_required_years(title, description)

            # Visa sponsorship (heuristic)
            sponsors_visa = remote  # Remote jobs more likely to sponsor

            return Job(
                id=url,  # Use URL as unique ID
                title=title,
                company=company,
                description=description,
                url=url,
                location=location,
                remote=remote,
                required_skills=required_skills,
                required_years=required_years,
                salary_min=salary_min,
                salary_max=salary_max,
                company_size=company_size,
                sponsors_visa=sponsors_visa,
                posted_date=date_posted,
                source=source,
                fit_score=float(applypilot_score) if applypilot_score else None
            )

        except Exception as e:
            print(f"Warning: Failed to parse job {row.get('url', 'unknown')}: {e}")
            return None

    # Known ATS/job-board domains that never identify the employer in the URL.
    _KNOWN_ATS_DOMAINS = (
        'greenhouse.io', 'grnh.se', 'lever.co', 'indeed.com', 'linkedin.com',
        'glassdoor.com', 'workday.com', 'myworkdayjobs.com', 'ashbyhq.com',
        'bamboohr.com', 'smartrecruiters.com', 'icims.com', 'jobvite.com',
    )

    # Generic words the description regexes below sometimes capture instead
    # of an actual company name (e.g. "About This Role", "Join Us").
    _COMPANY_BLOCKLIST = {
        'this', 'us', 'our', 'we', 'the', 'about', 'a', 'an', 'our client',
        'this role', 'this position', 'this job', 'this team', 'build',
        'i', 'you', 'they', 'it', 'our team', 'our company',
    }

    def _extract_company(self, title: str, url: str,
                          application_url: Optional[str] = None,
                          description: str = "") -> str:
        """
        Extract company name from title, URL, application URL, or description.

        None of these are reliable alone - most postings in practice (esp.
        $/hr contractor listings via evaluation platforms) simply don't name
        the employer anywhere ApplyPilot stores. This tries several signals
        in order and falls back to "Unknown" rather than guessing.
        """
        # LinkedIn job postings sometimes link the employer's own page
        if 'linkedin.com' in url:
            match = re.search(r'/company/([^/]+)', url)
            if match:
                return match.group(1).replace('-', ' ').title()

        # "Title - Company" or "Title at Company"
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) >= 2:
                return parts[-1].strip()

        if ' at ' in title:
            parts = title.split(' at ')
            if len(parts) >= 2:
                return parts[-1].strip()

        # The apply link sometimes goes straight to the employer's own
        # domain (e.g. https://digitalharborfoundation.org/apply/...) rather
        # than a generic ATS - extract the registrable domain as a last resort.
        if application_url:
            domain_match = re.search(r'https?://(?:www\.)?([a-z0-9\-]+)\.[a-z.]+',
                                      application_url, re.IGNORECASE)
            if domain_match:
                domain = domain_match.group(0)
                if not any(ats in domain.lower() for ats in self._KNOWN_ATS_DOMAINS):
                    return domain_match.group(1).replace('-', ' ').title()

        # Common description openers: "At Acme, we build..." / "Join Acme!"
        if description:
            text = description[:600]
            patterns = [
                r'^At ([A-Z][\w&.,\'’\-]*(?:\s+[A-Z][\w&.,\'’\-]*){0,4}),\s+we',
                r'\bJoin ([A-Z][\w&.,\'’\-]*(?:\s+[A-Z][\w&.,\'’\-]*){0,4})[\s,!.]',
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    candidate = match.group(1).strip().rstrip('.,')
                    if candidate.lower() not in self._COMPANY_BLOCKLIST and len(candidate) > 1:
                        return candidate

        # No reliable signal found - be honest about it rather than guessing
        return "Unknown"

    def _is_remote(self, location: str, description: str) -> bool:
        """Check if job is remote."""
        text = (location + " " + description).lower()

        remote_keywords = ['remote', 'anywhere', 'work from home', 'wfh']

        for keyword in remote_keywords:
            if keyword in text:
                return True

        return False

    def _parse_salary(self, salary_str: Optional[str]) -> tuple[Optional[int], Optional[int]]:
        """
        Parse salary string.

        Args:
            salary_str: Salary string from DB

        Returns:
            (min, max) tuple
        """
        if not salary_str:
            return None, None

        # Extract numbers
        numbers = re.findall(r'\d+', salary_str.replace(',', ''))

        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), None

        return None, None

    def _guess_company_size(self, company: str) -> str:
        """
        Guess company size from name.

        Args:
            company: Company name

        Returns:
            Size category
        """
        company_lower = company.lower()

        # Big tech
        big_tech = ['google', 'meta', 'amazon', 'apple', 'microsoft', 'netflix',
                   'openai', 'anthropic', 'facebook']

        if any(name in company_lower for name in big_tech):
            return "big_tech"

        # Default
        return "unknown"

    # Headings that typically introduce the actual requirements, as opposed
    # to company-overview or benefits paragraphs that happen to namedrop
    # tools the candidate would use day-to-day but didn't ask for.
    _REQUIREMENTS_HEADING_RE = re.compile(
        r'(requirements?|qualifications?|what you.?ll need|skills?( required)?'
        r'|tech stack|you have|must have)\s*:?\s*\n',
        re.IGNORECASE
    )

    def _extract_skills(self, description: str, title: str) -> List[str]:
        """
        Extract required skills from description.

        When the posting has an identifiable "Requirements"/"Qualifications"/
        etc. section, only that section is scanned for skill keywords - this
        avoids picking up tools mentioned in passing (company's tech stack,
        "nice to have"s buried in a benefits blurb) as if they were required.
        About 35% of real postings have such a heading; the rest fall back to
        scanning the full text, which is noisier but better than nothing.

        Args:
            description: Job description
            title: Job title

        Returns:
            List of skill names
        """
        heading_match = self._REQUIREMENTS_HEADING_RE.search(description)
        if heading_match:
            # Scan from the heading to the next blank-line-delimited heading
            # (or end of text), capped so a missing closing boundary can't
            # pull in the rest of the posting.
            section = description[heading_match.end():heading_match.end() + 1500]
            next_heading = re.search(r'\n[A-Z][^\n]{0,40}:?\s*\n', section)
            if next_heading:
                section = section[:next_heading.start()]
            text = (section + " " + title).lower()
        else:
            text = (description + " " + title).lower()

        # Common skills to look for
        skill_keywords = {
            'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'C++',
            'PyTorch', 'TensorFlow', 'scikit-learn', 'Keras',
            'React', 'Vue', 'Angular', 'Next.js',
            'FastAPI', 'Django', 'Flask', 'Spring Boot', 'Express.js',
            'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
            'Machine Learning', 'Deep Learning', 'Computer Vision', 'NLP',
            'LLM', 'AI', 'MLOps', 'Data Engineering'
        }

        found_skills = []

        for skill in skill_keywords:
            pattern = r'(?<![a-z0-9])' + re.escape(skill.lower()) + r'(?![a-z0-9])'
            if re.search(pattern, text):
                found_skills.append(skill)

        return found_skills

    def _extract_required_years(self, title: str, description: str) -> float:
        """
        Extract required years from title/description.

        Args:
            title: Job title
            description: Job description

        Returns:
            Required years (default 2.0)
        """
        text = (title + " " + description).lower()

        # Check for seniority in title
        if "senior" in title.lower() or "sr." in title.lower():
            return 5.0
        elif "junior" in title.lower() or "jr." in title.lower():
            return 1.0
        elif "lead" in title.lower() or "principal" in title.lower():
            return 7.0

        # Look for "X years" or "X+ years"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))

        # Default
        return 2.0


# Skill proficiency levels and AI-dependency multipliers aren't part of
# config.yaml's schema (candidate.core_skills is a flat list of names) - they
# require a hand-assessed judgment call this dict captures. Any skill listed
# in config.yaml that isn't covered here falls back to _DEFAULT_SKILL_PROFILE.
_SKILL_PROFILES: Dict[str, Tuple[SkillLevel, float, List[str]]] = {
    "AI": (SkillLevel.WORKING, 0.7, ["ML systems, LLM integrations"]),
    "Machine Learning": (SkillLevel.WORKING, 0.7, ["YOLOv8 production system"]),
    "Deep Learning": (SkillLevel.WORKING, 0.7, []),
    "Computer Vision": (SkillLevel.WORKING, 0.7, ["92% mAP on edge devices"]),
    "PyTorch": (SkillLevel.WORKING, 0.7, ["Fine-tuned models, custom pipelines"]),
    "YOLOv8": (SkillLevel.WORKING, 0.7, []),
    "OpenCV": (SkillLevel.WORKING, 0.6, []),
    "Python": (SkillLevel.INDEPENDENT, 0.8, ["Multiple production projects"]),
    "FastAPI": (SkillLevel.WORKING, 0.6, []),
    "REST API": (SkillLevel.WORKING, 0.7, []),
    "gRPC": (SkillLevel.AI_ASSISTED, 0.5, []),
    "Docker": (SkillLevel.WORKING, 0.5, ["Containerized ML apps"]),
    "AWS": (SkillLevel.AI_ASSISTED, 0.4, []),
    "Kubernetes": (SkillLevel.AI_ASSISTED, 0.3, []),
    "Rust": (SkillLevel.WORKING, 0.6, ["Sentropy Engine"]),
    "Java": (SkillLevel.AI_ASSISTED, 0.4, []),
    "Go": (SkillLevel.AI_ASSISTED, 0.3, []),
    "React": (SkillLevel.AI_ASSISTED, 0.3, []),
    "Next.js": (SkillLevel.AI_ASSISTED, 0.3, []),
    "TypeScript": (SkillLevel.AI_ASSISTED, 0.4, []),
    "LLM": (SkillLevel.WORKING, 0.6, []),
    "NLP": (SkillLevel.WORKING, 0.6, []),
}
_DEFAULT_SKILL_PROFILE: Tuple[SkillLevel, float, List[str]] = (SkillLevel.WORKING, 0.6, [])


def _find_config_path() -> Optional[Path]:
    """Look for config.yaml at the project root, then ~/.applypilot/."""
    project_config = Path(__file__).parent.parent.parent / "config.yaml"
    if project_config.exists():
        return project_config

    home_config = Path.home() / ".applypilot" / "config.yaml"
    if home_config.exists():
        return home_config

    return None


def create_user_profile_from_config() -> UserProfile:
    """
    Build a UserProfile from config.yaml's `candidate` section.

    Contact info, years of experience, target roles, salary range, and
    sponsorship/remote preferences come directly from config.yaml. Skill
    proficiency levels come from _SKILL_PROFILES above, since config.yaml
    only stores skill names, not levels.

    Raises:
        FileNotFoundError: if config.yaml isn't found at the project root
            or in ~/.applypilot/.
    """
    import yaml
    from ..models import UserPreferences

    config_path = _find_config_path()
    if config_path is None:
        raise FileNotFoundError(
            "config.yaml not found at project root or ~/.applypilot/config.yaml"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    candidate = config.get("candidate", {})
    job_search = config.get("job_search", {})

    skills = []
    for skill_name in candidate.get("core_skills", []):
        level, ai_multiplier, evidence = _SKILL_PROFILES.get(skill_name, _DEFAULT_SKILL_PROFILE)
        skills.append(Skill(skill_name, level, ai_multiplier=ai_multiplier, evidence=list(evidence)))

    # Target roles in config.yaml are a single comma-separated string
    # ("ML Engineer, Backend Engineer, ..."); target_roles needs a list.
    target_role_field = candidate.get("target_role", "")
    target_roles = [r.strip() for r in target_role_field.split(",") if r.strip()]

    resume_path = Path(__file__).parent.parent.parent / "personal" / f"{candidate.get('name', '').replace(' ', '_')}.txt"
    if resume_path.exists():
        resume_text = resume_path.read_text(encoding="utf-8")
    else:
        resume_text = (
            f"{candidate.get('current_title', 'Engineer')} with "
            f"{candidate.get('years_experience', 0)} years of experience."
        )

    remote_only = bool(job_search.get("remote_only", True))

    return UserProfile(
        name=candidate.get("name", "Unknown"),
        email=candidate.get("email", ""),
        years_experience=float(candidate.get("years_experience", 0)),
        ai_proficiency=0.8,  # not in config.yaml's schema; reasonable default
        skills=skills,
        experience=[],
        target_roles=target_roles,
        target_domains=[],
        resume_text=resume_text,
        preferences=UserPreferences(
            remote=remote_only,
            hybrid_acceptable=True,
            onsite_acceptable=not remote_only,
            work_visa_required=bool(candidate.get("needs_sponsorship", False)),
            min_salary=candidate.get("salary_min"),
            max_salary=candidate.get("salary_max"),
            preferred_company_sizes=["startup", "midsize"],
        )
    )
