"""Skill domain entity — AI-adjusted proficiency levels."""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


class SkillLevel(IntEnum):
    """AI-adjusted skill proficiency levels."""

    UNKNOWN = 0
    AI_ASSISTED = 1
    WORKING = 2
    INDEPENDENT = 3
    ADVANCED = 4
    EXPERT = 5


@dataclass
class Skill:
    """A technical skill with proficiency level and learning metadata."""

    name: str
    level: SkillLevel

    evidence: List[str] = field(default_factory=list)
    ai_multiplier: float = 1.0
    base_hours_to_next_level: int = 20
    last_used: Optional[datetime] = None
    transferability: Dict[str, float] = field(default_factory=dict)

    def learning_cost(self, target_level: SkillLevel) -> int:
        if target_level <= self.level:
            return 0
        cost = 0
        for i in range(target_level - self.level):
            cost += self.base_hours_to_next_level * (1.5 ** i)
        return int(cost)

    def transfer_discount(self, related_skills: List["Skill"]) -> float:
        if not self.transferability:
            return 1.0
        discount = 1.0
        for skill in related_skills:
            if skill.name in self.transferability:
                discount *= 1 - self.transferability[skill.name] * (skill.level / 5.0)
        return max(discount, 0.3)

    def effective_level(self) -> float:
        return float(self.level) * self.ai_multiplier

    def __repr__(self) -> str:
        return f"Skill({self.name}, L{self.level.value})"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, Skill):
            return self.name == other.name
        return False


SKILL_CATEGORIES: Dict[str, List[str]] = {
    "languages": [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
        "C++", "C#", "Kotlin", "Swift", "Ruby", "PHP", "Scala",
    ],
    "ml_ai": [
        "Machine Learning", "Deep Learning", "Computer Vision", "NLP",
        "PyTorch", "TensorFlow", "scikit-learn", "Hugging Face",
        "LangChain", "LLM", "Transformers", "YOLO", "OpenCV",
        "AI Agents", "RAG", "Vector Databases",
    ],
    "backend": [
        "FastAPI", "Django", "Flask", "Spring Boot", "Express.js",
        "Node.js", "gRPC", "GraphQL", "REST API", "WebSockets",
    ],
    "frontend": [
        "React", "Next.js", "Vue", "Angular", "Svelte",
        "HTML", "CSS", "Tailwind", "Material-UI",
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "Neo4j", "SQLite",
    ],
    "cloud_infra": [
        "AWS", "GCP", "Azure", "Docker", "Kubernetes",
        "Terraform", "Ansible", "CI/CD", "Jenkins", "GitHub Actions",
        "Lambda", "EC2", "S3", "CloudFormation",
    ],
    "data_engineering": [
        "Spark", "Kafka", "Airflow", "dbt", "Snowflake",
        "Databricks", "Hadoop", "Flink",
    ],
    "tools": [
        "Git", "Linux", "Bash", "Vim", "VS Code", "IntelliJ",
        "Postman", "Jupyter", "Docker Compose",
    ],
}


def categorize_skill(skill_name: str) -> Optional[str]:
    for category, skills in SKILL_CATEGORIES.items():
        if skill_name in skills:
            return category
    return None
