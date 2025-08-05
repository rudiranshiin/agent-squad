"""
Cooking Assistant Agent Module

This is a template module that demonstrates how to create a complete
agent module with all necessary components.
"""

from typing import Dict, Any, List, Type
import asyncio
from framework.core.agent_module import AgentModule, AgentModuleInfo
from framework.core.agent_base import BaseAgent
from framework.mcp.tools.base_tool import BaseTool


class RecipeTool(BaseTool):
    """Tool for searching and providing recipes."""

    def __init__(self):
        super().__init__(
            name="recipe_search",
            description="Search for recipes based on ingredients and cuisine type"
        )

    async def execute(self, query: str, cuisine: str = "any", diet: str = "any") -> Dict[str, Any]:
        """Search for recipes."""
        # Simulate recipe search
        recipes = [
            {
                "name": f"Delicious {cuisine} {query}",
                "ingredients": ["ingredient1", "ingredient2", "ingredient3"],
                "instructions": "1. Prepare ingredients\n2. Cook\n3. Serve",
                "cook_time": "30 minutes",
                "difficulty": "medium",
                "diet_friendly": diet
            }
        ]

        return {
            "recipes": recipes,
            "total_found": len(recipes),
            "query": query,
            "cuisine": cuisine,
            "diet": diet
        }

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Recipe search query (e.g., 'pasta', 'chicken')"
                },
                "cuisine": {
                    "type": "string",
                    "description": "Cuisine type",
                    "enum": ["italian", "chinese", "indian", "mexican", "french", "any"],
                    "default": "any"
                },
                "diet": {
                    "type": "string",
                    "description": "Dietary preference",
                    "enum": ["vegetarian", "vegan", "gluten-free", "keto", "any"],
                    "default": "any"
                }
            },
            "required": ["query"]
        }


class NutritionTool(BaseTool):
    """Tool for nutritional analysis."""

    def __init__(self):
        super().__init__(
            name="nutrition_analyzer",
            description="Analyze nutritional content of ingredients or recipes"
        )

    async def execute(self, ingredients: List[str], serving_size: int = 1) -> Dict[str, Any]:
        """Analyze nutrition."""
        # Simulate nutrition analysis
        total_calories = len(ingredients) * 50 * serving_size

        return {
            "calories": total_calories,
            "protein": f"{total_calories * 0.2:.1f}g",
            "carbs": f"{total_calories * 0.5:.1f}g",
            "fat": f"{total_calories * 0.3:.1f}g",
            "serving_size": serving_size,
            "ingredients_analyzed": ingredients
        }

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ingredients": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of ingredients to analyze"
                },
                "serving_size": {
                    "type": "integer",
                    "description": "Number of servings",
                    "default": 1
                }
            },
            "required": ["ingredients"]
        }


class CookingTimerTool(BaseTool):
    """Tool for managing cooking timers."""

    def __init__(self):
        super().__init__(
            name="cooking_timer",
            description="Set and manage cooking timers"
        )
        self.active_timers: Dict[str, float] = {}

    async def execute(self, action: str, duration: int = None, timer_name: str = "default") -> Dict[str, Any]:
        """Manage cooking timers."""
        import time

        if action == "start":
            if duration is None:
                return {"error": "Duration required for starting timer"}

            self.active_timers[timer_name] = time.time() + duration * 60
            return {
                "action": "timer_started",
                "timer_name": timer_name,
                "duration_minutes": duration,
                "ends_at": self.active_timers[timer_name]
            }

        elif action == "check":
            if timer_name not in self.active_timers:
                return {"error": f"Timer '{timer_name}' not found"}

            remaining = self.active_timers[timer_name] - time.time()
            if remaining <= 0:
                del self.active_timers[timer_name]
                return {
                    "action": "timer_finished",
                    "timer_name": timer_name,
                    "message": "Timer has finished!"
                }

            return {
                "action": "timer_active",
                "timer_name": timer_name,
                "remaining_seconds": int(remaining)
            }

        elif action == "list":
            current_time = time.time()
            active_timers = {}

            for name, end_time in list(self.active_timers.items()):
                remaining = end_time - current_time
                if remaining <= 0:
                    del self.active_timers[name]
                else:
                    active_timers[name] = int(remaining)

            return {
                "action": "list_timers",
                "active_timers": active_timers
            }

        return {"error": f"Unknown action: {action}"}

    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "check", "list"],
                    "description": "Timer action to perform"
                },
                "duration": {
                    "type": "integer",
                    "description": "Timer duration in minutes (for start action)"
                },
                "timer_name": {
                    "type": "string",
                    "description": "Name of the timer",
                    "default": "default"
                }
            },
            "required": ["action"]
        }


class CookingAssistantAgent(BaseAgent):
    """
    Cooking assistant agent that helps with recipes, nutrition, and cooking.
    """

    async def generate_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cooking-related response."""
        # Analyze the message to determine intent
        message_lower = message.lower()

        response_data = {
            "response": "",
            "suggestions": [],
            "tool_results": []
        }

        try:
            # Recipe search
            if any(word in message_lower for word in ["recipe", "cook", "make", "dish"]):
                recipe_result = await self.use_tool("recipe_search", {
                    "query": message,
                    "cuisine": "any"
                })
                response_data["tool_results"].append(recipe_result)

                if recipe_result.get("recipes"):
                    recipe = recipe_result["recipes"][0]
                    response_data["response"] = f"I found a great {recipe['name']} recipe! "
                    response_data["response"] += f"It takes {recipe['cook_time']} and has {recipe['difficulty']} difficulty. "
                    response_data["response"] += f"Here are the ingredients: {', '.join(recipe['ingredients'])}. "
                    response_data["response"] += f"Instructions: {recipe['instructions']}"

                    response_data["suggestions"] = [
                        "Would you like nutritional information?",
                        "Need help with cooking timing?",
                        "Want a different cuisine style?"
                    ]

            # Nutrition analysis
            elif any(word in message_lower for word in ["nutrition", "calories", "healthy", "diet"]):
                # Extract ingredients from message (simplified)
                ingredients = [word for word in message.split() if len(word) > 3][:3]

                if ingredients:
                    nutrition_result = await self.use_tool("nutrition_analyzer", {
                        "ingredients": ingredients
                    })
                    response_data["tool_results"].append(nutrition_result)

                    response_data["response"] = f"Nutritional analysis for your ingredients: "
                    response_data["response"] += f"{nutrition_result['calories']} calories, "
                    response_data["response"] += f"{nutrition_result['protein']} protein, "
                    response_data["response"] += f"{nutrition_result['carbs']} carbs, "
                    response_data["response"] += f"{nutrition_result['fat']} fat per serving."
                else:
                    response_data["response"] = "I'd be happy to analyze nutrition! Please provide some ingredients."

            # Timer management
            elif any(word in message_lower for word in ["timer", "time", "minutes", "alarm"]):
                # Simple timer parsing
                if "start" in message_lower or "set" in message_lower:
                    # Extract duration (simplified)
                    import re
                    duration_match = re.search(r'(\d+)\s*(?:minute|min)', message_lower)
                    duration = int(duration_match.group(1)) if duration_match else 10

                    timer_result = await self.use_tool("cooking_timer", {
                        "action": "start",
                        "duration": duration
                    })
                    response_data["tool_results"].append(timer_result)
                    response_data["response"] = f"Timer set for {duration} minutes! I'll let you know when it's done."

                elif "check" in message_lower:
                    timer_result = await self.use_tool("cooking_timer", {
                        "action": "list"
                    })
                    response_data["tool_results"].append(timer_result)

                    if timer_result.get("active_timers"):
                        timers_text = ", ".join([
                            f"{name}: {seconds//60}m {seconds%60}s"
                            for name, seconds in timer_result["active_timers"].items()
                        ])
                        response_data["response"] = f"Active timers: {timers_text}"
                    else:
                        response_data["response"] = "No active timers."

            # General cooking help
            else:
                response_data["response"] = "I'm your cooking assistant! I can help you with:"
                response_data["suggestions"] = [
                    "🍳 Finding recipes based on ingredients",
                    "📊 Analyzing nutritional content",
                    "⏰ Setting cooking timers",
                    "🥗 Dietary recommendations",
                    "👨‍🍳 Cooking tips and techniques"
                ]

        except Exception as e:
            response_data["response"] = f"I encountered an issue: {str(e)}. Let me help you in a different way!"
            response_data["suggestions"] = [
                "Try asking for a specific recipe",
                "Ask about nutrition for specific ingredients",
                "Request cooking timer assistance"
            ]

        return response_data


class CookingModule(AgentModule):
    """Cooking assistant agent module."""

    def get_module_info(self) -> AgentModuleInfo:
        return AgentModuleInfo(
            name="{module_name}",
            version="1.0.0",
            description="Comprehensive cooking assistant with recipe search, nutrition analysis, and cooking timers",
            author="Agentic Framework",
            dependencies=["asyncio", "re"],
            agent_types=["cooking_assistant"],
            tools=["recipe_search", "nutrition_analyzer", "cooking_timer"],
            config_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["cooking_assistant"]},
                    "personality": {
                        "type": "object",
                        "properties": {
                            "style": {"type": "string"},
                            "expertise": {"type": "string"},
                            "tone": {"type": "string"}
                        }
                    }
                },
                "required": ["name", "type"]
            },
            module_path=__file__
        )

    async def initialize(self) -> None:
        """Initialize the cooking module."""
        # Register tools
        self.register_tool(RecipeTool())
        self.register_tool(NutritionTool())
        self.register_tool(CookingTimerTool())

    async def cleanup(self) -> None:
        """Cleanup module resources."""
        # Clear any active timers
        for tool in self.tools.values():
            if hasattr(tool, 'active_timers'):
                tool.active_timers.clear()

    def get_agent_class(self, agent_type: str) -> Type[BaseAgent]:
        """Get agent class for the specified type."""
        if agent_type == "cooking_assistant":
            return CookingAssistantAgent
        raise ValueError(f"Unknown agent type: {agent_type}")


# This is what gets imported when the module is loaded
module_class = CookingModule
