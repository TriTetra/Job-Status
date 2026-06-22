"""
Skill models with AI-adjusted proficiency levels.
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


class SkillLevel(IntEnum):
    """
    AI-adjusted skill proficiency levels.

    This represents actual capability, not just exposure.
    """

    UNKNOWN = 0
    """No experience with this skill."""

    AI_ASSISTED = 1
    """Can accomplish tasks with AI assistance (Cursor, Claude, GPT).

    Examples:
    - Generated code with Cursor/Copilot
    - Used ChatGPT for implementation
    - Can debug with AI help
    - Familiar with concepts but needs guidance
    """

    WORKING = 2
    """Can handle small-medium tasks independently with occasional AI help.

    Examples:
    - Can implement features from specs
    - Understands core concepts
    - Needs AI for complex edge cases
    - Can maintain existing code
    """

    INDEPENDENT = 3
    """Self-sufficient with documentation. Minimal AI needed.

    Examples:
    - Can design and implement features
    - Reads docs and applies knowledge
    - Uses AI for productivity, not necessity
    - Can troubleshoot independently
    """

    ADVANCED = 4
    """Can optimize, architect, and handle complex scenarios.

    Examples:
    - Designs system architecture
    - Optimizes performance
    - Handles production issues
    - Knows internals and best practices
    """

    EXPERT = 5
    """Teaching level. Deep expertise.

    Examples:
    - Contributes to open source
    - Writes technical articles
    - Mentors others
    - Recognized authority
    """


@dataclass
class Skill:
    """
    Represents a technical skill with proficiency level and learning metadata.
    """

    name: str
    level: SkillLevel

    # Evidence of proficiency
    evidence: List[str] = field(default_factory=list)
    """
    Projects, experiences, or achievements demonstrating this skill.
    Example: ["Built YOLOv8 system with 92% mAP", "Production deployment on AWS"]
    """

    # AI usage factor
    ai_multiplier: float = 1.0
    """
    How much AI assistance was used (0.0 = all AI, 1.0 = no AI).
    This adjusts effective skill level for matching.
    """

    # Learning characteristics
    base_hours_to_next_level: int = 20
    """Estimated hours to reach next proficiency level."""

    last_used: Optional[datetime] = None
    """When this skill was last applied (for decay modeling)."""

    # Transfer learning
    transferability: Dict[str, float] = field(default_factory=dict)
    """
    Related skills and transfer learning coefficients.
    Example: {"Spring Boot": 0.8, "Hibernate": 0.6} for Java
    """

    def learning_cost(self, target_level: SkillLevel) -> int:
        """
        Calculate hours needed to reach target proficiency level.

        Args:
            target_level: Desired proficiency level

        Returns:
            Estimated learning hours
        """
        if target_level <= self.level:
            return 0

        levels_to_gain = target_level - self.level
        cost = 0

        # Each level requires more time (exponential)
        for i in range(levels_to_gain):
            multiplier = 1.5 ** i
            cost += self.base_hours_to_next_level * multiplier

        return int(cost)

    def transfer_discount(self, related_skills: List['Skill']) -> float:
        """
        Calculate learning cost reduction from related skills.

        Transfer learning: knowing Python makes learning Go easier.

        Args:
            related_skills: Skills you already know

        Returns:
            Discount factor (0.3-1.0). Lower = bigger discount.
        """
        if not self.transferability:
            return 1.0  # No discount

        discount = 1.0

        for skill in related_skills:
            if skill.name in self.transferability:
                transfer_factor = self.transferability[skill.name]

                # Higher skill level = better transfer
                skill_contribution = skill.level / 5.0

                # Reduce cost proportionally
                discount *= (1 - transfer_factor * skill_contribution)

        # Maximum 70% discount
        return max(discount, 0.3)

    def effective_level(self) -> float:
        """
        Effective skill level adjusted for AI assistance.

        Returns:
            Adjusted level (0.0-5.0)
        """
        return float(self.level) * self.ai_multiplier

    def __repr__(self) -> str:
        return f"Skill({self.name}, L{self.level.value})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Skill):
            return self.name == other.name
        return False


# Predefined skill categories for organization
SKILL_CATEGORIES = {
    'languages': [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'Go', 'Rust',
        'C++', 'C#', 'Kotlin', 'Swift', 'Ruby', 'PHP', 'Scala'
    ],
    'ml_ai': [
        'Machine Learning', 'Deep Learning', 'Computer Vision', 'NLP',
        'PyTorch', 'TensorFlow', 'scikit-learn', 'Hugging Face',
        'LangChain', 'LLM', 'Transformers', 'YOLO', 'OpenCV',
        'AI Agents', 'RAG', 'Vector Databases'
    ],
    'backend': [
        'FastAPI', 'Django', 'Flask', 'Spring Boot', 'Express.js',
        'Node.js', 'gRPC', 'GraphQL', 'REST API', 'WebSockets'
    ],
    'frontend': [
        'React', 'Next.js', 'Vue', 'Angular', 'Svelte',
        'HTML', 'CSS', 'Tailwind', 'Material-UI'
    ],
    'databases': [
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'DynamoDB', 'Cassandra', 'Neo4j', 'SQLite'
    ],
    'cloud_infra': [
        'AWS', 'GCP', 'Azure', 'Docker', 'Kubernetes',
        'Terraform', 'Ansible', 'CI/CD', 'Jenkins', 'GitHub Actions',
        'Lambda', 'EC2', 'S3', 'CloudFormation'
    ],
    'data_engineering': [
        'Spark', 'Kafka', 'Airflow', 'dbt', 'Snowflake',
        'Databricks', 'Hadoop', 'Flink'
    ],
    'tools': [
        'Git', 'Linux', 'Bash', 'Vim', 'VS Code', 'IntelliJ',
        'Postman', 'Jupyter', 'Docker Compose'
    ]
}


def categorize_skill(skill_name: str) -> Optional[str]:
    """
    Find category for a skill.

    Args:
        skill_name: Name of the skill

    Returns:
        Category name or None if not found
    """
    for category, skills in SKILL_CATEGORIES.items():
        if skill_name in skills:
            return category
    return None
