"""
Enhanced Context Engine for sophisticated context management with semantic relevance.
"""

from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import asyncio
from collections import defaultdict
import tiktoken
import numpy as np

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context items with different priorities and behaviors."""
    SYSTEM = "system"           # Agent personality, core instructions
    USER = "user"              # Current user interactions
    AGENT = "agent"            # Agent's own outputs and thoughts
    TOOL = "tool"              # Tool execution results
    MEMORY = "memory"          # Retrieved relevant memories
    COLLABORATION = "collaboration"  # Inter-agent communications
    ENVIRONMENT = "environment"      # External environment state


@dataclass
class ContextItem:
    """A single context item with enhanced metadata and semantic information."""
    type: ContextType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    timestamp: float = field(default_factory=time.time)
    expiration: Optional[float] = None
    semantic_embedding: Optional[List[float]] = None
    token_count: Optional[int] = None
    relevance_score: float = 1.0
    compression_level: int = 0  # 0=original, 1=compressed, 2=summary only

    def is_expired(self) -> bool:
        """Check if the context item has expired."""
        if self.expiration is None:
            return False
        return time.time() > self.expiration

    def get_age(self) -> float:
        """Get the age of the context item in seconds."""
        return time.time() - self.timestamp

    def get_effective_priority(self) -> float:
        """Calculate effective priority considering age and relevance."""
        age_factor = max(0.1, 1.0 - (self.get_age() / 3600))  # Decay over 1 hour
        return self.priority * self.relevance_score * age_factor


class ContextProcessor(Protocol):
    """Protocol for context processors that can modify or compress context."""

    async def process(self, item: ContextItem) -> ContextItem:
        """Process a context item and return modified version."""
        ...


class SemanticContextOptimizer:
    """Optimizes context based on semantic similarity and relevance."""

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if not embedding1 or not embedding2:
            return 0.0

        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def find_redundant_items(self, items: List[ContextItem]) -> List[int]:
        """Find indices of redundant context items based on semantic similarity."""
        redundant_indices = []

        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if (items[i].semantic_embedding and items[j].semantic_embedding and
                    items[i].type == items[j].type):

                    similarity = self.calculate_similarity(
                        items[i].semantic_embedding,
                        items[j].semantic_embedding
                    )

                    if similarity > self.similarity_threshold:
                        # Keep the one with higher priority
                        if items[i].get_effective_priority() < items[j].get_effective_priority():
                            redundant_indices.append(i)
                        else:
                            redundant_indices.append(j)

        return list(set(redundant_indices))


class ContextEngine:
    """
    Enhanced context management with semantic understanding and advanced optimization.

    Features:
    - Accurate token counting with tiktoken
    - Semantic similarity-based deduplication
    - Dynamic context compression
    - Context type-specific strategies
    - Performance monitoring
    """

    def __init__(
        self,
        max_context_length: int = 4000,
        max_items: int = 100,
        model_name: str = "gpt-3.5-turbo",
        enable_semantic_optimization: bool = True
    ):
        self.max_context_length = max_context_length
        self.max_items = max_items
        self.model_name = model_name
        self.enable_semantic_optimization = enable_semantic_optimization

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found, using cl100k_base encoding")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Context storage
        self.context_items: List[ContextItem] = []
        self.context_processors: Dict[ContextType, List[ContextProcessor]] = defaultdict(list)

        # Semantic optimizer
        if enable_semantic_optimization:
            self.semantic_optimizer = SemanticContextOptimizer()
        else:
            self.semantic_optimizer = None

        # Priority mappings with enhanced strategy
        self.default_priorities = {
            ContextType.SYSTEM: 10,
            ContextType.USER: 8,
            ContextType.COLLABORATION: 7,
            ContextType.AGENT: 6,
            ContextType.TOOL: 5,
            ContextType.MEMORY: 4,
            ContextType.ENVIRONMENT: 3
        }

        # Performance metrics
        self.metrics = {
            "items_added": 0,
            "items_removed_by_expiration": 0,
            "items_removed_by_optimization": 0,
            "total_optimizations": 0,
            "average_optimization_time": 0.0
        }

    def count_tokens(self, text: str) -> int:
        """Accurately count tokens using tiktoken."""
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback estimation
            return len(text) // 4

    def add_context(self, item: ContextItem):
        """Add context item with enhanced processing and optimization."""
        start_time = time.time()

        # Set default priority if not specified
        if item.priority == 0:
            item.priority = self.default_priorities.get(item.type, 1)

        # Count tokens if not already done
        if item.token_count is None:
            item.token_count = self.count_tokens(item.content)

        # Apply context processors
        asyncio.create_task(self._apply_processors(item))

        self.context_items.append(item)
        self.metrics["items_added"] += 1

        # Cleanup and optimize
        self._cleanup_expired()
        self._optimize_context()

        optimization_time = time.time() - start_time
        self._update_optimization_metrics(optimization_time)

        logger.debug(
            f"Added context item: {item.type.value} "
            f"(priority: {item.priority}, tokens: {item.token_count})"
        )

    async def _apply_processors(self, item: ContextItem):
        """Apply registered processors to context item."""
        processors = self.context_processors.get(item.type, [])
        for processor in processors:
            try:
                item = await processor.process(item)
            except Exception as e:
                logger.error(f"Error in context processor: {e}")

    def add_system_context(
        self,
        content: str,
        metadata: Dict = None,
        priority: int = None,
        embedding: List[float] = None
    ):
        """Add system-level context with highest priority."""
        item = ContextItem(
            type=ContextType.SYSTEM,
            content=content,
            metadata=metadata or {},
            priority=priority or self.default_priorities[ContextType.SYSTEM],
            semantic_embedding=embedding
        )
        self.add_context(item)

    def add_user_context(
        self,
        content: str,
        metadata: Dict = None,
        embedding: List[float] = None
    ):
        """Add user interaction context."""
        item = ContextItem(
            type=ContextType.USER,
            content=content,
            metadata=metadata or {},
            priority=self.default_priorities[ContextType.USER],
            semantic_embedding=embedding
        )
        self.add_context(item)

    def add_memory_context(
        self,
        content: str,
        relevance_score: float = 0.5,
        metadata: Dict = None,
        embedding: List[float] = None
    ):
        """Add memory-based context with relevance scoring."""
        item = ContextItem(
            type=ContextType.MEMORY,
            content=content,
            metadata={**(metadata or {}), "relevance": relevance_score},
            priority=int(relevance_score * 10),
            relevance_score=relevance_score,
            semantic_embedding=embedding
        )
        self.add_context(item)

    def add_tool_context(
        self,
        content: str,
        tool_name: str,
        metadata: Dict = None,
        embedding: List[float] = None
    ):
        """Add tool execution context."""
        item = ContextItem(
            type=ContextType.TOOL,
            content=content,
            metadata={**(metadata or {}), "tool_name": tool_name},
            priority=self.default_priorities[ContextType.TOOL],
            semantic_embedding=embedding
        )
        self.add_context(item)

    def add_collaboration_context(
        self,
        content: str,
        collaboration_id: str,
        metadata: Dict = None,
        embedding: List[float] = None
    ):
        """Add collaboration context between agents."""
        item = ContextItem(
            type=ContextType.COLLABORATION,
            content=content,
            metadata={**(metadata or {}), "collaboration_id": collaboration_id},
            priority=self.default_priorities[ContextType.COLLABORATION],
            semantic_embedding=embedding
        )
        self.add_context(item)

    def _cleanup_expired(self):
        """Remove expired context items."""
        before_count = len(self.context_items)
        self.context_items = [item for item in self.context_items if not item.is_expired()]
        after_count = len(self.context_items)

        removed_count = before_count - after_count
        if removed_count > 0:
            self.metrics["items_removed_by_expiration"] += removed_count
            logger.debug(f"Removed {removed_count} expired context items")

    def _optimize_context(self):
        """Enhanced context optimization with multiple strategies."""
        self.metrics["total_optimizations"] += 1

        # Sort by effective priority
        self.context_items.sort(key=lambda x: x.get_effective_priority(), reverse=True)

        # Remove redundant items if semantic optimization is enabled
        if self.semantic_optimizer:
            redundant_indices = self.semantic_optimizer.find_redundant_items(self.context_items)
            if redundant_indices:
                # Remove redundant items (in reverse order to maintain indices)
                for idx in sorted(redundant_indices, reverse=True):
                    self.context_items.pop(idx)
                self.metrics["items_removed_by_optimization"] += len(redundant_indices)
                logger.debug(f"Removed {len(redundant_indices)} redundant context items")

        # Limit by number of items
        if len(self.context_items) > self.max_items:
            removed_count = len(self.context_items) - self.max_items
            self.context_items = self.context_items[:self.max_items]
            self.metrics["items_removed_by_optimization"] += removed_count
            logger.debug(f"Removed {removed_count} items due to item limit")

        # Optimize by token count
        total_tokens = sum(item.token_count or self.count_tokens(item.content)
                          for item in self.context_items)

        while total_tokens > self.max_context_length and self.context_items:
            removed = self.context_items.pop()
            removed_tokens = removed.token_count or self.count_tokens(removed.content)
            total_tokens -= removed_tokens
            self.metrics["items_removed_by_optimization"] += 1
            logger.debug(f"Removed context item due to token limit: {removed.type.value}")

    def get_context_by_type(self, context_type: ContextType) -> List[ContextItem]:
        """Get all context items of a specific type."""
        return [item for item in self.context_items if item.type == context_type]

    def get_recent_context(self, max_age_seconds: int = 3600) -> List[ContextItem]:
        """Get context items within the specified age limit."""
        cutoff_time = time.time() - max_age_seconds
        return [item for item in self.context_items if item.timestamp > cutoff_time]

    def build_prompt(self, template: str, **kwargs) -> str:
        """
        Build final prompt with enhanced context organization.

        Template placeholders:
        - {system_context}: All system context items
        - {user_context}: Recent user interactions
        - {memory_context}: Relevant memories
        - {agent_context}: Inter-agent communications
        - {tool_context}: Tool execution results
        - {collaboration_context}: Agent collaboration context
        - {environment_context}: Environment state
        - {token_count}: Total token count
        """
        context_by_type = defaultdict(list)

        for item in self.context_items:
            context_by_type[item.type].append(item.content)

        total_tokens = sum(item.token_count or self.count_tokens(item.content)
                          for item in self.context_items)

        # Build context strings with priorities
        template_vars = {
            "system_context": "\n".join(context_by_type.get(ContextType.SYSTEM, [])),
            "user_context": "\n".join(context_by_type.get(ContextType.USER, [])),
            "memory_context": "\n".join(context_by_type.get(ContextType.MEMORY, [])),
            "agent_context": "\n".join(context_by_type.get(ContextType.AGENT, [])),
            "tool_context": "\n".join(context_by_type.get(ContextType.TOOL, [])),
            "collaboration_context": "\n".join(context_by_type.get(ContextType.COLLABORATION, [])),
            "environment_context": "\n".join(context_by_type.get(ContextType.ENVIRONMENT, [])),
            "token_count": total_tokens,
            **kwargs
        }

        try:
            return template.format(**template_vars)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return template

    def get_context_summary(self) -> Dict[str, Any]:
        """Get comprehensive context summary with metrics."""
        context_stats = defaultdict(int)
        total_tokens = 0

        for item in self.context_items:
            context_stats[item.type.value] += 1
            total_tokens += item.token_count or self.count_tokens(item.content)

        return {
            "total_items": len(self.context_items),
            "total_tokens": total_tokens,
            "max_tokens": self.max_context_length,
            "token_utilization": total_tokens / self.max_context_length,
            "context_by_type": dict(context_stats),
            "metrics": self.metrics.copy()
        }

    def register_processor(self, context_type: ContextType, processor: ContextProcessor):
        """Register a context processor for a specific context type."""
        self.context_processors[context_type].append(processor)
        logger.info(f"Registered processor for {context_type.value} context")

    def clear_context_type(self, context_type: ContextType):
        """Clear all context items of a specific type."""
        before_count = len(self.context_items)
        self.context_items = [item for item in self.context_items if item.type != context_type]
        after_count = len(self.context_items)

        removed_count = before_count - after_count
        if removed_count > 0:
            logger.debug(f"Cleared {removed_count} items of type {context_type.value}")

    def reset(self):
        """Reset the context engine to initial state."""
        self.context_items.clear()
        self.metrics = {
            "items_added": 0,
            "items_removed_by_expiration": 0,
            "items_removed_by_optimization": 0,
            "total_optimizations": 0,
            "average_optimization_time": 0.0
        }
        logger.info("Context engine reset")

    def _update_optimization_metrics(self, optimization_time: float):
        """Update optimization performance metrics."""
        current_avg = self.metrics["average_optimization_time"]
        total_opts = self.metrics["total_optimizations"]

        if total_opts == 0:
            self.metrics["average_optimization_time"] = optimization_time
        else:
            self.metrics["average_optimization_time"] = (
                (current_avg * (total_opts - 1) + optimization_time) / total_opts
            )
