"""
Weather Agent implementation for providing weather information and forecasts.
"""

from typing import Dict, Any, List
import logging
from framework.core.agent_base import BaseAgent

logger = logging.getLogger(__name__)


class WeatherAgent(BaseAgent):
    """
    Weather agent specialized in providing weather information and forecasts.

    Features:
    - Current weather conditions
    - Weather forecasts
    - Activity recommendations based on weather
    - Severe weather alerts
    - Climate information
    """

    def __init__(self, config_path: str):
        super().__init__(config_path)

        # Weather-specific configuration
        self.weather_specialties = self.config.get("weather_specialties", [])
        self.response_formats = self.config.get("response_formats", {})

        logger.info(f"Initialized weather agent: {self.name}")

    async def generate_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate weather-related response.

        Args:
            message: User's weather query
            context: Additional context including collaboration info

        Returns:
            Weather response with data and recommendations
        """
        try:
            # Check if this is a collaboration request
            if context.get("collaboration_from"):
                return await self._handle_collaboration(message, context)

            # Check if this is a health check
            if context.get("internal_health_check"):
                return {"response": "Weather agent is ready to provide forecasts!", "success": True}

            # Analyze the weather query
            query_analysis = await self._analyze_weather_query(message)

            # Generate weather response
            weather_response = await self._generate_weather_response(message, query_analysis)

            # Format response
            response = {
                "response": weather_response["text"],
                "weather_data": weather_response.get("weather_data"),
                "forecast": weather_response.get("forecast"),
                "recommendations": weather_response.get("recommendations", []),
                "alerts": weather_response.get("alerts", []),
                "location": query_analysis.get("location"),
                "success": True
            }

            # Track tools used
            tools_used = []
            if query_analysis.get("location_resolved"):
                tools_used.append("location_resolver")
            if weather_response.get("weather_data"):
                tools_used.append("weather_api")

            response["tools_used"] = tools_used

            return response

        except Exception as e:
            logger.error(f"Error generating weather response: {e}")
            return {
                "response": "I apologize, but I'm having trouble accessing weather data right now. Please try again later.",
                "error": str(e),
                "success": False
            }

    async def _analyze_weather_query(self, message: str) -> Dict[str, Any]:
        """
        Analyze weather query to understand what information is needed.

        Args:
            message: User's weather query

        Returns:
            Analysis of the weather query
        """
        analysis = {
            "query_type": self._determine_query_type(message),
            "location": None,
            "time_frame": self._extract_time_frame(message),
            "location_resolved": False,
            "specific_conditions": []
        }

        try:
            # Extract and resolve location
            if "location_resolver" in self.tool_registry.list_tools():
                location_result = await self.use_tool("location_resolver", {"text": message})
                if location_result.success:
                    analysis["location"] = location_result.data
                    analysis["location_resolved"] = True

            # Identify specific weather conditions of interest
            weather_keywords = {
                "temperature": ["temp", "temperature", "hot", "cold", "warm", "cool"],
                "precipitation": ["rain", "snow", "sleet", "hail", "precipitation"],
                "wind": ["wind", "windy", "breeze", "gust"],
                "humidity": ["humid", "humidity", "moisture"],
                "visibility": ["fog", "foggy", "visibility", "clear"],
                "storms": ["storm", "thunder", "lightning", "severe"]
            }

            message_lower = message.lower()
            for condition, keywords in weather_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    analysis["specific_conditions"].append(condition)

        except Exception as e:
            logger.error(f"Error analyzing weather query: {e}")
            analysis["analysis_error"] = str(e)

        return analysis

    async def _generate_weather_response(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate weather response based on query analysis.

        Args:
            message: Original weather query
            analysis: Query analysis results

        Returns:
            Weather response with data and recommendations
        """
        weather_response = {
            "text": "",
            "weather_data": None,
            "forecast": None,
            "recommendations": [],
            "alerts": []
        }

        try:
            # Get weather data if location is available
            if analysis.get("location") and "weather_api" in self.tool_registry.list_tools():
                weather_params = {
                    "location": analysis["location"]
                }

                # Add forecast days based on time frame
                time_frame = analysis.get("time_frame", "current")
                if time_frame != "current":
                    weather_params["forecast_days"] = self._get_forecast_days(time_frame)

                weather_result = await self.use_tool("weather_api", weather_params)
                if weather_result.success:
                    weather_response["weather_data"] = weather_result.data

            # Get weather alerts if available
            if analysis.get("location") and "weather_alerts" in self.tool_registry.list_tools():
                try:
                    alerts_result = await self.use_tool("weather_alerts", {
                        "location": analysis["location"]
                    })
                    if alerts_result.success:
                        weather_response["alerts"] = alerts_result.data
                except Exception as e:
                    logger.debug(f"No weather alerts available: {e}")

            # Generate activity recommendations
            if weather_response["weather_data"] and "activity_advisor" in self.tool_registry.list_tools():
                try:
                    activity_result = await self.use_tool("activity_advisor", {
                        "weather_data": weather_response["weather_data"],
                        "query": message
                    })
                    if activity_result.success:
                        weather_response["recommendations"] = activity_result.data
                except Exception as e:
                    logger.debug(f"No activity recommendations available: {e}")

            # Build response text
            weather_response["text"] = await self._build_weather_response_text(
                message, analysis, weather_response
            )

        except Exception as e:
            logger.error(f"Error generating weather response: {e}")
            weather_response["text"] = "I'm having trouble accessing weather data at the moment."

        return weather_response

    async def _build_weather_response_text(
        self,
        message: str,
        analysis: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> str:
        """
        Build weather response text.

        Args:
            message: Original query
            analysis: Query analysis
            weather_data: Weather data and recommendations

        Returns:
            Formatted weather response text
        """
        # Build weather prompt
        weather_prompt = self._build_weather_prompt(message, analysis, weather_data)

        # Generate response using context engine
        response_text = await self._generate_contextual_response(weather_prompt)

        return response_text

    def _build_weather_prompt(
        self,
        message: str,
        analysis: Dict[str, Any],
        weather_data: Dict[str, Any]
    ) -> str:
        """
        Build context-aware weather prompt.

        Args:
            message: User query
            analysis: Query analysis
            weather_data: Weather data

        Returns:
            Formatted weather prompt
        """
        template = """
        {system_context}

        User weather query: "{message}"

        Query analysis:
        - Query type: {query_type}
        - Location: {location}
        - Time frame: {time_frame}
        - Specific conditions: {conditions}

        Weather data: {weather_data}
        Alerts: {alerts}
        Recommendations: {recommendations}

        {memory_context}

        Please provide a helpful weather response that:
        1. Directly answers the user's weather question
        2. Includes relevant weather data and forecasts
        3. Provides practical recommendations if appropriate
        4. Mentions any weather alerts or safety concerns
        5. Maintains a {personality} tone

        Response:
        """

        return self.context_engine.build_prompt(
            template,
            message=message,
            query_type=analysis.get("query_type", "general"),
            location=analysis.get("location", "unknown"),
            time_frame=analysis.get("time_frame", "current"),
            conditions=", ".join(analysis.get("specific_conditions", [])),
            weather_data=weather_data.get("weather_data", "No data available"),
            alerts=weather_data.get("alerts", []),
            recommendations=weather_data.get("recommendations", []),
            personality=self._build_personality_context()
        )

    async def _generate_contextual_response(self, prompt: str) -> str:
        """
        Generate response using LLM with context.

        This is a placeholder - in a real implementation, you would integrate
        with an LLM.
        """
        # For demonstration, return a template response
        return """Thank you for your weather inquiry! Based on the available data, here's what I can tell you:

The current weather conditions show typical patterns for this time of year. I recommend checking for any weather updates and planning accordingly.

For detailed and up-to-date weather information, I suggest monitoring local weather services and alerts.

Stay safe and prepared for any weather changes!"""

    def _determine_query_type(self, message: str) -> str:
        """
        Determine the type of weather query.

        Args:
            message: User message

        Returns:
            Query type (current, forecast, historical, etc.)
        """
        message_lower = message.lower()

        if any(word in message_lower for word in ["now", "current", "currently", "today"]):
            return "current"
        elif any(word in message_lower for word in ["tomorrow", "next", "future", "forecast"]):
            return "forecast"
        elif any(word in message_lower for word in ["week", "weekend", "7 day"]):
            return "weekly_forecast"
        elif any(word in message_lower for word in ["yesterday", "last", "historical", "past"]):
            return "historical"
        else:
            return "general"

    def _extract_time_frame(self, message: str) -> str:
        """
        Extract time frame from weather query.

        Args:
            message: User message

        Returns:
            Time frame identifier
        """
        message_lower = message.lower()

        if any(word in message_lower for word in ["now", "current", "currently"]):
            return "current"
        elif "today" in message_lower:
            return "today"
        elif "tomorrow" in message_lower:
            return "tomorrow"
        elif any(word in message_lower for word in ["week", "7 day"]):
            return "week"
        elif "weekend" in message_lower:
            return "weekend"
        else:
            return "current"

    def _get_forecast_days(self, time_frame: str) -> int:
        """
        Get number of forecast days based on time frame.

        Args:
            time_frame: Time frame identifier

        Returns:
            Number of forecast days
        """
        time_frame_mapping = {
            "today": 1,
            "tomorrow": 2,
            "weekend": 3,
            "week": 7
        }

        return time_frame_mapping.get(time_frame, 3)

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

        if "language" in collaborator.lower() or "teacher" in collaborator.lower():
            # Help with weather-related language learning
            return {
                "response": f"I'd be delighted to collaborate with {collaborator}! Weather is a fantastic topic for language learning. I can provide current weather conditions, forecasts, and weather-related vocabulary to support language practice. Weather discussions are great for learning descriptive language, cultural expressions, and practical conversation skills.",
                "weather_learning_opportunities": [
                    "Weather vocabulary and terminology",
                    "Descriptive language for conditions",
                    "Cultural weather expressions",
                    "Seasonal conversation topics"
                ],
                "collaboration_accepted": True,
                "success": True
            }
        else:
            # General collaboration response
            return {
                "response": f"Happy to collaborate with {collaborator}! I can provide weather data, forecasts, and climate information to support our discussion.",
                "collaboration_accepted": True,
                "success": True
            }
