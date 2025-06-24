from datetime import datetime, timedelta

import pytest

from consciousness.database import drop_db, get_async_session, init_db
from consciousness.models.consciousness import EmotionalState, Memory
from consciousness.models.entities import Device, House
from consciousness.models.interview import DeviceCandidate, InterviewSession
from consciousness.repositories.consciousness import EmotionalStateRepository


@pytest.fixture
async def db_session():
    """Create test database session."""
    await init_db()
    async for session in get_async_session():
        yield session
        break
    await drop_db()


@pytest.fixture
async def test_house(db_session):
    """Create test house."""
    house = House(name="Test House", timezone="America/New_York")
    db_session.add(house)
    await db_session.commit()
    await db_session.refresh(house)
    return house


@pytest.mark.asyncio
async def test_emotional_state_creation(db_session):
    """Test emotional state creation and retrieval."""
    repo = EmotionalStateRepository(db_session)

    state = await repo.create(
        happiness=0.8,
        worry=0.2,
        boredom=0.1,
        excitement=0.7,
        primary_emotion="happy",
        intensity=0.8,
        confidence=0.9,
        trigger_event="user_returned_home",
    )

    assert state.id is not None
    assert state.primary_emotion == "happy"
    assert state.happiness == 0.8

    # Test retrieval
    retrieved = await repo.get_current_state()
    assert retrieved.id == state.id


@pytest.mark.asyncio
async def test_house_creation(db_session):
    """Test house creation and properties."""
    house = House(
        name="Test Smart Home",
        address="123 Main St",
        square_footage=2000.0,
        num_rooms=4,
        timezone="UTC",
        preferences={"temperature": 72, "lighting": "auto"},
    )

    db_session.add(house)
    await db_session.commit()
    await db_session.refresh(house)

    assert house.id is not None
    assert house.name == "Test Smart Home"
    assert house.preferences["temperature"] == 72


@pytest.mark.asyncio
async def test_device_dynamic_schema(db_session, test_house):
    """Test dynamic device creation with flexible schema."""
    from consciousness.repositories.consciousness import DeviceRepository

    repo = DeviceRepository(db_session)

    # Create device with dynamic typing
    device = await repo.create(
        house_id=test_house.id,
        user_name="Living room lights",
        user_description="Philips Hue color bulbs above the couch",
        detected_brand="Philips",
        detected_model="Hue Color Bulb A19",
        integration_type="hue",
        device_class="light",
        supported_features=["brightness", "color", "effects"],
        discovery_method="interview",
        discovery_confidence=0.95,
    )

    assert device.integration_type == "hue"
    assert device.device_class == "light"
    assert "brightness" in device.supported_features

    # Test search functionality
    results = await repo.search_by_description(test_house.id, ["philips", "lights"])
    assert len(results) == 1
    assert results[0].id == device.id


@pytest.mark.asyncio
async def test_memory_operations(db_session):
    """Test memory creation and search."""
    from consciousness.repositories.consciousness import MemoryRepository

    repo = MemoryRepository(db_session)

    # Create memory
    memory = await repo.create(
        memory_type="episodic",
        category="user_interaction",
        importance=0.8,
        title="User changed temperature",
        description="User adjusted thermostat to 72 degrees F in the evening",
        content={"action": "thermostat_change", "value": 72, "time": "evening"},
        source="user_interaction",
        confidence=0.9,
        tags=["temperature", "user", "evening"],
        related_entities=["thermostat", "living_room"],
    )

    assert memory.id is not None
    assert memory.memory_type == "episodic"
    assert memory.importance == 0.8

    # Test search
    results = await repo.search_memories("temperature")
    assert len(results) == 1
    assert results[0].id == memory.id

    # Test related entity search
    related = await repo.get_related_memories("thermostat")
    assert len(related) == 1
    assert related[0].id == memory.id
