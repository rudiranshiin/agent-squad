"""
Language Teacher Agent implementation for teaching languages with cultural context.
"""

from typing import Dict, Any, Optional, List
import logging
from framework.core.agent_base import BaseAgent

logger = logging.getLogger(__name__)


class LanguageTeacherAgent(BaseAgent):
    """
    Language teacher agent specialized in language instruction with cultural context.

    Features:
    - Language-specific teaching methods
    - Cultural context integration
    - Progress tracking
    - Pronunciation guidance
    - Grammar correction
    """

    def __init__(self, config_path: str):
        super().__init__(config_path)

        # Language-specific configuration
        self.language_config = self.config.get("language_config", {})
        self.primary_language = self.language_config.get("primary_language", "en")
        self.specialties = self.language_config.get("specialties", [])
        self.teaching_preferences = self.config.get("teaching_preferences", {})

        logger.info(f"Initialized {self.primary_language} teacher: {self.name}")

    async def generate_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate language teaching response with educational context.

        Args:
            message: Student's message or question
            context: Additional context including collaboration info

        Returns:
            Teaching response with feedback and guidance
        """
        try:
            # Check if this is a collaboration request
            if context.get("collaboration_from"):
                return await self._handle_collaboration(message, context)

            # Check if this is a health check
            if context.get("internal_health_check"):
                return {"response": "Language teacher is ready to help students learn!", "success": True}

            # Check if this is a collaboration mode (multi-agent response)
            if context.get("collaboration_mode"):
                return await self._handle_collaboration_mode(message, context)

            # Analyze the student's input for learning opportunities
            analysis_result = await self._analyze_student_input(message)

            # Generate educational response
            teaching_response = await self._generate_teaching_response(message, analysis_result)

            # Add educational metadata
            response = {
                "response": teaching_response["text"],
                "analysis": analysis_result,
                "teaching_points": teaching_response.get("teaching_points", []),
                "corrections": teaching_response.get("corrections", []),
                "cultural_notes": teaching_response.get("cultural_notes", []),
                "next_steps": teaching_response.get("next_steps", []),
                "success": True
            }

            # Track tools used
            tools_used = []
            if analysis_result.get("grammar_checked"):
                tools_used.append("grammar_checker")
            if analysis_result.get("pronunciation_analyzed"):
                tools_used.append("pronunciation_tool")

            response["tools_used"] = tools_used

            return response

        except Exception as e:
            logger.error(f"Error generating teaching response: {e}")
            return {
                "response": "I apologize, but I encountered an issue. Could you please try again?",
                "error": str(e),
                "success": False
            }

    async def _analyze_student_input(self, message: str) -> Dict[str, Any]:
        """
        Analyze student input for learning opportunities.

        Args:
            message: Student's message

        Returns:
            Analysis results with grammar, pronunciation, and content insights
        """
        analysis = {
            "message_length": len(message),
            "complexity_level": self._assess_complexity(message),
            "grammar_checked": False,
            "pronunciation_analyzed": False,
            "cultural_context_needed": False
        }

        try:
            # Grammar analysis
            if "grammar_checker" in self.tool_registry.list_tools():
                grammar_result = await self.use_tool("grammar_checker", {"text": message})
                if grammar_result.success:
                    analysis["grammar_issues"] = grammar_result.data.get("issues", [])
                    analysis["grammar_score"] = grammar_result.data.get("score", 0)
                    analysis["grammar_checked"] = True

            # Pronunciation analysis (for spoken languages)
            pronunciation_tool = None
            if self.primary_language.startswith("en") and "british_pronunciation" in self.tool_registry.list_tools():
                pronunciation_tool = "british_pronunciation"
            elif "pinyin_converter" in self.tool_registry.list_tools() and self.primary_language.startswith("zh"):
                pronunciation_tool = "pinyin_converter"

            if pronunciation_tool:
                pronunciation_result = await self.use_tool(pronunciation_tool, {"text": message})
                if pronunciation_result.success:
                    analysis["pronunciation_notes"] = pronunciation_result.data
                    analysis["pronunciation_analyzed"] = True

            # Cultural context assessment
            cultural_keywords = ["culture", "tradition", "custom", "holiday", "food", "family"]
            if any(keyword in message.lower() for keyword in cultural_keywords):
                analysis["cultural_context_needed"] = True

            # Progress tracking
            if "progress_tracker" in self.tool_registry.list_tools():
                await self.use_tool("progress_tracker", {
                    "student_input": message,
                    "analysis": analysis
                })

        except Exception as e:
            logger.error(f"Error analyzing student input: {e}")
            analysis["analysis_error"] = str(e)

        return analysis

    async def _generate_teaching_response(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate educational response based on analysis.

        Args:
            message: Original student message
            analysis: Analysis results

        Returns:
            Teaching response with educational content
        """
        # Build teaching prompt
        teaching_prompt = self._build_teaching_prompt(message, analysis)

        # Generate response using context engine
        response_text = await self._generate_contextual_response(teaching_prompt)

        # Extract teaching components
        teaching_response = {
            "text": response_text,
            "teaching_points": [],
            "corrections": [],
            "cultural_notes": [],
            "next_steps": []
        }

        # Add grammar corrections if found
        if analysis.get("grammar_issues"):
            teaching_response["corrections"] = analysis["grammar_issues"]

        # Add pronunciation guidance
        if analysis.get("pronunciation_notes"):
            teaching_response["teaching_points"].append({
                "type": "pronunciation",
                "content": analysis["pronunciation_notes"]
            })

        # Add cultural context if needed
        if analysis.get("cultural_context_needed") and "cultural_context" in self.tool_registry.list_tools():
            try:
                cultural_result = await self.use_tool("cultural_context", {"query": message})
                if cultural_result.success:
                    teaching_response["cultural_notes"] = cultural_result.data
            except Exception as e:
                logger.error(f"Error getting cultural context: {e}")

        # Suggest next steps based on complexity
        complexity = analysis.get("complexity_level", "beginner")
        teaching_response["next_steps"] = self._suggest_next_steps(complexity, analysis)

        return teaching_response

    def _build_teaching_prompt(self, message: str, analysis: Dict[str, Any]) -> str:
        """
        Build context-aware teaching prompt.

        Args:
            message: Student message
            analysis: Analysis results

        Returns:
            Formatted teaching prompt
        """
        template = """
        {system_context}

        Student message: "{message}"

        Analysis results:
        - Complexity level: {complexity}
        - Grammar checked: {grammar_checked}
        - Pronunciation analyzed: {pronunciation_analyzed}
        - Cultural context needed: {cultural_context}

        {memory_context}

        Please provide a helpful response that:
        1. Addresses the student's question or input
        2. Provides constructive feedback if there are areas for improvement
        3. Includes relevant cultural context if appropriate
        4. Encourages continued learning
        5. Maintains the personality and teaching style of {personality}

        Teaching methodology: {methodology}
        Feedback style: {feedback_style}

        Response:
        """

        return self.context_engine.build_prompt(
            template,
            message=message,
            complexity=analysis.get("complexity_level", "unknown"),
            grammar_checked=analysis.get("grammar_checked", False),
            pronunciation_analyzed=analysis.get("pronunciation_analyzed", False),
            cultural_context=analysis.get("cultural_context_needed", False),
            personality=self._build_personality_context(),
            methodology=self.teaching_preferences.get("methodology", "communicative"),
            feedback_style=self.teaching_preferences.get("feedback_style", "encouraging")
        )

    async def _generate_contextual_response(self, prompt: str) -> str:
        """
        Generate response using LLM with context.
        """
        try:
            # Build system message for the language teacher
            system_message = self._build_system_message()

            # Generate response using the LLM client
            response = await self.generate_llm_response(
                prompt=prompt,
                system_message=system_message,
                max_tokens=self.config.get("max_response_tokens", 800),
                temperature=self.config.get("response_temperature", 0.7),
                provider=self.config.get("llm_config", {}).get("preferred_provider")
            )

            return response

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to a basic response if LLM fails
            return self._get_fallback_response()

    def _get_default_teaching_response(self) -> str:
        """Get a default teaching response based on language and specialties."""
        if self.primary_language.startswith("en"):
            return """Here are some tips for improving your English:
- Focus on natural conversation patterns
- Pay attention to British pronunciation and intonation
- Learn common idioms and cultural expressions
- Practice reading British literature and news"""
        elif self.primary_language.startswith("zh"):
            return """Here are some tips for improving your Chinese:
- Practice tone pronunciation daily
- Learn character components and radicals
- Study sentence patterns and grammar structures
- Immerse yourself in Chinese culture and media"""
        else:
            return "Keep practicing and stay motivated in your language learning journey!"

    def _assess_complexity(self, message: str) -> str:
        """
        Assess the complexity level of student input.

        Args:
            message: Student message

        Returns:
            Complexity level (beginner, intermediate, advanced)
        """
        word_count = len(message.split())
        sentence_count = len([s for s in message.split('.') if s.strip()])

        if word_count < 10:
            return "beginner"
        elif word_count < 30:
            return "intermediate"
        else:
            return "advanced"

    def _suggest_next_steps(self, complexity: str, analysis: Dict[str, Any]) -> List[str]:
        """
        Suggest next learning steps based on student level and analysis.

        Args:
            complexity: Student's complexity level
            analysis: Analysis results

        Returns:
            List of suggested next steps
        """
        steps = []

        if complexity == "beginner":
            steps.extend([
                "Focus on basic vocabulary and common phrases",
                "Practice simple sentence structures",
                "Work on fundamental pronunciation"
            ])
        elif complexity == "intermediate":
            steps.extend([
                "Expand vocabulary with specialized terms",
                "Practice complex sentence structures",
                "Focus on cultural expressions and idioms"
            ])
        else:  # advanced
            steps.extend([
                "Refine nuanced language use",
                "Practice professional and academic language",
                "Study advanced cultural and historical contexts"
            ])

        # Add language-specific suggestions
        if self.primary_language.startswith("zh"):
            steps.append("Practice writing characters and understanding radicals")
        elif self.primary_language.startswith("en") and "british" in self.personality.get("cultural_background", "").lower():
            steps.append("Study British cultural references and regional variations")

        return steps

    def _build_system_message(self) -> str:
        """
        Build comprehensive system message for the language teacher LLM.
        """
        personality_desc = self._build_personality_context()
        specialties_desc = ", ".join(self.specialties) if self.specialties else "general language instruction"

        methodology = self.teaching_preferences.get("methodology", "communicative")
        feedback_style = self.teaching_preferences.get("feedback_style", "encouraging")

        system_message = f"""You are an expert {self.primary_language} language teacher with the following characteristics:

PERSONALITY: {personality_desc}

TEACHING APPROACH:
- Methodology: {methodology} approach
- Feedback Style: {feedback_style}
- Specialties: {specialties_desc}
- Focus on practical, conversational skills
- Provide constructive corrections when needed
- Include cultural context when relevant

RESPONSE GUIDELINES:
1. Be encouraging and supportive
2. Correct errors gently and constructively
3. Provide specific examples and explanations
4. Suggest next steps for improvement
5. Include pronunciation tips when relevant
6. Add cultural context for better understanding
7. Keep responses focused and educational

Your goal is to help students improve their {self.primary_language} skills through engaging, practical instruction while maintaining an {feedback_style} teaching style."""

        return system_message

    def _get_fallback_response(self) -> str:
        """
        Get fallback response when LLM is not available.
        """
        return f"""Thank you for your message! As your {self.primary_language} teacher, I'm here to help you learn effectively.

I'm currently experiencing some technical difficulties, but I can still provide you with some general guidance:

{self._get_default_teaching_response()}

Please try again in a moment, and I'll be able to provide more personalized feedback!"""

    async def _handle_collaboration_mode(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle collaboration mode where multiple agents work together on a response.

        Args:
            message: User's message
            context: Collaboration context

        Returns:
            Teaching response with collaboration awareness
        """
        collaborating_agents = context.get("collaborating_agents", [])

        # Analyze the student's input for learning opportunities
        analysis_result = await self._analyze_student_input(message)

        # Generate educational response with collaboration awareness
        teaching_response = await self._generate_teaching_response(message, analysis_result)

        # Add collaboration context to the response
        if self.primary_language.startswith("zh") and "professor_james" in collaborating_agents:
            # Chinese teacher working with British teacher
            teaching_response["text"] += f"\n\n*I notice Professor James is also here to help. He can assist with English pronunciation and grammar while I focus on Chinese language learning.*"
        elif self.primary_language.startswith("en") and "teacher_li" in collaborating_agents:
            # British teacher working with Chinese teacher
            teaching_response["text"] += f"\n\n*Teacher Li is also available to help with Chinese language questions. I'll focus on English language instruction and cultural context.*"

        # Add educational metadata
        response = {
            "response": teaching_response["text"],
            "analysis": analysis_result,
            "teaching_points": teaching_response.get("teaching_points", []),
            "corrections": teaching_response.get("corrections", []),
            "cultural_notes": teaching_response.get("cultural_notes", []),
            "next_steps": teaching_response.get("next_steps", []),
            "collaboration_mode": True,
            "collaborating_agents": collaborating_agents,
            "success": True
        }

        # Track tools used
        tools_used = []
        if analysis_result.get("grammar_checked"):
            tools_used.append("grammar_checker")
        if analysis_result.get("pronunciation_analyzed"):
            tools_used.append("pronunciation_tool")

        response["tools_used"] = tools_used
        return response

    async def _handle_collaboration(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle collaboration with other agents.

        Args:
            message: Collaboration message
            context: Collaboration context

        Returns:
            Collaboration response
        """
        collaborator = context.get("collaboration_from")
        collaboration_type = context.get("collaboration_type", "request")

        # Add collaboration context
        self.context_engine.add_collaboration_context(
            f"Collaborating with {collaborator}: {message}",
            collaboration_id=context.get("collaboration_id", "unknown"),
            metadata={"partner": collaborator, "type": collaboration_type, "direction": "incoming"}
        )

        if collaboration_type == "weather_inquiry":
            # Help with weather-related language learning
            return {
                "response": f"Excellent! Weather is a wonderful topic for language practice. Let me help you learn weather-related vocabulary and expressions in {self.primary_language}. This is also a great opportunity to discuss cultural differences in how weather is discussed in different regions.",
                "teaching_suggestions": [
                    "Weather vocabulary expansion",
                    "Cultural weather expressions",
                    "Seasonal conversation patterns"
                ],
                "collaboration_accepted": True,
                "success": True
            }
        else:
            # General collaboration response
            return {
                "response": f"I'd be happy to collaborate with {collaborator}! As a {self.primary_language} teacher, I can provide language learning context and cultural insights to enhance our discussion.",
                "collaboration_accepted": True,
                "success": True
            }
