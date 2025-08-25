"""
Memory Manager for persistent conversation memory with relevance scoring.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta

import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """A single memory item with metadata and embeddings."""
    id: str
    content: str
    memory_type: str  # conversation, fact, preference, etc.
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    importance: float = 0.5  # 0-1 scale
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score,
            "importance": self.importance,
            "embedding": self.embedding
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        return cls(**data)


class MemoryManager:
    """
    Manages persistent conversation memory with vector-based semantic search.

    Features:
    - Vector embeddings for semantic similarity
    - Importance scoring for memory prioritization
    - Automatic memory consolidation
    - Context-aware retrieval
    """

    def __init__(
        self,
        agent_name: str,
        embedding_model: str = "all-MiniLM-L6-v2",
        max_memories: int = 1000,
        collection_name: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.max_memories = max_memories

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(path=f"./data/memory/{agent_name}")
        self.collection_name = collection_name or f"{agent_name}_memories"

        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": f"Memory collection for agent {agent_name}"}
            )

        logger.info(f"Initialized memory manager for agent: {agent_name}")

    async def store_interaction(
        self,
        user_message: str,
        agent_response: Dict[str, Any],
        importance: float = None,
        user_id: str = None
    ) -> str:
        """Store a conversation interaction in memory."""
        interaction_content = f"User: {user_message}\nAgent: {agent_response.get('response', '')}"

        # Generate unique ID
        interaction_id = self._generate_memory_id(interaction_content)

        # Calculate importance if not provided
        if importance is None:
            importance = self._calculate_importance(user_message, agent_response)

        # Create memory item
        memory_item = MemoryItem(
            id=interaction_id,
            content=interaction_content,
            memory_type="conversation",
            timestamp=time.time(),
            metadata={
                "user_message": user_message,
                "agent_response": agent_response,
                "agent_name": self.agent_name,
                "user_id": user_id
            },
            importance=importance
        )

        await self._store_memory(memory_item)
        logger.debug(f"Stored interaction memory: {interaction_id}")

        return interaction_id

    async def store_fact(
        self,
        fact: str,
        category: str = "general",
        importance: float = 0.7,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store a factual memory."""
        fact_id = self._generate_memory_id(fact)

        memory_item = MemoryItem(
            id=fact_id,
            content=fact,
            memory_type="fact",
            timestamp=time.time(),
            metadata={
                "category": category,
                **(metadata or {})
            },
            importance=importance
        )

        await self._store_memory(memory_item)
        logger.debug(f"Stored fact memory: {fact_id}")

        return fact_id

    async def store_preference(
        self,
        preference: str,
        user_id: Optional[str] = None,
        importance: float = 0.8,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Store a user preference."""
        pref_id = self._generate_memory_id(preference)

        memory_item = MemoryItem(
            id=pref_id,
            content=preference,
            memory_type="preference",
            timestamp=time.time(),
            metadata={
                "user_id": user_id,
                **(metadata or {})
            },
            importance=importance
        )

        await self._store_memory(memory_item)
        logger.debug(f"Stored preference memory: {pref_id}")

        return pref_id

    async def retrieve_relevant_memories(
        self,
        query: str,
        max_results: int = 5,
        min_relevance: float = 0.3,
        memory_types: Optional[List[str]] = None,
        user_id: str = None
    ) -> List[MemoryItem]:
        """Retrieve memories relevant to the query using semantic search."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()

            # Build filter for memory types and user_id
            where_clause = {}
            if memory_types:
                where_clause["memory_type"] = {"$in": memory_types}
            if user_id:
                where_clause["user_id"] = user_id

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results * 2,  # Get extra to filter by relevance
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances"]
            )

            memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    # Calculate relevance score
                    # ChromaDB returns cosine distance, convert to similarity
                    distance = results["distances"][0][i]
                    # For cosine distance, similarity = 1 - (distance / 2)
                    # This normalizes the range to [0, 1] where 1 is most similar
                    relevance_score = max(0, 1 - (distance / 2))

                    if relevance_score >= min_relevance:
                        metadata = results["metadatas"][0][i]
                        content = results["documents"][0][i]

                        memory_item = MemoryItem(
                            id=memory_id,
                            content=content,
                            memory_type=metadata.get("memory_type", "unknown"),
                            timestamp=metadata.get("timestamp", time.time()),
                            metadata=metadata,
                            relevance_score=relevance_score,
                            importance=metadata.get("importance", 0.5)
                        )
                        memories.append(memory_item)

            # Sort by relevance and importance
            memories.sort(key=lambda x: (x.relevance_score, x.importance), reverse=True)

            logger.debug(f"Retrieved {len(memories)} relevant memories for query: {query[:50]}...")
            return memories[:max_results]

        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    async def get_recent_memories(
        self,
        hours: int = 24,
        max_results: int = 10,
        memory_types: Optional[List[str]] = None
    ) -> List[MemoryItem]:
        """Get recent memories within the specified time window."""
        try:
            cutoff_time = time.time() - (hours * 3600)

            where_clause = {
                "timestamp": {"$gte": cutoff_time}
            }

            if memory_types:
                where_clause["memory_type"] = {"$in": memory_types}

            results = self.collection.get(
                where=where_clause,
                limit=max_results,
                include=["metadatas", "documents"]
            )

            memories = []
            if results["ids"]:
                for i, memory_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i]
                    content = results["documents"][i]

                    memory_item = MemoryItem(
                        id=memory_id,
                        content=content,
                        memory_type=metadata.get("memory_type", "unknown"),
                        timestamp=metadata.get("timestamp", time.time()),
                        metadata=metadata,
                        importance=metadata.get("importance", 0.5)
                    )
                    memories.append(memory_item)

            # Sort by timestamp (most recent first)
            memories.sort(key=lambda x: x.timestamp, reverse=True)

            logger.debug(f"Retrieved {len(memories)} recent memories")
            return memories

        except Exception as e:
            logger.error(f"Error retrieving recent memories: {e}")
            return []

    async def update_memory_importance(self, memory_id: str, importance: float):
        """Update the importance score of a memory."""
        try:
            # Get existing memory
            result = self.collection.get(
                ids=[memory_id],
                include=["metadatas"]
            )

            if result["ids"] and result["ids"][0] == memory_id:
                metadata = result["metadatas"][0]
                metadata["importance"] = importance

                # Update in ChromaDB
                self.collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )

                logger.debug(f"Updated importance for memory {memory_id}: {importance}")

        except Exception as e:
            logger.error(f"Error updating memory importance: {e}")

    async def delete_memory(self, memory_id: str):
        """Delete a specific memory."""
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Deleted memory: {memory_id}")
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")

    async def consolidate_memories(self, max_age_days: int = 30):
        """
        Consolidate old memories to reduce storage while preserving important information.
        This is a placeholder for more sophisticated consolidation strategies.
        """
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 3600)

            # Get old memories
            old_memories = self.collection.get(
                where={"timestamp": {"$lt": cutoff_time}},
                include=["metadatas", "documents"]
            )

            if not old_memories["ids"]:
                return

            # Group by type and importance for consolidation
            consolidation_groups = {}

            for i, memory_id in enumerate(old_memories["ids"]):
                metadata = old_memories["metadatas"][i]
                importance = metadata.get("importance", 0.5)
                memory_type = metadata.get("memory_type", "unknown")

                # Only consolidate low-importance memories
                if importance < 0.6:
                    group_key = f"{memory_type}_{int(importance * 10)}"
                    if group_key not in consolidation_groups:
                        consolidation_groups[group_key] = []
                    consolidation_groups[group_key].append({
                        "id": memory_id,
                        "content": old_memories["documents"][i],
                        "metadata": metadata
                    })

            # Perform consolidation (simplified: remove duplicates and low-importance items)
            for group_key, group_memories in consolidation_groups.items():
                if len(group_memories) > 5:  # Consolidate if more than 5 similar memories
                    # Keep the most important ones
                    group_memories.sort(key=lambda x: x["metadata"].get("importance", 0), reverse=True)
                    to_delete = [m["id"] for m in group_memories[3:]]  # Keep top 3

                    if to_delete:
                        self.collection.delete(ids=to_delete)
                        logger.info(f"Consolidated {len(to_delete)} memories in group {group_key}")

        except Exception as e:
            logger.error(f"Error consolidating memories: {e}")

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories."""
        try:
            # Get all memories
            all_memories = self.collection.get(include=["metadatas"])

            if not all_memories["ids"]:
                return {"total_memories": 0}

            total_memories = len(all_memories["ids"])

            # Group by type
            by_type = {}
            by_importance = {"low": 0, "medium": 0, "high": 0}

            for metadata in all_memories["metadatas"]:
                memory_type = metadata.get("memory_type", "unknown")
                importance = metadata.get("importance", 0.5)

                by_type[memory_type] = by_type.get(memory_type, 0) + 1

                if importance < 0.4:
                    by_importance["low"] += 1
                elif importance < 0.7:
                    by_importance["medium"] += 1
                else:
                    by_importance["high"] += 1

            return {
                "total_memories": total_memories,
                "by_type": by_type,
                "by_importance": by_importance,
                "collection_name": self.collection_name
            }

        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    def _generate_memory_id(self, content: str) -> str:
        """Generate a unique ID for memory content."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp_str = str(int(time.time()))
        return f"{self.agent_name}_{content_hash[:8]}_{timestamp_str}"

    def _calculate_importance(self, user_message: str, agent_response: Dict[str, Any]) -> float:
        """
        Calculate importance score for an interaction.
        This is a simplified heuristic - could be enhanced with ML models.
        """
        importance = 0.5  # Base importance

        # Increase importance for certain keywords
        important_keywords = [
            "remember", "important", "preference", "like", "dislike",
            "always", "never", "favorite", "hate", "love"
        ]

        message_lower = user_message.lower()
        for keyword in important_keywords:
            if keyword in message_lower:
                importance += 0.1

        # Increase importance for longer interactions
        if len(user_message) > 100:
            importance += 0.1

        # Increase importance if agent used tools
        if agent_response.get("tools_used"):
            importance += 0.1

        # Cap at 1.0
        return min(importance, 1.0)

    async def _store_memory(self, memory_item: MemoryItem):
        """Store a memory item in the vector database."""
        try:
            # Generate embedding
            embedding = self.embedding_model.encode([memory_item.content])[0].tolist()
            memory_item.embedding = embedding

            # Prepare metadata (ChromaDB doesn't support nested dicts well)
            flat_metadata = self._flatten_metadata(memory_item.metadata)
            flat_metadata.update({
                "memory_type": memory_item.memory_type,
                "timestamp": memory_item.timestamp,
                "importance": memory_item.importance,
                "agent_name": self.agent_name
            })

            # Store in ChromaDB
            self.collection.add(
                ids=[memory_item.id],
                embeddings=[embedding],
                documents=[memory_item.content],
                metadatas=[flat_metadata]
            )

            # Clean up old memories if we exceed the limit
            await self._cleanup_old_memories()

        except Exception as e:
            logger.error(f"Error storing memory: {e}")

    def _flatten_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested metadata for ChromaDB storage."""
        flat = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                flat[key] = value
            else:
                flat[key] = json.dumps(value)
        return flat

    async def _cleanup_old_memories(self):
        """Remove oldest memories if we exceed the maximum."""
        try:
            # Get count of memories
            all_memories = self.collection.get()
            total_memories = len(all_memories["ids"]) if all_memories["ids"] else 0

            if total_memories > self.max_memories:
                excess = total_memories - self.max_memories

                # Get oldest memories
                all_with_metadata = self.collection.get(include=["metadatas"])

                if all_with_metadata["ids"]:
                    # Sort by timestamp
                    memory_data = [
                        (all_with_metadata["ids"][i], all_with_metadata["metadatas"][i])
                        for i in range(len(all_with_metadata["ids"]))
                    ]
                    memory_data.sort(key=lambda x: x[1].get("timestamp", 0))

                    # Delete oldest memories
                    to_delete = [item[0] for item in memory_data[:excess]]
                    self.collection.delete(ids=to_delete)

                    logger.info(f"Cleaned up {len(to_delete)} old memories")

        except Exception as e:
            logger.error(f"Error cleaning up old memories: {e}")
