"""
Enhanced FastAPI application for the Agentic AI Framework with module support.
"""

import asyncio
import logging
import tempfile
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from framework.core.agent_registry import AgentRegistry
from framework.core.agent_module import global_module_manager, global_optimizer
from framework.utils.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Agentic AI Framework API",
    description="Enhanced API for managing AI agents with modular architecture",
    version="2.0.0",
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


# Pydantic models
class MessageRequest(BaseModel):
    text: str = Field(..., description="Message text to send to the agent")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context")
    user_id: Optional[str] = Field(default=None, description="User identifier")


class CollaborationRequest(BaseModel):
    message: str = Field(..., description="Message for collaboration")
    collaboration_type: Optional[str] = Field(default="request", description="Type of collaboration")


class BroadcastRequest(BaseModel):
    message: str = Field(..., description="Message to broadcast")
    exclude_agents: Optional[List[str]] = Field(default=None, description="Agents to exclude from broadcast")


class AgentConfigRequest(BaseModel):
    config: Dict[str, Any] = Field(..., description="Agent configuration")


class ModuleConfigRequest(BaseModel):
    template_name: str = Field(..., description="Template name for module creation")
    module_name: str = Field(..., description="Name for the new module")
    config: Dict[str, Any] = Field(..., description="Module configuration")


class AgentCreateRequest(BaseModel):
    module_name: str = Field(..., description="Module to use for agent creation")
    config: Dict[str, Any] = Field(..., description="Agent configuration")


# Health and status endpoints
@app.get("/health")
async def health_check():
    """Framework health check endpoint."""
    try:
        module_status = global_module_manager.get_all_status()
        performance_report = global_optimizer.get_performance_report()

        return {
            "status": "healthy",
            "version": "2.0.0",
            "modules": module_status,
            "performance": performance_report,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/status")
async def get_framework_status():
    """Get detailed framework status."""
    return {
        "agents": {name: AgentRegistry.get_agent(name).get_status() if AgentRegistry.get_agent(name) else None
                  for name in AgentRegistry.list_agents()},
        "modules": global_module_manager.get_all_status(),
        "performance": global_optimizer.get_performance_report()
    }


# Module management endpoints
@app.get("/modules")
async def list_modules():
    """List all loaded modules."""
    return {
        "modules": global_module_manager.list_modules(),
        "status": global_module_manager.get_all_status()
    }


@app.get("/modules/{module_name}")
async def get_module_status(module_name: str):
    """Get status of a specific module."""
    status = global_module_manager.get_module_status(module_name)
    if not status:
        raise HTTPException(status_code=404, detail="Module not found")
    return status


@app.post("/modules/install")
async def install_module(request: ModuleConfigRequest):
    """Install a new module from template."""
    try:
        module_path = await global_module_manager.install_module_from_template(
            request.template_name,
            request.module_name,
            request.config
        )

        # Load the module
        await global_module_manager.load_module(module_path)

        return {
            "message": f"Module {request.module_name} installed successfully",
            "module_name": request.module_name,
            "module_path": module_path,
            "status": global_module_manager.get_module_status(request.module_name)
        }
    except Exception as e:
        logger.error(f"Error installing module: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/modules/{module_name}/load")
async def load_module(module_name: str, module_path: str):
    """Load a module from path."""
    try:
        module = await global_module_manager.load_module(module_path)
        return {
            "message": f"Module {module_name} loaded successfully",
            "module_info": module.info.__dict__
        }
    except Exception as e:
        logger.error(f"Error loading module: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/modules/{module_name}/unload")
async def unload_module(module_name: str):
    """Unload a module."""
    success = await global_module_manager.unload_module(module_name)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": f"Module {module_name} unloaded successfully"}


@app.post("/modules/{module_name}/reload")
async def reload_module(module_name: str):
    """Reload a module."""
    success = await global_module_manager.reload_module(module_name)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found or reload failed")

    return {"message": f"Module {module_name} reloaded successfully"}


@app.delete("/modules/{module_name}")
async def uninstall_module(module_name: str):
    """Completely uninstall a module."""
    success = await global_module_manager.uninstall_module(module_name)
    if not success:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": f"Module {module_name} uninstalled successfully"}


# Enhanced agent management endpoints
@app.get("/agents")
async def list_agents():
    """List all available agents across all modules."""
    agents_info = {}

    for agent_name in global_module_manager.list_agents():
        agent = global_module_manager.get_agent(agent_name)
        if agent:
            agents_info[agent_name] = {
                "name": agent.name,
                "type": agent.agent_type,
                "status": "running" if getattr(agent, '_is_running', False) else "stopped",
                "module": None  # Find which module this agent belongs to
            }

            # Find the module
            for module_name, module in global_module_manager.modules.items():
                if agent_name in module.agents:
                    agents_info[agent_name]["module"] = module_name
                    break

    return {"agents": agents_info}


@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get detailed information about a specific agent."""
    agent = global_module_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "name": agent.name,
        "type": agent.agent_type,
        "personality": agent.personality,
        "status": "running" if getattr(agent, '_is_running', False) else "stopped",
        "context_summary": agent.context_engine.get_context_summary(),

        "tools": agent.tool_registry.list_tools()
    }


@app.post("/agents/create")
async def create_agent(request: AgentCreateRequest):
    """Create a new agent using a module."""
    try:
        agent = await global_module_manager.create_agent(
            request.module_name,
            request.config
        )

        # Apply performance optimizations
        await global_optimizer.optimize_agent_performance(agent)

        return {
            "message": f"Agent {agent.name} created successfully",
            "agent_name": agent.name,
            "agent_type": agent.agent_type,
            "module": request.module_name
        }
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/agents/{agent_name}/message")
async def send_message_to_agent(agent_name: str, request: MessageRequest):
    """Send a message to a specific agent."""
    agent = global_module_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        # Apply performance optimizations before processing
        await global_optimizer.optimize_agent_performance(agent)

        response = await agent.process_message(
            request.text,
            request.context,
            request.user_id
        )

        return response
    except Exception as e:
        logger.error(f"Error processing message for {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/start")
async def start_agent(agent_name: str):
    """Start an agent."""
    agent = global_module_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        await agent.start()
        return {"message": f"Agent {agent_name} started successfully"}
    except Exception as e:
        logger.error(f"Error starting agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/stop")
async def stop_agent(agent_name: str):
    """Stop an agent."""
    agent = global_module_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        await agent.stop()
        return {"message": f"Agent {agent_name} stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping agent {agent_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/agents/{agent_name}")
async def remove_agent(agent_name: str):
    """Remove an agent."""
    success = await global_module_manager.remove_agent(agent_name)
    if not success:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {"message": f"Agent {agent_name} removed successfully"}


# Agent collaboration endpoints
@app.post("/agents/{agent1}/collaborate/{agent2}")
async def agent_collaboration(agent1: str, agent2: str, request: CollaborationRequest):
    """Enable collaboration between two agents."""
    agent_1 = global_module_manager.get_agent(agent1)
    agent_2 = global_module_manager.get_agent(agent2)

    if not agent_1:
        raise HTTPException(status_code=404, detail=f"Agent {agent1} not found")
    if not agent_2:
        raise HTTPException(status_code=404, detail=f"Agent {agent2} not found")

    try:
        response = await agent_1.collaborate_with_agent(agent2, request.message)
        return response
    except Exception as e:
        logger.error(f"Error in collaboration between {agent1} and {agent2}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/collaboration/graph")
async def get_collaboration_graph():
    """Get the agent collaboration graph."""
    try:
        # Build collaboration graph
        agents = {}
        for agent_name in global_module_manager.list_agents():
            agent = global_module_manager.get_agent(agent_name)
            if agent:
                collaboration_config = agent.config.get("collaboration", {})
                agents[agent_name] = {
                    "type": agent.agent_type,
                    "can_collaborate_with": collaboration_config.get("can_collaborate_with", []),
                    "collaboration_style": collaboration_config.get("collaboration_style", "helpful")
                }

        return {"collaboration_graph": agents}
    except Exception as e:
        logger.error(f"Error generating collaboration graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Broadcast a message to multiple agents."""
    try:
        responses = {}
        exclude_set = set(request.exclude_agents or [])

        for agent_name in global_module_manager.list_agents():
            if agent_name not in exclude_set:
                agent = global_module_manager.get_agent(agent_name)
                if agent:
                    try:
                        response = await agent.process_message(request.message)
                        responses[agent_name] = response
                    except Exception as e:
                        responses[agent_name] = {"error": str(e)}

        return {
            "message": "Broadcast completed",
            "responses": responses,
            "total_agents": len(responses)
        }
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail="Failed to broadcast message")


# Performance and monitoring endpoints
@app.get("/performance")
async def get_performance_metrics():
    """Get framework performance metrics."""
    return global_optimizer.get_performance_report()


@app.post("/performance/optimize")
async def optimize_all_agents():
    """Optimize performance for all agents."""
    optimized_count = 0

    for agent_name in global_module_manager.list_agents():
        agent = global_module_manager.get_agent(agent_name)
        if agent:
            await global_optimizer.optimize_agent_performance(agent)
            optimized_count += 1

    return {
        "message": f"Optimized {optimized_count} agents",
        "performance_report": global_optimizer.get_performance_report()
    }


# Configuration endpoints
@app.get("/config/agents")
async def list_agent_configs():
    """List all available agent configuration files."""
    try:
        config_dir = Path("agents/configs")
        configs = []

        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)

                    configs.append({
                        "file": str(config_file),
                        "name": config.get("name", "Unknown"),
                        "type": config.get("type", "Unknown"),
                        "valid": True
                    })
                except Exception as e:
                    configs.append({
                        "file": str(config_file),
                        "name": "Error",
                        "type": "Error",
                        "valid": False,
                        "error": str(e)
                    })

        return {"configs": configs}
    except Exception as e:
        logger.error(f"Error listing config files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/validate")
async def validate_config(request: AgentConfigRequest):
    """Validate an agent configuration."""
    try:
        config = request.config

        # Basic validation
        required_fields = ["name", "type"]
        errors = []

        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        if errors:
            return {"valid": False, "errors": errors}

        return {"valid": True, "message": "Configuration is valid"}
    except Exception as e:
        logger.error(f"Error validating config: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Enhanced startup with module discovery."""
    logger.info("Starting Enhanced Agentic AI Framework...")

    try:
        # Load server configuration
        try:
            server_config = ConfigLoader.load_server_config()
        except Exception:
            # Use default config if none exists
            server_config = {"agents": {"auto_load": True, "config_directory": "agents/configs"}}

        # Discover and load modules
        await global_module_manager.discover_and_load_modules()

        # Auto-load agents if configured
        if server_config.get("agents", {}).get("auto_load", True):
            config_dir = server_config.get("agents", {}).get("config_directory", "agents/configs")
            config_path = Path(config_dir)

            if config_path.exists():
                for config_file in config_path.glob("*.yaml"):
                    try:
                        # Try to load using legacy method for existing configs
                        agent = await AgentRegistry.create_agent_from_config(str(config_file))
                        logger.info(f"Loaded legacy agent: {agent.name}")
                    except Exception as e:
                        logger.warning(f"Failed to load agent from {config_file}: {e}")

        total_agents = len(global_module_manager.list_agents())
        total_modules = len(global_module_manager.list_modules())

        logger.info(f"Framework started successfully with {total_modules} modules and {total_agents} agents")

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Enhanced cleanup on shutdown."""
    logger.info("Shutting down Enhanced Agentic AI Framework...")

    try:
        # Stop all agents in all modules
        for module in global_module_manager.modules.values():
            await module.stop_all_agents()

        # Unload all modules
        module_names = list(global_module_manager.modules.keys())
        for module_name in module_names:
            await global_module_manager.unload_module(module_name)

        logger.info("Framework shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
