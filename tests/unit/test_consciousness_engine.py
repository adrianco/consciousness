"""
Comprehensive test suite for the consciousness engine.
Tests all consciousness components integration and functionality.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.core.emotion_processor import EmotionProcessor
from consciousness.core.query_engine import QueryEngine


@pytest.fixture
async def consciousness_engine():
    """Create consciousness engine for testing."""
    engine = ConsciousnessEngine()

    # Mock the database session to avoid actual database calls
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        await engine.initialize()
        yield engine
        await engine.stop()


@pytest.mark.asyncio
async def test_consciousness_initialization(consciousness_engine):
    """Test consciousness engine initialization."""
    assert consciousness_engine.is_active
    assert consciousness_engine.session_id is not None
    assert consciousness_engine.emotion_processor is not None
    assert consciousness_engine.query_engine is not None


@pytest.mark.asyncio
async def test_consciousness_engine_lifecycle():
    """Test complete lifecycle of consciousness engine."""
    engine = ConsciousnessEngine()

    # Test initial state
    assert not engine.is_active
    assert engine.session_id is None

    # Mock database session
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        # Test initialization
        await engine.initialize()
        assert engine.is_active
        assert engine.session_id is not None

        # Test stop
        await engine.stop()
        assert not engine.is_active
        assert engine.session_id is None


@pytest.mark.asyncio
async def test_emotional_state_processing():
    """Test emotional state processing."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)

        processor = EmotionProcessor(mock_session)

        # Mock all the methods that are called in process_current_emotions
        processor._gather_emotional_factors = AsyncMock(
            return_value={
                "system_health": {"score": 0.8},
                "user_interaction": {"satisfaction": 0.7, "interaction_frequency": 0.5},
                "environmental": {"overall_score": 0.6},
                "task_completion": {"completion_rate": 0.9, "task_load": 0.4},
                "learning_progress": {
                    "improvement_score": 0.6,
                    "learning_activity": 0.3,
                },
            }
        )

        # Mock emotional score calculation
        processor._calculate_emotions = AsyncMock(
            return_value={
                "happiness": 0.7,
                "worry": 0.2,
                "boredom": 0.3,
                "excitement": 0.5,
            }
        )

        # Mock state transitions
        processor._apply_state_transitions = AsyncMock(
            return_value={
                "happiness": 0.7,
                "worry": 0.2,
                "boredom": 0.3,
                "excitement": 0.5,
            }
        )

        # Mock primary emotion determination
        processor._determine_primary_emotion = MagicMock(
            return_value=("happiness", 0.7)
        )

        # Mock reasoning generation
        processor._generate_emotional_reasoning = MagicMock(
            return_value="All systems are running smoothly"
        )

        # Mock repository
        mock_state = MagicMock()
        mock_state.id = 1
        mock_state.happiness = 0.7
        mock_state.worry = 0.2
        mock_state.boredom = 0.3
        mock_state.excitement = 0.5

        processor.repository.create = AsyncMock(return_value=mock_state)

        result = await processor.process_current_emotions()

        assert "happiness" in result
        assert "primary_emotion" in result
        assert "reasoning" in result
        assert result["happiness"] > 0.5  # Should be happy with good system health
        assert (
            result["primary_emotion"] == "happiness"
        )  # Highest score should be happiness


@pytest.mark.asyncio
async def test_emotional_score_calculation():
    """Test emotional score calculation algorithms."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        processor = EmotionProcessor(mock_session)

        # Test high system health scenario
        factors = {
            "system_health": {"score": 0.9},
            "user_interaction": {"satisfaction": 0.8, "interaction_frequency": 0.7},
            "environmental": {"overall_score": 0.7},
            "task_completion": {"completion_rate": 0.95, "task_load": 0.3},
            "learning_progress": {"improvement_score": 0.8, "learning_activity": 0.6},
        }

        # Test the actual calculation method from the real implementation
        scores = await processor._calculate_emotions(factors)

        # Verify the scores are reasonable (not exact since the algorithm is complex)
        assert isinstance(scores, dict)
        assert "happiness" in scores
        assert "worry" in scores
        assert "boredom" in scores
        assert "excitement" in scores

        # Verify scores are in valid range
        for emotion, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{emotion} score {score} out of range"


@pytest.mark.asyncio
async def test_emotional_primary_emotion_detection():
    """Test primary emotion detection logic."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        processor = EmotionProcessor(mock_session)

        # Test happiness dominant
        scores = {"happiness": 0.8, "worry": 0.2, "boredom": 0.1, "excitement": 0.6}
        primary, intensity = processor._determine_primary_emotion(scores)
        assert primary == "happiness"
        assert 0.0 <= intensity <= 1.0

        # Test worry dominant
        scores = {"happiness": 0.3, "worry": 0.7, "boredom": 0.2, "excitement": 0.1}
        primary, intensity = processor._determine_primary_emotion(scores)
        assert primary == "worry"
        assert 0.0 <= intensity <= 1.0


@pytest.mark.asyncio
async def test_natural_language_query():
    """Test natural language query processing."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()

        engine = QueryEngine(mock_session)

        # Mock emotional state
        mock_state = MagicMock()
        mock_state.primary_emotion = "happy"
        mock_state.intensity = 0.8
        mock_state.happiness = 0.8
        mock_state.worry = 0.1
        mock_state.boredom = 0.2
        mock_state.excitement = 0.6
        mock_state.reasoning = "All systems are running smoothly"

        engine.emotion_repo.get_current_state = AsyncMock(return_value=mock_state)

        response = await engine.process_query("How are you feeling?")

        assert response["query_type"] == "emotional_state"
        assert "happy" in response["response"].lower()
        assert "feeling" in response["response"].lower()


@pytest.mark.asyncio
async def test_query_classification():
    """Test query classification logic."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        engine = QueryEngine(mock_session)

        # Test emotional queries (convert to lowercase like the actual system does)
        assert engine._classify_query("how are you feeling?") == "emotional_state"
        assert engine._classify_query("what's your mood?") == "emotional_state"
        assert engine._classify_query("are you happy?") == "emotional_state"

        # Test status queries
        assert engine._classify_query("what's your status?") == "status"
        assert engine._classify_query("how are you doing?") == "status"
        assert engine._classify_query("system health check") == "status"

        # Test device queries
        assert engine._classify_query("turn on the lights") == "devices"
        assert engine._classify_query("what's the temperature?") == "devices"

        # Test general queries
        assert engine._classify_query("hello there") == "general"
        assert engine._classify_query("what can you do?") == "general"


@pytest.mark.asyncio
async def test_consciousness_loop_integration():
    """Test the main consciousness processing loop."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        engine = ConsciousnessEngine()
        await engine.initialize()

        # Mock emotion processing
        mock_emotional_state = {
            "happiness": 0.7,
            "worry": 0.2,
            "boredom": 0.1,
            "excitement": 0.6,
            "primary_emotion": "happiness",
            "reasoning": "Test reasoning",
            "intensity": 0.7,
        }

        engine.emotion_processor.process_current_emotions = AsyncMock(
            return_value=mock_emotional_state
        )

        # Test consciousness loop
        result = await engine.process_consciousness_loop()

        assert result == mock_emotional_state
        assert engine.query_engine.emotional_context == mock_emotional_state

        await engine.stop()


@pytest.mark.asyncio
async def test_consciousness_query_handling():
    """Test end-to-end query handling through consciousness engine."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        engine = ConsciousnessEngine()
        await engine.initialize()

        # Mock query processing
        mock_response = {
            "query": "How are you?",
            "query_type": "emotional_state",
            "response": "I am feeling happy right now",
            "emotional_context": {"happiness": 0.8},
        }

        engine.query_engine.process_query = AsyncMock(return_value=mock_response)

        # Test query handling
        result = await engine.handle_query("How are you?")

        assert result["query"] == "How are you?"
        assert result["query_type"] == "emotional_state"
        assert "happy" in result["response"]

        await engine.stop()


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in consciousness components."""
    # Test engine initialization failure
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session_gen.side_effect = Exception("Database connection failed")

        engine = ConsciousnessEngine()

        with pytest.raises(
            RuntimeError, match="Failed to initialize consciousness engine"
        ):
            await engine.initialize()

    # Test processing with inactive engine
    engine = ConsciousnessEngine()

    with pytest.raises(RuntimeError, match="Consciousness engine not initialized"):
        await engine.process_consciousness_loop()

    with pytest.raises(RuntimeError, match="Consciousness engine not initialized"):
        await engine.handle_query("test query")


@pytest.mark.asyncio
async def test_emotional_reasoning_generation():
    """Test emotional reasoning generation."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        processor = EmotionProcessor(mock_session)

        factors = {
            "system_health": {"score": 0.9},
            "user_interaction": {"satisfaction": 0.8, "interaction_frequency": 0.7},
            "environmental": {"overall_score": 0.7},
            "task_completion": {"completion_rate": 0.95, "task_load": 0.3},
            "learning_progress": {"improvement_score": 0.8, "learning_activity": 0.6},
        }

        scores = {"happiness": 0.8, "worry": 0.1, "boredom": 0.2, "excitement": 0.7}

        # Use the actual method name from the implementation
        reasoning = processor._generate_emotional_reasoning(factors, scores)

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0


@pytest.mark.asyncio
async def test_integration_component_communication():
    """Test communication between consciousness components."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        engine = ConsciousnessEngine()
        await engine.initialize()

        # Test that emotional context is properly shared
        mock_emotional_state = {
            "happiness": 0.8,
            "primary_emotion": "happiness",
            "reasoning": "All systems running well",
        }

        # Update emotional context in query engine
        engine.query_engine.update_emotional_context(mock_emotional_state)

        assert engine.query_engine.emotional_context == mock_emotional_state

        await engine.stop()


@pytest.mark.asyncio
async def test_system_robustness():
    """Test system robustness and edge cases."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()

        # Test empty emotional factors
        processor = EmotionProcessor(mock_session)

        # Should handle empty factors gracefully
        try:
            scores = await processor._calculate_emotions({})
            # Should not crash, should return default scores
            assert isinstance(scores, dict)
            # Should have baseline emotional scores even with empty factors
            for emotion_name in ["happiness", "worry", "boredom", "excitement"]:
                assert emotion_name in scores
                assert 0.0 <= scores[emotion_name] <= 1.0
        except Exception as e:
            # If it fails, it should at least fail gracefully
            assert "factors" in str(e).lower()

        # Test query engine with None emotional state
        engine = QueryEngine(mock_session)
        engine.emotion_repo.get_current_state = AsyncMock(return_value=None)

        response = await engine._generate_emotional_response([], {})
        assert "learning" in response.lower() or "moment" in response.lower()


@pytest.mark.asyncio
async def test_performance_characteristics():
    """Test performance characteristics of consciousness components."""
    import time

    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        # Test engine initialization time
        start_time = time.time()
        engine = ConsciousnessEngine()
        await engine.initialize()
        initialization_time = time.time() - start_time

        # Should initialize quickly (less than 1 second)
        assert initialization_time < 1.0

        # Test consciousness loop processing time
        engine.emotion_processor.process_current_emotions = AsyncMock(
            return_value={"happiness": 0.7, "primary_emotion": "happiness"}
        )

        start_time = time.time()
        await engine.process_consciousness_loop()
        processing_time = time.time() - start_time

        # Should process quickly (less than 0.5 seconds)
        assert processing_time < 0.5

        await engine.stop()
