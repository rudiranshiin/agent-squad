"""
Tool registry for MCP tools.
"""

from typing import Dict, List, Any, Optional, Type
import logging
from .base_tool import BaseTool, ToolExecutionResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing MCP tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def register_tool_class(self, name: str, tool_class: Type[BaseTool]) -> None:
        """Register a tool class."""
        self._tool_classes[name] = tool_class
        logger.info(f"Registered tool class: {name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def create_tool(self, name: str, **kwargs) -> Optional[BaseTool]:
        """Create a tool instance from registered class."""
        tool_class = self._tool_classes.get(name)
        if tool_class:
            return tool_class(**kwargs)
        return None

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def list_tool_classes(self) -> List[str]:
        """List all registered tool class names."""
        return list(self._tool_classes.keys())

    def remove_tool(self, name: str) -> bool:
        """Remove a tool from registry."""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Removed tool: {name}")
            return True
        return False

    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolExecutionResult(
                success=False,
                result=None,
                error=f"Tool '{name}' not found"
            )

        try:
            return await tool.execute(parameters)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            return ToolExecutionResult(
                success=False,
                result=None,
                error=str(e)
            )
