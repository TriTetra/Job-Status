"""
Semantic job matching with multi-aspect scoring.
"""

from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from core.domain import UserProfile, Job, MatchResult, Skill, SkillLevel
from career_os.core.skill_graph import SkillGraph


class SemanticMatcher:
    """
    Multi-dimensional semantic job matching.

    Matches jobs to user profiles across multiple aspects:
    1. Technical skills (with level awareness)
    2. Domain experience (semantic similarity)
    3. Seniority level (years + responsibilities)
    4. Work mode preferences (remote/hybrid/onsite)
    5. AI capability bonus
    """

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize matcher.

        Args:
            model_name: SentenceTransformer model to use
                - 'all-mpnet-base-v2': Best quality (420MB)
                - 'all-MiniLM-L6-v2': Faster, smaller (80MB)
        """
        print(f"Loading embedding model: {model_name}...")
        self.encoder = SentenceTransformer(model_name)
        self.skill_graph = SkillGraph()
        print("Semantic matcher ready")

    def match(self, user: UserProfile, job: Job) -> MatchResult:
        """
        Comprehensive multi-aspect matching.

        Args:
            user: User profile
            job: Job posting

        Returns:
            MatchResult with overall score and breakdown
        """

        # Component 1: Technical Skills (40% weight)
        skill_score = self._match_skills(user.skills, job.all_skills())

        # Component 2: Domain Experience (25% weight)
        domain_score = self._match_domain(user, job)

        # Component 3: Seniority Level (20% weight)
        level_score = self._match_level(user.years_experience, job.required_years)

        # Component 4: Work Mode (10% weight)
        mode_score = self._match_work_mode(user.preferences, job)

        # Component 5: AI Capability Bonus (5% weight)
        ai_bonus = self._calculate_ai_bonus(user.ai_proficiency, job.description)

        # Weighted combination
        raw_score = (
            0.40 * skill_score +
            0.25 * domain_score +
            0.20 * level_score +
            0.10 * mode_score +
            0.05 * ai_bonus
        )

        # Scale to 0-100
        overall = raw_score * 100

        # Identify skill gaps
        gaps = self._identify_gaps(user.skills, job.required_skills)

        # Calculate confidence
        confidence = self._calculate_confidence(user, job, skill_score, domain_score)

        # Generate explanation
        explanation = self._generate_explanation(
            overall, skill_score, domain_score, level_score, gaps
        )

        return MatchResult(
            job=job,
            overall_score=overall,
            breakdown={
                'technical_skills': skill_score * 100,
                'domain_experience': domain_score * 100,
                'seniority_level': level_score * 100,
                'work_mode': mode_score * 100,
                'ai_capability': ai_bonus * 100
            },
            skill_gaps=gaps,
            confidence=confidence,
            explanation=explanation
        )

    def _match_skills(self, user_skills: List[Skill], required_skills: List[str]) -> float:
        """
        Match technical skills with level awareness and transfer learning.

        Scoring:
        - Exact match at INDEPENDENT+: 1.0
        - Exact match at WORKING: 0.7
        - Exact match at AI_ASSISTED: 0.4
        - Transfer learning: 0.0-0.5 based on related skills

        Args:
            user_skills: User's skills with proficiency levels
            required_skills: Job's required skills

        Returns:
            Score 0.0-1.0
        """
        if not required_skills:
            return 1.0

        user_skill_map = {s.name.lower(): s for s in user_skills}

        total_score = 0.0

        for req_skill in required_skills:
            req_lower = req_skill.lower()

            # Exact match
            if req_lower in user_skill_map:
                skill = user_skill_map[req_lower]

                # Level-based scoring
                if skill.level >= SkillLevel.INDEPENDENT:
                    score = 1.0
                elif skill.level == SkillLevel.WORKING:
                    score = 0.7
                elif skill.level == SkillLevel.AI_ASSISTED:
                    score = 0.4
                else:
                    score = 0.0

                # Adjust for AI multiplier
                score *= skill.ai_multiplier

                total_score += score
            else:
                # Check transfer learning
                transfer_score = self._check_transfer(user_skills, req_skill)
                total_score += transfer_score

        return total_score / len(required_skills)

    def _check_transfer(self, user_skills: List[Skill], target: str) -> float:
        """
        Score from transferable skills.

        Example: Knowing Python at L3 gives partial credit for FastAPI

        Args:
            user_skills: Skills user knows
            target: Skill required by job

        Returns:
            Transfer score 0.0-0.5
        """
        best_transfer = 0.0

        for skill in user_skills:
            # Get transfer coefficient
            factor = self.skill_graph.get_transfer_factor(skill.name, target)

            if factor > 0:
                # Adjust by skill level (higher = better transfer)
                level_factor = skill.level / 5.0

                # Cap at 0.5 (half credit for transfer)
                adjusted = factor * level_factor * 0.5

                best_transfer = max(best_transfer, adjusted)

        return best_transfer

    def _match_domain(self, user: UserProfile, job: Job) -> float:
        """
        Semantic domain/experience matching.

        Compares user's experience description with job description
        using embeddings.

        Args:
            user: User profile
            job: Job posting

        Returns:
            Similarity score 0.0-1.0
        """
        # Build experience text
        exp_texts = []

        for exp in user.experience:
            exp_texts.append(f"{exp.title} at {exp.company}: {exp.description}")

        if user.resume_text:
            exp_texts.append(user.resume_text)

        if not exp_texts:
            # No experience data - use skills as proxy
            exp_text = " ".join(s.name for s in user.skills)
        else:
            exp_text = " ".join(exp_texts)

        # Encode
        exp_embedding = self.encoder.encode([exp_text])
        job_embedding = self.encoder.encode([job.description])

        # Cosine similarity
        similarity = cosine_similarity(exp_embedding, job_embedding)[0][0]

        # Clip negative values
        return float(max(similarity, 0.0))

    def _match_level(self, user_years: float, required_years: float) -> float:
        """
        Seniority level matching.

        Scoring:
        - Exact match: 1.0
        - User has more: 0.9 (slight penalty for overqualification)
        - User has less: exponential decay

        Args:
            user_years: User's years of experience
            required_years: Job's required years

        Returns:
            Score 0.0-1.0
        """
        if required_years == 0:
            return 1.0

        ratio = user_years / required_years

        if ratio >= 1.0:
            # Meet or exceed
            if ratio > 2.0:
                # Overqualified penalty
                return 0.8
            return 0.95
        else:
            # Under-qualified - exponential decay
            # 0.5x = 0.7, 0.75x = 0.85, etc.
            return ratio ** 0.5

    def _match_work_mode(self, prefs, job: Job) -> float:
        """
        Work mode preference matching.

        Args:
            prefs: User preferences
            job: Job posting

        Returns:
            Score 0.0-1.0
        """
        if job.remote and prefs.remote:
            return 1.0
        elif job.hybrid and prefs.hybrid_acceptable:
            return 0.8
        elif not job.remote and not job.hybrid and prefs.onsite_acceptable:
            return 0.6
        else:
            return 0.3  # Mismatch but not dealbreaker

    def _calculate_ai_bonus(self, user_proficiency: float, job_description: str) -> float:
        """
        Bonus for AI-native capabilities.

        Jobs mentioning AI tools get bonus for high AI proficiency.

        Args:
            user_proficiency: User's AI proficiency (0-1)
            job_description: Job description text

        Returns:
            Bonus score 0.0-1.0
        """
        ai_keywords = [
            'ai', 'llm', 'gpt', 'claude', 'cursor', 'copilot',
            'ai-assisted', 'automation', 'agent', 'langchain',
            'openai', 'anthropic', 'hugging face'
        ]

        desc_lower = job_description.lower()

        # Count AI mentions
        ai_mentions = sum(1 for kw in ai_keywords if kw in desc_lower)

        if ai_mentions == 0:
            return 0.0

        # Scale by user proficiency and mentions
        bonus = user_proficiency * min(ai_mentions / 3, 1.0)

        return bonus

    def _identify_gaps(self, user_skills: List[Skill], required: List[str]) -> List[str]:
        """
        Find skills user is missing.

        Args:
            user_skills: User's skills
            required: Job requirements

        Returns:
            List of missing skill names
        """
        user_names = {s.name.lower() for s in user_skills}

        gaps = []
        for req in required:
            if req.lower() not in user_names:
                gaps.append(req)

        return gaps

    def _calculate_confidence(self,
                             user: UserProfile,
                             job: Job,
                             skill_score: float,
                             domain_score: float) -> float:
        """
        Confidence in the match score.

        Lower confidence when:
        - Little profile data
        - Low domain similarity
        - Missing many skills

        Args:
            user: User profile
            job: Job posting
            skill_score: Skill match score
            domain_score: Domain match score

        Returns:
            Confidence 0.0-1.0
        """
        confidence = 1.0

        # Penalty for incomplete profile
        if len(user.skills) < 5:
            confidence *= 0.8

        if not user.experience:
            confidence *= 0.7

        # Penalty for low scores
        if skill_score < 0.5:
            confidence *= 0.8

        if domain_score < 0.3:
            confidence *= 0.7

        return confidence

    def _generate_explanation(self,
                             overall: float,
                             skill_score: float,
                             domain_score: float,
                             level_score: float,
                             gaps: List[str]) -> str:
        """
        Generate human-readable explanation.

        Args:
            overall: Overall match score
            skill_score: Skills component
            domain_score: Domain component
            level_score: Level component
            gaps: Missing skills

        Returns:
            Explanation text
        """
        lines = []

        # Overall assessment
        if overall >= 80:
            lines.append("Excellent match. Highly recommended to apply.")
        elif overall >= 70:
            lines.append("Strong match. Good fit for this role.")
        elif overall >= 60:
            lines.append("Moderate match. Consider applying if interested.")
        else:
            lines.append("Weak match. May want to build more skills first.")

        # Skills analysis
        if skill_score >= 0.8:
            lines.append("Technical skills align very well.")
        elif skill_score >= 0.6:
            lines.append("Most technical requirements covered.")
        else:
            lines.append(f"Missing {len(gaps)} key skills: {', '.join(gaps[:3])}.")

        # Domain fit
        if domain_score >= 0.7:
            lines.append("Domain experience is a strong match.")
        elif domain_score >= 0.5:
            lines.append("Reasonable domain experience overlap.")

        # Level fit
        if level_score >= 0.9:
            lines.append("Experience level is perfect.")
        elif level_score < 0.7:
            lines.append("May be under/over-qualified for stated requirements.")

        return " ".join(lines)
