"""
Tool Registry for managing and executing tools across the framework.
"""

from typing import Dict, Any, List, Optional, Type
import importlib
import logging
from framework.mcp.tools.base_tool import BaseTool, ToolExecutionResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for managing tools across the framework.

    Features:
    - Dynamic tool loading from configuration
    - Tool sharing across agents
    - Tool health monitoring
    - Execution statistics
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, tool: BaseTool):
        """Register a tool instance."""
        self.tools[tool.name] = tool
        self._execution_stats[tool.name] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "last_execution": None
        }
        logger.info(f"Registered tool: {tool.name}")

    def register_tool_class(self, tool_class: Type[BaseTool], class_name: str = None):
        """Register a tool class for dynamic instantiation."""
        name = class_name or tool_class.__name__
        self._tool_classes[name] = tool_class
        logger.debug(f"Registered tool class: {name}")

    def register_tool_from_config(self, tool_config: Dict[str, Any]):
        """Register tool from configuration."""
        try:
            tool_class_path = tool_config["class"]
            tool_params = tool_config.get("parameters", {})
            tool_name = tool_config.get("name")

            # Dynamic import
            module_path, class_name = tool_class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)

            # Instantiate tool
            tool_instance = tool_class(**tool_params)

            # Use configured name if provided
            if tool_name:
                tool_instance.name = tool_name

            self.register_tool(tool_instance)

        except Exception as e:
            logger.error(f"Failed to register tool from config: {e}", exc_info=True)
            raise

    def create_tool_from_class(self, class_name: str, **parameters) -> BaseTool:
        """Create tool instance from registered class."""
        if class_name not in self._tool_classes:
            raise ValueError(f"Tool class {class_name} not registered")

        tool_class = self._tool_classes[class_name]
        return tool_class(**parameters)

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool by name."""
        if tool_name not in self.tools:
            return ToolExecutionResult(
                success=False,
                data=None,
                error=f"Tool {tool_name} not found"
            )

        tool = self.tools[tool_name]

        try:
            result = await tool.execute_with_validation(**parameters)

            # Update execution statistics
            stats = self._execution_stats[tool_name]
            stats["total_executions"] += 1
            stats["total_execution_time"] += result.execution_time
            stats["last_execution"] = {
                "timestamp": result.metadata.get("timestamp"),
                "success": result.success,
                "execution_time": result.execution_time
            }

            if result.success:
                stats["successful_executions"] += 1
            else:
                stats["failed_executions"] += 1

            return result

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)

            # Update failure statistics
            stats = self._execution_stats[tool_name]
            stats["total_executions"] += 1
            stats["failed_executions"] += 1

            return ToolExecutionResult(
                success=False,
                data=None,
                error=f"Tool execution error: {str(e)}"
            )

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool instance by name."""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List available tools."""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information."""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        stats = self._execution_stats.get(tool_name, {})

        info = tool.get_info()
        info["registry_statistics"] = stats

        return info

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category (based on class hierarchy or metadata)."""
        matching_tools = []

        for tool in self.tools.values():
            # Check if tool has category metadata
            if hasattr(tool, 'category') and tool.category == category:
                matching_tools.append(tool)
            # Check class name for category hints
            elif category.lower() in tool.__class__.__name__.lower():
                matching_tools.append(tool)

        return matching_tools

    async def health_check_tools(self) -> Dict[str, bool]:
        """Perform health check on all tools."""
        health_status = {}

        for tool_name, tool in self.tools.items():
            try:
                is_healthy = await tool.health_check()
                health_status[tool_name] = is_healthy

                if not is_healthy:
                    logger.warning(f"Tool {tool_name} failed health check")

            except Exception as e:
                logger.error(f"Health check error for tool {tool_name}: {e}")
                health_status[tool_name] = False

        return health_status

    def get_execution_statistics(self, tool_name: str = None) -> Dict[str, Any]:
        """Get execution statistics for a specific tool or all tools."""
        if tool_name:
            return self._execution_stats.get(tool_name, {})
        else:
            return self._execution_stats.copy()

    def reset_statistics(self, tool_name: str = None):
        """Reset execution statistics."""
        if tool_name:
            if tool_name in self._execution_stats:
                self._execution_stats[tool_name] = {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "total_execution_time": 0.0,
                    "last_execution": None
                }

                # Also reset tool's internal statistics
                if tool_name in self.tools:
                    self.tools[tool_name].reset_statistics()

                logger.info(f"Reset statistics for tool: {tool_name}")
        else:
            # Reset all statistics
            for tool_name in self._execution_stats:
                self.reset_statistics(tool_name)
            logger.info("Reset statistics for all tools")

    def unregister_tool(self, tool_name: str):
        """Unregister a tool."""
        if tool_name in self.tools:
            del self.tools[tool_name]

        if tool_name in self._execution_stats:
            del self._execution_stats[tool_name]

        logger.info(f"Unregistered tool: {tool_name}")

    async def cleanup_tools(self):
        """Cleanup all tools (useful for async tools)."""
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                try:
                    await tool.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up tool {tool.name}: {e}")

        logger.info("Cleaned up all tools")

    def get_tools_summary(self) -> Dict[str, Any]:
        """Get summary of all tools and their status."""
        summary = {
            "total_tools": len(self.tools),
            "tool_categories": {},
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "tools": []
        }

        for tool_name, tool in self.tools.items():
            stats = self._execution_stats.get(tool_name, {})

            # Aggregate statistics
            summary["total_executions"] += stats.get("total_executions", 0)
            summary["successful_executions"] += stats.get("successful_executions", 0)
            summary["failed_executions"] += stats.get("failed_executions", 0)

            # Categorize tools
            tool_category = getattr(tool, 'category', 'general')
            if tool_category not in summary["tool_categories"]:
                summary["tool_categories"][tool_category] = 0
            summary["tool_categories"][tool_category] += 1

            # Tool details
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "version": tool.version,
                "category": tool_category,
                "statistics": stats
            }
            summary["tools"].append(tool_info)

        return summary

    def search_tools(self, query: str) -> List[BaseTool]:
        """Search tools by name or description."""
        query_lower = query.lower()
        matching_tools = []

        for tool in self.tools.values():
            if (query_lower in tool.name.lower() or
                query_lower in tool.description.lower()):
                matching_tools.append(tool)

        return matching_tools

    def validate_tool_config(self, tool_config: Dict[str, Any]) -> List[str]:
        """Validate tool configuration."""
        errors = []

        required_fields = ["class"]
        for field in required_fields:
            if field not in tool_config:
                errors.append(f"Missing required field: {field}")

        # Validate class path
        if "class" in tool_config:
            try:
                class_path = tool_config["class"]
                if "." not in class_path:
                    errors.append("Class path must include module name")
                else:
                    module_path, class_name = class_path.rsplit(".", 1)
                    # Try to import to validate
                    try:
                        module = importlib.import_module(module_path)
                        if not hasattr(module, class_name):
                            errors.append(f"Class {class_name} not found in module {module_path}")
                    except ImportError as e:
                        errors.append(f"Cannot import module {module_path}: {e}")
            except Exception as e:
                errors.append(f"Invalid class path: {e}")

        return errors

    def export_configuration(self) -> List[Dict[str, Any]]:
        """Export current tool configuration."""
        configs = []

        for tool_name, tool in self.tools.items():
            config = {
                "name": tool.name,
                "class": f"{tool.__class__.__module__}.{tool.__class__.__name__}",
                "description": tool.description,
                "version": tool.version
            }

            # Add any custom configuration parameters if available
            if hasattr(tool, 'get_config'):
                config["parameters"] = tool.get_config()

            configs.append(config)

        return configs


# Global tool registry instance
global_tool_registry = ToolRegistry()


def get_global_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return global_tool_registry
