"""Resume processing pipeline: PDF → LLM extraction → evidence items."""

import logging
from typing import Callable

from sqlalchemy.orm import Session

from core.db.models.evidence_item import EvidenceItem
from core.db.models.resume_document import ResumeDocument
from .pdf_parser import PDFParser
from .resume_extractor import extract_resume
from .skill_matcher import find_canonical, load_all_skills

logger = logging.getLogger(__name__)

LogFn = Callable[[str], None]


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
        text = PDFParser.extract_text(file_path)
        resume_doc.parsed_text = text[:50000]  # cap at 50k chars
        log(f"Extracted {len(text):,} characters from {len(text.splitlines())} lines")

        # ── 2. LLM extraction ────────────────────────────────────────────────
        resume_doc.parse_status = "extracting"
        db.commit()

        log("Running LLM skill extraction...")
        structured = extract_resume(text)
        resume_doc.parse_result = structured

        skills_raw   = structured.get("skills", [])
        experience   = structured.get("experience", [])
        projects     = structured.get("projects", [])
        education    = structured.get("education", [])
        certs        = structured.get("certifications", [])

        log(
            f"Found {len(skills_raw)} skills, "
            f"{len(experience)} positions, "
            f"{len(projects)} projects"
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

        # ── 6. Finalize ───────────────────────────────────────────────────────
        resume_doc.parse_status = "completed"
        db.commit()

        summary = {
            "status": "completed",
            "skills_count": created,
            "experience_count": len(experience),
            "projects_count": len(projects),
            "education_count": len(education),
            "certifications_count": len(certs),
        }
        log(f"Saved {created} skill evidence items")
        logger.info("Resume pipeline complete: %s", summary)
        return summary

    except Exception as exc:
        logger.exception("Resume pipeline failed: %s", exc)
        resume_doc.parse_status = "failed"
        db.commit()
        raise
