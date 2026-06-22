"""
Load data from ApplyPilot database and convert to Career OS models.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
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

        print(f"✓ Connected to ApplyPilot DB: {db_path}")

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
                description,
                fit_score,
                score_reasoning,
                site,
                salary,
                discovered_at
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

        print(f"✓ Loaded {len(jobs)} jobs from ApplyPilot (score >= {min_score})")

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

            # Extract company from title or URL
            company = self._extract_company(title, url)

            # Date
            date_posted = None
            if row['discovered_at']:
                try:
                    date_posted = datetime.fromisoformat(row['discovered_at'])
                except:
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

    def _extract_company(self, title: str, url: str) -> str:
        """Extract company name from title or URL."""
        # Try to extract from URL (linkedin.com/company/xyz)
        import re

        if 'linkedin.com' in url:
            match = re.search(r'/company/([^/]+)', url)
            if match:
                return match.group(1).replace('-', ' ').title()

        # Try to extract from title (often "Title - Company" or "Title at Company")
        if ' - ' in title:
            parts = title.split(' - ')
            if len(parts) >= 2:
                return parts[-1].strip()

        if ' at ' in title:
            parts = title.split(' at ')
            if len(parts) >= 2:
                return parts[-1].strip()

        # Default
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

        import re

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

    def _extract_skills(self, description: str, title: str) -> List[str]:
        """
        Extract required skills from description.

        Args:
            description: Job description
            title: Job title

        Returns:
            List of skill names
        """
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
            if skill.lower() in text:
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
        import re

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


def create_user_profile_from_config() -> UserProfile:
    """
    Create user profile from your actual skills.

    TODO: Could load from config.yaml or resume.txt
    For now, hardcoded based on your background.
    """
    from ..models import Experience, UserPreferences

    return UserProfile(
        name="Abdullokh Abdukodirov",
        email="abdullahabdulkadir0@gmail.com",
        years_experience=2.0,
        ai_proficiency=0.8,  # High AI usage
        skills=[
            # ML/AI - Core strengths
            Skill("Machine Learning", SkillLevel.WORKING, ai_multiplier=0.7,
                  evidence=["YOLOv8 production system"]),
            Skill("Deep Learning", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("Computer Vision", SkillLevel.WORKING, ai_multiplier=0.7,
                  evidence=["92% mAP on edge devices"]),
            Skill("PyTorch", SkillLevel.WORKING, ai_multiplier=0.7,
                  evidence=["Fine-tuned models, custom pipelines"]),
            Skill("YOLOv8", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("OpenCV", SkillLevel.WORKING, ai_multiplier=0.6),

            # Programming - Strong
            Skill("Python", SkillLevel.INDEPENDENT, ai_multiplier=0.8,
                  evidence=["Multiple production projects"]),

            # Backend - Moderate
            Skill("FastAPI", SkillLevel.WORKING, ai_multiplier=0.6),
            Skill("REST API", SkillLevel.WORKING, ai_multiplier=0.7),
            Skill("gRPC", SkillLevel.AI_ASSISTED, ai_multiplier=0.5),

            # Infrastructure - Learning
            Skill("Docker", SkillLevel.WORKING, ai_multiplier=0.5,
                  evidence=["Containerized ML apps"]),
            Skill("AWS", SkillLevel.AI_ASSISTED, ai_multiplier=0.4),
            Skill("Kubernetes", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),

            # Other languages - Varied
            Skill("Rust", SkillLevel.WORKING, ai_multiplier=0.6,
                  evidence=["Sentropy Engine"]),
            Skill("Java", SkillLevel.AI_ASSISTED, ai_multiplier=0.4),
            Skill("Go", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),

            # Frontend - Basic
            Skill("React", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),
            Skill("Next.js", SkillLevel.AI_ASSISTED, ai_multiplier=0.3),
            Skill("TypeScript", SkillLevel.AI_ASSISTED, ai_multiplier=0.4),

            # LLM/AI - Growing
            Skill("LLM", SkillLevel.WORKING, ai_multiplier=0.6),
            Skill("AI", SkillLevel.WORKING, ai_multiplier=0.7),
        ],
        experience=[
            Experience(
                title="ML Engineer / Developer",
                company="KOU STORM UAV",
                description="Built YOLOv8 object detection system achieving 92% mAP on edge devices. Optimized inference to 40ms latency.",
                start_date=datetime(2023, 1, 1),
                achievements=[
                    "92% mAP accuracy on custom dataset",
                    "40ms inference latency on Raspberry Pi 5",
                    "Real-time detection at 20+ FPS"
                ],
                skills_used=["Python", "PyTorch", "Computer Vision", "YOLOv8", "OpenCV"]
            )
        ],
        target_roles=["ML Engineer", "AI Engineer", "Backend Engineer", "Full Stack Developer"],
        target_domains=["Machine Learning", "Computer Vision", "AI/ML"],
        resume_text="ML Engineer with 2 years experience in computer vision, deep learning, and production ML systems. Built YOLOv8 detection achieving 92% mAP on edge devices.",
        preferences=UserPreferences(
            remote=True,
            hybrid_acceptable=True,
            onsite_acceptable=False,
            work_visa_required=True,
            preferred_company_sizes=["startup", "midsize"],
        )
    )
