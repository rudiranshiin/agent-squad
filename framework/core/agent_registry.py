"""
Agent Registry for managing agent lifecycle and communication.
"""

from typing import Dict, Optional, List
import asyncio
import importlib
import logging
from pathlib import Path
from .agent_base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Global registry for managing agents across the framework.

    Features:
    - Agent registration and lifecycle management
    - Dynamic agent loading from configuration
    - Agent discovery and communication
    - Health monitoring
    """

    _agents: Dict[str, BaseAgent] = {}
    _running_agents: Dict[str, asyncio.Task] = {}
    _agent_configs: Dict[str, Dict] = {}

    @classmethod
    def register_agent(cls, agent: BaseAgent):
        """
        Register an agent instance.

        Args:
            agent: Agent instance to register
        """
        cls._agents[agent.name] = agent
        cls._agent_configs[agent.name] = agent.get_config()
        logger.info(f"Registered agent: {agent.name} (type: {agent.agent_type})")

    @classmethod
    def unregister_agent(cls, agent_name: str):
        """
        Unregister an agent.

        Args:
            agent_name: Name of the agent to unregister
        """
        if agent_name in cls._agents:
            del cls._agents[agent_name]

        if agent_name in cls._agent_configs:
            del cls._agent_configs[agent_name]

        if agent_name in cls._running_agents:
            task = cls._running_agents[agent_name]
            task.cancel()
            del cls._running_agents[agent_name]

        logger.info(f"Unregistered agent: {agent_name}")

    @classmethod
    def get_agent(cls, agent_name: str) -> Optional[BaseAgent]:
        """
        Get agent by name.

        Args:
            agent_name: Name of the agent

        Returns:
            Agent instance or None if not found
        """
        return cls._agents.get(agent_name)

    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all registered agent names.

        Returns:
            List of agent names
        """
        return list(cls._agents.keys())

    @classmethod
    def get_agents_by_type(cls, agent_type: str) -> List[BaseAgent]:
        """
        Get all agents of a specific type.

        Args:
            agent_type: Type of agents to retrieve

        Returns:
            List of agent instances
        """
        return [
            agent for agent in cls._agents.values()
            if agent.agent_type == agent_type
        ]

    @classmethod
    async def start_agent(cls, agent_name: str):
        """
        Start an agent.

        Args:
            agent_name: Name of the agent to start
        """
        if agent_name not in cls._agents:
            raise ValueError(f"Agent {agent_name} not found")

        if agent_name in cls._running_agents:
            logger.warning(f"Agent {agent_name} is already running")
            return

        agent = cls._agents[agent_name]

        try:
            await agent.start()

            # Create background task if needed
            task = asyncio.create_task(cls._run_agent_loop(agent))
            cls._running_agents[agent_name] = task

            logger.info(f"Started agent: {agent_name}")

        except Exception as e:
            logger.error(f"Failed to start agent {agent_name}: {e}")
            raise

    @classmethod
    async def stop_agent(cls, agent_name: str):
        """
        Stop an agent.

        Args:
            agent_name: Name of the agent to stop
        """
        if agent_name not in cls._agents:
            raise ValueError(f"Agent {agent_name} not found")

        if agent_name in cls._running_agents:
            task = cls._running_agents[agent_name]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del cls._running_agents[agent_name]

        agent = cls._agents[agent_name]
        await agent.stop()

        logger.info(f"Stopped agent: {agent_name}")

    @classmethod
    async def stop_all_agents(cls):
        """Stop all running agents."""
        agents_to_stop = list(cls._running_agents.keys())

        for agent_name in agents_to_stop:
            try:
                await cls.stop_agent(agent_name)
            except Exception as e:
                logger.error(f"Error stopping agent {agent_name}: {e}")

    @classmethod
    async def create_agent_from_config(cls, config_path: str) -> BaseAgent:
        """
        Create and register agent from configuration file.

        Args:
            config_path: Path to agent configuration file

        Returns:
            Created agent instance
        """
        try:
            from ..utils.config_loader import ConfigLoader

            # Load configuration
            config = ConfigLoader.load_agent_config(config_path)

            # Get implementation class
            implementation_path = config["implementation"]
            module_path, class_name = implementation_path.rsplit(".", 1)

            # Dynamic import
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)

            # Create agent instance
            agent = agent_class(config_path)

            # Register agent
            cls.register_agent(agent)

            logger.info(f"Created agent from config: {agent.name}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create agent from config {config_path}: {e}")
            raise

    @classmethod
    async def load_agents_from_directory(cls, directory: str, pattern: str = "*.yaml"):
        """
        Load all agent configurations from a directory.

        Args:
            directory: Directory containing agent configurations
            pattern: File pattern to match
        """
        try:
            directory_path = Path(directory)

            if not directory_path.exists():
                logger.warning(f"Agent configuration directory not found: {directory}")
                return

            config_files = list(directory_path.glob(pattern))

            for config_file in config_files:
                try:
                    await cls.create_agent_from_config(str(config_file))
                except Exception as e:
                    logger.error(f"Failed to load agent from {config_file}: {e}")

            logger.info(f"Loaded {len(config_files)} agent configurations from {directory}")

        except Exception as e:
            logger.error(f"Error loading agents from directory {directory}: {e}")

    @classmethod
    async def get_registry_status(cls) -> Dict:
        """
        Get status of all agents in the registry.

        Returns:
            Dictionary with registry status information
        """
        status = {
            "total_agents": len(cls._agents),
            "running_agents": len(cls._running_agents),
            "agents": []
        }

        for agent_name, agent in cls._agents.items():
            agent_status = await agent.get_agent_status()
            agent_status["is_running"] = agent_name in cls._running_agents
            status["agents"].append(agent_status)

        return status

    @classmethod
    async def health_check_agents(cls) -> Dict[str, bool]:
        """
        Perform health check on all agents.

        Returns:
            Dictionary mapping agent names to health status
        """
        health_status = {}

        for agent_name, agent in cls._agents.items():
            try:
                # Check if agent is responsive
                start_time = asyncio.get_event_loop().time()
                response = await agent.process_message(
                    "health check",
                    context={"internal_health_check": True}
                )
                response_time = asyncio.get_event_loop().time() - start_time

                # Agent is healthy if it responds and doesn't have errors
                is_healthy = (
                    response.get("success", True) and
                    response_time < 5.0  # Response within 5 seconds
                )

                health_status[agent_name] = is_healthy

                if not is_healthy:
                    logger.warning(f"Agent {agent_name} failed health check")

            except Exception as e:
                logger.error(f"Health check error for agent {agent_name}: {e}")
                health_status[agent_name] = False

        return health_status

    @classmethod
    async def broadcast_message(
        cls,
        message: str,
        agent_types: Optional[List[str]] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Broadcast a message to multiple agents.

        Args:
            message: Message to broadcast
            agent_types: Optional list of agent types to target
            exclude_agents: Optional list of agent names to exclude

        Returns:
            Dictionary mapping agent names to their responses
        """
        responses = {}
        exclude_agents = exclude_agents or []

        target_agents = []
        for agent_name, agent in cls._agents.items():
            if agent_name in exclude_agents:
                continue

            if agent_types and agent.agent_type not in agent_types:
                continue

            target_agents.append((agent_name, agent))

        # Send messages concurrently
        tasks = []
        for agent_name, agent in target_agents:
            task = asyncio.create_task(
                agent.process_message(
                    message,
                    context={"broadcast": True, "from": "registry"}
                )
            )
            tasks.append((agent_name, task))

        # Collect responses
        for agent_name, task in tasks:
            try:
                response = await task
                responses[agent_name] = response
            except Exception as e:
                logger.error(f"Error broadcasting to agent {agent_name}: {e}")
                responses[agent_name] = {"error": str(e), "success": False}

        logger.info(f"Broadcasted message to {len(target_agents)} agents")
        return responses

    @classmethod
    async def facilitate_collaboration(
        cls,
        initiator_name: str,
        target_name: str,
        message: str
    ) -> Dict:
        """
        Facilitate collaboration between two agents.

        Args:
            initiator_name: Name of the initiating agent
            target_name: Name of the target agent
            message: Message to facilitate collaboration

        Returns:
            Result of the collaboration
        """
        if initiator_name not in cls._agents:
            return {"error": f"Initiator agent {initiator_name} not found", "success": False}

        if target_name not in cls._agents:
            return {"error": f"Target agent {target_name} not found", "success": False}

        initiator = cls._agents[initiator_name]

        try:
            result = await initiator.collaborate_with_agent(target_name, message)
            logger.info(f"Facilitated collaboration: {initiator_name} -> {target_name}")
            return result

        except Exception as e:
            logger.error(f"Error facilitating collaboration: {e}")
            return {"error": str(e), "success": False}

    @classmethod
    def get_collaboration_graph(cls) -> Dict:
        """
        Get the collaboration graph showing which agents can collaborate.

        Returns:
            Graph structure showing collaboration relationships
        """
        graph = {
            "nodes": [],
            "edges": []
        }

        # Add nodes
        for agent_name, agent in cls._agents.items():
            graph["nodes"].append({
                "id": agent_name,
                "type": agent.agent_type,
                "running": agent_name in cls._running_agents
            })

        # Add edges based on collaboration configuration
        for agent_name, agent in cls._agents.items():
            collaboration_config = agent.config.get("collaboration", {})
            can_collaborate_with = collaboration_config.get("can_collaborate_with", [])

            for target in can_collaborate_with:
                if target in cls._agents:
                    graph["edges"].append({
                        "from": agent_name,
                        "to": target,
                        "type": collaboration_config.get("collaboration_style", "general")
                    })

        return graph

    @classmethod
    async def _run_agent_loop(cls, agent: BaseAgent):
        """
        Background loop for running an agent.

        Args:
            agent: Agent instance to run
        """
        try:
            while agent._is_running:
                # Process any queued messages
                try:
                    if not agent._message_queue.empty():
                        message_data = await asyncio.wait_for(
                            agent._message_queue.get(),
                            timeout=1.0
                        )

                        await agent.process_message(**message_data)

                except asyncio.TimeoutError:
                    pass

                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.debug(f"Agent loop cancelled for: {agent.name}")
        except Exception as e:
            logger.error(f"Error in agent loop for {agent.name}: {e}")

    @classmethod
    async def cleanup(cls):
        """Cleanup the registry and stop all agents."""
        await cls.stop_all_agents()
        cls._agents.clear()
        cls._agent_configs.clear()
        cls._running_agents.clear()
        logger.info("Agent registry cleaned up")
