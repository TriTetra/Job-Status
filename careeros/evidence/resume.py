"""Uploaded CV (PDF) → LLM extraction → evidence items (source="resume")."""

import logging
from typing import Callable, Optional

from sqlalchemy.orm import Session

from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.evidence.models.resume_document import ResumeDocument

from careeros.evidence.resume_llm import extract_resume
from careeros.evidence.skills import find_canonical, load_all_skills
from careeros.knowledge.skill_names import split_skill_names

logger = logging.getLogger(__name__)

LogFn = Callable[[str], None]

# Fewer characters than this means the PDF is a scan / image, not text
MIN_TEXT_CHARS = 200


class ResumeTextError(ValueError):
    """The PDF has no usable text (message is safe to show the user)."""


def extract_pdf_text(pdf_path: str) -> str:
    """All text from a PDF, page by page (PyMuPDF)."""
    import fitz  # PyMuPDF — imported lazily, it is only needed here

    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text() for page in doc).strip()
    logger.info("Extracted %d chars from %s", len(text), pdf_path)
    return text


# Externally-validated evidence carries higher confidence than self-reported skills.
ACHIEVEMENT_CONFIDENCE: dict[str, float] = {
    "patent":       0.94,
    "license":      0.94,
    "publication":  0.93,
    "grant":        0.93,
    "award":        0.92,
    "sport":        0.90,
    "opensource":   0.89,
    "exhibition":   0.88,
    "press":        0.87,
    "teaching":     0.86,
    "volunteering": 0.85,
}
# A submitted paper or pending grant is a claim, not yet external validation
PENDING_ACHIEVEMENT_CONFIDENCE = 0.6
EDUCATION_CONFIDENCE = 0.9
CERTIFICATION_CONFIDENCE = 0.88


def merge_skills(raw_skills) -> list[tuple[str, float, str]]:
    """LLM skills → (canonical name, best confidence, evidence), split and de-duplicated.

    "Redis (Asynq)" → Redis + Asynq, "React 19" → React; the same skill twice keeps
    its highest confidence.
    """
    merged: dict[str, list] = {}
    for raw in raw_skills:
        for name in split_skill_names(raw.name):
            key = name.lower()
            if key not in merged:
                merged[key] = [name, raw.confidence, raw.evidence]
            elif raw.confidence > merged[key][1]:
                merged[key][1:] = [raw.confidence, raw.evidence or merged[key][2]]
    return [(n, c, e) for n, c, e in merged.values()]


def _techs(raw: list[str]) -> list[str]:
    return [t for item in raw for t in split_skill_names(item)]


def process_resume(
    resume_doc: ResumeDocument,
    db: Session,
    log: LogFn = lambda msg: None,
) -> dict:
    """
    Full pipeline: parse PDF → LLM extract → match skills → write evidence items.

    A new CV replaces the previous CV's evidence. `log` is called with status
    messages so callers can stream progress. Returns summary dict.
    """
    try:
        # ── 1. Parse PDF ──────────────────────────────────────────────────────
        resume_doc.parse_status = "parsing"
        db.commit()

        log("Parsing PDF structure...")
        text = extract_pdf_text(resume_doc.storage_key)
        if len(text) < MIN_TEXT_CHARS:
            raise ResumeTextError(
                "This PDF has no selectable text (it looks like a scan or an image). "
                "Export your CV from Word, Google Docs or LaTeX as a PDF and upload that."
            )
        resume_doc.parsed_text = text[:50000]  # cap at 50k chars
        log(f"Extracted {len(text):,} characters from {len(text.splitlines())} lines")

        # ── 2. LLM extraction ────────────────────────────────────────────────
        resume_doc.parse_status = "extracting"
        db.commit()

        log("Running LLM skill extraction...")
        structured = extract_resume(text, user_id=resume_doc.user_id)
        resume_doc.parse_result = structured.model_dump()

        skills       = merge_skills(structured.skills)
        experience   = structured.experience
        projects     = structured.projects
        education    = [e for e in structured.education if e.institution or e.degree]
        certs        = structured.certifications
        achievements = [a for a in structured.achievements if a.title]

        log(
            f"Found {len(skills)} skills, "
            f"{len(experience)} positions, "
            f"{len(projects)} projects, "
            f"{len(achievements)} achievements"
        )

        # A new CV replaces the previous one's evidence (no duplicates on re-upload)
        db.query(EvidenceItem).filter(
            EvidenceItem.user_id == resume_doc.user_id,
            EvidenceItem.source == "resume",
        ).delete(synchronize_session=False)

        def add(name: str, confidence: float, data: dict,
                text: Optional[str] = None, skill_id: Optional[int] = None) -> None:
            db.add(EvidenceItem(
                user_id=resume_doc.user_id,
                skill_name=name[:200],
                skill_id=skill_id,
                source="resume",
                source_ref=str(resume_doc.id),
                confidence_score=round(confidence, 3),
                evidence_text=text[:500] if text else None,
                evidence_data=data,
                resume_document_id=resume_doc.id,
            ))

        # ── 3. Skills, matched to the taxonomy ────────────────────────────────
        log("Matching skills to taxonomy...")
        canonical_skills = load_all_skills(db)
        matched = 0
        for name, confidence, evidence in skills:
            canonical = find_canonical(name, canonical_skills)
            matched += canonical is not None
            add(canonical.name if canonical else name, confidence,
                {"type": "skill", "matched_canonical": canonical.name if canonical else None},
                text=evidence, skill_id=canonical.id if canonical else None)
        log(f"{matched} of {len(skills)} skills matched the skill catalog")

        # ── 4. Experience, with its measurable highlights ─────────────────────
        for exp in experience:
            role = exp.role or "Unknown Role"
            company = exp.company or "Unknown Company"
            add(f"{role} @ {company}", 0.90, {
                "type": "experience",
                "company": company,
                "role": role,
                "duration": exp.duration,
                "technologies": _techs(exp.technologies),
                "highlights": exp.highlights[:3],
            })

        # ── 5. Projects ───────────────────────────────────────────────────────
        for proj in projects:
            add(proj.name or "Project", 0.85, {
                "type": "project",
                "description": proj.description,
                "technologies": _techs(proj.technologies),
                "url": proj.url or None,
            })

        # ── 6. Education and certifications ───────────────────────────────────
        for edu in education:
            title = ", ".join(x for x in (edu.degree, edu.field) if x) or edu.institution
            add(title, EDUCATION_CONFIDENCE, {
                "type": "education", "institution": edu.institution, "degree": edu.degree,
                "field": edu.field, "year": edu.year,
            })
        for cert in certs:
            add(cert, CERTIFICATION_CONFIDENCE, {"type": "certification"})

        # ── 7. Achievements — the proof most parsers lose (medals, papers, patents…)
        for ach in achievements:
            confidence = (PENDING_ACHIEVEMENT_CONFIDENCE if ach.pending
                          else ACHIEVEMENT_CONFIDENCE.get(ach.type, 0.88))
            add(ach.title, confidence, {
                "type": ach.type,
                "title": ach.title,
                "detail": ach.detail,
                "year": ach.year,
                "status": ach.status,
            })
        if achievements:
            log(f"🏆 Captured {len(achievements)} achievements (awards, papers, medals, OSS)")

        # ── 8. Finalize ───────────────────────────────────────────────────────
        resume_doc.parse_status = "completed"
        db.commit()

        summary = {
            "status": "completed",
            "skills_count": len(skills),
            "skills_matched": matched,
            "experience_count": len(experience),
            "projects_count": len(projects),
            "education_count": len(education),
            "certifications_count": len(certs),
            "achievements_count": len(achievements),
            "evidence_items": (len(skills) + len(experience) + len(projects)
                               + len(education) + len(certs) + len(achievements)),
        }
        log(f"Saved {len(skills)} skill evidence items")
        logger.info("Resume pipeline complete: %s", summary)
        return summary

    except Exception as exc:
        logger.exception("Resume pipeline failed: %s", exc)
        db.rollback()
        resume_doc.parse_status = "failed"
        db.commit()
        raise
