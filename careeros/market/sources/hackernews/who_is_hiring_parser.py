"""Parse job postings from HN 'Who is hiring?' comments."""

import re
from typing import Dict, List

from careeros.shared.text import sponsorship_stance, word_pattern


_SKILL_KEYWORDS = [
    # ── Engineering / Backend ─────────────────────────────────────────────
    "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "Elixir", "Haskell",
    "Django", "FastAPI", "Flask", "Rails", "Spring", "Laravel", "Express",
    "GraphQL", "gRPC", "REST", "WebSockets",
    # ── Frontend ─────────────────────────────────────────────────────────
    "React", "Vue", "Angular", "Next.js", "Svelte", "Nuxt", "Remix",
    "Tailwind", "CSS", "HTML", "WebAssembly",
    # ── Mobile ───────────────────────────────────────────────────────────
    "React Native", "Flutter", "SwiftUI", "Jetpack Compose", "iOS", "Android",
    # ── Cloud / DevOps ────────────────────────────────────────────────────
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "Pulumi",
    "CI/CD", "GitHub Actions", "Jenkins", "Ansible", "Helm",
    # ── Data / ML ─────────────────────────────────────────────────────────
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "Elasticsearch",
    "Spark", "Databricks", "dbt", "Airflow", "Snowflake", "BigQuery",
    "PyTorch", "TensorFlow", "scikit-learn", "LLM", "RAG", "MLOps",
    "Machine Learning", "Deep Learning", "Computer Vision", "NLP",
    "Hugging Face", "LangChain", "OpenAI", "Embeddings", "Vector DB",
    # ── Security ──────────────────────────────────────────────────────────
    "Penetration Testing", "SIEM", "SOC", "Zero Trust", "OAuth", "SAML",
    # ── Design / Creative ─────────────────────────────────────────────────
    "Figma", "Sketch", "Adobe CC", "Photoshop", "Illustrator", "After Effects",
    "Blender", "Unity", "Unreal Engine", "Design Systems", "Prototyping",
    "UX Research", "Wireframing", "Motion Design",
    # ── Marketing / Growth ────────────────────────────────────────────────
    "SEO", "SEM", "Google Analytics", "Growth Hacking", "Content Marketing",
    "Copywriting", "HubSpot", "Salesforce", "A/B Testing", "CRM",
    "Email Marketing", "Paid Ads", "Meta Ads", "Performance Marketing",
    # ── Medical / Science ─────────────────────────────────────────────────
    "Clinical Trials", "Patient Care", "ICU", "Oncology", "Radiology",
    "PCR", "CRISPR", "Genomics", "Bioinformatics", "Flow Cytometry",
    "GMP", "FDA Compliance", "Pharmacovigilance",
    # ── Legal / Finance / Ops ─────────────────────────────────────────────
    "Compliance", "Contract Law", "IP Law", "GAAP", "IFRS", "Auditing",
    "Six Sigma", "Lean", "Supply Chain", "Procurement", "FP&A",
    "Venture Capital", "Private Equity", "Financial Modeling",
    # ── Education / Research ──────────────────────────────────────────────
    "Curriculum Design", "LMS", "Pedagogy", "Grant Writing", "Peer Review",
    "Instructional Design", "E-learning",
]

_REMOTE_RE = re.compile(r'\b(remote|anywhere|work from home|wfh)\b', re.IGNORECASE)
_VISA_RE = re.compile(r'\b(visa|h1b|sponsor|sponsorship)\b', re.IGNORECASE)
_SKILL_PATTERNS = [(s, word_pattern(s)) for s in _SKILL_KEYWORDS]
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
        sponsors_visa = self._sponsors_visa(text)
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
        return [s for s, rx in _SKILL_PATTERNS if rx.search(text)]

    @staticmethod
    def _sponsors_visa(text: str) -> bool:
        """"No visa sponsorship" is a no; on HN a bare "VISA" / "H1B" in the header means yes."""
        stance = sponsorship_stance(text)
        return stance if stance is not None else bool(_VISA_RE.search(text))
