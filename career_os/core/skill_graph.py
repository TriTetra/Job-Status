"""
Skill taxonomy and transfer learning graph.
"""

import networkx as nx
from typing import List, Dict, Tuple
from core.domain.identity.skill import Skill


class SkillGraph:
    """
    Hierarchical skill relationships with transfer learning coefficients.

    This models:
    1. Skill families (Python → FastAPI, Django, etc.)
    2. Transfer learning (Java → Spring Boot is easier than Python → Spring Boot)
    3. Optimal learning paths
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_taxonomy()

    def _build_taxonomy(self):
        """Load skill graph from YAML, fall back to hardcoded edges if YAML unavailable."""
        try:
            from core.knowledge import SkillLoader
            loader = SkillLoader()
            for from_skill, to_skill, weight in loader.transfer_edges:
                self.graph.add_edge(from_skill, to_skill, weight=weight)
            return
        except Exception:
            pass
        self._build_taxonomy_hardcoded()

    def _build_taxonomy_hardcoded(self):
        """
        Build complete skill relationship graph.

        Transfer weights (0.0-1.0):
        - 0.9+: Almost identical (React → Next.js)
        - 0.7-0.9: Strong transfer (Python → FastAPI)
        - 0.5-0.7: Moderate transfer (Python → Go)
        - 0.3-0.5: Weak transfer (Java → Python)
        - <0.3: Minimal transfer (Python → Rust)
        """

        # ===================================================================
        # PROGRAMMING LANGUAGES
        # ===================================================================

        # Python family
        self._add_family("Python", [
            ("FastAPI", 0.8),
            ("Django", 0.8),
            ("Flask", 0.8),
            ("NumPy", 0.7),
            ("Pandas", 0.7),
            ("PyTorch", 0.7),
            ("TensorFlow", 0.7),
            ("scikit-learn", 0.7),
            ("LangChain", 0.7),
            ("Hugging Face", 0.7),
        ])

        # Java family
        self._add_family("Java", [
            ("Spring Boot", 0.9),
            ("Hibernate", 0.8),
            ("Maven", 0.7),
            ("Gradle", 0.7),
            ("Kotlin", 0.8),
        ])

        # JavaScript family
        self._add_family("JavaScript", [
            ("TypeScript", 0.9),
            ("Node.js", 0.8),
            ("React", 0.7),
            ("Vue", 0.7),
            ("Angular", 0.7),
            ("Express.js", 0.8),
            ("Next.js", 0.7),
        ])

        # TypeScript family
        self._add_family("TypeScript", [
            ("React", 0.8),
            ("Next.js", 0.8),
            ("Node.js", 0.8),
            ("NestJS", 0.8),
        ])

        # React family
        self._add_family("React", [
            ("Next.js", 0.9),
            ("React Native", 0.8),
        ])

        # Go family
        self._add_family("Go", [
            ("gRPC", 0.8),
            ("Kubernetes", 0.6),
        ])

        # Rust family
        self._add_family("Rust", [
            ("Systems Programming", 0.9),
        ])

        # ===================================================================
        # INFRASTRUCTURE & CLOUD
        # ===================================================================

        # Docker family
        self._add_family("Docker", [
            ("Docker Compose", 0.9),
            ("Kubernetes", 0.7),
            ("Podman", 0.8),
        ])

        # Kubernetes family
        self._add_family("Kubernetes", [
            ("Helm", 0.8),
            ("Istio", 0.7),
            ("ArgoCD", 0.7),
        ])

        # AWS family
        self._add_family("AWS", [
            ("Lambda", 0.7),
            ("EC2", 0.7),
            ("S3", 0.7),
            ("RDS", 0.7),
            ("ECS", 0.7),
            ("EKS", 0.7),
            ("CloudFormation", 0.7),
            ("SageMaker", 0.6),
        ])

        # Terraform family
        self._add_family("Terraform", [
            ("CloudFormation", 0.6),
            ("Ansible", 0.5),
        ])

        # ===================================================================
        # DATABASES
        # ===================================================================

        # SQL family
        self._add_family("PostgreSQL", [
            ("MySQL", 0.8),
            ("SQL", 0.9),
        ])

        self._add_family("MySQL", [
            ("PostgreSQL", 0.8),
            ("SQL", 0.9),
        ])

        # NoSQL family
        self._add_family("MongoDB", [
            ("DynamoDB", 0.6),
            ("Cassandra", 0.5),
        ])

        # ===================================================================
        # ML/AI
        # ===================================================================

        # PyTorch family
        self._add_family("PyTorch", [
            ("Computer Vision", 0.7),
            ("NLP", 0.7),
            ("Transformers", 0.7),
            ("YOLO", 0.6),
        ])

        # TensorFlow family
        self._add_family("TensorFlow", [
            ("Keras", 0.9),
            ("TensorFlow Lite", 0.8),
        ])

        # LLM family
        self._add_family("LLM", [
            ("LangChain", 0.8),
            ("Hugging Face", 0.7),
            ("RAG", 0.7),
            ("AI Agents", 0.6),
        ])

        # ===================================================================
        # CROSS-LANGUAGE TRANSFERS
        # ===================================================================

        # Similar paradigms
        self.graph.add_edge("Python", "JavaScript", weight=0.5)
        self.graph.add_edge("JavaScript", "Python", weight=0.5)
        self.graph.add_edge("Python", "Go", weight=0.4)
        self.graph.add_edge("Java", "Kotlin", weight=0.9)
        self.graph.add_edge("Java", "Scala", weight=0.7)
        self.graph.add_edge("Java", "C#", weight=0.6)
        self.graph.add_edge("JavaScript", "TypeScript", weight=0.9)

        # Frontend frameworks
        self.graph.add_edge("React", "Vue", weight=0.7)
        self.graph.add_edge("React", "Angular", weight=0.6)
        self.graph.add_edge("Vue", "React", weight=0.7)

        # Cloud platforms
        self.graph.add_edge("AWS", "GCP", weight=0.6)
        self.graph.add_edge("AWS", "Azure", weight=0.6)
        self.graph.add_edge("GCP", "AWS", weight=0.6)

        # Databases
        self.graph.add_edge("PostgreSQL", "MySQL", weight=0.9)
        self.graph.add_edge("MongoDB", "DynamoDB", weight=0.7)

    def _add_family(self, parent: str, children: List[Tuple[str, float]]):
        """
        Add a skill family with transfer weights.

        Args:
            parent: Parent skill
            children: List of (child_skill, transfer_weight) tuples
        """
        for child, weight in children:
            self.graph.add_edge(parent, child, weight=weight)

    def get_transfer_factor(self, from_skill: str, to_skill: str) -> float:
        """
        Get transfer learning coefficient between two skills.

        Args:
            from_skill: Skill you already know
            to_skill: Skill you want to learn

        Returns:
            Transfer coefficient (0.0-1.0). Higher = easier to learn.
        """
        if from_skill == to_skill:
            return 1.0

        if not self.graph.has_edge(from_skill, to_skill):
            # Try reverse edge
            if self.graph.has_edge(to_skill, from_skill):
                return self.graph[to_skill][from_skill]['weight'] * 0.8
            return 0.0

        return self.graph[from_skill][to_skill]['weight']

    def shortest_learning_path(self,
                                known_skills: List[str],
                                target_skill: str) -> List[str]:
        """
        Find optimal learning path from known skills to target.

        Args:
            known_skills: Skills you already know
            target_skill: Skill you want to learn

        Returns:
            Shortest path (list of skills). Empty if target already known.
        """
        if target_skill in known_skills:
            return []

        # Skills outside the hardcoded taxonomy (most real job postings
        # mention skills this graph doesn't know about) have no path to find.
        if not self.graph.has_node(target_skill):
            return [target_skill]

        best_path = None
        min_cost = float('inf')

        for skill in known_skills:
            if not self.graph.has_node(skill):
                continue

            try:
                path = nx.shortest_path(
                    self.graph,
                    skill,
                    target_skill,
                    weight=lambda u, v, d: 1 - d['weight']  # Invert: high weight = low cost
                )

                # Calculate path cost
                cost = 0
                for i in range(len(path) - 1):
                    edge_weight = self.graph[path[i]][path[i + 1]]['weight']
                    cost += (1 - edge_weight)

                if cost < min_cost:
                    min_cost = cost
                    best_path = path

            except nx.NetworkXNoPath:
                continue

        # If no path found, direct learning
        return best_path[1:] if best_path else [target_skill]

    def get_related_skills(self, skill: str, max_distance: int = 2) -> Dict[str, float]:
        """
        Get all skills related to a given skill within distance.

        Args:
            skill: Source skill
            max_distance: Maximum graph distance

        Returns:
            Dict of {related_skill: transfer_factor}
        """
        if not self.graph.has_node(skill):
            return {}

        related = {}

        # BFS to find related skills
        for node in nx.single_source_shortest_path_length(
            self.graph, skill, cutoff=max_distance
        ):
            if node == skill:
                continue

            # Calculate cumulative transfer factor
            try:
                path = nx.shortest_path(self.graph, skill, node)
                transfer = 1.0

                for i in range(len(path) - 1):
                    edge_weight = self.graph[path[i]][path[i + 1]]['weight']
                    transfer *= edge_weight

                related[node] = transfer

            except nx.NetworkXNoPath:
                continue

        return related

    def calculate_learning_discount(self,
                                    known_skills: List[Skill],
                                    target_skill: str) -> float:
        """
        Calculate learning cost discount from related skills.

        Args:
            known_skills: Skills you know with proficiency levels
            target_skill: Skill to learn

        Returns:
            Discount factor (0.3-1.0). Lower = bigger discount (less time needed).
        """
        discount = 1.0

        for skill in known_skills:
            transfer = self.get_transfer_factor(skill.name, target_skill)

            if transfer > 0:
                # Higher skill level = better transfer
                skill_contribution = skill.level / 5.0

                # Reduce cost proportionally
                discount *= (1 - transfer * skill_contribution)

        # Maximum 70% discount
        return max(discount, 0.3)

    def visualize_path(self, path: List[str]) -> str:
        """
        Create ASCII visualization of learning path.

        Args:
            path: List of skills in order

        Returns:
            ASCII diagram
        """
        if not path:
            return "Already proficient"

        diagram = []
        for i, skill in enumerate(path):
            if i == 0:
                diagram.append(f"START: {skill}")
            elif i == len(path) - 1:
                diagram.append(f"  ↓\nTARGET: {skill}")
            else:
                diagram.append(f"  ↓\n  {skill}")

        return "\n".join(diagram)
