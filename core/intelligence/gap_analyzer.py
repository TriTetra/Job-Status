"""
ROI-optimized skill gap analysis.
"""

from dataclasses import dataclass
from typing import List, Dict
from collections import Counter

from core.domain import SkillLevel, UserProfile, Job
from career_os.core.skill_graph import SkillGraph


@dataclass
class SkillGap:
    """Represents a skill gap with learning metadata."""

    skill: str
    current_level: SkillLevel
    target_level: SkillLevel

    learning_cost_hours: int
    """Estimated hours to reach target level (with transfer discount)"""

    learning_path: List[str]
    """Optimal learning path through skill graph"""

    impact_score: float
    """Career value of learning this skill"""

    roi: float
    """Return on investment: impact per hour"""

    resources: List[str]
    """Recommended learning resources"""

    validation_project: str
    """Project to validate mastery"""

    jobs_unlocked: int
    """Number of target jobs requiring this skill"""

    def __repr__(self) -> str:
        return f"SkillGap({self.skill}, ROI={self.roi:.2f}, {self.learning_cost_hours}h)"


@dataclass
class LearningTask:
    """Single learning task in a roadmap."""

    skill: str
    start_week: int
    duration_weeks: int
    hours_per_week: int
    total_hours: int
    resources: List[str]
    validation: str
    impact: float


@dataclass
class LearningRoadmap:
    """Complete learning plan."""

    tasks: List[LearningTask]
    total_weeks: int
    total_hours: int
    expected_fit_improvement: float
    """Expected improvement in job match scores"""

    def summary(self) -> str:
        """Generate summary text."""
        lines = [
            f"Learning Roadmap: {self.total_weeks} weeks, {self.total_hours} hours",
            f"Expected fit improvement: +{self.expected_fit_improvement:.0f}%",
            "",
            "Timeline:"
        ]

        for task in self.tasks:
            lines.append(
                f"  Week {task.start_week}-{task.start_week + task.duration_weeks - 1}: "
                f"{task.skill} ({task.total_hours}h)"
            )

        return "\n".join(lines)


class GapAnalyzer:
    """
    Analyze skill gaps and generate ROI-optimized learning plans.
    """

    def __init__(self):
        self.skill_graph = SkillGraph()

        # Learning resources database
        self.resources = self._build_resource_db()

        # Validation projects
        self.projects = self._build_project_db()

    def analyze(self,
                user: UserProfile,
                target_jobs: List[Job],
                target_level: SkillLevel = SkillLevel.WORKING) -> List[SkillGap]:
        """
        Analyze skill gaps against target jobs.

        Args:
            user: User profile
            target_jobs: Jobs to target
            target_level: Minimum proficiency to aim for

        Returns:
            List of SkillGaps sorted by ROI (highest first)
        """

        # Aggregate skill demand across jobs
        skill_demand = self._aggregate_requirements(target_jobs)

        # Build skill map
        user_skill_map = {s.name.lower(): s for s in user.skills}

        gaps = []

        for skill_name, job_count in skill_demand.items():
            skill_lower = skill_name.lower()

            # Current level
            if skill_lower in user_skill_map:
                current = user_skill_map[skill_lower]
                current_level = current.level
            else:
                current_level = SkillLevel.UNKNOWN

            # Skip if already proficient
            if current_level >= target_level:
                continue

            # Base learning cost
            base_cost = self._estimate_base_cost(skill_name, current_level, target_level)

            # Transfer learning discount
            discount = self.skill_graph.calculate_learning_discount(user.skills, skill_name)

            actual_cost = int(base_cost * discount)

            # Impact calculation
            impact = self._calculate_impact(skill_name, target_jobs, job_count)

            # ROI
            roi = impact / actual_cost if actual_cost > 0 else 0

            # Learning path
            path = self.skill_graph.shortest_learning_path(
                [s.name for s in user.skills],
                skill_name
            )

            # Resources and project
            resources = self.resources.get(skill_name, [f"Search: {skill_name} tutorial"])
            project = self.projects.get(skill_name, f"Build demo project with {skill_name}")

            gaps.append(SkillGap(
                skill=skill_name,
                current_level=current_level,
                target_level=target_level,
                learning_cost_hours=actual_cost,
                learning_path=path,
                impact_score=impact,
                roi=roi,
                resources=resources,
                validation_project=project,
                jobs_unlocked=job_count
            ))

        # Sort by ROI descending
        return sorted(gaps, key=lambda g: g.roi, reverse=True)

    def create_roadmap(self,
                      gaps: List[SkillGap],
                      hours_per_week: int = 10,
                      max_weeks: int = 8) -> LearningRoadmap:
        """
        Generate optimal learning roadmap.

        Args:
            gaps: Skill gaps to learn
            hours_per_week: Available study hours per week
            max_weeks: Maximum timeline

        Returns:
            LearningRoadmap with scheduled tasks
        """

        # Topological sort (prerequisites first)
        ordered = self._topological_sort(gaps)

        tasks = []
        current_week = 1
        total_hours = 0
        total_impact = 0

        for gap in ordered:
            # Calculate weeks needed
            weeks_needed = max(1, int(np.ceil(gap.learning_cost_hours / hours_per_week)))

            # Check if we have time
            if current_week + weeks_needed > max_weeks:
                break

            task = LearningTask(
                skill=gap.skill,
                start_week=current_week,
                duration_weeks=weeks_needed,
                hours_per_week=min(hours_per_week, gap.learning_cost_hours),
                total_hours=gap.learning_cost_hours,
                resources=gap.resources,
                validation=gap.validation_project,
                impact=gap.impact_score
            )

            tasks.append(task)

            current_week += weeks_needed
            total_hours += gap.learning_cost_hours
            total_impact += gap.impact_score

        return LearningRoadmap(
            tasks=tasks,
            total_weeks=current_week - 1,
            total_hours=total_hours,
            expected_fit_improvement=total_impact
        )

    def _aggregate_requirements(self, jobs: List[Job]) -> Dict[str, int]:
        """
        Count how many jobs require each skill.

        Args:
            jobs: Target jobs

        Returns:
            Dict of {skill: count}
        """
        all_skills = []

        for job in jobs:
            all_skills.extend(job.required_skills)
            all_skills.extend(job.preferred_skills)

        # Normalize case
        all_skills = [s.strip() for s in all_skills]

        # Count
        return dict(Counter(all_skills))

    def _estimate_base_cost(self,
                           skill: str,
                           current: SkillLevel,
                           target: SkillLevel) -> int:
        """
        Estimate base learning hours (before transfer discount).

        Args:
            skill: Skill name
            current: Current level
            target: Target level

        Returns:
            Hours estimate
        """
        if target <= current:
            return 0

        # Base hours per level
        level_hours = {
            SkillLevel.AI_ASSISTED: 10,
            SkillLevel.WORKING: 20,
            SkillLevel.INDEPENDENT: 40,
            SkillLevel.ADVANCED: 80,
            SkillLevel.EXPERT: 160
        }

        total = 0
        for level in range(current + 1, target + 1):
            total += level_hours.get(SkillLevel(level), 20)

        return total

    def _calculate_impact(self,
                         skill: str,
                         jobs: List[Job],
                         job_count: int) -> float:
        """
        Calculate career impact of learning this skill.

        Factors:
        - Number of jobs requiring it
        - Salary potential
        - Market demand trend

        Args:
            skill: Skill name
            jobs: All target jobs
            job_count: Jobs requiring this skill

        Returns:
            Impact score (higher = more valuable)
        """

        # Base: jobs unlocked (weight: 2x)
        impact = job_count * 2.0

        # Salary impact (if data available)
        skill_salaries = []
        for job in jobs:
            if skill in job.all_skills() and job.salary_min:
                skill_salaries.append(job.salary_min)

        if skill_salaries:
            avg_salary = sum(skill_salaries) / len(skill_salaries)
            # Normalize to 0-10 scale
            salary_impact = min(avg_salary / 15000, 10)
            impact += salary_impact

        # Market demand (heuristic - could use real data)
        high_demand = ['AWS', 'Kubernetes', 'Python', 'React', 'LLM', 'PyTorch']
        if skill in high_demand:
            impact += 5.0

        return impact

    def _topological_sort(self, gaps: List[SkillGap]) -> List[SkillGap]:
        """
        Sort skills by learning dependencies.

        Args:
            gaps: Unsorted gaps

        Returns:
            Sorted gaps (prerequisites first)
        """

        # Simple heuristic: if skill A appears in path to skill B, A comes first
        ordered = []
        remaining = list(gaps)

        while remaining:
            # Find skill with no dependencies in remaining
            for gap in remaining:
                # Check if any other remaining skill requires this one
                is_dependency = False

                for other in remaining:
                    if other == gap:
                        continue

                    if gap.skill in other.learning_path:
                        is_dependency = True
                        break

                if not is_dependency:
                    ordered.append(gap)
                    remaining.remove(gap)
                    break
            else:
                # No clear dependencies - just take first
                ordered.append(remaining.pop(0))

        return ordered

    def _build_resource_db(self) -> Dict[str, List[str]]:
        """Build learning resources database."""
        return {
            'AWS': [
                'AWS Free Tier (hands-on practice)',
                'AWS Skill Builder (official courses)',
                'freeCodeCamp AWS tutorial',
            ],
            'Kubernetes': [
                'Kubernetes.io official tutorials',
                'Play with Kubernetes (free lab)',
                'TechWorld with Nana (YouTube)',
            ],
            'Docker': [
                'Docker official getting started',
                'Docker for Beginners (freeCodeCamp)',
            ],
            'React': [
                'React official tutorial',
                'Full Stack Open (free course)',
            ],
            'PyTorch': [
                'PyTorch official tutorials',
                'Fast.ai course (free)',
            ],
            'FastAPI': [
                'FastAPI official tutorial',
                'Build REST API course (YouTube)',
            ],
        }

    def _build_project_db(self) -> Dict[str, str]:
        """Build validation project database."""
        return {
            'AWS': 'Deploy ML model to AWS Lambda with API Gateway',
            'Kubernetes': 'Deploy multi-container app to local Kubernetes',
            'Docker': 'Dockerize existing Python project with multi-stage build',
            'React': 'Build interactive dashboard with React + hooks',
            'PyTorch': 'Train image classifier from scratch',
            'FastAPI': 'Build REST API with auth + database',
            'LLM': 'Build RAG chatbot with LangChain',
            'Terraform': 'Provision AWS infrastructure with Terraform',
        }


# Utility import
import numpy as np
