"""
Agent Module System for complete encapsulation and lifecycle management.
"""

from typing import Dict, Any, List, Optional, Type, Protocol
from abc import ABC, abstractmethod
import asyncio
import logging
import importlib
import inspect
from pathlib import Path
import shutil
import yaml
from dataclasses import dataclass
from .agent_base import BaseAgent
from .tool_registry import ToolRegistry
from ..mcp.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


@dataclass
class AgentModuleInfo:
    """Information about an agent module."""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    agent_types: List[str]
    tools: List[str]
    config_schema: Dict[str, Any]
    module_path: str
    is_active: bool = False


class AgentLifecycleHook(Protocol):
    """Protocol for agent lifecycle hooks."""

    async def on_create(self, agent: BaseAgent) -> None:
        """Called when agent is created."""
        ...

    async def on_start(self, agent: BaseAgent) -> None:
        """Called when agent starts."""
        ...

    async def on_stop(self, agent: BaseAgent) -> None:
        """Called when agent stops."""
        ...

    async def on_destroy(self, agent: BaseAgent) -> None:
        """Called when agent is destroyed."""
        ...


class AgentModule(ABC):
    """
    Base class for agent modules that provide complete encapsulation.

    An agent module contains:
    - Agent implementation(s)
    - Associated tools
    - Configuration schema
    - Dependencies
    - Lifecycle hooks
    """

    def __init__(self):
        self.info = self.get_module_info()
        self.agents: Dict[str, BaseAgent] = {}
        self.tools: Dict[str, BaseTool] = {}
        self.hooks: List[AgentLifecycleHook] = []
        self._initialized = False

    @abstractmethod
    def get_module_info(self) -> AgentModuleInfo:
        """Return module information."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the module (load tools, setup resources)."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup module resources."""
        pass

    @abstractmethod
    def get_agent_class(self, agent_type: str) -> Type[BaseAgent]:
        """Get agent class for the specified type."""
        pass

    async def create_agent(self, config: Dict[str, Any]) -> BaseAgent:
        """Create an agent instance from configuration."""
        agent_type = config.get("type")
        if agent_type not in self.info.agent_types:
            raise ValueError(f"Unsupported agent type: {agent_type}")

        agent_class = self.get_agent_class(agent_type)

        # Create temporary config file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            temp_config_path = f.name

        try:
            agent = agent_class(temp_config_path)
            self.agents[agent.name] = agent

            # Register module tools with agent
            for tool in self.tools.values():
                agent.tool_registry.register_tool(tool)

            # Call lifecycle hooks
            for hook in self.hooks:
                await hook.on_create(agent)

            logger.info(f"Created agent {agent.name} from module {self.info.name}")
            return agent

        finally:
            # Cleanup temporary file
            import os
            os.unlink(temp_config_path)

    async def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the module."""
        if agent_name not in self.agents:
            return False

        agent = self.agents[agent_name]

        # Call lifecycle hooks
        for hook in self.hooks:
            await hook.on_destroy(agent)

        # Stop agent if running
        if hasattr(agent, '_is_running') and agent._is_running:
            await agent.stop()

        del self.agents[agent_name]
        logger.info(f"Removed agent {agent_name} from module {self.info.name}")
        return True

    def register_tool(self, tool: BaseTool):
        """Register a tool with this module."""
        self.tools[tool.name] = tool

        # Add to existing agents
        for agent in self.agents.values():
            agent.tool_registry.register_tool(tool)

        logger.info(f"Registered tool {tool.name} with module {self.info.name}")

    def add_lifecycle_hook(self, hook: AgentLifecycleHook):
        """Add a lifecycle hook."""
        self.hooks.append(hook)

    async def start_all_agents(self):
        """Start all agents in this module."""
        for agent in self.agents.values():
            try:
                await agent.start()
                for hook in self.hooks:
                    await hook.on_start(agent)
            except Exception as e:
                logger.error(f"Failed to start agent {agent.name}: {e}")

    async def stop_all_agents(self):
        """Stop all agents in this module."""
        for agent in self.agents.values():
            try:
                await agent.stop()
                for hook in self.hooks:
                    await hook.on_stop(agent)
            except Exception as e:
                logger.error(f"Failed to stop agent {agent.name}: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get module status information."""
        agent_status = {}
        for name, agent in self.agents.items():
            agent_status[name] = {
                "type": agent.agent_type,
                "running": getattr(agent, '_is_running', False),
                "memory_items": len(agent.memory_manager.collection.get()["ids"]) if hasattr(agent.memory_manager, 'collection') else 0,
                "context_items": len(agent.context_engine.context_items)
            }

        return {
            "module_info": self.info.__dict__,
            "agents": agent_status,
            "tools": list(self.tools.keys()),
            "hooks": len(self.hooks),
            "initialized": self._initialized
        }


class AgentModuleManager:
    """
    Manages agent modules with dynamic loading and lifecycle management.
    """

    def __init__(self, modules_directory: str = "modules"):
        self.modules_directory = Path(modules_directory)
        self.modules_directory.mkdir(exist_ok=True)
        self.modules: Dict[str, AgentModule] = {}
        self.module_registry: Dict[str, AgentModuleInfo] = {}
        self._global_hooks: List[AgentLifecycleHook] = []

    async def load_module(self, module_path: str) -> AgentModule:
        """Load an agent module from path."""
        try:
            # Import module
            spec = importlib.util.spec_from_file_location("agent_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find AgentModule class
            module_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    issubclass(obj, AgentModule) and
                    obj != AgentModule):
                    module_class = obj
                    break

            if not module_class:
                raise ValueError("No AgentModule class found in module")

            # Create and initialize module
            agent_module = module_class()
            await agent_module.initialize()
            agent_module._initialized = True

            # Add global hooks
            for hook in self._global_hooks:
                agent_module.add_lifecycle_hook(hook)

            self.modules[agent_module.info.name] = agent_module
            self.module_registry[agent_module.info.name] = agent_module.info

            logger.info(f"Loaded module: {agent_module.info.name} v{agent_module.info.version}")
            return agent_module

        except Exception as e:
            logger.error(f"Failed to load module from {module_path}: {e}")
            raise

    async def unload_module(self, module_name: str) -> bool:
        """Unload an agent module."""
        if module_name not in self.modules:
            return False

        module = self.modules[module_name]

        try:
            # Stop all agents
            await module.stop_all_agents()

            # Remove all agents
            agent_names = list(module.agents.keys())
            for agent_name in agent_names:
                await module.remove_agent(agent_name)

            # Cleanup module
            await module.cleanup()

            del self.modules[module_name]
            del self.module_registry[module_name]

            logger.info(f"Unloaded module: {module_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload module {module_name}: {e}")
            return False

    async def reload_module(self, module_name: str) -> bool:
        """Reload an agent module."""
        if module_name not in self.modules:
            return False

        module_path = self.modules[module_name].info.module_path

        # Unload and reload
        if await self.unload_module(module_name):
            try:
                await self.load_module(module_path)
                return True
            except Exception:
                return False

        return False

    async def create_agent(self, module_name: str, config: Dict[str, Any]) -> BaseAgent:
        """Create an agent using a specific module."""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not found")

        module = self.modules[module_name]
        return await module.create_agent(config)

    async def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from any module."""
        for module in self.modules.values():
            if agent_name in module.agents:
                return await module.remove_agent(agent_name)
        return False

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent by name from any module."""
        for module in self.modules.values():
            if agent_name in module.agents:
                return module.agents[agent_name]
        return None

    def list_modules(self) -> List[str]:
        """List all loaded modules."""
        return list(self.modules.keys())

    def list_agents(self) -> List[str]:
        """List all agents across all modules."""
        agents = []
        for module in self.modules.values():
            agents.extend(module.agents.keys())
        return agents

    def get_module_status(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific module."""
        if module_name not in self.modules:
            return None
        return self.modules[module_name].get_status()

    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all modules."""
        return {
            "modules": {name: module.get_status() for name, module in self.modules.items()},
            "total_agents": len(self.list_agents()),
            "total_modules": len(self.modules)
        }

    async def install_module_from_template(
        self,
        template_name: str,
        module_name: str,
        config: Dict[str, Any]
    ) -> str:
        """Install a new module from a template."""
        template_path = Path(__file__).parent.parent.parent / "templates" / f"{template_name}_module.py"

        if not template_path.exists():
            raise ValueError(f"Template {template_name} not found")

        # Create module directory
        module_dir = self.modules_directory / module_name
        module_dir.mkdir(exist_ok=True)

        # Copy and customize template
        module_file = module_dir / "module.py"
        with open(template_path, 'r') as src, open(module_file, 'w') as dst:
            template_content = src.read()

            # Replace template variables
            customized_content = template_content.format(
                module_name=module_name,
                **config
            )
            dst.write(customized_content)

        # Create module config
        config_file = module_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f)

        logger.info(f"Installed module {module_name} from template {template_name}")
        return str(module_file)

    async def uninstall_module(self, module_name: str) -> bool:
        """Completely uninstall a module."""
        # Unload if loaded
        if module_name in self.modules:
            await self.unload_module(module_name)

        # Remove module directory
        module_dir = self.modules_directory / module_name
        if module_dir.exists():
            shutil.rmtree(module_dir)
            logger.info(f"Uninstalled module {module_name}")
            return True

        return False

    def add_global_hook(self, hook: AgentLifecycleHook):
        """Add a global lifecycle hook that applies to all modules."""
        self._global_hooks.append(hook)

        # Add to existing modules
        for module in self.modules.values():
            module.add_lifecycle_hook(hook)

    async def discover_and_load_modules(self):
        """Discover and load all modules in the modules directory."""
        for module_dir in self.modules_directory.iterdir():
            if module_dir.is_dir():
                module_file = module_dir / "module.py"
                if module_file.exists():
                    try:
                        await self.load_module(str(module_file))
                    except Exception as e:
                        logger.error(f"Failed to load module {module_dir.name}: {e}")


# Global module manager instance
global_module_manager = AgentModuleManager()


class ScalabilityOptimizer:
    """
    Optimizes framework for scalability with connection pooling,
    resource management, and performance monitoring.
    """

    def __init__(self):
        self.connection_pools: Dict[str, Any] = {}
        self.resource_limits: Dict[str, int] = {
            "max_agents_per_module": 10,
            "max_context_items_per_agent": 100,
            "max_memory_items_per_agent": 1000,
            "max_concurrent_tool_executions": 50
        }
        self.performance_metrics: Dict[str, Any] = {
            "agent_creation_time": [],
            "message_processing_time": [],
            "memory_usage": [],
            "tool_execution_time": []
        }

    async def optimize_agent_performance(self, agent: BaseAgent):
        """Apply performance optimizations to an agent."""
        # Optimize context engine
        if len(agent.context_engine.context_items) > self.resource_limits["max_context_items_per_agent"]:
            agent.context_engine._optimize_context()

        # Optimize memory manager
        if hasattr(agent.memory_manager, 'collection'):
            memory_count = len(agent.memory_manager.collection.get()["ids"])
            if memory_count > self.resource_limits["max_memory_items_per_agent"]:
                await agent.memory_manager.cleanup_old_memories(
                    keep_count=self.resource_limits["max_memory_items_per_agent"] // 2
                )

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {
            "resource_limits": self.resource_limits,
            "connection_pools": {name: len(pool) for name, pool in self.connection_pools.items()},
            "performance_metrics": {}
        }

        for metric_name, values in self.performance_metrics.items():
            if values:
                report["performance_metrics"][metric_name] = {
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }

        return report


# Global scalability optimizer
global_optimizer = ScalabilityOptimizer()
