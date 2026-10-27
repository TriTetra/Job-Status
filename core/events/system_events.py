"""System-level events."""

from dataclasses import dataclass, field
from typing import Dict, List

from .event_types import Event


@dataclass
class WeeklyReportGenerated(Event):
    """Weekly briefing generated."""

    user_id: str = ""
    week_start: str = ""
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    new_jobs_this_week: int = 0
    applications_submitted: int = 0
    interviews_scheduled: int = 0


@dataclass
class ModelCalibrated(Event):
    """ML model recalibrated from feedback data."""

    model_name: str = ""
    old_weights: Dict[str, float] = field(default_factory=dict)
    new_weights: Dict[str, float] = field(default_factory=dict)
    training_samples: int = 0
    accuracy_improvement: float = 0.0


@dataclass
class FeatureToggled(Event):
    """Feature flag changed."""

    feature_name: str = ""
    enabled: bool = False
    rollout_percentage: int = 100
    changed_by: str = ""
