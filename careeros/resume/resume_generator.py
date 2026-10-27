"""
Target-Aware Resume Generator.

Evidence > Claim in action: generates a resume tailored to a specific
target job, using evidence-backed skills from the Evidence Graph.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from careeros.db.connection import db
from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.resume.prompts import template_loader
from careeros.evidence.aggregation import aggregate_user_skills

from careeros.shared.config import ROOT
from careeros.shared.llm import get_llm_client

_TEMPLATES_DIR = Path(__file__).parent / "templates" / "resume"

logger = logging.getLogger(__name__)

_JSON_SYSTEM = "You are a career strategist. Always respond with valid JSON."
_TEXT_SYSTEM = "You are a career strategist applying the Evidence > Claim principle."


def build_project_list(items: List[Any]) -> List[dict]:
    """Project evidence items → the project dicts the resume prompts expect.

    GitHub projects carry real repo signals; resume/portfolio projects only a
    description and technologies. Metrics we do not have stay None — the
    templates skip them rather than show invented numbers.
    """
    projects = []
    for item in items:
        data = item.evidence_data or {}
        if data.get("type") != "project":
            continue
        code_bytes = data.get("code_bytes")
        projects.append({
            "name": item.skill_name,
            "source": item.source,
            "technologies": data.get("technologies") or [],
            "author_commit_count": None,  # not known per author; never estimate on a resume
            "github_url": item.source_url if item.source == "github" else None,
            "github_details": {
                "stars": data.get("stars", 0),
                "language": data.get("language"),
                "topics": data.get("topics") or [],
                "description": data.get("description") or "",
                "size": f"{code_bytes // 1024:,} KB of code" if code_bytes else None,
                "has_tests": data.get("has_tests"),
                "has_docs": data.get("has_docs"),
                "has_releases": data.get("has_releases"),
            },
        })
    projects.sort(key=lambda p: (p["source"] != "github", -(p["github_details"]["stars"] or 0)))
    return projects


def build_skill_evidence(aggregated: List[dict], projects: List[dict], per_skill: int = 3) -> Dict[str, dict]:
    """{skill: {"confidence", "evidence_list"}} — each skill linked to projects that used it."""
    evidence: Dict[str, dict] = {}
    for agg in aggregated:
        skill = agg["skill_name"]
        related = [p for p in projects if skill.lower() in {t.lower() for t in p["technologies"]}]
        evidence[skill] = {
            "confidence": agg["aggregated_confidence"],
            "evidence_list": [
                {
                    "project_name": p["name"],
                    "author_commits": None,
                    "stars": p["github_details"]["stars"],
                    "github_url": p["github_url"],
                    "loc_count": None,
                    "language": p["github_details"]["language"],
                    "topics": p["github_details"]["topics"],
                    "has_tests": p["github_details"]["has_tests"],
                    "has_docs": p["github_details"]["has_docs"],
                    "has_releases": p["github_details"]["has_releases"],
                    "pr_count": None,
                    "issue_count": None,
                }
                for p in related[:per_skill]
            ],
        }
    return evidence


class ResumeGenerator:
    """
    Generates target-aware resumes using Evidence Graph + LLM.

    Workflow:
    1. Load the user's evidence_items (skills + projects, all sources)
    2. Extract job priorities (LLM)
    3. Select best evidence (LLM)
    4. Rank projects (LLM)
    5. Generate 2-line summary (LLM)
    6. Render Markdown template
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.llm = get_llm_client()

    def generate(
        self,
        target_company: str,
        target_title: str,
        template_name: str,
        job_description: str = "",
        candidate_info: Optional[dict] = None,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate a target-aware resume.

        Args:
            target_company: Company name (e.g., "Google")
            target_title: Role title (e.g., "ML Engineer")
            template_name: "ml_research" or "backend"
            job_description: Optional full JD for deeper analysis
            candidate_info: Optional candidate metadata
            output_path: Where to save the Markdown

        Returns:
            Path to generated Markdown file
        """
        logger.info("Generating resume: %s @ %s (template=%s)", target_title, target_company, template_name)

        logger.info("[1/5] Loading evidence (skills + projects)")
        evidence, projects = self._load_evidence()
        logger.info("  %d skills, %d projects", len(evidence), len(projects))

        logger.info("[2/5] Extracting job priorities (LLM)")
        priorities = self._extract_priorities(target_title, target_company, job_description)
        logger.info("  must_have=%s", priorities.get("must_have", []))

        logger.info("[3/5] Tailoring evidence for target (LLM)")
        tailoring = self._tailor_evidence(target_company, target_title, priorities, evidence, projects)
        logger.info("  emphasized=%s", tailoring.get("emphasized_skills", []))

        logger.info("[4/5] Selecting best projects (LLM)")
        project_selection = self._select_projects(target_company, target_title, projects)
        selected = project_selection.get("selected", [])
        for p in selected:
            logger.info("  - %s: %s", p.get("name"), p.get("score", 0))

        logger.info("[5/5] Generating 2-line summary (LLM)")
        candidate_info = candidate_info or self._default_candidate_info()
        summary = self._generate_summary(
            target_company, target_title, candidate_info,
            tailoring.get("emphasized_skills", []),
            selected,
        )
        logger.info("  %s...", summary[:80])

        logger.info("Rendering Markdown")
        markdown = self._render_template(
            template_name=template_name,
            target_company=target_company,
            target_title=target_title,
            candidate=candidate_info,
            summary=summary,
            emphasized_skills=tailoring.get("emphasized_skills", []),
            selected_projects=selected,
            evidence=evidence,
            priorities=priorities,
        )

        if output_path is None:
            slug = f"{target_company}_{target_title}".replace(" ", "_")
            name = candidate_info.get("name", "User").replace(" ", "_")
            output_path = ROOT / "personal" / f"{name}_{slug}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        logger.info("Resume saved: %s (%d chars)", output_path, len(markdown))
        return output_path

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_evidence(self) -> tuple[Dict[str, dict], List[dict]]:
        """This user's evidence from `evidence_items`, shaped for the prompts/templates."""
        with db.session_scope() as session:
            aggregated = aggregate_user_skills(self.user_id, session)
            items = session.query(EvidenceItem).filter(EvidenceItem.user_id == self.user_id).all()
            projects = build_project_list(items)
        return build_skill_evidence(aggregated, projects), projects

    def _default_candidate_info(self) -> dict:
        from careeros.shared.config import load_config
        config = load_config()
        c = config.get("candidate", {})
        return {
            "name": c.get("name", "User"),
            "email": c.get("email", ""),
            "github": c.get("github", ""),
            "linkedin": c.get("linkedin", ""),
            "years_experience": c.get("years_experience", 0),
            "education": c.get("education", ""),
            "current_title": c.get("current_title", ""),
        }

    # ------------------------------------------------------------------
    # LLM calls
    # ------------------------------------------------------------------

    # Role-type keyword → inferred domain hints for when no JD is provided.
    _ROLE_HINTS = {
        "backend": "API design, REST/gRPC, distributed systems, reliability, scalability, SQL/NoSQL databases.",
        "frontend": "React/Vue, TypeScript, CSS, performance optimization, accessibility.",
        "fullstack": "frontend frameworks, REST APIs, databases, CI/CD.",
        "ml engineer": "model training, PyTorch/TensorFlow, data pipelines, production ML serving.",
        "machine learning": "model training, PyTorch/TensorFlow, feature engineering, experiment tracking.",
        "data engineer": "data pipelines, Spark/Kafka, SQL, ETL, cloud data platforms.",
        "platform": "distributed systems, Kubernetes, infrastructure automation, observability.",
        "infrastructure": "Kubernetes, Terraform, CI/CD, cloud (AWS/GCP/Azure), SRE.",
        "devops": "CI/CD, Docker, Kubernetes, monitoring, IaC.",
        "security": "threat modeling, pentesting, encryption, compliance.",
    }

    def _role_hint(self, title: str) -> str:
        t = title.lower()
        for kw, hint in self._ROLE_HINTS.items():
            if kw in t:
                return hint
        return "general software engineering skills relevant to the role and company domain."

    def _extract_priorities(self, title: str, company: str, description: str) -> dict:
        if not description:
            hint = self._role_hint(title)
            description = (
                f"{title} role at {company}. "
                f"Infer typical requirements for this role type. "
                f"Focus on: {hint}"
            )
        prompt = template_loader.render(
            "job/extract_priorities.jinja",
            job_title=title,
            job_company=company,
            job_description=description,
        )
        return self._llm_json(prompt)

    def _llm_json(self, prompt: str) -> dict:
        return self.llm.complete_json(prompt, system=_JSON_SYSTEM, json_mode=True, max_tokens=2000)

    def _tailor_evidence(self, company, title, priorities, evidence, projects) -> dict:
        prompt = template_loader.render(
            "resume/tailor_for_target.jinja",
            target_company=company,
            target_title=title,
            required_skills=priorities.get("must_have", []),
            preferred_skills=priorities.get("important", []),
            culture_signals=priorities.get("culture_signals", []),
            role_hint=self._role_hint(title),
            job_description=priorities.get("summary", ""),
            evidence=evidence,
            projects=projects,
            available_skills=list(evidence.keys()),
        )
        result = self._llm_json(prompt)
        return self._normalize_skill_names(result, evidence)

    def _normalize_skill_names(self, tailoring: dict, evidence: dict) -> dict:
        """Map LLM-returned skill names to actual keys in the evidence graph."""
        available = set(evidence.keys())
        available_lower = {s.lower(): s for s in available}
        mappings = tailoring.get("skill_mappings", {})

        def resolve(skill: str):
            if skill in available:
                return skill
            if skill.lower() in available_lower:
                return available_lower[skill.lower()]
            if skill in mappings and mappings[skill] in available:
                return mappings[skill]
            sl = skill.lower()
            for real in available:
                if sl in real.lower() or real.lower() in sl:
                    return real
            return None

        normalized = []
        for s in tailoring.get("emphasized_skills", []):
            r = resolve(s)
            if r and r not in normalized:
                normalized.append(r)

        # If the LLM returned nothing usable, fall back to top-confidence skills
        if not normalized:
            normalized = sorted(available, key=lambda k: evidence[k]["confidence"], reverse=True)[:5]

        tailoring["emphasized_skills"] = normalized
        tailoring["de_emphasized_skills"] = [
            r for s in tailoring.get("de_emphasized_skills", [])
            if (r := resolve(s))
        ]
        return tailoring

    def _select_projects(self, company, title, projects) -> dict:
        if not projects:
            return {"selected": [], "rejected": []}
        prompt = template_loader.render(
            "resume/select_projects.jinja",
            target_company=company,
            target_title=title,
            max_projects=4,
            projects=projects,
        )
        return self._llm_json(prompt)

    def _generate_summary(self, company, title, candidate, emphasized_skills, selected_projects) -> str:
        top_skills = {skill: 0.85 for skill in emphasized_skills[:4]}
        featured = []
        for p in selected_projects[:3]:
            highlight = " | ".join(p.get("key_bullets", [])[:2])
            featured.append({
                "name": p.get("name", ""),
                "highlight": highlight or p.get("reasoning", ""),
            })

        prompt = template_loader.render(
            "resume/generate_summary.jinja",
            target_company=company,
            target_title=title,
            role_hint=self._role_hint(title),
            candidate_name=candidate.get("name", ""),
            years_experience=candidate.get("years_experience", 0),
            education=candidate.get("education", ""),
            top_skills=top_skills,
            featured_projects=featured,
        )
        return self.llm.complete(prompt, system=_TEXT_SYSTEM, temperature=0.5, max_tokens=200)

    # ------------------------------------------------------------------
    # Template rendering
    # ------------------------------------------------------------------

    def _render_template(
        self,
        template_name: str,
        target_company: str,
        target_title: str,
        candidate: dict,
        summary: str,
        emphasized_skills: List[str],
        selected_projects: List[dict],
        evidence: dict,
        priorities: dict,
    ) -> str:
        from jinja2 import Environment, FileSystemLoader

        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(
            f"{template_name}.md.jinja"
        )
        return template.render(
            target_company=target_company,
            target_title=target_title,
            candidate=candidate,
            summary=summary,
            emphasized_skills=emphasized_skills,
            selected_projects=selected_projects,
            evidence=evidence,
            priorities=priorities,
        )


def generate_resume(
    target_company: str,
    target_title: str,
    template_name: str = "ml_research",
    job_description: str = "",
    user_id: str = "default",
) -> Path:
    """Convenience function."""
    return ResumeGenerator(user_id=user_id).generate(
        target_company=target_company,
        target_title=target_title,
        template_name=template_name,
        job_description=job_description,
    )
