"""Resume domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class ResumeSection:
    title: str
    content: str
    order: int = 0


@dataclass
class Resume:
    user_id: str
    version: str
    target_company: str
    target_title: str
    template_used: str

    summary: str = ""
    sections: List[ResumeSection] = field(default_factory=list)

    output_path: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    evidence_count: int = 0

    def to_markdown(self) -> str:
        lines = [f"# {self.user_id}\n"]
        lines.append(f"**{self.target_title}** | {self.target_company}\n")
        lines.append(f"\n## Summary\n\n{self.summary}\n")
        for section in sorted(self.sections, key=lambda s: s.order):
            lines.append(f"\n## {section.title}\n\n{section.content}\n")
        return "\n".join(lines)
