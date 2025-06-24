"""Test configuration and fixtures."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.core.emotion_processor import EmotionProcessor
from consciousness.core.query_engine import QueryEngine


@pytest.fixture
async def mock_async_session():
    """Create a mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
async def mock_async_session_generator(mock_async_session):
    """Create a mock async session generator."""

    async def _get_session():
        yield mock_async_session

    return _get_session


@pytest.fixture
async def consciousness_engine_with_mocks(mock_async_session_generator):
    """Create consciousness engine with properly mocked dependencies."""
    with patch(
        "consciousness.database.get_async_session", mock_async_session_generator
    ):
        engine = ConsciousnessEngine()
        # Don't create session_id until initialized
        engine.session_id = None
        await engine.initialize()
        yield engine
        await engine.stop()


@pytest.fixture
def mock_emotion_processor(mock_async_session):
    """Create a mock emotion processor."""
    processor = EmotionProcessor(mock_async_session)
    processor._gather_emotional_factors = AsyncMock(
        return_value={
            "system_health": {"score": 0.8},
            "user_interaction": {"satisfaction": 0.7, "interaction_frequency": 0.5},
            "environmental": {"overall_score": 0.6},
            "task_completion": {"completion_rate": 0.9, "task_load": 0.4},
            "learning_progress": {"improvement_score": 0.6, "learning_activity": 0.3},
        }
    )
    return processor
