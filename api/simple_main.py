#!/usr/bin/env python3
"""
Simplified Agentic Framework API
A demo version that works with real agents when available, with mock fallbacks
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import time
import random
from datetime import datetime
import sys
import os
from pathlib import Path

# Add the project root to the Python path for agent imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import real agent functionality
try:
    from framework.core.agent_registry import AgentRegistry
    from framework.core.llm_client import get_llm_client
    REAL_AGENTS_AVAILABLE = True
    print("✅ Real agent framework available")
except ImportError as e:
    REAL_AGENTS_AVAILABLE = False
    print(f"⚠️  Real agent framework not available: {e}")
    print("🔄 Trying standalone LLM client...")

# Try standalone LLM client as fallback
STANDALONE_LLM_AVAILABLE = False
if not REAL_AGENTS_AVAILABLE:
    try:
        # Import our working standalone LLM client
        import sys
        sys.path.insert(0, str(project_root))
        from test_llm_standalone import StandaloneLLMClient, LLMMessage

        # Test if we have API keys
        test_client = StandaloneLLMClient()
        if test_client.get_available_providers():
            STANDALONE_LLM_AVAILABLE = True
            print("✅ Standalone LLM client available with API keys")
            print(f"✅ Available providers: {test_client.get_available_providers()}")
        else:
            print("❌ No LLM providers available (check API keys)")
    except Exception as e:
        print(f"❌ Standalone LLM client failed: {e}")
        print("🔄 Using mock responses")

app = FastAPI(
    title="Agentic Framework API (Demo)",
    description="Simplified demo version of the Enhanced Agentic AI Framework",
    version="2.0.0-demo"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize real agents (will be loaded during startup)
real_agents = {}
registry = None

# Store active collaborations
active_collaborations = {}

async def load_real_agents():
    """Load real agents during startup."""
    global real_agents, registry

    if not REAL_AGENTS_AVAILABLE:
        return

    try:
        registry = AgentRegistry()
        config_dir = project_root / "agents" / "configs"

        # Load available agent configs
        available_configs = {
            "professor_james": "british_teacher.yaml",
            "teacher_li": "chinese_teacher.yaml",
            "weather_bot": "weather_agent.yaml"
        }

        for agent_id, config_file in available_configs.items():
            config_path = config_dir / config_file
            if config_path.exists():
                try:
                    agent = await registry.create_agent_from_config(str(config_path))
                    # Start the agent automatically
                    await registry.start_agent(agent.name)
                    real_agents[agent_id] = agent
                    print(f"✅ Loaded and started real agent: {agent_id}")
                except Exception as e:
                    print(f"❌ Failed to load agent {agent_id}: {e}")

        # Test LLM availability
        llm_client = get_llm_client()
        llm_providers = llm_client.get_available_providers()
        if llm_providers:
            print(f"✅ LLM providers available: {llm_providers}")
        else:
            print("⚠️  No LLM providers available - agents will use fallback responses")

    except Exception as e:
        print(f"❌ Error initializing real agents: {e}")
        real_agents = {}

# Mock Data
mock_agents = {
    "chef_marco": {
        "name": "chef_marco",
        "type": "cooking_assistant",
        "status": "running",
        "module": "cooking_module",
        "personality": {"style": "Italian chef", "tone": "Passionate"},
        "tools": ["recipe_search", "nutrition_calculator", "cooking_timer"],
        "context_summary": {
            "total_items": 5,
            "total_tokens": 1250,
            "max_tokens": 4000,
            "token_utilization": 31.25,
            "context_by_type": {"system": 2, "user": 2, "memory": 1}
        },
        "memory_stats": {"conversations": 3, "facts": 12, "preferences": 5}
    },
    "professor_james": {
        "name": "professor_james",
        "type": "language_teacher",
        "status": "stopped",
        "module": "language_module",
        "personality": {"style": "British gentleman", "tone": "Encouraging"},
        "tools": ["grammar_checker", "pronunciation_helper", "progress_tracker"],
        "context_summary": {
            "total_items": 8,
            "total_tokens": 2100,
            "max_tokens": 4000,
            "token_utilization": 52.5,
            "context_by_type": {"system": 3, "user": 3, "memory": 2}
        },
        "memory_stats": {"conversations": 7, "facts": 25, "preferences": 8}
    },
    "weather_bot": {
        "name": "weather_bot",
        "type": "weather_assistant",
        "status": "running",
        "module": "weather_module",
        "personality": {"style": "Friendly meteorologist", "tone": "Informative"},
        "tools": ["weather_api", "location_resolver", "forecast_analyzer"],
        "context_summary": {
            "total_items": 3,
            "total_tokens": 800,
            "max_tokens": 3000,
            "token_utilization": 26.67,
            "context_by_type": {"system": 1, "user": 1, "memory": 1}
        },
        "memory_stats": {"conversations": 2, "facts": 8, "preferences": 3}
    },
    "weather_wizard": {
        "name": "weather_wizard",
        "type": "weather_assistant",
        "status": "running",
        "module": "weather_module",
        "personality": {"style": "Mystical weather sage", "tone": "Wise and dramatic"},
        "tools": ["advanced_forecasting", "climate_analysis", "storm_tracking", "atmospheric_magic"],
        "context_summary": {
            "total_items": 4,
            "total_tokens": 950,
            "max_tokens": 4000,
            "token_utilization": 23.75,
            "context_by_type": {"system": 2, "user": 1, "memory": 1}
        },
        "memory_stats": {"conversations": 1, "facts": 15, "preferences": 7}
    }
}

mock_modules = {
    "cooking_module": {
        "module_info": {
            "name": "cooking_module",
            "version": "1.0.0",
            "description": "Professional cooking assistant with Italian flair",
            "author": "Agentic Framework",
            "dependencies": [],
            "agent_types": ["cooking_assistant"],
            "tools": ["recipe_search", "nutrition_calculator", "cooking_timer"],
            "config_schema": {},
            "module_path": "modules/cooking_module.py",
            "is_active": True
        },
        "agents": {"chef_marco": {"type": "cooking_assistant", "running": True, "memory_items": 20, "context_items": 5}},
        "tools": ["recipe_search", "nutrition_calculator", "cooking_timer"],
        "hooks": 2,
        "initialized": True
    },
    "language_module": {
        "module_info": {
            "name": "language_module",
            "version": "1.0.0",
            "description": "British English language learning assistant",
            "author": "Agentic Framework",
            "dependencies": [],
            "agent_types": ["language_teacher"],
            "tools": ["grammar_checker", "pronunciation_helper", "progress_tracker"],
            "config_schema": {},
            "module_path": "modules/language_module.py",
            "is_active": True
        },
        "agents": {"professor_james": {"type": "language_teacher", "running": False, "memory_items": 40, "context_items": 8}},
        "tools": ["grammar_checker", "pronunciation_helper", "progress_tracker"],
        "hooks": 1,
        "initialized": True
    },
    "weather_module": {
        "module_info": {
            "name": "weather_module",
            "version": "1.0.0",
            "description": "Comprehensive weather information assistant",
            "author": "Agentic Framework",
            "dependencies": [],
            "agent_types": ["weather_assistant"],
            "tools": ["weather_api", "location_resolver", "forecast_analyzer"],
            "config_schema": {},
            "module_path": "modules/weather_module.py",
            "is_active": True
        },
        "agents": {"weather_bot": {"type": "weather_assistant", "running": True, "memory_items": 13, "context_items": 3}},
        "tools": ["weather_api", "location_resolver", "forecast_analyzer"],
        "hooks": 1,
        "initialized": True
    }
}

# Pydantic Models
class MessageRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = "demo-user"

class MessageResponse(BaseModel):
    response: str
    agent_name: str
    agent_type: str
    processing_time: float
    suggestions: Optional[List[str]] = []
    tool_results: Optional[List[Any]] = []
    context_summary: Optional[Dict[str, Any]] = {}

class AgentCreateRequest(BaseModel):
    module_name: str
    config: Dict[str, Any]

class CollaborativeMessageRequest(BaseModel):
    primary_agent: str
    message: str
    collaborating_agents: List[str]

class CollabMessageRequest(BaseModel):
    primary_agent: str
    text: str
    collaborating_agents: List[str]

# Helper Functions
async def generate_agent_response(agent_name: str, message: str, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
    """Generate response using real agent if available, otherwise use mock"""
    context = context or {}

    # Try real agent first
    if REAL_AGENTS_AVAILABLE and agent_name in real_agents:
        try:
            agent = real_agents[agent_name]
            response = await agent.process_message(message, context, user_id)

            return {
                "response": response.get("response", "I apologize, but I couldn't generate a response."),
                "agent_name": agent.name,
                "agent_type": agent.agent_type,
                "processing_time": response.get("processing_time", 0.0),
                "suggestions": _extract_suggestions(response),
                "tool_results": _extract_tool_results(response),
                "context_summary": response.get("context_summary", {}),
                "llm_used": True,
                "success": response.get("success", False)
            }
        except Exception as e:
            print(f"❌ Real agent {agent_name} failed: {e}")
            # Fall back to standalone LLM

    # Try standalone LLM client
    if STANDALONE_LLM_AVAILABLE:
        try:
            return await _generate_standalone_llm_response(agent_name, message, context, user_id)
        except Exception as e:
            print(f"❌ Standalone LLM failed: {e}")
            # Fall back to mock response

    # Use mock response
    return _generate_mock_response(agent_name, message)

async def _generate_standalone_llm_response(agent_name: str, message: str, context: Dict[str, Any] = None, user_id: str = None) -> Dict[str, Any]:
    """Generate response using standalone LLM client."""
    import time
    start_time = time.time()

    try:
        # Create LLM client
        llm_client = StandaloneLLMClient()

        # Get agent config from mock_agents to determine type
        agent_config = mock_agents.get(agent_name, {})
        agent_type = agent_config.get("type", "unknown")

        # Build system prompt based on agent type
        system_prompt = _build_agent_system_prompt(agent_name, agent_type)

        # Create messages
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=message)
        ]

        # Choose provider based on agent type
        provider = "anthropic" if agent_type == "language_teacher" else "openai"
        temperature = 0.7 if agent_type == "language_teacher" else 0.3

        # Generate response
        llm_response = await llm_client.generate_response(
            messages,
            provider=provider,
            max_tokens=600,
            temperature=temperature
        )

        processing_time = time.time() - start_time

        return {
            "response": llm_response.content,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "processing_time": processing_time,
            "suggestions": _get_agent_suggestions(agent_type),
            "tool_results": [{"llm_provider": llm_response.metadata.get("provider")}],
            "context_summary": {
                "llm_provider": llm_response.metadata.get("provider"),
                "model": llm_response.model,
                "tokens_used": llm_response.tokens_used
            },
            "llm_used": True,
            "success": True
        }

    except Exception as e:
        print(f"Error in standalone LLM response: {e}")
        raise


def _build_agent_system_prompt(agent_name: str, agent_type: str) -> str:
    """Build system prompt for different agent types."""

    if agent_name == "professor_james" or agent_type == "language_teacher":
        return """You are Professor James, a distinguished British English teacher. You help students learn proper British English with correct pronunciation, grammar, and cultural context. You are patient, encouraging, and always maintain a professional yet warm demeanor.

Teaching approach:
- Be encouraging and constructive
- Provide specific examples and corrections
- Include cultural context when relevant
- Use proper British English
- Correct mistakes gently but clearly
- Suggest follow-up learning opportunities"""

    elif agent_name == "weather_bot" or agent_type == "weather_assistant":
        return """You are a helpful weather assistant. Provide accurate, practical weather advice and information. Focus on actionable recommendations and safety considerations.

Guidelines:
- Prioritize safety in weather-related advice
- Give specific, practical recommendations
- Include clothing and activity suggestions
- Be concise but comprehensive
- Use friendly, helpful tone
- Consider both current conditions and forecasts"""

    elif agent_name == "chef_marco" or agent_type == "cooking_assistant":
        return """You are Chef Marco, a passionate Italian chef. You help with cooking questions, recipes, and culinary techniques with Italian flair and expertise.

Cooking style:
- Share authentic Italian techniques
- Be passionate about food and ingredients
- Provide practical cooking tips
- Include ingredient substitutions when helpful
- Maintain warm, enthusiastic personality"""

    else:
        return f"""You are a helpful AI assistant specialized in {agent_type}. Provide accurate, helpful information and assistance while maintaining a professional and friendly demeanor."""


def _get_agent_suggestions(agent_type: str) -> List[str]:
    """Get suggestions based on agent type."""
    suggestions_map = {
        "language_teacher": [
            "Help me with pronunciation",
            "Check my grammar",
            "Explain British expressions",
            "Practice conversation"
        ],
        "weather_assistant": [
            "What should I wear today?",
            "Will it rain tomorrow?",
            "Is it good weather for outdoor activities?",
            "Show me the weekly forecast"
        ],
        "cooking_assistant": [
            "Suggest a recipe",
            "How do I make pasta?",
            "What wine pairs with fish?",
            "Cooking technique tips"
        ]
    }

    return suggestions_map.get(agent_type, [
        "How can you help me?",
        "What can you do?",
        "Tell me more",
        "Give me advice"
    ])


def _extract_suggestions(response: Dict[str, Any]) -> List[str]:
    """Extract suggestions from agent response"""
    suggestions = []

    # From teaching points
    teaching_points = response.get("teaching_points", [])
    for point in teaching_points:
        if isinstance(point, dict) and "content" in point:
            suggestions.append(f"Learn more about: {point['content']}")

    # From next steps
    next_steps = response.get("next_steps", [])
    suggestions.extend(next_steps[:3])  # Limit to 3

    # From recommendations
    recommendations = response.get("recommendations", [])
    if isinstance(recommendations, list):
        suggestions.extend(recommendations[:2])

    return suggestions[:5]  # Limit total suggestions

def _extract_tool_results(response: Dict[str, Any]) -> List[Any]:
    """Extract tool results from agent response"""
    tool_results = []

    # Tools used
    tools_used = response.get("tools_used", [])
    if tools_used:
        tool_results.append({"tools_executed": tools_used})

    # Weather data
    if "weather_data" in response:
        tool_results.append({"weather_data": response["weather_data"]})

    # Analysis results
    if "analysis" in response:
        tool_results.append({"analysis": response["analysis"]})

    return tool_results

def _generate_mock_response(agent_name: str, message: str) -> Dict[str, Any]:
    """Generate a mock response based on agent type and personality"""
    agent = mock_agents.get(agent_name)
    if not agent:
        return {
            "response": "I'm not sure how to respond to that.",
            "agent_name": agent_name,
            "agent_type": "unknown",
            "processing_time": 0.5,
            "suggestions": [],
            "tool_results": [],
            "context_summary": {},
            "llm_used": False,
            "success": False
        }

    agent_type = agent["type"]
    personality_style = agent.get("personality", {}).get("style", "")

    # Agent-specific responses based on personality
    if agent_name == "weather_wizard":
        responses = [
            f"🔮 *peers into the mystical weather crystal* Ah, I see the atmospheric spirits whisper of {random.choice(['sunshine', 'storms', 'gentle breezes', 'morning mist'])}...",
            f"⚡ The ancient winds tell me secrets! *dramatically gestures* Let me consult the cosmic weather patterns...",
            f"🌟 By the power of the four weather elements, I shall divine the forecast for you, seeker!",
            f"🌪️ *swirls cape dramatically* The meteorological magic flows through me! I sense disturbances in the atmospheric force...",
            f"❄️ Behold! The weather spirits have blessed me with visions of the skies above. Let me share their wisdom...",
        ]
    elif agent_name == "chef_marco":
        responses = [
            f"Ah, bellissimo! Let me help you with that recipe. *adjusts chef's hat*",
            f"Mamma mia! That sounds delicious. Here's what I suggest...",
            f"As a chef, I recommend using fresh ingredients for the best flavor!",
            f"Let me share a secret from my nonna's kitchen...",
        ]
    elif agent_name == "professor_james":
        responses = [
            f"Quite right! Let me help you improve your English, old chap.",
            f"Splendid question! In proper British English, we would say...",
            f"I say, that's a common mistake. Allow me to explain...",
            f"Excellent effort! Now, let's polish that grammar a bit more...",
        ]
    elif agent_name == "weather_bot":
        responses = [
            f"Let me check the current weather conditions for you!",
            f"Based on the latest meteorological data...",
            f"The forecast shows some interesting patterns...",
            f"Perfect question for a weather enthusiast like myself!",
        ]
    else:
        # Generic responses by type
        responses = {
            "cooking_assistant": ["I'm here to help with your cooking needs!"],
            "language_teacher": ["I'm here to help with your language learning!"],
            "weather_assistant": ["I'm here to help with weather information!"]
        }.get(agent_type, ["I'm here to help!"])

    response_text = random.choice(responses)

    # Simulate processing time
    processing_time = random.uniform(0.1, 0.3)

    return {
        "response": response_text,
        "agent_name": agent_name,
        "agent_type": agent_type,
        "processing_time": processing_time,
        "suggestions": [],
        "tool_results": [],
        "context_summary": agent.get("context_summary", {}),
        "llm_used": False,
        "success": True
    }

def get_mock_suggestions(agent_type: str, agent_name: str = None) -> List[str]:
    """Get mock suggestions based on agent type and personality"""
    if agent_name == "weather_wizard":
        suggestions = [
            "🔮 Divine tomorrow's weather for me",
            "⚡ What do the storm spirits say?",
            "🌟 Reveal the cosmic forecast",
            "🌪️ Show me the atmospheric magic",
            "❄️ What weather mysteries await?",
            "🌈 Cast a weather blessing spell"
        ]
    elif agent_name == "chef_marco":
        suggestions = [
            "What's a good pasta recipe?",
            "How do I make risotto?",
            "Tell me about Italian desserts",
            "What wine pairs with fish?"
        ]
    elif agent_name == "professor_james":
        suggestions = [
            "Help me with pronunciation",
            "Check my grammar",
            "Explain the difference between 'who' and 'whom'",
            "Practice British accent"
        ]
    elif agent_name == "weather_bot":
        suggestions = [
            "What's the weather like today?",
            "Will it rain tomorrow?",
            "Show me the 5-day forecast",
            "Is it good weather for hiking?"
        ]
    else:
        # Generic suggestions by type
        suggestions = {
            "cooking_assistant": [
                "What's a good recipe?",
                "How do I cook this?",
                "Tell me about ingredients",
                "What should I make for dinner?"
            ],
            "language_teacher": [
                "Help me with pronunciation",
                "Check my grammar",
                "Explain this word",
                "Practice conversation"
            ],
            "weather_assistant": [
                "What's the weather like?",
                "Will it rain?",
                "Show me the forecast",
                "Is it good weather for outdoor activities?"
            ]
        }.get(agent_type, ["How can you help me?", "What can you do?"])

    return random.sample(suggestions, min(2, len(suggestions)))

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Enhanced Agentic Framework API (Demo)",
        "version": "2.0.0-demo",
        "status": "operational",
        "features": ["agents", "modules", "chat", "visualization"]
    }

@app.get("/health")
async def health_check():
    llm_status = {}
    if REAL_AGENTS_AVAILABLE:
        try:
            llm_client = get_llm_client()
            providers = llm_client.get_available_providers()
            llm_status = {
                "available_providers": providers,
                "default_provider": llm_client.default_provider,
                "real_agents_loaded": len(real_agents)
            }
        except Exception as e:
            llm_status = {"error": str(e)}

    return {
        "status": "healthy",
        "version": "2.0.0-demo",
        "llm_integration": llm_status,
        "real_agents_available": REAL_AGENTS_AVAILABLE,
        "modules": mock_modules,
        "performance": {
            "resource_limits": {"max_memory_items_per_agent": 1000, "max_context_length": 4000},
            "connection_pools": {"http_pool_size": 10, "db_pool_size": 5},
            "performance_metrics": {
                "message_processing_time": {"avg": 0.15, "min": 0.05, "max": 0.30, "count": 47},
                "context_optimization_time": {"avg": 0.08, "min": 0.02, "max": 0.15, "count": 47}
            }
        },
        "timestamp": time.time()
    }

@app.get("/llm/status")
async def llm_status():
    """Check LLM integration status and test connectivity"""
    if REAL_AGENTS_AVAILABLE:
        # Use real agent framework
        pass  # Original logic would go here
    elif STANDALONE_LLM_AVAILABLE:
        # Use standalone LLM client
        try:
            llm_client = StandaloneLLMClient()
            providers = llm_client.get_available_providers()

            # Test each provider
            provider_tests = {}
            for provider in providers:
                test_result = await llm_client.test_connection(provider)
                provider_tests[provider] = test_result

            return {
                "status": "available",
                "message": "Standalone LLM client available",
                "providers": provider_tests,
                "default_provider": providers[0] if providers else None,
                "using_mock_responses": False,
                "using_standalone_llm": True
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "using_mock_responses": True
            }
    else:
        return {
            "status": "unavailable",
            "message": "No LLM integration available",
            "using_mock_responses": True
        }

    try:
        llm_client = get_llm_client()
        providers = llm_client.get_available_providers()

        if not providers:
            return {
                "status": "no_providers",
                "message": "No LLM providers configured. Set API keys.",
                "using_mock_responses": True
            }

        # Test each provider
        provider_tests = {}
        for provider in providers:
            test_result = await llm_client.test_connection(provider)
            provider_tests[provider] = test_result

        return {
            "status": "available",
            "providers": provider_tests,
            "default_provider": llm_client.default_provider,
            "real_agents_loaded": list(real_agents.keys()),
            "using_mock_responses": False
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "using_mock_responses": True
        }

@app.get("/agents")
async def list_agents():
    all_agents = {}

    # Add real agents if available
    if REAL_AGENTS_AVAILABLE and real_agents:
        for agent_id, agent in real_agents.items():
            # Check if agent is actually running in the registry
            is_running = agent.name in registry._running_agents if registry else False
            all_agents[agent_id] = {
                "name": agent.name,
                "type": agent.agent_type,
                "status": "running" if is_running else "stopped",
                "real_agent": True,
                "llm_enabled": True,
                "context_summary": agent.context_engine.get_context_summary() if hasattr(agent, 'context_engine') else {},
                "personality": getattr(agent, 'personality', {}),
                "tools": agent.tool_registry.list_tools() if hasattr(agent, 'tool_registry') else [],
                "memory_stats": {"conversations": 0, "facts": 0, "preferences": 0}  # Placeholder
            }
        print(f"✅ Returning {len(all_agents)} real agents: {list(all_agents.keys())}")
    else:
        # Only show mock agents if no real agents are available
        print("⚠️  No real agents available, showing mock agents")
        for agent_id, agent_data in mock_agents.items():
            agent_data = agent_data.copy()
            agent_data["real_agent"] = False
            agent_data["llm_enabled"] = False
            all_agents[agent_id] = agent_data

    return {"agents": all_agents}

@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return mock_agents[agent_name]

@app.post("/agents/collaboration/message")
async def send_collaborative_message(request_data: CollabMessageRequest):
    """
    Send a message that involves collaboration between multiple agents.
    """
    primary_agent = request_data.primary_agent
    message = request_data.text
    collaborating_agents = request_data.collaborating_agents

    # Check if agent exists and is running
    if REAL_AGENTS_AVAILABLE and real_agents and primary_agent in real_agents:
        # Real agent - check if it's running in the registry
        real_agent = real_agents[primary_agent]
        if registry and real_agent.name not in registry._running_agents:
            raise HTTPException(status_code=400, detail="Agent is not running")
    elif primary_agent in mock_agents:
        # Mock agent - check status
        agent = mock_agents[primary_agent]
        if agent["status"] != "running":
            raise HTTPException(status_code=400, detail="Agent is not running")
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Actually facilitate collaboration between agents
    try:
        # Check if we have real agents
        if REAL_AGENTS_AVAILABLE and primary_agent in real_agents:
            primary_real_agent = real_agents[primary_agent]

            # Step 1: Check if primary agent should handle this or delegate to collaborator
            # For language questions, check if the question is about a language the primary agent doesn't specialize in
            should_delegate = False
            delegate_to = None

            # Simple language detection for delegation
            if primary_agent == "professor_james":
                chinese_keywords = ["chinese", "中文", "名字", "pinyin", "mandarin", "李老师", "teacher li"]
                if any(keyword in message.lower() for keyword in chinese_keywords):
                    should_delegate = True
                    delegate_to = "teacher_li"
            elif primary_agent == "teacher_li":
                english_keywords = ["english", "british", "professor james", "grammar", "pronunciation"]
                if any(keyword in message.lower() for keyword in english_keywords):
                    should_delegate = True
                    delegate_to = "professor_james"

            if should_delegate and delegate_to in real_agents:
                # Delegate to the appropriate specialist
                original_primary_agent = primary_agent  # Store the original agent (professor_james)
                primary_real_agent = real_agents[delegate_to]
                primary_agent = delegate_to  # Switch to the specialist (teacher_li)
                # Add the original agent to collaborating agents if not already there
                if original_primary_agent not in collaborating_agents:
                    collaborating_agents.append(original_primary_agent)
                # Remove the delegate from collaborating agents to avoid duplication
                collaborating_agents = [agent for agent in collaborating_agents if agent != delegate_to]

            # Send message to primary agent with collaboration context
            collaboration_context = {
                "collaboration_mode": True,
                "collaborating_agents": collaborating_agents,
                "collaboration_type": "multi_agent_response"
            }

            primary_response = await primary_real_agent.process_message(
                message,
                collaboration_context,
                "ui-user"
            )

            # Step 2: Get responses from collaborating agents
            collaborative_responses = []
            for collab_agent_name in collaborating_agents:
                if collab_agent_name != primary_agent and collab_agent_name in real_agents:
                    collab_agent = real_agents[collab_agent_name]

                    # Create collaboration message for the other agent
                    collab_message = f"A user asked: '{message}'. {primary_agent} responded: '{primary_response.get('response', '')}'. Please provide your perspective or additional information."

                    collab_context = {
                        "collaboration_from": primary_agent,
                        "collaboration_type": "response_enhancement",
                        "original_message": message,
                        "primary_response": primary_response.get("response", "")
                    }

                    try:
                        collab_response = await collab_agent.process_message(
                            collab_message,
                            collab_context,
                            "ui-user"
                        )
                        collaborative_responses.append({
                            "agent": collab_agent_name,
                            "response": collab_response.get("response", "")
                        })
                    except Exception as e:
                        print(f"Error getting response from {collab_agent_name}: {e}")

            # Step 3: Combine responses
            combined_response = primary_response.get("response", "")

            if collaborative_responses:
                combined_response += "\n\n---\n\n"
                for collab in collaborative_responses:
                    combined_response += f"**{collab['agent']} adds:**\n{collab['response']}\n\n"

            return {
                "response": combined_response,
                "agent_name": primary_agent,
                "agent_type": primary_real_agent.agent_type,
                "processing_time": primary_response.get("processing_time", 0.0),
                "collaboration_mode": True,
                "collaborating_agents": collaborating_agents,
                "collaborative_responses": collaborative_responses,
                "suggestions": primary_response.get("suggestions", []),
                "tool_results": primary_response.get("tool_results", []),
                "context_summary": primary_response.get("context_summary", {}),
                "success": primary_response.get("success", False)
            }
        else:
            # Mock collaborative response - simulate actual agent collaboration
            processing_time = random.uniform(0.5, 2.0)

            # Generate primary response
            primary_mock_response = ""
            if primary_agent == "professor_james":
                primary_mock_response = f"Ah, excellent question! In British English, we say 'name' - quite straightforward, really. Now, let me consult with my colleague Teacher Li for the Chinese translation."
            elif primary_agent == "teacher_li":
                primary_mock_response = f"Great question! In Chinese, 'name' is called '名字' (míngzi). Let me work with Professor James to give you both perspectives."

            # Generate collaborative responses
            collaborative_mock_responses = []
            for collab_agent in collaborating_agents:
                if collab_agent != primary_agent:
                    if collab_agent == "teacher_li":
                        collab_response = f"**Teacher Li adds:**\nIn Chinese, 'name' is '名字' (míngzi). The character '名' means 'name' and '字' means 'character' or 'word'. So literally it means 'name-word'. We also have '姓名' (xìngmíng) which is more formal and includes both family name and given name."
                        collaborative_mock_responses.append(collab_response)
                    elif collab_agent == "professor_james":
                        collab_response = f"**Professor James adds:**\nIn British English, we have several ways to ask for someone's name: 'What's your name?', 'May I ask your name?', or more formally 'Could you please state your name?' The word 'name' comes from Old English 'nama', related to German 'Name'."
                        collaborative_mock_responses.append(collab_response)

            # Combine responses
            collaborative_response = primary_mock_response
            if collaborative_mock_responses:
                collaborative_response += "\n\n---\n\n" + "\n\n".join(collaborative_mock_responses)

            return {
                "response": collaborative_response,
                "agent_name": primary_agent,
                "agent_type": mock_agents[primary_agent]["type"],
                "processing_time": processing_time,
                "collaboration_mode": True,
                "collaborating_agents": collaborating_agents,
                "suggestions": [
                    "Ask about language learning strategies",
                    "Compare teaching approaches",
                    "Request cultural insights",
                    "Practice conversation skills"
                ],
                "tool_results": [{"collaboration": "active", "agents_involved": len(collaborating_agents)}],
                "context_summary": {"collaborative_session": True},
                "success": True
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in collaborative messaging: {str(e)}")

@app.post("/agents/{agent_name}/message")
async def send_message_to_agent(agent_name: str, message_data: MessageRequest):
    # Check if agent exists and is running
    if REAL_AGENTS_AVAILABLE and real_agents and agent_name in real_agents:
        # Real agent - check if it's running in the registry
        real_agent = real_agents[agent_name]
        if registry and real_agent.name not in registry._running_agents:
            raise HTTPException(status_code=400, detail="Agent is not running")
    elif agent_name in mock_agents:
        # Mock agent - check status
        agent = mock_agents[agent_name]
        if agent["status"] != "running":
            raise HTTPException(status_code=400, detail="Agent is not running")
    else:
        raise HTTPException(status_code=404, detail="Agent not found")

    # # Check for automatic delegation opportunities
    # message = message_data.text
    # should_delegate = False
    # delegate_to = None

    # if REAL_AGENTS_AVAILABLE and agent_name in real_agents:
    #     # Simple language detection for delegation
    #     if agent_name == "professor_james":
    #         chinese_keywords = ["chinese", "中文", "名字", "pinyin", "mandarin", "李老师", "teacher li"]
    #         if any(keyword in message.lower() for keyword in chinese_keywords):
    #             should_delegate = True
    #             delegate_to = "teacher_li"
    #     elif agent_name == "teacher_li":
    #         english_keywords = ["english", "british", "professor james", "grammar", "pronunciation"]
    #         if any(keyword in message.lower() for keyword in english_keywords):
    #             should_delegate = True
    #             delegate_to = "professor_james"

    #     # If delegation is needed and target agent is available, redirect to collaborative endpoint
    #     if should_delegate and delegate_to in real_agents:
    #         print(f"🔄 Auto-delegating from {agent_name} to {delegate_to} for message: {message}")
    #         # Create collaborative request
    #         collab_request = CollabMessageRequest(
    #             primary_agent=agent_name,
    #             text=message,
    #             collaborating_agents=[delegate_to]
    #         )
    #         # Call the collaborative endpoint
    #         return await send_collaborative_message(collab_request)

    # Generate response using real or mock agent
    try:
        response_data = await generate_agent_response(
            agent_name,
            message_data.text,
            message_data.context,
            message_data.user_id
        )

        # Add mock suggestions if not provided by real agent
        if not response_data.get("suggestions"):
            agent_type = response_data.get("agent_type", "unknown")
            response_data["suggestions"] = get_mock_suggestions(agent_type, agent_name)

        return MessageResponse(
            response=response_data["response"],
            agent_name=response_data["agent_name"],
            agent_type=response_data["agent_type"],
            processing_time=response_data["processing_time"],
            suggestions=response_data["suggestions"],
            tool_results=response_data.get("tool_results", []),
            context_summary=response_data.get("context_summary", {})
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/agents/{agent_name}/start")
async def start_agent(agent_name: str):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    mock_agents[agent_name]["status"] = "running"
    return {"message": f"Agent {agent_name} started successfully"}

@app.post("/agents/{agent_name}/stop")
async def stop_agent(agent_name: str):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    mock_agents[agent_name]["status"] = "stopped"
    return {"message": f"Agent {agent_name} stopped successfully"}

@app.delete("/agents/{agent_name}")
async def remove_agent(agent_name: str):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    del mock_agents[agent_name]
    return {"message": f"Agent {agent_name} removed successfully"}

@app.post("/agents/create")
async def create_agent(agent_config: AgentCreateRequest):
    agent_name = agent_config.config.get("name", f"agent_{len(mock_agents)}")
    agent_type = agent_config.config.get("type", "general_assistant")

    new_agent = {
        "name": agent_name,
        "type": agent_type,
        "status": "stopped",
        "module": agent_config.module_name,
        "personality": agent_config.config.get("personality", {}),
        "tools": ["basic_tool"],
        "context_summary": {
            "total_items": 0,
            "total_tokens": 0,
            "max_tokens": 4000,
            "token_utilization": 0,
            "context_by_type": {}
        },
        "memory_stats": {"conversations": 0, "facts": 0, "preferences": 0}
    }

    mock_agents[agent_name] = new_agent
    return {
        "message": f"Agent {agent_name} created successfully",
        "agent_name": agent_name,
        "agent_type": agent_type,
        "module": agent_config.module_name
    }

@app.get("/modules")
async def list_modules():
    return {
        "modules": list(mock_modules.keys()),
        "status": mock_modules
    }

@app.get("/modules/{module_name}")
async def get_module_status(module_name: str):
    if module_name not in mock_modules:
        raise HTTPException(status_code=404, detail="Module not found")
    return mock_modules[module_name]

@app.get("/performance")
async def get_performance():
    return {
        "resource_limits": {"max_memory_items_per_agent": 1000, "max_context_length": 4000},
        "connection_pools": {"http_pool_size": 10, "db_pool_size": 5},
        "performance_metrics": {
            "message_processing_time": {"avg": 0.15, "min": 0.05, "max": 0.30, "count": 47},
            "context_optimization_time": {"avg": 0.08, "min": 0.02, "max": 0.15, "count": 47}
        }
    }

@app.post("/performance/optimize")
async def optimize_performance():
    return {
        "message": "Performance optimization completed",
        "performance_report": {
            "optimizations_applied": 3,
            "memory_freed": "15MB",
            "response_time_improvement": "12%"
        }
    }

# Collaboration endpoints (simplified)
@app.get("/agents/collaboration/graph")
async def get_collaboration_graph():
    return {
        "collaboration_graph": {
            "chef_marco": {
                "type": "cooking_assistant",
                "can_collaborate_with": ["weather_bot", "weather_wizard"],
                "collaboration_style": "helpful"
            },
            "professor_james": {
                "type": "language_teacher",
                "can_collaborate_with": ["chef_marco", "weather_bot", "weather_wizard"],
                "collaboration_style": "educational"
            },
            "weather_bot": {
                "type": "weather_assistant",
                "can_collaborate_with": ["chef_marco", "weather_wizard"],
                "collaboration_style": "informative"
            },
            "weather_wizard": {
                "type": "weather_assistant",
                "can_collaborate_with": ["chef_marco", "weather_bot"],
                "collaboration_style": "mystical"
            }
            }
}

@app.post("/agents/{agent1}/collaborate/{agent2}")
async def collaborate_agents(agent1: str, agent2: str, message_data: dict = None):
    """
    Initiate collaboration between two agents.
    """
    # Check if both agents exist and are running
    agent1_found = False
    agent2_found = False
    agent1_running = False
    agent2_running = False

    # Check real agents first
    if REAL_AGENTS_AVAILABLE and real_agents:
        if agent1 in real_agents:
            agent1_found = True
            agent1_running = registry and real_agents[agent1].name in registry._running_agents
        if agent2 in real_agents:
            agent2_found = True
            agent2_running = registry and real_agents[agent2].name in registry._running_agents

    # Check mock agents if not found in real agents
    if not agent1_found and agent1 in mock_agents:
        agent1_found = True
        agent1_running = mock_agents[agent1]["status"] == "running"
    if not agent2_found and agent2 in mock_agents:
        agent2_found = True
        agent2_running = mock_agents[agent2]["status"] == "running"

    # Validate agents exist
    if not agent1_found:
        raise HTTPException(status_code=404, detail=f"Agent {agent1} not found")
    if not agent2_found:
        raise HTTPException(status_code=404, detail=f"Agent {agent2} not found")

    # Validate agents are running
    if not agent1_running:
        raise HTTPException(status_code=400, detail=f"Agent {agent1} is not running")
    if not agent2_running:
        raise HTTPException(status_code=400, detail=f"Agent {agent2} is not running")

    # Try real agent collaboration first
    if REAL_AGENTS_AVAILABLE and registry:
        try:
            result = await registry.facilitate_collaboration(
                agent1, agent2, message_data.get("message", "") if message_data else ""
            )
            if result.get("success"):
                collaboration_id = f"{agent1}-{agent2}-{int(time.time())}"

                # Store the active collaboration
                active_collaborations[collaboration_id] = {
                    "agent1": agent1,
                    "agent2": agent2,
                    "established_at": time.time(),
                    "status": "active"
                }

                return {
                    "success": True,
                    "message": f"Collaboration established between {agent1} and {agent2}",
                    "collaboration_id": collaboration_id,
                    "result": result,
                    "real_collaboration": True
                }
        except Exception as e:
            print(f"Real collaboration failed: {e}")

    # Mock collaboration response
    collaboration_id = f"{agent1}-{agent2}-{int(time.time())}"

    # Get agent data from real agents or mock agents
    agent1_data = None
    agent2_data = None

    if REAL_AGENTS_AVAILABLE and agent1 in real_agents:
        agent1_data = {"type": real_agents[agent1].agent_type}
    elif agent1 in mock_agents:
        agent1_data = mock_agents[agent1]

    if REAL_AGENTS_AVAILABLE and agent2 in real_agents:
        agent2_data = {"type": real_agents[agent2].agent_type}
    elif agent2 in mock_agents:
        agent2_data = mock_agents[agent2]

    collaboration_response = {
        "success": True,
        "message": f"Collaboration thread established between {agent1} and {agent2}",
        "collaboration_id": collaboration_id,
        "participants": [
            {
                "name": agent1,
                "type": agent1_data["type"],
                "role": "initiator"
            },
            {
                "name": agent2,
                "type": agent2_data["type"],
                "role": "collaborator"
            }
        ],
        "collaboration_type": "thread_connection",
        "established_at": time.time(),
        "status": "active",
        "real_collaboration": False
    }

    # Store the active collaboration
    active_collaborations[collaboration_id] = {
        "agent1": agent1,
        "agent2": agent2,
        "established_at": time.time(),
        "status": "active"
    }

    return collaboration_response



@app.get("/agents/collaboration/active")
async def get_active_collaborations():
    """Get all active collaboration threads."""
    return {
        "active_collaborations": active_collaborations,
        "total_active": len(active_collaborations)
    }

@app.delete("/agents/collaboration/{collaboration_id}")
async def remove_collaboration(collaboration_id: str):
    """Remove an active collaboration thread."""
    if collaboration_id in active_collaborations:
        removed_collab = active_collaborations.pop(collaboration_id)
        return {
            "success": True,
            "message": f"Collaboration between {removed_collab['agent1']} and {removed_collab['agent2']} removed",
            "removed_collaboration": removed_collab
        }
    else:
        raise HTTPException(status_code=404, detail="Collaboration not found")

@app.delete("/agents/{agent1}/collaborate/{agent2}")
async def remove_collaboration_by_agents(agent1: str, agent2: str):
    """Remove collaboration between two specific agents."""
    # Find collaboration by agent names
    collab_to_remove = None
    collab_id_to_remove = None

    for collab_id, collab in active_collaborations.items():
        if (collab['agent1'] == agent1 and collab['agent2'] == agent2) or \
           (collab['agent1'] == agent2 and collab['agent2'] == agent1):
            collab_to_remove = collab
            collab_id_to_remove = collab_id
            break

    if collab_to_remove:
        active_collaborations.pop(collab_id_to_remove)
        return {
            "success": True,
            "message": f"Collaboration between {agent1} and {agent2} removed",
            "removed_collaboration": collab_to_remove
        }
    else:
        raise HTTPException(status_code=404, detail=f"No active collaboration found between {agent1} and {agent2}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Load real agents on startup."""
    print("🚀 Starting Agentic Framework API...")
    await load_real_agents()
    print(f"✅ Startup complete. Real agents loaded: {len(real_agents)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
