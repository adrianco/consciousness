from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.consciousness import EmotionalState, Experience, Memory
from ..models.entities import Device
from ..models.interview import DeviceCandidate, InterviewSession
from .base import BaseRepository


class EmotionalStateRepository(BaseRepository[EmotionalState]):
    """Repository for emotional state management."""

    def __init__(self, session: AsyncSession):
        super().__init__(EmotionalState, session)

    async def get_current_state(self) -> Optional[EmotionalState]:
        """Get the most recent emotional state."""
        result = await self.session.execute(
            select(EmotionalState).order_by(desc(EmotionalState.created_at)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_state_history(
        self, hours: int = 24, limit: int = 100
    ) -> List[EmotionalState]:
        """Get emotional state history."""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(EmotionalState)
            .where(EmotionalState.created_at >= since)
            .order_by(desc(EmotionalState.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_dominant_emotion_periods(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get periods where specific emotions were dominant."""
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(
                EmotionalState.primary_emotion,
                func.count(EmotionalState.id).label("count"),
                func.avg(EmotionalState.intensity).label("avg_intensity"),
            )
            .where(EmotionalState.created_at >= since)
            .group_by(EmotionalState.primary_emotion)
            .order_by(desc("count"))
        )
        return [
            {
                "emotion": row.primary_emotion,
                "count": row.count,
                "avg_intensity": row.avg_intensity,
            }
            for row in result
        ]


class MemoryRepository(BaseRepository[Memory]):
    """Repository for memory management."""

    def __init__(self, session: AsyncSession):
        super().__init__(Memory, session)

    async def search_memories(
        self,
        query: str,
        memory_type: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> List[Memory]:
        """Search memories by content and filters."""
        filters = [Memory.importance >= min_importance]

        if memory_type:
            filters.append(Memory.memory_type == memory_type)
        if category:
            filters.append(Memory.category == category)

        # Simple text search (enhance with full-text search in production)
        filters.append(
            or_(Memory.title.contains(query), Memory.description.contains(query))
        )

        result = await self.session.execute(
            select(Memory)
            .where(and_(*filters))
            .order_by(desc(Memory.importance), desc(Memory.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_related_memories(self, entity: str, limit: int = 5) -> List[Memory]:
        """Get memories related to a specific entity."""
        # For SQLite, we use JSON_EXTRACT function to search in JSON arrays
        from sqlalchemy import func, text

        result = await self.session.execute(
            select(Memory)
            .where(
                func.json_extract(Memory.related_entities, "$").like(f'%"{entity}"%')
            )
            .order_by(desc(Memory.importance), desc(Memory.last_accessed))
            .limit(limit)
        )
        return result.scalars().all()

    async def update_access(self, memory_id: int):
        """Update memory access tracking."""
        await self.session.execute(
            update(Memory)
            .where(Memory.id == memory_id)
            .values(
                access_count=Memory.access_count + 1, last_accessed=datetime.utcnow()
            )
        )
        await self.session.commit()


class InterviewRepository(BaseRepository[InterviewSession]):
    """Repository for interview session management."""

    def __init__(self, session: AsyncSession):
        super().__init__(InterviewSession, session)

    async def get_active_session(self, house_id: int) -> Optional[InterviewSession]:
        """Get the active interview session for a house."""
        result = await self.session.execute(
            select(InterviewSession)
            .where(
                and_(
                    InterviewSession.house_id == house_id,
                    InterviewSession.status == "active",
                )
            )
            .order_by(desc(InterviewSession.started_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def add_conversation_turn(
        self,
        session_id: int,
        speaker: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a conversation turn to the interview log."""
        session = await self.get(session_id)
        if session:
            conversation_turn = {
                "timestamp": datetime.utcnow().isoformat(),
                "speaker": speaker,
                "message": message,
                "metadata": metadata or {},
            }
            session.conversation_log.append(conversation_turn)
            await self.update(session_id, conversation_log=session.conversation_log)


class DeviceCandidateRepository(BaseRepository[DeviceCandidate]):
    """Repository for device candidate management."""

    def __init__(self, session: AsyncSession):
        super().__init__(DeviceCandidate, session)

    async def get_pending_candidates(
        self, interview_session_id: int
    ) -> List[DeviceCandidate]:
        """Get pending device candidates for an interview session."""
        result = await self.session.execute(
            select(DeviceCandidate)
            .where(
                and_(
                    DeviceCandidate.interview_session_id == interview_session_id,
                    DeviceCandidate.status == "pending",
                )
            )
            .order_by(desc(DeviceCandidate.confidence_score))
        )
        return result.scalars().all()

    async def confirm_candidate(
        self, candidate_id: int, device_id: int
    ) -> Optional[DeviceCandidate]:
        """Confirm a device candidate and link to created device."""
        return await self.update(
            candidate_id, status="confirmed", created_device_id=device_id
        )


class DeviceRepository(BaseRepository[Device]):
    """Repository for dynamic device management."""

    def __init__(self, session: AsyncSession):
        super().__init__(Device, session)

    async def search_by_description(
        self, house_id: int, search_terms: List[str], limit: int = 10
    ) -> List[Device]:
        """Search devices by description keywords."""
        filters = [Device.house_id == house_id]

        # Build OR conditions for search terms
        search_conditions = []
        for term in search_terms:
            search_conditions.extend(
                [
                    Device.user_name.ilike(f"%{term}%"),
                    Device.user_description.ilike(f"%{term}%"),
                    Device.detected_brand.ilike(f"%{term}%"),
                    Device.detected_model.ilike(f"%{term}%"),
                ]
            )

        if search_conditions:
            filters.append(or_(*search_conditions))

        result = await self.session.execute(
            select(Device).where(and_(*filters)).order_by(Device.user_name).limit(limit)
        )
        return result.scalars().all()

    async def get_by_integration_type(
        self, house_id: int, integration_type: str
    ) -> List[Device]:
        """Get all devices of a specific integration type."""
        result = await self.session.execute(
            select(Device)
            .where(
                and_(
                    Device.house_id == house_id,
                    Device.integration_type == integration_type,
                )
            )
            .order_by(Device.user_name)
        )
        return result.scalars().all()
