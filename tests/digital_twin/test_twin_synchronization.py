"""
Digital Twin Synchronization Testing
Tests the bidirectional synchronization between physical devices and their digital twins.
"""
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.digital_twin.synchronization import SynchronizationEngine
from consciousness.digital_twin.twin_manager import DigitalTwinManager
from consciousness.digital_twin.twin_model import DeviceTwin
from consciousness.models.entities import Device


@pytest.fixture
async def twin_manager():
    """Create digital twin manager for testing."""
    mock_session = AsyncMock()
    manager = DigitalTwinManager(mock_session)
    await manager.initialize()
    return manager


@pytest.fixture
async def mock_physical_device():
    """Create mock physical device."""
    device = Device(
        id="device_001",
        name="Smart Thermostat",
        device_type="thermostat",
        location="living_room",
        capabilities=["temperature_control", "scheduling", "energy_monitoring"],
        status="online",
    )

    # Mock device interface
    device.interface = AsyncMock()
    device.interface.get_state = AsyncMock(
        return_value={
            "temperature": 22.0,
            "target_temperature": 21.0,
            "mode": "cooling",
            "fan_speed": "auto",
            "energy_usage": 150.0,
            "last_update": datetime.now().isoformat(),
        }
    )

    device.interface.set_state = AsyncMock(return_value={"success": True})
    return device


@pytest.fixture
async def device_twin(twin_manager, mock_physical_device):
    """Create device twin for testing."""
    twin = await twin_manager.create_twin(mock_physical_device, fidelity="advanced")
    return twin


@pytest.mark.asyncio
async def test_twin_creation_from_physical_device(twin_manager, mock_physical_device):
    """Test creating a digital twin from a physical device."""
    twin = await twin_manager.create_twin(mock_physical_device, fidelity="advanced")

    assert twin.device_id == mock_physical_device.id
    assert twin.device_type == mock_physical_device.device_type
    assert twin.capabilities == mock_physical_device.capabilities
    assert twin.fidelity_level == "advanced"
    assert twin.is_active is True


@pytest.mark.asyncio
async def test_device_to_twin_synchronization(device_twin, mock_physical_device):
    """Test synchronization from physical device to digital twin."""
    # Update physical device state
    new_state = {
        "temperature": 23.5,
        "target_temperature": 22.0,
        "mode": "heating",
        "fan_speed": "high",
        "energy_usage": 200.0,
    }
    mock_physical_device.interface.get_state.return_value = new_state

    # Trigger synchronization
    sync_result = await device_twin.sync_from_device()

    assert sync_result.success is True
    assert device_twin.current_state["temperature"] == 23.5
    assert device_twin.current_state["mode"] == "heating"
    assert device_twin.last_sync_time is not None
    assert device_twin.sync_latency < 100  # Less than 100ms


@pytest.mark.asyncio
async def test_twin_to_device_synchronization(device_twin, mock_physical_device):
    """Test synchronization from digital twin to physical device."""
    # Update twin state
    twin_changes = {
        "target_temperature": 20.0,
        "mode": "cooling",
        "fan_speed": "medium",
    }

    # Apply changes to twin
    update_result = await device_twin.update_state(twin_changes)

    assert update_result.safe is True
    assert update_result.validation_passed is True

    # Sync to physical device
    sync_result = await device_twin.sync_to_device()

    assert sync_result.success is True
    mock_physical_device.interface.set_state.assert_called_once()

    # Verify the correct state was sent to device
    call_args = mock_physical_device.interface.set_state.call_args[0][0]
    assert call_args["target_temperature"] == 20.0
    assert call_args["mode"] == "cooling"


@pytest.mark.asyncio
async def test_bidirectional_synchronization_conflict_resolution(
    device_twin, mock_physical_device
):
    """Test conflict resolution when both device and twin are modified simultaneously."""
    # Simulate simultaneous changes
    device_state = {
        "target_temperature": 19.0,
        "mode": "cooling",
        "timestamp": datetime.now().isoformat(),
    }

    twin_state = {
        "target_temperature": 24.0,
        "mode": "heating",
        "timestamp": (
            datetime.now() - timedelta(seconds=5)
        ).isoformat(),  # Older change
    }

    # Mock device returns newer state
    mock_physical_device.interface.get_state.return_value = device_state

    # Set conflicting twin state
    await device_twin.update_state_internal(twin_state)

    # Trigger conflict resolution
    sync_engine = SynchronizationEngine()
    resolution = await sync_engine.resolve_conflict(device_twin, mock_physical_device)

    # Device should win (newer timestamp)
    assert resolution.strategy == "device_wins"
    assert resolution.final_state["target_temperature"] == 19.0
    assert resolution.final_state["mode"] == "cooling"


@pytest.mark.asyncio
async def test_high_frequency_synchronization_performance(
    device_twin, mock_physical_device
):
    """Test performance under high-frequency synchronization."""
    sync_count = 50
    latencies = []

    for i in range(sync_count):
        # Vary device state
        state = {
            "temperature": 20.0 + (i * 0.1),
            "energy_usage": 150.0 + (i * 2),
            "timestamp": datetime.now().isoformat(),
        }
        mock_physical_device.interface.get_state.return_value = state

        # Measure sync latency
        start_time = asyncio.get_event_loop().time()
        sync_result = await device_twin.sync_from_device()
        end_time = asyncio.get_event_loop().time()

        latency_ms = (end_time - start_time) * 1000
        latencies.append(latency_ms)

        assert sync_result.success is True

        # Small delay to prevent overwhelming
        await asyncio.sleep(0.01)

    # Performance assertions
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    assert avg_latency < 50  # Average under 50ms
    assert max_latency < 200  # Max under 200ms
    assert all(l < 500 for l in latencies)  # No sync over 500ms


@pytest.mark.asyncio
async def test_synchronization_data_integrity(device_twin, mock_physical_device):
    """Test data integrity during synchronization."""
    # Test various data types and edge cases
    test_states = [
        {
            "temperature": 21.5,
            "target_temperature": 22.0,
            "mode": "auto",
            "schedule": [
                {"time": "06:00", "temperature": 20.0},
                {"time": "22:00", "temperature": 18.0},
            ],
            "energy_usage": 175.5,
            "last_maintenance": "2024-01-15T10:30:00Z",
            "firmware_version": "v2.1.3",
        },
        {
            "temperature": None,  # Sensor failure
            "target_temperature": 23.0,
            "mode": "heating",
            "error_codes": ["E001", "E003"],
            "energy_usage": 0.0,  # Device offline
        },
    ]

    for test_state in test_states:
        mock_physical_device.interface.get_state.return_value = test_state

        sync_result = await device_twin.sync_from_device()

        if test_state["temperature"] is None:
            # Should handle missing data gracefully
            assert (
                device_twin.current_state.get("temperature")
                != test_state["temperature"]
            )
            assert "sensor_failure" in device_twin.diagnostics
        else:
            # Should preserve data accuracy
            assert device_twin.current_state["temperature"] == test_state["temperature"]
            assert device_twin.current_state["schedule"] == test_state["schedule"]


@pytest.mark.asyncio
async def test_safety_constraint_validation(device_twin, mock_physical_device):
    """Test safety constraints prevent unsafe synchronization."""
    # Define safety constraints for thermostat
    safety_constraints = {
        "temperature_range": {"min": 10.0, "max": 35.0},
        "max_temperature_change_per_hour": 5.0,
        "energy_limit": 500.0,
        "maintenance_mode_restrictions": True,
    }

    device_twin.safety_constraints = safety_constraints

    # Test unsafe temperature setting
    unsafe_changes = {"target_temperature": 40.0, "mode": "heating"}  # Above max

    update_result = await device_twin.update_state(unsafe_changes)

    assert update_result.safe is False
    assert "temperature_range" in update_result.constraint_violations
    assert update_result.suggested_alternative is not None
    assert update_result.suggested_alternative["target_temperature"] <= 35.0

    # Test rapid temperature change
    current_time = datetime.now()
    device_twin.state_history = [
        {"target_temperature": 20.0, "timestamp": current_time - timedelta(minutes=30)}
    ]

    rapid_change = {
        "target_temperature": 28.0,  # 8 degree change in 30 minutes
        "mode": "heating",
    }

    update_result = await device_twin.update_state(rapid_change)

    assert update_result.safe is False
    assert "max_temperature_change_per_hour" in update_result.constraint_violations


@pytest.mark.asyncio
async def test_twin_state_prediction(device_twin, mock_physical_device):
    """Test digital twin's ability to predict future states."""
    # Provide historical state data
    historical_states = [
        {
            "temperature": 20.0,
            "energy_usage": 100.0,
            "timestamp": datetime.now() - timedelta(hours=3),
        },
        {
            "temperature": 21.0,
            "energy_usage": 120.0,
            "timestamp": datetime.now() - timedelta(hours=2),
        },
        {
            "temperature": 22.0,
            "energy_usage": 140.0,
            "timestamp": datetime.now() - timedelta(hours=1),
        },
        {"temperature": 23.0, "energy_usage": 160.0, "timestamp": datetime.now()},
    ]

    device_twin.state_history = historical_states

    # Predict next hour state
    prediction = await device_twin.predict_future_state(horizon_minutes=60)

    assert prediction.confidence > 0.6
    assert (
        prediction.predicted_state["temperature"] > 23.0
    )  # Should predict continued warming
    assert (
        prediction.predicted_state["energy_usage"] > 160.0
    )  # Should predict higher usage
    assert "temperature_trend" in prediction.metadata
    assert prediction.metadata["temperature_trend"] == "increasing"


@pytest.mark.asyncio
async def test_multi_twin_synchronization_coordination(twin_manager):
    """Test coordination between multiple digital twins."""
    # Create multiple related devices
    devices = [
        Device(id="hvac_001", device_type="thermostat", location="living_room"),
        Device(
            id="temp_sensor_001",
            device_type="temperature_sensor",
            location="living_room",
        ),
        Device(
            id="humidity_sensor_001",
            device_type="humidity_sensor",
            location="living_room",
        ),
    ]

    # Mock device interfaces
    for device in devices:
        device.interface = AsyncMock()
        if device.device_type == "thermostat":
            device.interface.get_state.return_value = {
                "temperature": 22.0,
                "target_temperature": 21.0,
                "mode": "cooling",
            }
        elif device.device_type == "temperature_sensor":
            device.interface.get_state.return_value = {
                "temperature": 22.5,
                "accuracy": 0.1,
            }
        else:  # humidity sensor
            device.interface.get_state.return_value = {
                "humidity": 45.0,
                "temperature": 22.3,
            }

    # Create twins
    twins = []
    for device in devices:
        twin = await twin_manager.create_twin(device)
        twins.append(twin)

    # Coordinate synchronization
    coordination_result = await twin_manager.coordinate_synchronization(
        twins, sync_strategy="environmental_consistency"
    )

    assert coordination_result.success is True
    assert coordination_result.consistency_score > 0.8

    # Verify temperature consistency across twins
    hvac_twin = next(t for t in twins if t.device_type == "thermostat")
    temp_twin = next(t for t in twins if t.device_type == "temperature_sensor")

    temp_diff = abs(
        hvac_twin.current_state["temperature"] - temp_twin.current_state["temperature"]
    )
    assert temp_diff < 1.0  # Should be within 1 degree


@pytest.mark.asyncio
async def test_synchronization_error_recovery(device_twin, mock_physical_device):
    """Test error recovery during synchronization failures."""
    # Simulate communication failure
    mock_physical_device.interface.get_state.side_effect = Exception(
        "Connection timeout"
    )

    # Attempt synchronization
    sync_result = await device_twin.sync_from_device()

    assert sync_result.success is False
    assert sync_result.error_type == "communication_error"
    assert device_twin.last_successful_sync is not None
    assert device_twin.sync_failures == 1

    # Test retry mechanism
    mock_physical_device.interface.get_state.side_effect = None
    mock_physical_device.interface.get_state.return_value = {
        "temperature": 21.0,
        "mode": "auto",
    }

    # Should retry and succeed
    retry_result = await device_twin.retry_synchronization()

    assert retry_result.success is True
    assert device_twin.sync_failures == 0
    assert device_twin.current_state["temperature"] == 21.0


@pytest.mark.asyncio
async def test_synchronization_bandwidth_optimization(
    device_twin, mock_physical_device
):
    """Test bandwidth optimization through selective synchronization."""
    # Enable delta synchronization
    device_twin.sync_mode = "delta_only"

    # Initial state
    initial_state = {
        "temperature": 22.0,
        "target_temperature": 21.0,
        "mode": "cooling",
        "fan_speed": "auto",
        "energy_usage": 150.0,
        "schedule": [{"time": "06:00", "temp": 20.0}],
    }
    mock_physical_device.interface.get_state.return_value = initial_state
    await device_twin.sync_from_device()

    # Minor change (only temperature)
    changed_state = initial_state.copy()
    changed_state["temperature"] = 22.2
    mock_physical_device.interface.get_state.return_value = changed_state

    sync_result = await device_twin.sync_from_device()

    assert sync_result.success is True
    assert sync_result.delta_size < sync_result.full_state_size
    assert sync_result.bandwidth_saved > 0.7  # Should save significant bandwidth
    assert device_twin.current_state["temperature"] == 22.2
    assert (
        device_twin.current_state["schedule"] == initial_state["schedule"]
    )  # Unchanged data preserved


@pytest.mark.asyncio
async def test_synchronization_event_triggers(device_twin, mock_physical_device):
    """Test event-driven synchronization triggers."""
    # Set up event handlers
    sync_events = []

    async def on_sync_event(event_type, data):
        sync_events.append(
            {"type": event_type, "data": data, "timestamp": datetime.now()}
        )

    device_twin.add_sync_event_handler(on_sync_event)

    # Trigger significant state change
    significant_change = {
        "temperature": 25.0,  # 3 degree change
        "mode": "emergency_cooling",
        "alert": "high_temperature_detected",
    }
    mock_physical_device.interface.get_state.return_value = significant_change

    sync_result = await device_twin.sync_from_device()

    # Should trigger events
    assert len(sync_events) >= 2  # sync_start, sync_complete
    assert any(event["type"] == "significant_change_detected" for event in sync_events)
    assert any(event["type"] == "alert_triggered" for event in sync_events)

    # Verify event data
    change_event = next(
        event for event in sync_events if event["type"] == "significant_change_detected"
    )
    assert change_event["data"]["temperature_delta"] >= 3.0
    assert change_event["data"]["mode_change"] is True
