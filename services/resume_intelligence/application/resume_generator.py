"""
Target-Aware Resume Generator.

Evidence > Claim in action: generates a resume tailored to a specific
target job, using evidence-backed skills from the Evidence Graph.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from core.db.connection import db
from core.db.repositories import EvidenceRepository
from core.prompts import template_loader

from .llm_client import get_llm_client


class ResumeGenerator:
    """
    Generates target-aware resumes using Evidence Graph + LLM.

    Workflow:
    1. Load user's evidence (DB) + GitHub projects (cache)
    2. Extract job priorities (LLM)
    3. Select best evidence (LLM)
    4. Rank projects (LLM)
    5. Generate 2-line summary (LLM)
    6. Render Markdown template
    """

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.llm = get_llm_client()
        self.hiring_agent_dir = Path("services/hiring-agent")

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
        print(f"\n[ResumeGenerator] {target_title} @ {target_company}  template={template_name}")
        print("-" * 60)

        print("[1/5] Loading Evidence Graph + GitHub projects...")
        evidence = self._load_evidence()
        projects = self._load_github_projects()
        print(f"  {len(evidence)} skills, {len(projects)} projects")

        print("[2/5] Extracting job priorities (LLM)...")
        priorities = self._extract_priorities(target_title, target_company, job_description)
        print(f"  must_have={priorities.get('must_have', [])}")

        print("[3/5] Tailoring evidence for target (LLM)...")
        tailoring = self._tailor_evidence(target_company, target_title, priorities, evidence, projects)
        print(f"  emphasized={tailoring.get('emphasized_skills', [])}")

        print("[4/5] Selecting best projects (LLM)...")
        project_selection = self._select_projects(target_company, target_title, projects)
        selected = project_selection.get("selected", [])
        for p in selected:
            print(f"  - {p.get('name')}: {p.get('score', 0):.1f}")

        print("[5/5] Generating 2-line summary (LLM)...")
        candidate_info = candidate_info or self._default_candidate_info()
        summary = self._generate_summary(
            target_company, target_title, candidate_info,
            tailoring.get("emphasized_skills", []),
            selected,
        )
        print(f"  {summary[:80]}...")

        print("Rendering Markdown...")
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
            output_path = Path("personal") / f"{name}_{slug}.md"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        print(f"\nResume saved: {output_path} ({len(markdown)} chars)")
        return output_path

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_evidence(self) -> Dict[str, dict]:
        with db.session_scope() as session:
            repo = EvidenceRepository(session)
            all_evidence = repo.get_all_evidence_for_user(self.user_id)

        grouped = {}
        for ev in all_evidence:
            skill = ev.skill_name
            if skill not in grouped:
                grouped[skill] = {"confidence": 0.0, "evidence_list": []}
            grouped[skill]["evidence_list"].append({
                "project_name": ev.project_name,
                "author_commits": ev.author_commits,
                "stars": ev.stars,
                "github_url": ev.github_url,
                # Real GitHub metrics from Phase 3B enrichment
                "loc_count": ev.loc_count,
                "language": ev.language,
                "topics": ev.topics or [],
                "has_tests": ev.has_tests,
                "has_docs": ev.has_docs,
                "has_releases": ev.has_releases,
                "pr_count": ev.pr_count,
                "issue_count": ev.issue_count,
            })
            grouped[skill]["confidence"] = max(grouped[skill]["confidence"], ev.confidence)

        return grouped

    def _load_github_projects(self) -> List[dict]:
        cache_dir = self.hiring_agent_dir / "cache"
        if not cache_dir.exists():
            return []

        cache_files = sorted(
            cache_dir.glob("githubcache_*.json"),
            key=lambda p: p.stat().st_mtime,
        )
        if not cache_files:
            return []

        data = json.loads(cache_files[-1].read_text(encoding="utf-8"))
        return data.get("projects", [])

    def _default_candidate_info(self) -> dict:
        from career_os.config_loader import load_config
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
        return self.llm.generate_json(prompt)

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
        result = self.llm.generate_json(prompt)
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
        return self.llm.generate_json(prompt)

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
        return self.llm.generate(prompt, json_mode=False, temperature=0.5, max_tokens=200).strip()

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
            loader=FileSystemLoader("."),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        template = env.get_template(
            f"services/resume_intelligence/templates/resume/{template_name}.md.jinja"
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
