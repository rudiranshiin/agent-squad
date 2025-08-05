"""
Context Engine for intelligent context management with priority-based optimization.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context items with different priorities."""
    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"
    TOOL = "tool"
    MEMORY = "memory"
    COLLABORATION = "collaboration"


@dataclass
class ContextItem:
    """A single context item with metadata and priority."""
    type: ContextType
    content: str
    metadata: Dict[str, Any]
    priority: int = 0
    timestamp: float = 0.0
    expires_at: Optional[float] = None

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()

    def is_expired(self) -> bool:
        """Check if the context item has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def get_age(self) -> float:
        """Get the age of the context item in seconds."""
        return time.time() - self.timestamp


class ContextEngine:
    """
    Manages context items with intelligent prioritization and optimization.

    Features:
    - Priority-based context ordering
    - Automatic expiration handling
    - Token-based context optimization
    - Context compression for older items
    """

    def __init__(self, max_context_length: int = 4000, max_items: int = 100):
        self.max_context_length = max_context_length
        self.max_items = max_items
        self.context_items: List[ContextItem] = []
        self.context_processors = {}

        # Priority mappings for different context types
        self.default_priorities = {
            ContextType.SYSTEM: 10,
            ContextType.USER: 8,
            ContextType.AGENT: 6,
            ContextType.TOOL: 5,
            ContextType.MEMORY: 4,
            ContextType.COLLABORATION: 7
        }

    def add_context(self, item: ContextItem):
        """Add context item with automatic prioritization and optimization."""
        if item.priority == 0:
            item.priority = self.default_priorities.get(item.type, 1)

        self.context_items.append(item)
        self._cleanup_expired()
        self._optimize_context()

        logger.debug(f"Added context item: {item.type.value} (priority: {item.priority})")

    def add_system_context(self, content: str, metadata: Dict = None, priority: int = None):
        """Add system-level context (highest priority)."""
        item = ContextItem(
            type=ContextType.SYSTEM,
            content=content,
            metadata=metadata or {},
            priority=priority or self.default_priorities[ContextType.SYSTEM]
        )
        self.add_context(item)

    def add_user_context(self, content: str, metadata: Dict = None):
        """Add user interaction context."""
        item = ContextItem(
            type=ContextType.USER,
            content=content,
            metadata=metadata or {},
            priority=self.default_priorities[ContextType.USER]
        )
        self.add_context(item)

    def add_memory_context(self, content: str, relevance_score: float = 0.5, metadata: Dict = None):
        """Add memory-based context with relevance scoring."""
        priority = int(relevance_score * 10)
        item = ContextItem(
            type=ContextType.MEMORY,
            content=content,
            metadata={**(metadata or {}), "relevance": relevance_score},
            priority=priority
        )
        self.add_context(item)

    def add_agent_context(self, content: str, agent_name: str, metadata: Dict = None):
        """Add inter-agent communication context."""
        item = ContextItem(
            type=ContextType.AGENT,
            content=content,
            metadata={**(metadata or {}), "agent": agent_name},
            priority=self.default_priorities[ContextType.AGENT]
        )
        self.add_context(item)

    def add_tool_context(self, content: str, tool_name: str, metadata: Dict = None):
        """Add tool execution context."""
        item = ContextItem(
            type=ContextType.TOOL,
            content=content,
            metadata={**(metadata or {}), "tool": tool_name},
            priority=self.default_priorities[ContextType.TOOL]
        )
        self.add_context(item)

    def add_collaboration_context(self, content: str, collaboration_id: str, metadata: Dict = None):
        """Add collaboration context between agents."""
        item = ContextItem(
            type=ContextType.COLLABORATION,
            content=content,
            metadata={**(metadata or {}), "collaboration_id": collaboration_id},
            priority=self.default_priorities[ContextType.COLLABORATION]
        )
        self.add_context(item)

    def _cleanup_expired(self):
        """Remove expired context items."""
        before_count = len(self.context_items)
        self.context_items = [item for item in self.context_items if not item.is_expired()]
        after_count = len(self.context_items)

        if before_count != after_count:
            logger.debug(f"Removed {before_count - after_count} expired context items")

    def _optimize_context(self):
        """Optimize context to fit within token and item limits."""
        # Sort by priority (descending) and recency (descending for same priority)
        self.context_items.sort(
            key=lambda x: (x.priority, x.timestamp),
            reverse=True
        )

        # Limit number of items
        if len(self.context_items) > self.max_items:
            removed_items = len(self.context_items) - self.max_items
            self.context_items = self.context_items[:self.max_items]
            logger.debug(f"Removed {removed_items} items due to item limit")

        # Estimate token usage and remove low-priority items if needed
        total_length = sum(len(item.content) for item in self.context_items)

        while total_length > self.max_context_length and self.context_items:
            removed = self.context_items.pop()
            total_length -= len(removed.content)
            logger.debug(f"Removed context item due to length limit: {removed.type.value}")

    def get_context_by_type(self, context_type: ContextType) -> List[ContextItem]:
        """Get all context items of a specific type."""
        return [item for item in self.context_items if item.type == context_type]

    def get_recent_context(self, max_age_seconds: int = 3600) -> List[ContextItem]:
        """Get context items within the specified age limit."""
        cutoff_time = time.time() - max_age_seconds
        return [item for item in self.context_items if item.timestamp > cutoff_time]

    def build_prompt(self, template: str, **kwargs) -> str:
        """
        Build final prompt with context using the provided template.

        Template placeholders:
        - {system_context}: All system context items
        - {user_context}: Recent user interactions
        - {memory_context}: Relevant memories
        - {agent_context}: Inter-agent communications
        - {tool_context}: Tool execution results
        - {collaboration_context}: Agent collaboration context
        """
        context_by_type = {}

        for item in self.context_items:
            if item.type not in context_by_type:
                context_by_type[item.type] = []
            context_by_type[item.type].append(item.content)

        # Build context strings
        template_vars = {
            "system_context": "\n".join(context_by_type.get(ContextType.SYSTEM, [])),
            "user_context": "\n".join(context_by_type.get(ContextType.USER, [])),
            "memory_context": "\n".join(context_by_type.get(ContextType.MEMORY, [])),
            "agent_context": "\n".join(context_by_type.get(ContextType.AGENT, [])),
            "tool_context": "\n".join(context_by_type.get(ContextType.TOOL, [])),
            "collaboration_context": "\n".join(context_by_type.get(ContextType.COLLABORATION, [])),
            **kwargs
        }

        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of current context state."""
        summary = {
            "total_items": len(self.context_items),
            "total_length": sum(len(item.content) for item in self.context_items),
            "by_type": {},
            "oldest_item_age": 0,
            "newest_item_age": 0
        }

        if self.context_items:
            ages = [item.get_age() for item in self.context_items]
            summary["oldest_item_age"] = max(ages)
            summary["newest_item_age"] = min(ages)

        for context_type in ContextType:
            items = self.get_context_by_type(context_type)
            summary["by_type"][context_type.value] = {
                "count": len(items),
                "total_length": sum(len(item.content) for item in items)
            }

        return summary

    def clear_context_type(self, context_type: ContextType):
        """Clear all context items of a specific type."""
        before_count = len(self.context_items)
        self.context_items = [
            item for item in self.context_items
            if item.type != context_type
        ]
        after_count = len(self.context_items)

        logger.info(f"Cleared {before_count - after_count} {context_type.value} context items")

    def clear_all_context(self):
        """Clear all context items."""
        count = len(self.context_items)
        self.context_items.clear()
        logger.info(f"Cleared all {count} context items")

    def compress_old_context(self, max_age_seconds: int = 7200, compression_ratio: float = 0.3):
        """
        Compress old context items to save space while preserving key information.
        This is a placeholder for more sophisticated compression strategies.
        """
        cutoff_time = time.time() - max_age_seconds
        old_items = [item for item in self.context_items if item.timestamp < cutoff_time]

        if not old_items:
            return

        # Simple compression: take first part of content for old items
        for item in old_items:
            original_length = len(item.content)
            compressed_length = int(original_length * compression_ratio)

            if compressed_length < original_length:
                item.content = item.content[:compressed_length] + "..."
                item.metadata["compressed"] = True
                item.metadata["original_length"] = original_length

        logger.info(f"Compressed {len(old_items)} old context items")
