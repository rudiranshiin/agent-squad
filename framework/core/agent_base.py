"""
Base Agent class for all agent implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import asyncio
import logging
import time
from .context_engine import ContextEngine
from .memory_manager import MemoryManager
from .tool_registry import ToolRegistry
from .llm_client import get_llm_client, LLMMessage, LLMResponse
from ..utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the framework.

    Features:
    - Context engineering with intelligent management
    - Memory system with semantic search
    - Tool integration and execution
    - Inter-agent communication
    - Configuration-driven setup
    """

    def __init__(self, config_path: str):
        self.config = ConfigLoader.load_agent_config(config_path)
        self.name = self.config["name"]
        self.agent_type = self.config["type"]
        self.personality = self.config.get("personality", {})

        # Initialize core components
        self.context_engine = ContextEngine(
            max_context_length=self.config.get("max_context_length", 4000),
            max_items=self.config.get("max_context_items", 100)
        )

        self.memory_manager = MemoryManager(
            agent_name=self.name,
            max_memories=self.config.get("max_memories", 1000)
        )

        self.tool_registry = ToolRegistry()

        # Initialize LLM client
        llm_config = self.config.get("llm_config", {})
        self.llm_client = get_llm_client(llm_config)

        # Agent state
        self._is_running = False
        self._message_queue = asyncio.Queue()
        self._collaboration_sessions: Dict[str, Dict[str, Any]] = {}

        # Load agent-specific context and tools
        self._load_system_context()
        self._load_tools()

        logger.info(f"Initialized agent: {self.name} (type: {self.agent_type})")

    def _load_system_context(self):
        """Load system context from configuration."""
        system_prompt = self.config.get("system_prompt", "")
        personality_context = self._build_personality_context()

        full_system_context = f"{system_prompt}\n\nPersonality: {personality_context}"

        self.context_engine.add_system_context(
            full_system_context,
            metadata={"source": "config", "agent_name": self.name}
        )

        # Add agent capabilities context
        capabilities = self._get_agent_capabilities()
        if capabilities:
            self.context_engine.add_system_context(
                f"Agent Capabilities: {capabilities}",
                metadata={"source": "capabilities"}
            )

    def _build_personality_context(self) -> str:
        """Build personality context from configuration."""
        if not self.personality:
            return "Professional and helpful AI assistant"

        traits = []
        for key, value in self.personality.items():
            traits.append(f"{key}: {value}")
        return ", ".join(traits)

    def _get_agent_capabilities(self) -> str:
        """Get description of agent capabilities."""
        capabilities = []

        # Tool capabilities
        if self.tool_registry.list_tools():
            tool_names = ", ".join(self.tool_registry.list_tools())
            capabilities.append(f"Available tools: {tool_names}")

        # Memory capabilities
        if self.config.get("memory_config", {}).get("remember_conversations", False):
            capabilities.append("Long-term conversation memory")

        # Collaboration capabilities
        collaboration_config = self.config.get("collaboration", {})
        if collaboration_config.get("can_collaborate_with"):
            partners = ", ".join(collaboration_config["can_collaborate_with"])
            capabilities.append(f"Can collaborate with: {partners}")

        return "; ".join(capabilities)

    def _load_tools(self):
        """Load tools specified in configuration."""
        tool_configs = self.config.get("tools", [])

        for tool_config in tool_configs:
            try:
                self.tool_registry.register_tool_from_config(tool_config)
                logger.debug(f"Loaded tool: {tool_config.get('name', 'unnamed')}")
            except Exception as e:
                logger.error(f"Failed to load tool {tool_config}: {e}")

    async def process_message(
        self,
        message: str,
        context: Dict[str, Any] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Main message processing pipeline.

        Args:
            message: User message to process
            context: Additional context information
            user_id: Identifier for the user (for personalization)

        Returns:
            Agent response with metadata
        """
        start_time = time.time()
        context = context or {}

        try:
            # Add user context
            self.context_engine.add_user_context(
                message,
                metadata={
                    "user_id": user_id,
                    "timestamp": start_time,
                    **context
                }
            )

            # Retrieve relevant memories
            memories = await self.memory_manager.retrieve_relevant_memories(
                message,
                max_results=self.config.get("memory_config", {}).get("context_window", 5),
                user_id=user_id
            )

            for memory in memories:
                self.context_engine.add_memory_context(
                    memory.content,
                    relevance_score=memory.relevance_score,
                    metadata={"memory_id": memory.id}
                )

            # Pre-process with agent-specific logic
            await self.pre_process(message, context)

            # Generate response
            response = await self.generate_response(message, context)

            # Post-process
            final_response = await self.post_process(response, message, context)

            # Store interaction in memory
            if self.config.get("memory_config", {}).get("remember_conversations", True):
                await self.memory_manager.store_interaction(message, final_response, user_id=user_id)

            # Add processing metadata
            final_response["processing_time"] = time.time() - start_time
            final_response["agent_name"] = self.name
            final_response["agent_type"] = self.agent_type
            final_response["context_summary"] = self.context_engine.get_context_summary()

            logger.debug(f"Processed message for {self.name} in {final_response['processing_time']:.2f}s")

            return final_response

        except Exception as e:
            logger.error(f"Error processing message for {self.name}: {e}", exc_info=True)

            error_response = {
                "response": "I apologize, but I encountered an error processing your message. Please try again.",
                "error": str(e),
                "agent_name": self.name,
                "processing_time": time.time() - start_time,
                "success": False
            }

            return error_response

    async def pre_process(self, message: str, context: Dict[str, Any]):
        """
        Pre-processing hook for agent-specific logic.

        Override in subclasses to add custom pre-processing steps.
        """
        pass

    @abstractmethod
    async def generate_response(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the main response - must be implemented by subclasses.

        Args:
            message: User message
            context: Additional context

        Returns:
            Response dictionary with at least 'response' key
        """
        pass

    async def post_process(
        self,
        response: Dict[str, Any],
        original_message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-processing hook for response modification.

        Override in subclasses to add custom post-processing steps.
        """
        return response

    async def generate_llm_response(
        self,
        prompt: str,
        system_message: str = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: str = None
    ) -> str:
        """
        Generate response using LLM client.

        Args:
            prompt: User prompt/message
            system_message: Optional system message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            provider: Specific LLM provider to use

        Returns:
            Generated response text
        """
        try:
            messages = []

            # Add system message if provided
            if system_message:
                messages.append(LLMMessage(role="system", content=system_message))

            # Add user prompt
            messages.append(LLMMessage(role="user", content=prompt))

            # Generate response using LLM client
            response = await self.llm_client.generate_response(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                provider=provider
            )

            # Add LLM usage to context
            self.context_engine.add_tool_context(
                f"LLM response generated using {response.metadata.get('provider', 'unknown')}",
                tool_name="llm_client",
                metadata={
                    "provider": response.metadata.get('provider'),
                    "model": response.model,
                    "tokens_used": response.tokens_used,
                    "temperature": temperature
                }
            )

            logger.debug(f"Generated LLM response: {len(response.content)} chars, {response.tokens_used} tokens")
            return response.content

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise

    async def use_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a tool and add results to context.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            result = await self.tool_registry.execute_tool(tool_name, parameters)

            # Add tool execution to context
            if result.success:
                self.context_engine.add_tool_context(
                    f"Tool {tool_name} executed successfully. Result: {result.data}",
                    tool_name=tool_name,
                    metadata={
                        "execution_time": result.execution_time,
                        "parameters": parameters
                    }
                )
            else:
                self.context_engine.add_tool_context(
                    f"Tool {tool_name} failed: {result.error}",
                    tool_name=tool_name,
                    metadata={
                        "execution_time": result.execution_time,
                        "parameters": parameters,
                        "error": True
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {e}")
            self.context_engine.add_tool_context(
                f"Tool {tool_name} error: {str(e)}",
                tool_name=tool_name,
                metadata={"error": True, "exception": str(e)}
            )
            raise

    async def collaborate_with_agent(
        self,
        agent_name: str,
        message: str,
        collaboration_type: str = "request"
    ) -> Dict[str, Any]:
        """
        Collaborate with another agent.

        Args:
            agent_name: Name of the agent to collaborate with
            message: Message to send to the other agent
            collaboration_type: Type of collaboration (request, share, etc.)

        Returns:
            Response from the other agent
        """
        from .agent_registry import AgentRegistry

        try:
            other_agent = AgentRegistry.get_agent(agent_name)
            if not other_agent:
                error_msg = f"Agent {agent_name} not found for collaboration"
                logger.warning(error_msg)
                return {"error": error_msg, "success": False}

            # Check if collaboration is allowed
            allowed_collaborators = self.config.get("collaboration", {}).get("can_collaborate_with", [])
            if allowed_collaborators and agent_name not in allowed_collaborators:
                error_msg = f"Collaboration with {agent_name} not allowed"
                logger.warning(error_msg)
                return {"error": error_msg, "success": False}

            # Create collaboration session
            collaboration_id = f"{self.name}-{agent_name}-{int(time.time())}"
            self._collaboration_sessions[collaboration_id] = {
                "partner": agent_name,
                "type": collaboration_type,
                "started_at": time.time(),
                "messages": []
            }

            # Add collaboration context
            self.context_engine.add_collaboration_context(
                f"Collaborating with {agent_name}: {message}",
                collaboration_id=collaboration_id,
                metadata={
                    "partner": agent_name,
                    "type": collaboration_type,
                    "direction": "outgoing"
                }
            )

            # Send message to other agent
            response = await other_agent.process_message(
                message,
                context={
                    "collaboration_from": self.name,
                    "collaboration_id": collaboration_id,
                    "collaboration_type": collaboration_type
                }
            )

            # Record collaboration
            self._collaboration_sessions[collaboration_id]["messages"].extend([
                {"from": self.name, "message": message, "timestamp": time.time()},
                {"from": agent_name, "message": response.get("response", ""), "timestamp": time.time()}
            ])

            # Add response to context
            self.context_engine.add_collaboration_context(
                f"Response from {agent_name}: {response.get('response', '')}",
                collaboration_id=collaboration_id,
                metadata={
                    "partner": agent_name,
                    "type": collaboration_type,
                    "direction": "incoming"
                }
            )

            logger.info(f"Collaboration between {self.name} and {agent_name} completed")
            return response

        except Exception as e:
            logger.error(f"Collaboration error between {self.name} and {agent_name}: {e}")
            return {"error": str(e), "success": False}

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        return {
            "name": self.name,
            "type": self.agent_type,
            "is_running": self._is_running,
            "context_summary": self.context_engine.get_context_summary(),
            "memory_stats": await self.memory_manager.get_memory_stats(),
            "tool_stats": self.tool_registry.get_execution_statistics(),
            "active_collaborations": len(self._collaboration_sessions),
            "configuration": {
                "max_context_length": self.context_engine.max_context_length,
                "max_memories": self.memory_manager.max_memories,
                "available_tools": self.tool_registry.list_tools()
            }
        }

    async def reset_agent_state(self):
        """Reset agent state (clear context, reset statistics)."""
        self.context_engine.clear_all_context()
        self.tool_registry.reset_statistics()
        self._collaboration_sessions.clear()

        # Reload system context
        self._load_system_context()

        logger.info(f"Reset state for agent: {self.name}")

    async def update_configuration(self, new_config: Dict[str, Any]):
        """Update agent configuration dynamically."""
        # Update personality if provided
        if "personality" in new_config:
            self.personality.update(new_config["personality"])

        # Update context limits
        if "max_context_length" in new_config:
            self.context_engine.max_context_length = new_config["max_context_length"]

        # Update memory config
        if "memory_config" in new_config:
            self.config["memory_config"].update(new_config["memory_config"])

        # Reload system context with new personality
        self.context_engine.clear_context_type(self.context_engine.ContextType.SYSTEM)
        self._load_system_context()

        logger.info(f"Updated configuration for agent: {self.name}")

    async def start(self):
        """Start the agent (for background processing)."""
        if self._is_running:
            return

        self._is_running = True
        logger.info(f"Started agent: {self.name}")

        # Start background tasks if needed
        await self._start_background_tasks()

    async def stop(self):
        """Stop the agent and cleanup resources."""
        if not self._is_running:
            return

        self._is_running = False

        # Cleanup resources
        await self.tool_registry.cleanup_tools()

        logger.info(f"Stopped agent: {self.name}")

    async def _start_background_tasks(self):
        """Start background tasks (override in subclasses if needed)."""
        pass

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration."""
        return self.config.copy()

    def __str__(self) -> str:
        return f"Agent({self.name}, type={self.agent_type})"

    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', type='{self.agent_type}', running={self._is_running})"
