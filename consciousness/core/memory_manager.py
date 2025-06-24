import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState, Experience, Memory
from ..models.entities import Device
from ..models.events import Event, SensorReading
from ..repositories.consciousness import EmotionalStateRepository, MemoryRepository


class MemoryManager:
    """Manages memory formation, consolidation, retrieval, and learning."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.memory_repo = MemoryRepository(session)
        self.emotion_repo = EmotionalStateRepository(session)

        # Memory configuration
        self.memory_types = {
            "episodic": {
                "description": "Specific events and experiences",
                "decay_rate": 0.02,
                "consolidation_threshold": 0.7,
            },
            "semantic": {
                "description": "Facts and knowledge",
                "decay_rate": 0.01,
                "consolidation_threshold": 0.8,
            },
            "procedural": {
                "description": "Skills and procedures",
                "decay_rate": 0.005,
                "consolidation_threshold": 0.9,
            },
        }

        # Importance calculation weights
        self.importance_weights = {
            "emotional_impact": 0.3,
            "novelty": 0.25,
            "relevance": 0.2,
            "frequency": 0.15,
            "recency": 0.1,
        }

        # Memory consolidation parameters
        self.consolidation_interval = timedelta(hours=6)
        self.max_memories_per_consolidation = 50
        self.similarity_threshold = 0.75

    async def consolidate_recent_memories(self) -> int:
        """Consolidate recent memories into more stable long-term memories."""

        # Get recent memories that haven't been consolidated
        recent_memories = await self._get_unconsolidated_memories()

        if not recent_memories:
            return 0

        consolidation_count = 0

        # Group related memories for consolidation
        memory_groups = await self._group_related_memories(recent_memories)

        for group in memory_groups:
            if len(group) > 1:
                # Consolidate group into a single memory
                consolidated_memory = await self._consolidate_memory_group(group)
                if consolidated_memory:
                    consolidation_count += 1
            else:
                # Single memory - update importance and make permanent
                await self._stabilize_single_memory(group[0])

        # Perform memory decay for old memories
        await self._apply_memory_decay()

        return consolidation_count

    async def form_memory_from_experience(
        self,
        experience_data: Dict[str, Any],
        emotional_state: Optional[EmotionalState] = None,
    ) -> Memory:
        """Form a new memory from an experience."""

        # Classify the memory type
        memory_type = self._classify_memory_type(experience_data)

        # Calculate importance score
        importance = await self._calculate_importance(experience_data, emotional_state)

        # Extract key information
        title = self._generate_memory_title(experience_data)
        description = self._generate_memory_description(experience_data)
        category = self._determine_memory_category(experience_data)

        # Create tags and related entities
        tags = self._extract_tags(experience_data)
        related_entities = self._extract_related_entities(experience_data)

        # Create the memory
        memory = await self.memory_repo.create(
            memory_type=memory_type,
            category=category,
            importance=importance,
            title=title,
            description=description,
            content=experience_data,
            source=experience_data.get("source", "internal"),
            confidence=experience_data.get("confidence", 0.8),
            tags=tags,
            related_entities=related_entities,
        )

        # Create experience record if emotional state is provided
        if emotional_state:
            await self._create_experience_record(
                memory, emotional_state, experience_data
            )

        return memory

    async def retrieve_memories(
        self,
        query: str,
        context: Dict[str, Any] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories based on query and context."""

        # Search memories using repository
        memories = await self.memory_repo.search_memories(
            query=query, memory_type=memory_type, limit=limit
        )

        # Enhance with context relevance scoring
        enhanced_memories = []
        for memory in memories:
            # Update access tracking
            await self.memory_repo.update_access(memory.id)

            # Calculate context relevance
            relevance_score = await self._calculate_context_relevance(
                memory, context or {}
            )

            enhanced_memories.append(
                {
                    "memory": memory,
                    "relevance_score": relevance_score,
                    "access_info": {
                        "access_count": memory.access_count + 1,
                        "last_accessed": datetime.utcnow(),
                    },
                }
            )

        # Sort by relevance and importance
        enhanced_memories.sort(
            key=lambda x: (x["relevance_score"] * x["memory"].importance), reverse=True
        )

        return enhanced_memories[:limit]

    async def get_related_memories(self, entity: str, limit: int = 5) -> List[Memory]:
        """Get memories related to a specific entity."""
        return await self.memory_repo.get_related_memories(entity, limit)

    async def update_memory_importance(self, memory_id: int, new_importance: float):
        """Update the importance of a memory."""
        await self.memory_repo.update(memory_id, importance=new_importance)

    async def _get_unconsolidated_memories(self) -> List[Memory]:
        """Get recent memories that haven't been consolidated."""
        cutoff_time = datetime.utcnow() - self.consolidation_interval

        result = await self.session.execute(
            select(Memory)
            .where(
                and_(
                    Memory.created_at >= cutoff_time,
                    Memory.access_count
                    <= 3,  # Low access count indicates unconsolidated
                    Memory.importance < 0.9,  # Not already highly important
                )
            )
            .order_by(Memory.created_at.desc())
            .limit(self.max_memories_per_consolidation)
        )

        return result.scalars().all()

    async def _group_related_memories(
        self, memories: List[Memory]
    ) -> List[List[Memory]]:
        """Group related memories for potential consolidation."""
        groups = []
        processed = set()

        for memory in memories:
            if memory.id in processed:
                continue

            # Find similar memories
            similar_memories = [memory]
            processed.add(memory.id)

            for other_memory in memories:
                if other_memory.id in processed:
                    continue

                similarity = await self._calculate_memory_similarity(
                    memory, other_memory
                )
                if similarity >= self.similarity_threshold:
                    similar_memories.append(other_memory)
                    processed.add(other_memory.id)

            groups.append(similar_memories)

        return groups

    async def _calculate_memory_similarity(
        self, memory1: Memory, memory2: Memory
    ) -> float:
        """Calculate similarity between two memories."""
        similarity_score = 0.0

        # Category similarity
        if memory1.category == memory2.category:
            similarity_score += 0.3

        # Type similarity
        if memory1.memory_type == memory2.memory_type:
            similarity_score += 0.2

        # Tag overlap
        tags1 = set(memory1.tags)
        tags2 = set(memory2.tags)
        if tags1 and tags2:
            tag_overlap = len(tags1.intersection(tags2)) / len(tags1.union(tags2))
            similarity_score += tag_overlap * 0.2

        # Entity overlap
        entities1 = set(memory1.related_entities)
        entities2 = set(memory2.related_entities)
        if entities1 and entities2:
            entity_overlap = len(entities1.intersection(entities2)) / len(
                entities1.union(entities2)
            )
            similarity_score += entity_overlap * 0.2

        # Content similarity (simple keyword matching)
        content_similarity = self._calculate_content_similarity(
            memory1.description, memory2.description
        )
        similarity_score += content_similarity * 0.1

        return min(1.0, similarity_score)

    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate content similarity between two text strings."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _consolidate_memory_group(
        self, memory_group: List[Memory]
    ) -> Optional[Memory]:
        """Consolidate a group of related memories into a single memory."""
        if len(memory_group) < 2:
            return None

        # Calculate consolidated importance (max of group)
        consolidated_importance = max(m.importance for m in memory_group)

        # Merge content
        merged_content = await self._merge_memory_contents(memory_group)

        # Create consolidated title and description
        consolidated_title = f"Consolidated: {memory_group[0].category}"
        consolidated_description = self._create_consolidated_description(memory_group)

        # Merge tags and entities
        all_tags = set()
        all_entities = set()
        for memory in memory_group:
            all_tags.update(memory.tags)
            all_entities.update(memory.related_entities)

        # Create new consolidated memory
        consolidated_memory = await self.memory_repo.create(
            memory_type=memory_group[0].memory_type,
            category=memory_group[0].category,
            importance=consolidated_importance,
            title=consolidated_title,
            description=consolidated_description,
            content=merged_content,
            source="consolidation",
            confidence=0.9,
            tags=list(all_tags),
            related_entities=list(all_entities),
        )

        # Mark original memories as consolidated (update their importance to low)
        for memory in memory_group:
            await self.memory_repo.update(memory.id, importance=0.1)

        return consolidated_memory

    async def _merge_memory_contents(
        self, memory_group: List[Memory]
    ) -> Dict[str, Any]:
        """Merge the contents of multiple memories."""
        merged_content = {
            "consolidated_from": [m.id for m in memory_group],
            "consolidation_date": datetime.utcnow().isoformat(),
            "summary": {},
            "details": [],
        }

        # Collect all content
        for memory in memory_group:
            merged_content["details"].append(
                {
                    "memory_id": memory.id,
                    "title": memory.title,
                    "content": memory.content,
                    "importance": memory.importance,
                }
            )

        # Create summary
        merged_content["summary"] = {
            "total_memories": len(memory_group),
            "time_span": {
                "earliest": min(m.created_at for m in memory_group).isoformat(),
                "latest": max(m.created_at for m in memory_group).isoformat(),
            },
            "categories": list(set(m.category for m in memory_group)),
            "importance_range": {
                "min": min(m.importance for m in memory_group),
                "max": max(m.importance for m in memory_group),
            },
        }

        return merged_content

    def _create_consolidated_description(self, memory_group: List[Memory]) -> str:
        """Create a description for consolidated memory."""
        categories = set(m.category for m in memory_group)
        time_span = max(m.created_at for m in memory_group) - min(
            m.created_at for m in memory_group
        )

        description = f"Consolidated memory of {len(memory_group)} related experiences "
        description += f"in {', '.join(categories)} over {time_span.days} days. "
        description += f"Key themes: {', '.join(list(set(tag for m in memory_group for tag in m.tags))[:5])}."

        return description

    async def _stabilize_single_memory(self, memory: Memory):
        """Stabilize a single memory by updating its importance."""
        # Increase importance slightly for memories that survive consolidation
        new_importance = min(1.0, memory.importance + 0.1)
        await self.memory_repo.update(memory.id, importance=new_importance)

    async def _apply_memory_decay(self):
        """Apply decay to old memories based on their type and usage."""
        # Get memories older than 7 days
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        old_memories = await self.session.execute(
            select(Memory).where(
                and_(
                    Memory.created_at < cutoff_time,
                    Memory.importance
                    > 0.1,  # Don't decay already low-importance memories
                )
            )
        )

        for memory in old_memories.scalars():
            memory_type_config = self.memory_types.get(memory.memory_type, {})
            decay_rate = memory_type_config.get("decay_rate", 0.01)

            # Factor in access patterns
            days_since_access = (
                datetime.utcnow() - (memory.last_accessed or memory.created_at)
            ).days
            access_penalty = min(0.5, days_since_access * 0.01)

            # Calculate new importance
            new_importance = memory.importance * (1 - decay_rate - access_penalty)
            new_importance = max(0.05, new_importance)  # Minimum importance threshold

            await self.memory_repo.update(memory.id, importance=new_importance)

    def _classify_memory_type(self, experience_data: Dict[str, Any]) -> str:
        """Classify the type of memory based on experience data."""

        # Check for specific event types
        if "user_interaction" in experience_data.get("source", ""):
            return "episodic"

        if "learning" in experience_data.get("type", ""):
            return "procedural"

        if "fact" in experience_data.get(
            "type", ""
        ) or "knowledge" in experience_data.get("type", ""):
            return "semantic"

        # Default classification based on content
        content_type = experience_data.get("event_type", "").lower()

        if content_type in ["user_query", "conversation", "interaction"]:
            return "episodic"
        elif content_type in [
            "learning_update",
            "behavior_change",
            "skill_acquisition",
        ]:
            return "procedural"
        else:
            return "semantic"

    async def _calculate_importance(
        self, experience_data: Dict[str, Any], emotional_state: Optional[EmotionalState]
    ) -> float:
        """Calculate the importance score for a memory."""

        importance_factors = {}

        # Emotional impact
        if emotional_state:
            importance_factors["emotional_impact"] = emotional_state.intensity
        else:
            importance_factors["emotional_impact"] = 0.5

        # Novelty (how unique is this experience)
        importance_factors["novelty"] = await self._calculate_novelty(experience_data)

        # Relevance (how relevant to current goals/context)
        importance_factors["relevance"] = self._calculate_relevance(experience_data)

        # Frequency (how often do we see this type of experience)
        importance_factors["frequency"] = await self._calculate_frequency_impact(
            experience_data
        )

        # Recency (more recent experiences are more important initially)
        importance_factors["recency"] = 1.0  # New memories start with full recency

        # Calculate weighted importance
        total_importance = 0.0
        for factor, value in importance_factors.items():
            weight = self.importance_weights.get(factor, 0.0)
            total_importance += value * weight

        return min(1.0, max(0.1, total_importance))

    async def _calculate_novelty(self, experience_data: Dict[str, Any]) -> float:
        """Calculate how novel this experience is."""

        # Look for similar experiences in recent memory
        category = self._determine_memory_category(experience_data)

        recent_similar = await self.session.execute(
            select(func.count(Memory.id)).where(
                and_(
                    Memory.category == category,
                    Memory.created_at >= datetime.utcnow() - timedelta(days=7),
                )
            )
        )

        similar_count = recent_similar.scalar()

        # Higher novelty if fewer similar experiences
        novelty = 1.0 - min(0.9, similar_count * 0.1)
        return novelty

    def _calculate_relevance(self, experience_data: Dict[str, Any]) -> float:
        """Calculate relevance to current context and goals."""

        # This is a simplified relevance calculation
        # In a full implementation, this would consider current goals, user preferences, etc.

        relevance_score = 0.5  # Neutral baseline

        # User interactions are generally more relevant
        if "user" in experience_data.get("source", "").lower():
            relevance_score += 0.3

        # System health issues are highly relevant
        if (
            "error" in experience_data.get("type", "").lower()
            or "critical" in experience_data.get("severity", "").lower()
        ):
            relevance_score += 0.4

        # Learning experiences are relevant
        if "learning" in experience_data.get("type", "").lower():
            relevance_score += 0.2

        return min(1.0, relevance_score)

    async def _calculate_frequency_impact(
        self, experience_data: Dict[str, Any]
    ) -> float:
        """Calculate importance based on frequency of similar experiences."""

        event_type = experience_data.get("event_type", "")

        # Count similar events in recent history
        recent_count = await self.session.execute(
            select(func.count(Memory.id)).where(
                and_(
                    func.json_extract(Memory.content, "$.event_type") == event_type,
                    Memory.created_at >= datetime.utcnow() - timedelta(days=30),
                )
            )
        )

        count = recent_count.scalar()

        # Rare events are more important, but very common events might also be important
        if count == 0:
            return 0.9  # Very rare
        elif count <= 3:
            return 0.7  # Somewhat rare
        elif count <= 10:
            return 0.5  # Common
        else:
            return 0.3  # Very common

    def _determine_memory_category(self, experience_data: Dict[str, Any]) -> str:
        """Determine the category of the memory."""

        # Extract category from experience data
        if "category" in experience_data:
            return experience_data["category"]

        # Infer from event type
        event_type = experience_data.get("event_type", "").lower()

        if "user" in event_type:
            return "user_interaction"
        elif "device" in event_type:
            return "device_management"
        elif "sensor" in event_type:
            return "environmental_monitoring"
        elif "system" in event_type:
            return "system_operation"
        elif "learning" in event_type:
            return "learning_experience"
        else:
            return "general"

    def _generate_memory_title(self, experience_data: Dict[str, Any]) -> str:
        """Generate a title for the memory."""

        event_type = experience_data.get("event_type", "Experience")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        # Create descriptive title
        if "user_query" in event_type:
            return f"User Query - {timestamp}"
        elif "device_action" in event_type:
            device_name = experience_data.get("device_name", "Unknown Device")
            return f"Device Action: {device_name} - {timestamp}"
        elif "sensor_reading" in event_type:
            sensor_type = experience_data.get("sensor_type", "Unknown Sensor")
            return f"Sensor Reading: {sensor_type} - {timestamp}"
        else:
            return f"{event_type.replace('_', ' ').title()} - {timestamp}"

    def _generate_memory_description(self, experience_data: Dict[str, Any]) -> str:
        """Generate a description for the memory."""

        # Extract key details
        event_type = experience_data.get("event_type", "Unknown")
        description_parts = [f"Event type: {event_type}"]

        if "user_query" in experience_data:
            description_parts.append(f"User asked: {experience_data['user_query']}")

        if "device_name" in experience_data:
            description_parts.append(
                f"Device involved: {experience_data['device_name']}"
            )

        if "outcome" in experience_data:
            description_parts.append(f"Outcome: {experience_data['outcome']}")

        if "emotional_impact" in experience_data:
            description_parts.append(
                f"Emotional impact: {experience_data['emotional_impact']}"
            )

        return ". ".join(description_parts) + "."

    def _extract_tags(self, experience_data: Dict[str, Any]) -> List[str]:
        """Extract tags from experience data."""

        tags = []

        # Add event type as tag
        if "event_type" in experience_data:
            tags.append(experience_data["event_type"])

        # Add category as tag
        category = self._determine_memory_category(experience_data)
        tags.append(category)

        # Add severity as tag if present
        if "severity" in experience_data:
            tags.append(f"severity_{experience_data['severity']}")

        # Add outcome as tag if present
        if "outcome" in experience_data:
            tags.append(f"outcome_{experience_data['outcome']}")

        # Add time-based tags
        now = datetime.utcnow()
        tags.extend(
            [
                f"hour_{now.hour}",
                f"day_{now.strftime('%A').lower()}",
                f"month_{now.strftime('%B').lower()}",
            ]
        )

        return list(set(tags))  # Remove duplicates

    def _extract_related_entities(self, experience_data: Dict[str, Any]) -> List[str]:
        """Extract related entities from experience data."""

        entities = []

        # Add device name if present
        if "device_name" in experience_data:
            entities.append(experience_data["device_name"])

        # Add room name if present
        if "room_name" in experience_data:
            entities.append(experience_data["room_name"])

        # Add user name if present
        if "user_name" in experience_data:
            entities.append(experience_data["user_name"])

        # Add sensor type if present
        if "sensor_type" in experience_data:
            entities.append(f"sensor_{experience_data['sensor_type']}")

        return list(set(entities))  # Remove duplicates

    async def _create_experience_record(
        self,
        memory: Memory,
        emotional_state: EmotionalState,
        experience_data: Dict[str, Any],
    ):
        """Create an experience record linking memory to emotional state."""

        from ..models.consciousness import Experience

        # Determine outcome
        outcome = experience_data.get("outcome", "neutral")
        if outcome not in ["positive", "negative", "neutral"]:
            outcome = "neutral"

        # Calculate impact score
        impact_score = 0.0
        if outcome == "positive":
            impact_score = emotional_state.intensity * 0.5
        elif outcome == "negative":
            impact_score = -emotional_state.intensity * 0.5

        # Create experience record
        experience = Experience(
            memory_id=memory.id,
            emotional_state_id=emotional_state.id,
            experience_type=experience_data.get("event_type", "general"),
            outcome=outcome,
            impact_score=impact_score,
            lesson_learned=experience_data.get("lesson_learned"),
            behavior_change=experience_data.get("behavior_change"),
            context=experience_data,
        )

        self.session.add(experience)
        await self.session.commit()

    async def _calculate_context_relevance(
        self, memory: Memory, context: Dict[str, Any]
    ) -> float:
        """Calculate how relevant a memory is to the current context."""

        relevance_score = 0.5  # Base relevance

        # Check context keys against memory tags and content
        context_keys = set(context.keys())
        memory_tags = set(memory.tags)

        # Tag overlap
        if context_keys and memory_tags:
            tag_overlap = len(context_keys.intersection(memory_tags)) / len(
                context_keys
            )
            relevance_score += tag_overlap * 0.3

        # Entity overlap
        if "entities" in context:
            context_entities = set(context["entities"])
            memory_entities = set(memory.related_entities)
            if context_entities and memory_entities:
                entity_overlap = len(
                    context_entities.intersection(memory_entities)
                ) / len(context_entities)
                relevance_score += entity_overlap * 0.2

        # Recency bonus
        hours_since_created = (
            datetime.utcnow() - memory.created_at
        ).total_seconds() / 3600
        recency_bonus = max(0, 1 - hours_since_created / 168)  # Decay over a week
        relevance_score += recency_bonus * 0.1

        return min(1.0, relevance_score)
