"""
MCP Server implementation for hosting MCP tools.
"""

from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio

logger = logging.getLogger(__name__)


class MCPServer:
    """Server for hosting MCP tools."""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.running = False
        self._tools: Dict[str, Callable] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_tool(self, name: str, handler: Callable):
        """Register a tool handler."""
        self._tools[name] = handler
        logger.info(f"Registered tool: {name}")

    def register_handler(self, method: str, handler: Callable):
        """Register a method handler."""
        self._handlers[method] = handler
        logger.info(f"Registered handler: {method}")

    async def start(self):
        """Start the MCP server."""
        try:
            self.running = True
            logger.info(f"MCP server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise

    async def stop(self):
        """Stop the MCP server."""
        self.running = False
        logger.info("MCP server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.running

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming request."""
        method = request.get("method")
        params = request.get("params", {})

        if method in self._handlers:
            try:
                result = await self._handlers[method](params)
                return {"result": result}
            except Exception as e:
                logger.error(f"Error handling {method}: {e}")
                return {"error": str(e)}
        else:
            return {"error": f"Unknown method: {method}"}

    def list_tools(self) -> List[str]:
        """List registered tools."""
        return list(self._tools.keys())
