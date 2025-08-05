"""
Agentic AI Framework

A sophisticated framework for building context-engineered AI agents with MCP tool integration.
"""

__version__ = "1.0.0"
__author__ = "Agentic Framework Team"

from .core.agent_base import BaseAgent
from .core.context_engine import ContextEngine, ContextItem, ContextType
from .core.memory_manager import MemoryManager
from .core.tool_registry import ToolRegistry
from .core.agent_registry import AgentRegistry

__all__ = [
    "BaseAgent",
    "ContextEngine",
    "ContextItem",
    "ContextType",
    "MemoryManager",
    "ToolRegistry",
    "AgentRegistry"
]
