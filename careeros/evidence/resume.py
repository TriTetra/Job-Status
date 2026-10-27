"""Uploaded CV (PDF) → LLM extraction → evidence items (source="resume")."""

import logging
from typing import Callable

from sqlalchemy.orm import Session

from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.evidence.models.resume_document import ResumeDocument

from careeros.evidence.resume_llm import extract_resume
from careeros.evidence.skills import find_canonical, load_all_skills

logger = logging.getLogger(__name__)

LogFn = Callable[[str], None]


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


def process_resume(
    resume_doc: ResumeDocument,
    db: Session,
    log: LogFn = lambda msg: None,
) -> dict:
    """
    Full pipeline: parse PDF → LLM extract → match skills → write evidence items.

    `log` is called with status messages so callers can stream progress.
    Returns summary dict.
    """
    try:
        # ── 1. Parse PDF ──────────────────────────────────────────────────────
        resume_doc.parse_status = "parsing"
        db.commit()

        log("Parsing PDF structure...")
        file_path = resume_doc.storage_key
        text = extract_pdf_text(file_path)
        resume_doc.parsed_text = text[:50000]  # cap at 50k chars
        log(f"Extracted {len(text):,} characters from {len(text.splitlines())} lines")

        # ── 2. LLM extraction ────────────────────────────────────────────────
        resume_doc.parse_status = "extracting"
        db.commit()

        log("Running LLM skill extraction...")
        structured = extract_resume(text, user_id=resume_doc.user_id)
        resume_doc.parse_result = structured.model_dump()

        skills_raw   = structured.skills
        experience   = structured.experience
        projects     = structured.projects
        education    = structured.education
        certs        = structured.certifications
        achievements = structured.achievements

        log(
            f"Found {len(skills_raw)} skills, "
            f"{len(experience)} positions, "
            f"{len(projects)} projects, "
            f"{len(achievements)} achievements"
        )

        # ── 3. Match & create skill evidence items ────────────────────────────
        log("Matching skills to taxonomy...")
        canonical_skills = load_all_skills(db)

        created = 0
        for raw in skills_raw:
            name       = (raw.get("name") or "").strip()
            confidence = float(raw.get("confidence") or 0.5)
            evidence_t = raw.get("evidence") or ""
            if not name:
                continue

            canonical = find_canonical(name, canonical_skills)
            item = EvidenceItem(
                user_id=resume_doc.user_id,
                skill_name=name,
                skill_id=canonical.id if canonical else None,
                source="resume",
                source_ref=str(resume_doc.id),
                confidence_score=round(confidence, 3),
                evidence_text=evidence_t[:500] if evidence_t else None,
                evidence_data={"matched_canonical": canonical.name if canonical else None},
                resume_document_id=resume_doc.id,
            )
            db.add(item)
            created += 1

        # ── 4. Create experience evidence items ───────────────────────────────
        for exp in experience:
            role = exp.get("role", "Unknown Role")
            company = exp.get("company", "Unknown Company")
            db.add(EvidenceItem(
                user_id=resume_doc.user_id,
                skill_name=f"{role} @ {company}",
                source="resume",
                source_ref=str(resume_doc.id),
                confidence_score=0.90,
                evidence_data={
                    "type": "experience",
                    "company": company,
                    "role": role,
                    "duration": exp.get("duration"),
                    "technologies": exp.get("technologies", []),
                },
                resume_document_id=resume_doc.id,
            ))

        # ── 5. Create project evidence items ──────────────────────────────────
        for proj in projects:
            db.add(EvidenceItem(
                user_id=resume_doc.user_id,
                skill_name=proj.get("name", "Project"),
                source="resume",
                source_ref=str(resume_doc.id),
                confidence_score=0.85,
                evidence_data={
                    "type": "project",
                    "description": proj.get("description", ""),
                    "technologies": proj.get("technologies", []),
                },
                resume_document_id=resume_doc.id,
            ))

        # ── 6. Achievements — the proof most parsers lose (medals, papers, patents…)
        for ach in achievements:
            if not ach.title:
                continue
            db.add(EvidenceItem(
                user_id=resume_doc.user_id,
                skill_name=ach.title,
                source="resume",
                source_ref=str(resume_doc.id),
                confidence_score=ACHIEVEMENT_CONFIDENCE.get(ach.type, 0.88),
                evidence_data={
                    "type": ach.type,
                    "title": ach.title,
                    "detail": ach.detail,
                    "year": ach.year,
                },
                resume_document_id=resume_doc.id,
            ))

        if achievements:
            log(f"🏆 Captured {len(achievements)} achievements (awards, papers, medals, OSS)")

        # ── 7. Finalize ───────────────────────────────────────────────────────
        resume_doc.parse_status = "completed"
        db.commit()

        summary = {
            "status": "completed",
            "skills_count": created,
            "experience_count": len(experience),
            "projects_count": len(projects),
            "education_count": len(education),
            "certifications_count": len(certs),
            "achievements_count": len(achievements),
            "evidence_items": (
                created
                + len(experience)
                + len(projects)
                + len(achievements)
            ),
        }
        log(f"Saved {created} skill evidence items")
        logger.info("Resume pipeline complete: %s", summary)
        return summary

    except Exception as exc:
        logger.exception("Resume pipeline failed: %s", exc)
        resume_doc.parse_status = "failed"
        db.commit()
        raise
