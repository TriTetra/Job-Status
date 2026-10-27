"""services.onboarding — pure parts (no DB)."""

from types import SimpleNamespace

import pytest

from services.onboarding import resume_upload
from services.onboarding.career_graph import build_career_graph, split_evidence
from services.onboarding.profile import OnboardingInputError, classify_role_id, validate_goals


# ── identity / goals ──────────────────────────────────────────────────────

@pytest.mark.parametrize("role_id, kind", [
    ("3f2b8c1e-9d4a-4b6f-8e2a-1c5d7f9a0b3e", "uuid"),
    ("3F2B8C1E-9D4A-4B6F-8E2A-1C5D7F9A0B3E", "uuid"),
    ("custom_1730000000", "custom"),
    ("backend_engineer", "slug"),
])
def test_classify_role_id(role_id, kind):
    assert classify_role_id(role_id) == kind


def test_goals_salary_range_must_be_ordered():
    validate_goals({"salary_min": 50_000, "salary_max": 90_000})
    validate_goals({"salary_min": 50_000, "salary_max": None})
    with pytest.raises(OnboardingInputError):
        validate_goals({"salary_min": 90_000, "salary_max": 50_000})


# ── CV upload ─────────────────────────────────────────────────────────────

def test_store_resume_pdf_rejects_non_pdf(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_upload, "UPLOAD_DIR", tmp_path)
    with pytest.raises(resume_upload.UploadRejected) as e:
        resume_upload.store_resume_pdf("cv.docx", b"x")
    assert e.value.status_code == 400
    assert not list(tmp_path.iterdir())


def test_store_resume_pdf_rejects_oversize_before_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_upload, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(resume_upload, "MAX_PDF_BYTES", 10)
    with pytest.raises(resume_upload.UploadRejected) as e:
        resume_upload.store_resume_pdf("cv.PDF", b"x" * 11)
    assert e.value.status_code == 413
    assert not list(tmp_path.iterdir())


def test_store_resume_pdf_writes_under_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(resume_upload, "UPLOAD_DIR", tmp_path / "personal")
    path = resume_upload.store_resume_pdf("CV.pdf", b"%PDF-1.7")
    assert path.parent == tmp_path / "personal"
    assert path.read_bytes() == b"%PDF-1.7"


# ── Career Graph ──────────────────────────────────────────────────────────

def _item(id, name, source, data, conf=0.8, skill_id=None):
    return SimpleNamespace(id=id, skill_name=name, source=source, evidence_data=data,
                           confidence_score=conf, skill_id=skill_id)


ITEMS = [
    _item(1, "Python", "resume", {"type": "skill"}, conf=0.6),
    _item(2, "Python", "github", {"type": "skill"}, conf=0.9, skill_id=7),
    _item(3, "Rust", "github", None, conf=0.7),                       # no type → skill
    _item(4, "engine", "github", {"type": "project", "technologies": ["python", "rust", "Go"]}),
    _item(5, "Backend @ Acme", "resume", {"type": "experience", "company": "Acme", "technologies": ["Python"]}),
    _item(6, "Best Paper", "resume", {"type": "publication", "year": 2025}),
    _item(7, "ignored", "resume", {"type": "unknown_kind"}),
]


def test_split_evidence_groups_by_type():
    g = split_evidence(ITEMS)
    assert [len(g[k]) for k in ("skills", "projects", "experiences", "achievements")] == [3, 1, 1, 1]


def test_build_career_graph_nodes_edges_and_stats():
    graph, rows = build_career_graph(ITEMS)
    nodes = {n["id"]: n for n in graph["nodes"]}

    # skills deduped by name, confidence averaged across sources
    assert nodes["skill_Python"]["confidence"] == 0.75
    assert nodes["skill_Python"]["metadata"]["sources"] == ["github", "resume"]
    assert set(nodes) == {"skill_Python", "skill_Rust", "project_4", "experience_5", "achievement_6"}
    assert nodes["experience_5"]["type"] == "company"

    # edges link by technology, case-insensitively; unknown tech (Go) creates no edge
    assert {(e["source"], e["target"]) for e in graph["edges"]} == {
        ("project_4", "skill_Python"), ("project_4", "skill_Rust"), ("experience_5", "skill_Python"),
    }
    assert graph["stats"]["skills_count"] == 2
    assert graph["stats"]["edges_count"] == 3
    assert graph["stats"]["achievements_count"] == 1

    # one persisted row per node; canonical id carried from any source that had it
    assert len(rows) == len(graph["nodes"])
    python_row = next(r for r in rows if r["label"] == "Python")
    assert python_row["canonical_id"] == "7" and python_row["node_type"] == "skill"


def test_empty_evidence_gives_empty_graph():
    graph, rows = build_career_graph([])
    assert graph == {"nodes": [], "edges": [], "stats": {
        "skills_count": 0, "projects_count": 0, "companies_count": 0,
        "achievements_count": 0, "edges_count": 0, "confidence_score": 0.0,
    }}
    assert rows == []


# ── graph-building job (fake DB) ──────────────────────────────────────────

class _Q:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *a):
        return self

    def all(self):
        return list(self.rows)

    def delete(self):
        return 0


class _Session:
    def __init__(self, items):
        self.items, self.added, self.commits = items, [], 0

    def query(self, model):
        from core.db.models.evidence_item import EvidenceItem
        return _Q(self.items if model is EvidenceItem else [])

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


class _Repo:
    calls = []

    def __init__(self, session):
        pass

    def set_onboarding_state(self, user_id, state):
        _Repo.calls.append(("state", user_id, state))

    def patch_profile_data(self, user_id, data):
        _Repo.calls.append(("patch", user_id, sorted(data)))


def _fake_db(monkeypatch, module, session):
    from contextlib import contextmanager

    @contextmanager
    def scope():
        yield session
    monkeypatch.setattr(module, "db", SimpleNamespace(session_scope=scope))


def test_run_graph_building_persists_graph_and_finishes_onboarding(monkeypatch):
    from core.domain.identity.onboarding import OnboardingState
    from services.onboarding import career_graph
    from shared.background import JobStore

    session = _Session(ITEMS)
    _fake_db(monkeypatch, career_graph, session)
    _Repo.calls = []
    monkeypatch.setattr(career_graph, "UserRepository", _Repo)

    job = JobStore().create("user_1")
    career_graph.run_graph_building(job, "user_1", pause=lambda s: None)

    assert job.status == "completed" and job.progress == 100
    assert job.result["stats"]["skills_count"] == 2
    assert len(session.added) == len(job.result["nodes"])  # one CareerGraphNode per node
    assert ("state", "user_1", OnboardingState.READY) in _Repo.calls
    assert ("patch", "user_1", ["career_graph"]) in _Repo.calls


def test_run_graph_building_without_evidence_fails_cleanly(monkeypatch):
    from services.onboarding import career_graph
    from shared.background import JobStore

    _fake_db(monkeypatch, career_graph, _Session([]))
    job = JobStore().create("user_1")
    career_graph.run_graph_building(job, "user_1", pause=lambda s: None)
    assert job.status == "failed" and "No evidence items" in job.error
