"""
Progress Tracker tool for monitoring language learning progress.
"""

from typing import Dict, Any, List
import time
import json
from framework.mcp.tools.base_tool import BaseTool


class ProgressTracker(BaseTool):
    """
    Tool for tracking student progress in language learning.

    Features:
    - Track learning milestones
    - Monitor skill improvements
    - Store learning history
    - Generate progress reports
    """

    def __init__(self, focus_areas: List[str] = None):
        super().__init__(
            name="progress_tracker",
            description="Track and monitor language learning progress across different skill areas"
        )
        self.focus_areas = focus_areas or ["vocabulary", "grammar", "pronunciation", "cultural_understanding"]
        self.progress_data = {}

    async def execute(self, **parameters) -> Dict[str, Any]:
        """
        Track progress based on student interaction.

        Args:
            student_input: The student's input message
            analysis: Analysis results from the interaction
            user_id: Optional user identifier

        Returns:
            Progress tracking results
        """
        student_input = parameters.get("student_input", "")
        analysis = parameters.get("analysis", {})
        user_id = parameters.get("user_id", "default_user")

        # Initialize user progress if not exists
        if user_id not in self.progress_data:
            self.progress_data[user_id] = {
                "session_count": 0,
                "total_interactions": 0,
                "skill_scores": {area: 0.0 for area in self.focus_areas},
                "milestones": [],
                "last_updated": time.time(),
                "learning_history": []
            }

        user_progress = self.progress_data[user_id]

        # Update interaction count
        user_progress["total_interactions"] += 1
        user_progress["last_updated"] = time.time()

        # Analyze progress from current interaction
        progress_update = self._analyze_progress(student_input, analysis)

        # Update skill scores
        for skill, improvement in progress_update.get("skill_improvements", {}).items():
            if skill in user_progress["skill_scores"]:
                current_score = user_progress["skill_scores"][skill]
                new_score = min(1.0, current_score + improvement)
                user_progress["skill_scores"][skill] = new_score

        # Add to learning history
        history_entry = {
            "timestamp": time.time(),
            "input": student_input[:100],  # Truncate for storage
            "complexity": analysis.get("complexity_level", "unknown"),
            "improvements": progress_update.get("skill_improvements", {}),
            "notes": progress_update.get("notes", [])
        }
        user_progress["learning_history"].append(history_entry)

        # Keep only recent history (last 50 entries)
        if len(user_progress["learning_history"]) > 50:
            user_progress["learning_history"] = user_progress["learning_history"][-50:]

        # Check for new milestones
        new_milestones = self._check_milestones(user_progress)
        user_progress["milestones"].extend(new_milestones)

        return {
            "user_id": user_id,
            "current_scores": user_progress["skill_scores"],
            "improvements": progress_update.get("skill_improvements", {}),
            "new_milestones": new_milestones,
            "recommendations": self._generate_recommendations(user_progress),
            "total_interactions": user_progress["total_interactions"],
            "overall_progress": self._calculate_overall_progress(user_progress)
        }

    def _analyze_progress(self, student_input: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze learning progress from student interaction.

        Args:
            student_input: Student's input
            analysis: Analysis results

        Returns:
            Progress analysis with skill improvements
        """
        progress_update = {
            "skill_improvements": {},
            "notes": []
        }

        # Base improvement based on interaction
        base_improvement = 0.01

        # Grammar improvements
        if analysis.get("grammar_checked"):
            grammar_issues = len(analysis.get("grammar_issues", []))
            if grammar_issues == 0:
                progress_update["skill_improvements"]["grammar"] = base_improvement * 2
                progress_update["notes"].append("Excellent grammar usage!")
            elif grammar_issues < 3:
                progress_update["skill_improvements"]["grammar"] = base_improvement
                progress_update["notes"].append("Good grammar with minor improvements needed")
            else:
                progress_update["notes"].append("Focus on grammar practice")

        # Vocabulary improvements based on complexity
        complexity = analysis.get("complexity_level", "beginner")
        vocab_improvement = {
            "beginner": base_improvement,
            "intermediate": base_improvement * 1.5,
            "advanced": base_improvement * 2
        }
        progress_update["skill_improvements"]["vocabulary"] = vocab_improvement.get(complexity, base_improvement)

        # Pronunciation improvements
        if analysis.get("pronunciation_analyzed"):
            progress_update["skill_improvements"]["pronunciation"] = base_improvement
            progress_update["notes"].append("Pronunciation practice recorded")

        # Cultural understanding
        if analysis.get("cultural_context_needed"):
            progress_update["skill_improvements"]["cultural_understanding"] = base_improvement
            progress_update["notes"].append("Cultural learning opportunity identified")

        return progress_update

    def _check_milestones(self, user_progress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check for new learning milestones.

        Args:
            user_progress: User's progress data

        Returns:
            List of new milestones achieved
        """
        new_milestones = []
        existing_milestone_types = {m["type"] for m in user_progress["milestones"]}

        # Interaction milestones
        interactions = user_progress["total_interactions"]
        interaction_milestones = [10, 25, 50, 100, 250, 500]

        for milestone in interaction_milestones:
            milestone_type = f"interactions_{milestone}"
            if interactions >= milestone and milestone_type not in existing_milestone_types:
                new_milestones.append({
                    "type": milestone_type,
                    "title": f"Reached {milestone} interactions!",
                    "description": f"Congratulations on completing {milestone} learning interactions!",
                    "achieved_at": time.time()
                })

        # Skill-based milestones
        for skill, score in user_progress["skill_scores"].items():
            for threshold in [0.25, 0.5, 0.75, 0.9]:
                milestone_type = f"{skill}_{int(threshold*100)}"
                if score >= threshold and milestone_type not in existing_milestone_types:
                    new_milestones.append({
                        "type": milestone_type,
                        "title": f"{skill.title()} Progress: {int(threshold*100)}%",
                        "description": f"Great progress in {skill}! You've reached {int(threshold*100)}% proficiency.",
                        "achieved_at": time.time()
                    })

        return new_milestones

    def _generate_recommendations(self, user_progress: Dict[str, Any]) -> List[str]:
        """
        Generate personalized learning recommendations.

        Args:
            user_progress: User's progress data

        Returns:
            List of learning recommendations
        """
        recommendations = []
        skill_scores = user_progress["skill_scores"]

        # Find weakest skill
        weakest_skill = min(skill_scores.items(), key=lambda x: x[1])
        if weakest_skill[1] < 0.3:
            recommendations.append(f"Focus on improving {weakest_skill[0]} - consider dedicated practice sessions")

        # Find strongest skill
        strongest_skill = max(skill_scores.items(), key=lambda x: x[1])
        if strongest_skill[1] > 0.7:
            recommendations.append(f"Excellent progress in {strongest_skill[0]}! Consider advanced exercises")

        # General recommendations based on interaction count
        interactions = user_progress["total_interactions"]
        if interactions < 10:
            recommendations.append("Keep practicing regularly to build momentum")
        elif interactions < 50:
            recommendations.append("Great consistency! Try to explore more advanced topics")
        else:
            recommendations.append("Consider setting specific learning goals for continued improvement")

        return recommendations

    def _calculate_overall_progress(self, user_progress: Dict[str, Any]) -> float:
        """
        Calculate overall learning progress.

        Args:
            user_progress: User's progress data

        Returns:
            Overall progress score (0.0 to 1.0)
        """
        skill_scores = user_progress["skill_scores"]
        if not skill_scores:
            return 0.0

        return sum(skill_scores.values()) / len(skill_scores)

    def get_parameter_schema(self) -> Dict[str, Any]:
        """Get the parameter schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "student_input": {
                    "type": "string",
                    "description": "The student's input message to analyze for progress"
                },
                "analysis": {
                    "type": "object",
                    "description": "Analysis results from the student's interaction"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional user identifier for tracking individual progress"
                }
            },
            "required": ["student_input"]
        }
