"""evidence_items → Career Graph.

build_career_graph() is pure: it turns evidence items into graph nodes/edges
plus the CareerGraphNode rows to persist. run_graph_building() is the
background job that loads items, persists the graph and finishes onboarding.
"""

import logging
import time
from collections import defaultdict
from typing import Any, Iterable

from careeros.db.connection import db
from careeros.onboarding.models.career_graph_node import CareerGraphNode
from careeros.evidence.models.evidence_item import EvidenceItem
from careeros.identity.repositories.user_repo import UserRepository
from careeros.identity.domain.onboarding import OnboardingState
from careeros.shared.background import BackgroundJob

logger = logging.getLogger(__name__)

ACHIEVEMENT_TYPES = {
    "volunteering", "award", "publication", "patent", "sport",
    "opensource", "exhibition", "grant", "press", "teaching", "license",
}
EDGE_WEIGHT = 0.8

# The wizard animates each stage; these pauses keep the reveal readable.
# They are presentation pacing only — no work happens during them.
_STAGE_PAUSE_SECONDS = (1.0, 0.8, 0.5, 0.8)


def _kind(item: Any) -> str:
    return (item.evidence_data or {}).get("type", "skill")


def split_evidence(items: Iterable[Any]) -> dict[str, list]:
    """Group evidence items into skills / projects / experiences / achievements."""
    groups: dict[str, list] = {"skills": [], "projects": [], "experiences": [], "achievements": []}
    for item in items:
        kind = _kind(item)
        if kind == "skill":
            groups["skills"].append(item)
        elif kind == "project":
            groups["projects"].append(item)
        elif kind == "experience":
            groups["experiences"].append(item)
        elif kind in ACHIEVEMENT_TYPES:
            groups["achievements"].append(item)
    return groups


def build_career_graph(items: Iterable[Any]) -> tuple[dict, list[dict]]:
    """Return (graph, node_rows).

    graph      {"nodes": [...], "edges": [...], "stats": {...}} — the wire format
    node_rows  kwargs for CareerGraphNode(user_id=..., **row)
    """
    g = split_evidence(items)
    nodes: list[dict] = []
    edges: list[dict] = []
    rows: list[dict] = []

    # Skills — one node per name, confidence averaged across sources
    skill_agg: dict[str, dict] = defaultdict(lambda: {"confidences": [], "sources": set(), "skill_id": None})
    for s in g["skills"]:
        agg = skill_agg[s.skill_name]
        agg["confidences"].append(s.confidence_score)
        agg["sources"].add(s.source)
        agg["skill_id"] = agg["skill_id"] or s.skill_id

    for name, agg in skill_agg.items():
        conf = round(sum(agg["confidences"]) / len(agg["confidences"]), 3)
        sources = sorted(agg["sources"])
        nodes.append(_node(f"skill_{name}", "skill", name, conf,
                           {"evidence_count": len(agg["confidences"]), "sources": sources}))
        rows.append({"node_type": "skill", "label": name, "confidence": conf,
                     "canonical_id": str(agg["skill_id"]) if agg["skill_id"] else None,
                     "node_metadata": {"sources": sources, "evidence_count": len(agg["confidences"])}})

    skills_by_lower = {name.lower(): name for name in skill_agg}

    def link(node_id: str, technologies: list[str]) -> None:
        for tech in technologies:
            canonical = skills_by_lower.get(tech.lower())
            if canonical:
                edges.append({"source": node_id, "target": f"skill_{canonical}", "weight": EDGE_WEIGHT})

    for p in g["projects"]:
        data = p.evidence_data or {}
        techs = data.get("technologies", [])
        node_id = f"project_{p.id}"
        nodes.append(_node(node_id, "project", p.skill_name, p.confidence_score, {"technologies": techs}))
        rows.append({"node_type": "project", "label": p.skill_name, "confidence": p.confidence_score,
                     "node_metadata": {"source_type": p.source, "technologies": techs,
                                       "description": data.get("description", "")}})
        link(node_id, techs)

    for e in g["experiences"]:
        data = e.evidence_data or {}
        techs = data.get("technologies", [])
        node_id = f"experience_{e.id}"
        nodes.append(_node(node_id, "company", e.skill_name, e.confidence_score, {"company": data.get("company", "")}))
        rows.append({"node_type": "experience", "label": e.skill_name, "confidence": e.confidence_score,
                     "node_metadata": {"source_type": e.source, "company": data.get("company", ""),
                                       "role": data.get("role", ""), "duration": data.get("duration", ""),
                                       "technologies": techs}})
        link(node_id, techs)

    for a in g["achievements"]:
        data = a.evidence_data or {}
        kind = data.get("type", "award")
        nodes.append(_node(f"achievement_{a.id}", "achievement", a.skill_name, a.confidence_score,
                           {"kind": kind, "year": data.get("year")}))
        rows.append({"node_type": "achievement", "label": a.skill_name, "confidence": a.confidence_score,
                     "node_metadata": {"kind": kind, "detail": data.get("detail", ""), "year": data.get("year")}})

    # Only figures we actually computed (no job-match or commit stats yet)
    stats = {
        "skills_count": len(skill_agg),
        "projects_count": len(g["projects"]),
        "companies_count": len(g["experiences"]),
        "achievements_count": len(g["achievements"]),
        "edges_count": len(edges),
        "confidence_score": round(sum(n["confidence"] for n in nodes) / len(nodes), 3) if nodes else 0.0,
    }
    return {"nodes": nodes, "edges": edges, "stats": stats}, rows


def _node(node_id: str, type_: str, label: str, confidence: float, metadata: dict) -> dict:
    return {"id": node_id, "type": type_, "label": label, "confidence": confidence, "metadata": metadata}


def run_graph_building(job: BackgroundJob, user_id: str, pause=time.sleep) -> None:
    """Background task: build + persist the Career Graph, then mark onboarding READY."""
    p1, p2, p3, p4 = _STAGE_PAUSE_SECONDS
    try:
        with db.session_scope() as session:
            job.update(status="parsing", progress=15)
            job.log("📄 Fetching evidence items from database...")
            pause(p1)

            items = session.query(EvidenceItem).filter(EvidenceItem.user_id == user_id).all()
            if not items:
                raise ValueError("No evidence items found. Please upload your resume first.")
            g = split_evidence(items)
            job.progress = 35
            job.log(
                f"✓ Found {len(g['skills'])} skills, {len(g['projects'])} projects, "
                f"{len(g['experiences'])} experiences, {len(g['achievements'])} achievements",
                "success",
            )
            pause(p2)

            job.update(status="extracting", progress=50)
            job.log("🔄 Clearing existing Career Graph...")
            session.query(CareerGraphNode).filter(CareerGraphNode.user_id == user_id).delete()
            session.commit()
            pause(p3)

            job.update(status="matching", progress=70)
            job.log("▸ Creating Career Graph nodes...")
            graph, rows = build_career_graph(items)
            for row in rows:
                session.add(CareerGraphNode(user_id=user_id, **row))

            job.progress = 85
            job.log(f"✓ Positioned {len(graph['nodes'])} nodes and {len(graph['edges'])} connections", "success")
            pause(p4)

            job.progress = 95
            job.log("📊 Finalizing Career Graph...", "success")
            session.commit()

            repo = UserRepository(session)
            repo.set_onboarding_state(user_id, OnboardingState.READY)
            repo.patch_profile_data(user_id, {"career_graph": graph})
            session.commit()

            job.update(result=graph, progress=100, status="completed")
            job.log("✓ Career Graph ready", "success")
    except Exception as e:
        logger.exception("Career graph build failed for %s", user_id)
        job.fail(e, f"✗ Graph building failed: {e}")
