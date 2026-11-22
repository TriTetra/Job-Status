"""CV extraction: skill-name cleanup, schema leniency, and the evidence it writes."""

from types import SimpleNamespace

import pytest

from careeros.evidence import resume as resume_mod
from careeros.evidence.resume_llm import StructuredResume
from careeros.knowledge.skill_names import split_skill_names


@pytest.mark.parametrize("raw, expected", [
    ("React 19", ["React"]),
    ("PostgreSQL 17", ["PostgreSQL"]),
    ("Tailwind CSS v4", ["Tailwind CSS"]),
    ("Python 3.11", ["Python"]),
    ("Redis (Asynq)", ["Redis", "Asynq"]),
    ("LangChain / CrewAI", ["LangChain", "CrewAI"]),
    ("Python (advanced)", ["Python"]),
    ("CI/CD", ["CI/CD"]),
    ("C++", ["C++"]),
    ("GPT-4o", ["GPT-4o"]),
    ("golang", ["Go"]),
    ("OAuth 2.0", ["OAuth 2.0"]),   # a catalog name that ends in a number stays whole
    ("", []),
])
def test_split_skill_names(raw, expected):
    assert split_skill_names(raw) == expected


def test_schema_tolerates_sloppy_model_output():
    s = StructuredResume.model_validate({
        "skills": [{"name": "Python", "confidence": "high"}, "stray string", {"name": "Go", "confidence": 3}],
        "experience": [{"company": "Acme", "role": None, "highlights": ["30% faster"]}],
        "certifications": [{"name": "CKA"}, "AWS SAA", ""],
        "achievements": [
            {"category": "Publication", "title": "Paper", "description": "IEEE", "status": "under review"},
            {"type": "medal", "title": "Gold", "year": 2024},
        ],
    })
    assert [k.confidence for k in s.skills] == [0.7, 1.0]
    assert s.experience[0].role == "" and s.experience[0].highlights == ["30% faster"]
    assert s.certifications == ["CKA", "AWS SAA"]
    paper, gold = s.achievements
    assert paper.type == "publication" and paper.detail == "IEEE" and paper.pending
    assert gold.type == "award" and gold.year == "2024" and not gold.pending


class _Query:
    def __init__(self, rows=()):
        self.rows, self.deleted = list(rows), False

    def filter(self, *a):
        return self

    def all(self):
        return self.rows

    def delete(self, **k):
        self.deleted = True


class _Session:
    def __init__(self, skills):
        from careeros.evidence.models.skill import Skill

        self.skills, self.Skill = skills, Skill
        self.added, self.queries, self.commits, self.rollbacks = [], [], 0, 0

    def query(self, model):
        q = _Query(self.skills if model is self.Skill else ())
        self.queries.append((model, q))
        return q

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def _doc():
    return SimpleNamespace(id=7, user_id="u1", storage_key="cv.pdf", parse_status=None,
                           parsed_text=None, parse_result=None)


def test_process_resume_writes_clean_deduplicated_evidence(monkeypatch):
    from careeros.evidence.models.evidence_item import EvidenceItem

    monkeypatch.setattr(resume_mod, "extract_pdf_text", lambda p: "x" * 500)
    monkeypatch.setattr(resume_mod, "extract_resume", lambda text, user_id=None: StructuredResume.model_validate({
        "skills": [{"name": "React 19", "confidence": 0.8}, {"name": "React", "confidence": 0.95},
                   {"name": "Redis (Asynq)", "confidence": 0.75}, {"name": "py", "confidence": 0.9}],
        "experience": [{"company": "Acme", "role": "Engineer", "technologies": ["Next.js 15"],
                        "highlights": ["a", "b", "c", "d"]}],
        "education": [{"institution": "Uni", "degree": "B.Sc.", "field": "CS"}, {"year": "2020"}],
        "certifications": ["CKA"],
        "achievements": [{"type": "publication", "title": "Paper", "status": "submitted"},
                         {"type": "award", "title": "Medal"}],
    }))
    session = _Session([SimpleNamespace(id=1, name="Python", aliases=["py"])])

    summary = resume_mod.process_resume(_doc(), session)

    old = [q for model, q in session.queries if model is EvidenceItem]
    assert old and old[0].deleted                     # previous CV's evidence replaced
    by_type = {}
    for item in session.added:
        by_type.setdefault(item.evidence_data["type"], []).append(item)
    skills = {i.skill_name: i for i in by_type["skill"]}
    assert set(skills) == {"React", "Redis", "Asynq", "Python"}
    assert skills["React"].confidence_score == 0.95   # best of the duplicates
    assert skills["Python"].skill_id == 1
    exp = by_type["experience"][0].evidence_data
    assert exp["technologies"] == ["Next.js"] and exp["highlights"] == ["a", "b", "c"]
    assert [i.skill_name for i in by_type["education"]] == ["B.Sc., CS"]
    assert [i.skill_name for i in by_type["certification"]] == ["CKA"]
    assert by_type["publication"][0].confidence_score == resume_mod.PENDING_ACHIEVEMENT_CONFIDENCE
    assert by_type["award"][0].confidence_score == resume_mod.ACHIEVEMENT_CONFIDENCE["award"]
    assert summary["skills_count"] == 4 and summary["skills_matched"] == 1
    assert summary["evidence_items"] == 4 + 1 + 0 + 1 + 1 + 2


def test_scanned_pdf_fails_with_a_readable_message(monkeypatch):
    monkeypatch.setattr(resume_mod, "extract_pdf_text", lambda p: "   ")
    doc, session = _doc(), _Session([])
    with pytest.raises(resume_mod.ResumeTextError, match="scan"):
        resume_mod.process_resume(doc, session)
    assert doc.parse_status == "failed" and session.added == []
