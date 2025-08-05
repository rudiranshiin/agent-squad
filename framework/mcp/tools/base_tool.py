"""
Base Tool class for MCP tool implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """
    Base class for all MCP tools.

    Provides common functionality like:
    - Parameter validation
    - Error handling
    - Execution timing
    - Logging
    """

    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        timeout: float = 30.0
    ):
        self.name = name
        self.description = description
        self.version = version
        self.timeout = timeout
        self._execution_count = 0
        self._total_execution_time = 0.0

    @abstractmethod
    async def execute(self, **parameters) -> Any:
        """
        Execute the tool with the given parameters.

        Args:
            **parameters: Tool-specific parameters

        Returns:
            Tool execution result

        Raises:
            ToolExecutionError: If tool execution fails
        """
        pass

    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema for tool parameters.

        Returns:
            JSON schema describing expected parameters
        """
        pass

    async def execute_with_validation(self, **parameters) -> ToolExecutionResult:
        """
        Execute tool with parameter validation and error handling.

        Args:
            **parameters: Tool parameters

        Returns:
            ToolExecutionResult with execution details
        """
        start_time = time.time()

        try:
            # Validate parameters
            validation_error = self.validate_parameters(parameters)
            if validation_error:
                return ToolExecutionResult(
                    success=False,
                    data=None,
                    error=f"Parameter validation failed: {validation_error}",
                    execution_time=time.time() - start_time
                )

            # Execute with timeout
            try:
                result = await asyncio.wait_for(
                    self.execute(**parameters),
                    timeout=self.timeout
                )

                execution_time = time.time() - start_time

                # Update statistics
                self._execution_count += 1
                self._total_execution_time += execution_time

                logger.debug(f"Tool {self.name} executed successfully in {execution_time:.2f}s")

                return ToolExecutionResult(
                    success=True,
                    data=result,
                    execution_time=execution_time,
                    metadata={
                        "tool_name": self.name,
                        "tool_version": self.version,
                        "execution_count": self._execution_count
                    }
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                error_msg = f"Tool execution timed out after {self.timeout}s"
                logger.error(f"Tool {self.name}: {error_msg}")

                return ToolExecutionResult(
                    success=False,
                    data=None,
                    error=error_msg,
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"Tool {self.name}: {error_msg}", exc_info=True)

            return ToolExecutionResult(
                success=False,
                data=None,
                error=error_msg,
                execution_time=execution_time
            )

    def validate_parameters(self, parameters: Dict[str, Any]) -> Optional[str]:
        """
        Validate parameters against the tool's schema.

        Args:
            parameters: Parameters to validate

        Returns:
            Error message if validation fails, None if valid
        """
        try:
            schema = self.get_parameter_schema()
            required_params = schema.get("required", [])
            properties = schema.get("properties", {})

            # Check required parameters
            for param in required_params:
                if param not in parameters:
                    return f"Missing required parameter: {param}"

            # Check parameter types
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    param_schema = properties[param_name]
                    expected_type = param_schema.get("type")

                    if expected_type and not self._validate_type(param_value, expected_type):
                        return f"Parameter {param_name} must be of type {expected_type}"

            return None

        except Exception as e:
            return f"Schema validation error: {str(e)}"

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type."""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True  # Unknown type, assume valid

    def get_info(self) -> Dict[str, Any]:
        """Get tool information."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "timeout": self.timeout,
            "parameter_schema": self.get_parameter_schema(),
            "statistics": {
                "execution_count": self._execution_count,
                "total_execution_time": self._total_execution_time,
                "average_execution_time": (
                    self._total_execution_time / self._execution_count
                    if self._execution_count > 0 else 0
                )
            }
        }

    def reset_statistics(self):
        """Reset execution statistics."""
        self._execution_count = 0
        self._total_execution_time = 0.0
        logger.debug(f"Reset statistics for tool: {self.name}")

    async def health_check(self) -> bool:
        """
        Perform a health check on the tool.

        Returns:
            True if tool is healthy, False otherwise
        """
        try:
            # Default implementation - can be overridden by specific tools
            return True
        except Exception as e:
            logger.error(f"Health check failed for tool {self.name}: {e}")
            return False

    def __str__(self) -> str:
        return f"Tool({self.name}, v{self.version})"

    def __repr__(self) -> str:
        return f"Tool(name='{self.name}', version='{self.version}', description='{self.description[:50]}...')"


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""

    def __init__(self, message: str, tool_name: str, original_error: Exception = None):
        self.message = message
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Tool '{tool_name}' execution failed: {message}")


class ToolParameterError(Exception):
    """Exception raised when tool parameters are invalid."""

    def __init__(self, message: str, tool_name: str, parameter_name: str = None):
        self.message = message
        self.tool_name = tool_name
        self.parameter_name = parameter_name
        param_info = f" (parameter: {parameter_name})" if parameter_name else ""
        super().__init__(f"Tool '{tool_name}' parameter error{param_info}: {message}")


class AsyncTool(BaseTool):
    """
    Base class for asynchronous tools that require setup/teardown.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialized = False

    async def initialize(self):
        """Initialize the tool (e.g., connect to external services)."""
        if not self._initialized:
            await self._setup()
            self._initialized = True
            logger.info(f"Initialized async tool: {self.name}")

    async def cleanup(self):
        """Clean up tool resources."""
        if self._initialized:
            await self._teardown()
            self._initialized = False
            logger.info(f"Cleaned up async tool: {self.name}")

    async def _setup(self):
        """Override in subclasses for specific setup logic."""
        pass

    async def _teardown(self):
        """Override in subclasses for specific teardown logic."""
        pass

    async def execute_with_validation(self, **parameters) -> ToolExecutionResult:
        """Ensure tool is initialized before execution."""
        if not self._initialized:
            await self.initialize()

        return await super().execute_with_validation(**parameters)

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


class CachedTool(BaseTool):
    """
    Base class for tools that can cache results.
    """

    def __init__(self, *args, cache_ttl: float = 300.0, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_ttl = cache_ttl  # Cache time-to-live in seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, parameters: Dict[str, Any]) -> str:
        """Generate cache key from parameters."""
        import hashlib
        import json

        # Create deterministic string from parameters
        param_str = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry["timestamp"] < self.cache_ttl

    async def execute_with_validation(self, **parameters) -> ToolExecutionResult:
        """Execute with caching support."""
        cache_key = self._get_cache_key(parameters)

        # Check cache
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                logger.debug(f"Tool {self.name}: Cache hit for key {cache_key[:8]}...")
                result = cache_entry["result"]
                result.metadata = result.metadata or {}
                result.metadata["cache_hit"] = True
                return result
            else:
                # Remove expired cache entry
                del self._cache[cache_key]

        # Execute and cache result
        result = await super().execute_with_validation(**parameters)

        if result.success:
            self._cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
            logger.debug(f"Tool {self.name}: Cached result for key {cache_key[:8]}...")

        result.metadata = result.metadata or {}
        result.metadata["cache_hit"] = False

        return result

    def clear_cache(self):
        """Clear all cached results."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared cache for tool {self.name}: {cache_size} entries removed")
