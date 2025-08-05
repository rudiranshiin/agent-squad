#!/usr/bin/env python3
"""
Simplified Agentic Framework API
A demo version that works without complex dependencies
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import time
import random
import uuid
from datetime import datetime

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

# Helper Functions
def generate_agent_response(agent_name: str, message: str) -> str:
    """Generate a mock response based on agent type"""
    agent = mock_agents.get(agent_name)
    if not agent:
        return "I'm not sure how to respond to that."

    agent_type = agent["type"]
    responses = {
        "cooking_assistant": [
            f"Ah, bellissimo! Let me help you with that recipe. *adjusts chef's hat*",
            f"Mamma mia! That sounds delicious. Here's what I suggest...",
            f"As a chef, I recommend using fresh ingredients for the best flavor!",
            f"Let me share a secret from my nonna's kitchen...",
        ],
        "language_teacher": [
            f"Quite right! Let me help you improve your English, old chap.",
            f"Splendid question! In proper British English, we would say...",
            f"I say, that's a common mistake. Allow me to explain...",
            f"Excellent effort! Now, let's polish that grammar a bit more...",
        ],
        "weather_assistant": [
            f"Let me check the current weather conditions for you!",
            f"Based on the latest meteorological data...",
            f"The forecast shows some interesting patterns...",
            f"Perfect question for a weather enthusiast like myself!",
        ]
    }

    return random.choice(responses.get(agent_type, ["I'm here to help!"]))

def get_mock_suggestions(agent_type: str) -> List[str]:
    """Get mock suggestions based on agent type"""
    suggestions = {
        "cooking_assistant": [
            "What's a good pasta recipe?",
            "How do I make risotto?",
            "Tell me about Italian desserts",
            "What wine pairs with fish?"
        ],
        "language_teacher": [
            "Help me with pronunciation",
            "Check my grammar",
            "Explain the difference between 'who' and 'whom'",
            "Practice British accent"
        ],
        "weather_assistant": [
            "What's the weather like today?",
            "Will it rain tomorrow?",
            "Show me the 5-day forecast",
            "Is it good weather for hiking?"
        ]
    }
    return random.sample(suggestions.get(agent_type, []), 2)

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
    return {
        "status": "healthy",
        "version": "2.0.0-demo",
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

@app.get("/agents")
async def list_agents():
    return {"agents": mock_agents}

@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return mock_agents[agent_name]

@app.post("/agents/{agent_name}/message")
async def send_message_to_agent(agent_name: str, message_data: MessageRequest):
    if agent_name not in mock_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = mock_agents[agent_name]
    if agent["status"] != "running":
        raise HTTPException(status_code=400, detail="Agent is not running")

    # Simulate processing time
    processing_start = time.time()
    time.sleep(random.uniform(0.1, 0.3))  # Simulate processing
    processing_time = time.time() - processing_start

    response_text = generate_agent_response(agent_name, message_data.text)
    suggestions = get_mock_suggestions(agent["type"])

    return MessageResponse(
        response=response_text,
        agent_name=agent_name,
        agent_type=agent["type"],
        processing_time=processing_time,
        suggestions=suggestions,
        context_summary=agent.get("context_summary", {})
    )

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
                "can_collaborate_with": ["weather_bot"],
                "collaboration_style": "helpful"
            },
            "professor_james": {
                "type": "language_teacher",
                "can_collaborate_with": ["chef_marco", "weather_bot"],
                "collaboration_style": "educational"
            },
            "weather_bot": {
                "type": "weather_assistant",
                "can_collaborate_with": ["chef_marco"],
                "collaboration_style": "informative"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
