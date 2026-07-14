"""
Feature Registry — gradual rollout + A/B testing support.

Features are declarative YAML files under features/*/feature.yaml.
This module loads them and provides is_enabled() with deterministic
rollout (same user_id always gets same result).

Usage:
    from features import feature_registry

    if feature_registry.is_enabled("target_aware_resume", user_id="abdullokh"):
        # Show new feature
"""

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class FeatureRegistry:
    """
    Singleton feature registry.

    Features:
    - YAML-based metadata (declarative)
    - Deterministic rollout (hash-based, reproducible)
    - Dependency checking
    - Metrics tracking interface
    """

    _instance: Optional["FeatureRegistry"] = None
    _features: Dict[str, Dict[str, Any]]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._features = {}
            cls._instance._load_features()
        return cls._instance

    def _load_features(self):
        features_dir = Path(__file__).parent

        for feature_dir in features_dir.iterdir():
            if not feature_dir.is_dir():
                continue

            feature_yaml = feature_dir / "feature.yaml"
            if not feature_yaml.exists():
                continue

            try:
                with open(feature_yaml, encoding="utf-8") as f:
                    metadata = yaml.safe_load(f)

                name = metadata.get("name")
                if not name:
                    continue

                self._features[name] = {**metadata, "path": str(feature_dir)}

            except Exception as e:
                print(f"[FeatureRegistry] Failed to load {feature_yaml}: {e}")

    def get_feature(self, name: str) -> Optional[Dict[str, Any]]:
        return self._features.get(name)

    def list_features(self) -> List[str]:
        return list(self._features.keys())

    def is_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if feature is enabled for a user.

        Rollout logic:
        - feature.enabled = False  → always False
        - rollout_percentage >= 100 → always True
        - rollout_percentage <= 0  → always False
        - otherwise: deterministic SHA-256 hash of (name, user_id) % 100
          so the same user always lands in the same bucket (stable A/B).
        """
        feature = self._features.get(name)
        if not feature:
            return False

        if not feature.get("enabled", False):
            return False

        rollout = feature.get("rollout_percentage", 100)

        if rollout >= 100:
            return True
        if rollout <= 0:
            return False

        if user_id is None:
            return True

        bucket = self.get_rollout_bucket(name, user_id)
        return bucket < rollout

    def get_enabled_features(self, user_id: Optional[str] = None) -> List[str]:
        return [n for n in self._features if self.is_enabled(n, user_id)]

    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """Return {dep_name: is_enabled} for each declared dependency."""
        feature = self._features.get(name)
        if not feature:
            return {}
        return {dep: self.is_enabled(dep) for dep in feature.get("dependencies", [])}

    def get_rollout_bucket(self, name: str, user_id: str) -> int:
        """Deterministic bucket 0-99 for a (feature, user) pair."""
        hash_input = f"{name}:{user_id}"
        return int(hashlib.sha256(hash_input.encode()).hexdigest(), 16) % 100

    def reload(self):
        """Force reload all features (useful in tests)."""
        self._features.clear()
        self._load_features()


feature_registry = FeatureRegistry()
