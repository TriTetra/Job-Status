"""
SkillLoader — single source of truth for skill metadata.

Reads knowledge/v1/skills/skill_graph.yaml and exposes typed accessors.
Nothing in application code should hardcode skill names, topics, or edges.

Usage:
    loader = SkillLoader()
    loader.topic_map()          # {github_topic: canonical_skill_name}
    loader.language_map()       # {github_language: canonical_skill_name}
    loader.alias_map()          # {alias_lower: canonical_skill_name}
    loader.transfer_edges()     # [(from, to, weight), ...]
    loader.skill_names()        # [canonical names]
    loader.skill(name)          # raw dict for one skill
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

_DEFAULT_YAML = Path(__file__).parents[2] / "knowledge" / "v1" / "skills" / "skill_graph.yaml"


class SkillLoader:
    def __init__(self, yaml_path: Path = _DEFAULT_YAML):
        if not yaml_path.exists():
            raise FileNotFoundError(f"Skill graph YAML not found: {yaml_path}")
        with yaml_path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        self._skills: Dict[str, dict] = raw.get("skills", {})

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def skill_names(self) -> List[str]:
        return list(self._skills.keys())

    def skill(self, name: str) -> dict:
        return self._skills.get(name, {})

    @cached_property
    def topic_map(self) -> Dict[str, str]:
        """GitHub repo topic → canonical skill name (lower-keyed)."""
        out: Dict[str, str] = {}
        for name, data in self._skills.items():
            for topic in data.get("github_topics", []):
                out[topic.lower()] = name
        return out

    @cached_property
    def language_map(self) -> Dict[str, str]:
        """GitHub repo.language → canonical skill name (lower-keyed)."""
        out: Dict[str, str] = {}
        for name, data in self._skills.items():
            for lang in data.get("github_languages", []):
                out[lang.lower()] = name
        return out

    @cached_property
    def alias_map(self) -> Dict[str, str]:
        """Alias / job-posting keyword → canonical skill name (lower-keyed)."""
        out: Dict[str, str] = {}
        for name, data in self._skills.items():
            # canonical name itself
            out[name.lower()] = name
            for alias in data.get("aliases", []):
                out[alias.lower()] = name
        return out

    @cached_property
    def transfer_edges(self) -> List[Tuple[str, str, float]]:
        """All (from, to, weight) transfer-learning edges."""
        edges = []
        for from_skill, data in self._skills.items():
            for to_skill, weight in data.get("transfers_to", {}).items():
                edges.append((from_skill, to_skill, float(weight)))
        return edges

    def skills_by_category(self, category: str) -> List[str]:
        return [n for n, d in self._skills.items() if d.get("category") == category]

    def normalize(self, raw_name: str) -> str | None:
        """Normalize a raw skill name to canonical form via alias_map. None if unknown."""
        return self.alias_map.get(raw_name.lower())


# Singleton for import convenience
_loader: SkillLoader | None = None


def get_loader() -> SkillLoader:
    global _loader
    if _loader is None:
        _loader = SkillLoader()
    return _loader
