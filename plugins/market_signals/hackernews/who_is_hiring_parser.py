"""Parse job postings from HN 'Who is hiring?' comments."""

import re
from typing import Dict, List


_SKILL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#",
    "React", "Vue", "Angular", "Node.js", "Django", "FastAPI", "Flask",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "Elasticsearch",
    "PyTorch", "TensorFlow", "scikit-learn", "LLM", "RAG", "MLOps",
    "Machine Learning", "Deep Learning", "Computer Vision", "NLP",
    "GraphQL", "gRPC", "Spark", "Scala", "Databricks",
]

_REMOTE_RE = re.compile(r'\b(remote|anywhere|work from home|wfh)\b', re.IGNORECASE)
_VISA_RE = re.compile(r'\b(visa|h1b|sponsor|sponsorship)\b', re.IGNORECASE)
_HTML_RE = re.compile(r'<[^>]+>')
_ENTITY_RE = re.compile(r'&[a-z#0-9]+;')


class WhoIsHiringParser:
    def parse_comment(self, comment: Dict) -> Dict:
        text = comment.get("text", "")
        if not text:
            return {}

        text = self._clean_html(text)

        company = self._extract_company(text)
        role = self._extract_role(text)
        remote = bool(_REMOTE_RE.search(text))
        sponsors_visa = bool(_VISA_RE.search(text))
        skills = self._extract_skills(text)

        comment_id = comment.get("id")
        url = f"https://news.ycombinator.com/item?id={comment_id}" if comment_id else None

        return {
            "company": company,
            "role": role,
            "remote": remote,
            "sponsors_visa": sponsors_visa,
            "skills": skills,
            "url": url,
            "description": text[:400],
        }

    def _clean_html(self, text: str) -> str:
        text = _HTML_RE.sub(" ", text)
        text = _ENTITY_RE.sub(" ", text)
        return re.sub(r'\s+', ' ', text).strip()

    def _extract_company(self, text: str) -> str:
        if "|" in text:
            return text.split("|")[0].strip()[:100]
        return text.split(".")[0].strip()[:100]

    def _extract_role(self, text: str) -> str:
        parts = text.split("|")
        if len(parts) >= 2:
            return parts[1].strip()[:100]
        for kw in ["Engineer", "Developer", "Scientist", "Manager", "Analyst"]:
            m = re.search(rf'[\w\s]{{0,20}}{kw}', text, re.IGNORECASE)
            if m:
                return m.group().strip()[:100]
        return "Software Engineer"

    def _extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        return [s for s in _SKILL_KEYWORDS if s.lower() in text_lower]
