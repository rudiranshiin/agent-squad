"""
Main FastAPI application for the Agentic AI Framework.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import logging
from pathlib import Path

from framework.core.agent_registry import AgentRegistry
from framework.utils.config_loader import ConfigLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Framework",
    description="A sophisticated framework for building context-engineered AI agents with MCP tool integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API
class MessageRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class CollaborationRequest(BaseModel):
    text: str
    collaboration_type: Optional[str] = "request"


class AgentConfigRequest(BaseModel):
    config: Dict[str, Any]


class BroadcastRequest(BaseModel):
    message: str
    agent_types: Optional[List[str]] = None
    exclude_agents: Optional[List[str]] = None


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load all agent configurations on startup."""
    logger.info("Starting Agentic AI Framework...")

    try:
        # Load server configuration
        server_config = ConfigLoader.load_server_config()

        # Auto-load agents if configured
        if server_config.get("agents", {}).get("auto_load", True):
            config_dir = server_config.get("agents", {}).get("config_directory", "agents/configs")
            await AgentRegistry.load_agents_from_directory(config_dir)

        logger.info(f"Framework started successfully with {len(AgentRegistry.list_agents())} agents")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Agentic AI Framework...")
    await AgentRegistry.cleanup()
    logger.info("Framework shutdown complete")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with framework information."""
    return {
        "message": "Welcome to the Agentic AI Framework",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
        "agents": len(AgentRegistry.list_agents()),
        "endpoints": {
            "agents": "/agents",
            "health": "/health",
            "docs": "/docs"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        registry_status = await AgentRegistry.get_registry_status()
        agent_health = await AgentRegistry.health_check_agents()

        healthy_agents = sum(1 for status in agent_health.values() if status)
        total_agents = len(agent_health)

        return {
            "status": "healthy" if healthy_agents == total_agents else "degraded",
            "framework": "operational",
            "agents": {
                "total": total_agents,
                "healthy": healthy_agents,
                "unhealthy": total_agents - healthy_agents
            },
            "registry": registry_status
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


# Agent management endpoints
@app.get("/agents")
async def list_agents():
    """List all available agents."""
    try:
        registry_status = await AgentRegistry.get_registry_status()
        return {
            "agents": registry_status["agents"],
            "summary": {
                "total_agents": registry_status["total_agents"],
                "running_agents": registry_status["running_agents"]
            }
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")


@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get information about a specific agent."""
    agent = AgentRegistry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    try:
        agent_status = await agent.get_agent_status()
        return agent_status
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent information")


@app.post("/agents/{agent_name}/message")
async def send_message_to_agent(agent_name: str, request: MessageRequest):
    """Send a message to a specific agent."""
    agent = AgentRegistry.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    try:
        response = await agent.process_message(
            request.text,
            context=request.context or {},
            user_id=request.user_id
        )
        return response
    except Exception as e:
        logger.error(f"Error processing message for agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@app.post("/agents/{agent_name}/start")
async def start_agent(agent_name: str, background_tasks: BackgroundTasks):
    """Start an agent."""
    if agent_name not in AgentRegistry.list_agents():
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    try:
        background_tasks.add_task(AgentRegistry.start_agent, agent_name)
        return {"message": f"Agent {agent_name} is starting", "status": "starting"}
    except Exception as e:
        logger.error(f"Error starting agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start agent")


@app.post("/agents/{agent_name}/stop")
async def stop_agent(agent_name: str):
    """Stop an agent."""
    if agent_name not in AgentRegistry.list_agents():
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")

    try:
        await AgentRegistry.stop_agent(agent_name)
        return {"message": f"Agent {agent_name} stopped", "status": "stopped"}
    except Exception as e:
        logger.error(f"Error stopping agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop agent")


# Collaboration endpoints
@app.post("/agents/{agent1}/collaborate/{agent2}")
async def facilitate_collaboration(agent1: str, agent2: str, request: CollaborationRequest):
    """Facilitate collaboration between two agents."""
    try:
        result = await AgentRegistry.facilitate_collaboration(
            agent1, agent2, request.text
        )
        return result
    except Exception as e:
        logger.error(f"Error facilitating collaboration: {e}")
        raise HTTPException(status_code=500, detail="Failed to facilitate collaboration")


@app.get("/agents/collaboration/graph")
async def get_collaboration_graph():
    """Get the collaboration graph showing agent relationships."""
    try:
        graph = AgentRegistry.get_collaboration_graph()
        return graph
    except Exception as e:
        logger.error(f"Error getting collaboration graph: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collaboration graph")


# Broadcasting endpoints
@app.post("/agents/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Broadcast a message to multiple agents."""
    try:
        responses = await AgentRegistry.broadcast_message(
            request.message,
            agent_types=request.agent_types,
            exclude_agents=request.exclude_agents
        )
        return {
            "message": request.message,
            "responses": responses,
            "agents_contacted": len(responses)
        }
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


# Agent creation endpoints
@app.post("/agents/create")
async def create_agent(request: AgentConfigRequest):
    """Create a new agent from configuration."""
    try:
        # Save config temporarily
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(request.config, f)
            temp_config_path = f.name

        # Create agent
        agent = await AgentRegistry.create_agent_from_config(temp_config_path)

        # Clean up temp file
        import os
        os.unlink(temp_config_path)

        return {
            "message": f"Agent {agent.name} created successfully",
            "agent_name": agent.name,
            "agent_type": agent.agent_type
        }

    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Configuration endpoints
@app.get("/config/agents")
async def list_agent_configs():
    """List all available agent configuration files."""
    try:
        config_files = ConfigLoader.list_config_files("agents/configs")
        configs_info = []

        for config_file in config_files:
            config_info = ConfigLoader.get_config_info(str(config_file))
            if config_info:
                configs_info.append(config_info)

        return {
            "configs": configs_info,
            "total": len(configs_info)
        }

    except Exception as e:
        logger.error(f"Error listing config files: {e}")
        raise HTTPException(status_code=500, detail="Failed to list configurations")


@app.get("/config/validate/{config_name}")
async def validate_config(config_name: str):
    """Validate a specific configuration file."""
    try:
        config_path = f"agents/configs/{config_name}"
        if not config_path.endswith('.yaml'):
            config_path += '.yaml'

        is_valid, errors = ConfigLoader.validate_config_file(config_path)

        return {
            "config_name": config_name,
            "valid": is_valid,
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Error validating config: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate configuration")


# Statistics and monitoring endpoints
@app.get("/stats")
async def get_framework_stats():
    """Get framework statistics and metrics."""
    try:
        registry_status = await AgentRegistry.get_registry_status()

        # Aggregate statistics
        total_interactions = 0
        total_tools_used = 0

        for agent_info in registry_status["agents"]:
            tool_stats = agent_info.get("tool_stats", {})
            for tool_name, stats in tool_stats.items():
                total_interactions += stats.get("total_executions", 0)

        return {
            "framework": {
                "version": "1.0.0",
                "uptime": "calculated_runtime",  # Would calculate actual uptime
                "status": "operational"
            },
            "agents": {
                "total": registry_status["total_agents"],
                "running": registry_status["running_agents"],
                "types": {}  # Would aggregate by type
            },
            "interactions": {
                "total": total_interactions,
                "tools_used": total_tools_used
            }
        }

    except Exception as e:
        logger.error(f"Error getting framework stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "path": str(request.url)
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "path": str(request.url)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
