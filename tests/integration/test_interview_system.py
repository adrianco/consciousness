"""
Integration tests for the interview system and auto-discovery components.
Tests the complete device discovery and interview flow.
"""
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.discovery.auto_discovery import AutoDiscoveryService
from consciousness.interview.device_classifier import DeviceClassifier
from consciousness.interview.interview_controller import InterviewController
from consciousness.models.entities import House
from consciousness.models.interview import DeviceCandidate, InterviewSession


@pytest.fixture
async def interview_controller():
    """Create interview controller with mocked dependencies."""
    mock_session = AsyncMock()
    mock_llm_client = AsyncMock()
    mock_auto_discovery = AsyncMock()

    controller = InterviewController(mock_session, mock_llm_client, mock_auto_discovery)
    return controller


@pytest.fixture
async def device_classifier():
    """Create device classifier with mocked LLM."""
    mock_llm_client = AsyncMock()
    classifier = DeviceClassifier(mock_llm_client)
    return classifier


@pytest.fixture
async def auto_discovery_service():
    """Create auto-discovery service with mocked protocols."""
    service = AutoDiscoveryService()

    # Mock discovery protocols
    service.mdns_discovery = AsyncMock()
    service.upnp_discovery = AsyncMock()
    service.bluetooth_discovery = AsyncMock()
    service.zigbee_discovery = AsyncMock()

    return service


@pytest.fixture
async def test_house():
    """Create test house for interview sessions."""
    house = House(
        id="test_house_001", name="Test Smart Home", timezone="America/New_York"
    )
    return house


@pytest.mark.asyncio
async def test_interview_session_creation(interview_controller, test_house):
    """Test creating a new interview session."""
    # Mock database responses
    interview_controller.session.execute = AsyncMock()
    interview_controller.session.scalar = AsyncMock(
        return_value=None
    )  # No existing session

    mock_interview = InterviewSession(
        id=1,
        house_id=test_house.id,
        status="active",
        current_phase="introduction",
        created_at=datetime.now(),
    )

    interview_controller.session.merge = AsyncMock(return_value=mock_interview)
    interview_controller.session.commit = AsyncMock()

    # Start interview
    interview = await interview_controller.start_interview(test_house.id)

    assert interview.house_id == test_house.id
    assert interview.status == "active"
    assert interview.current_phase == "introduction"

    # Verify database operations
    interview_controller.session.merge.assert_called_once()
    interview_controller.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_device_mention_extraction(device_classifier):
    """Test extracting device mentions from natural language."""
    user_input = (
        "I have some Philips Hue lights in the living room and a Nest thermostat"
    )

    # Mock LLM response
    device_classifier.llm_client.generate_response = AsyncMock(
        return_value=json.dumps(
            [
                {
                    "description": "Philips Hue lights",
                    "brand": "Philips",
                    "product_line": "Hue",
                    "function": "lighting",
                    "location": "living room",
                    "keywords": ["philips", "hue", "lights"],
                    "confidence": 0.95,
                },
                {
                    "description": "Nest thermostat",
                    "brand": "Google/Nest",
                    "product_line": "Nest",
                    "function": "climate_control",
                    "location": "unspecified",
                    "keywords": ["nest", "thermostat"],
                    "confidence": 0.90,
                },
            ]
        )
    )

    mentions = await device_classifier.extract_device_mentions(user_input)

    assert len(mentions) == 2

    hue_mention = next(m for m in mentions if m["brand"] == "Philips")
    nest_mention = next(m for m in mentions if "Nest" in m["brand"])

    assert hue_mention["function"] == "lighting"
    assert hue_mention["location"] == "living room"
    assert hue_mention["confidence"] == 0.95

    assert nest_mention["function"] == "climate_control"
    assert nest_mention["confidence"] == 0.90


@pytest.mark.asyncio
async def test_auto_discovery_multi_protocol(auto_discovery_service):
    """Test auto-discovery across multiple protocols."""
    # Mock discovery results for different protocols
    auto_discovery_service.mdns_discovery.discover = AsyncMock(
        return_value=[
            {
                "name": "Philips Hue Bridge",
                "address": "192.168.1.100",
                "port": 80,
                "type": "_hue._tcp.local.",
                "properties": {"modelid": "BSB002", "version": "1.50.0"},
            }
        ]
    )

    auto_discovery_service.upnp_discovery.discover = AsyncMock(
        return_value=[
            {
                "name": "Samsung Smart TV",
                "address": "192.168.1.101",
                "device_type": "urn:samsung-com:device:RemoteControlReceiver:1",
                "model": "UN55TU8000",
            }
        ]
    )

    auto_discovery_service.bluetooth_discovery.discover = AsyncMock(
        return_value=[
            {
                "name": "Apple TV",
                "address": "AA:BB:CC:DD:EE:FF",
                "device_class": "7936",
                "rssi": -45,
            }
        ]
    )

    auto_discovery_service.zigbee_discovery.discover = AsyncMock(
        return_value=[
            {
                "name": "IKEA Outlet",
                "ieee_address": "0x0017880104e45520",
                "network_address": "0x1234",
                "model": "TRADFRI control outlet",
            }
        ]
    )

    # Run discovery across all protocols
    results = await auto_discovery_service.discover_all_protocols()

    assert "mdns" in results
    assert "upnp" in results
    assert "bluetooth" in results
    assert "zigbee" in results

    assert len(results["mdns"]) == 1
    assert results["mdns"][0]["name"] == "Philips Hue Bridge"

    assert len(results["upnp"]) == 1
    assert results["upnp"][0]["name"] == "Samsung Smart TV"

    assert len(results["bluetooth"]) == 1
    assert results["bluetooth"][0]["name"] == "Apple TV"

    assert len(results["zigbee"]) == 1
    assert results["zigbee"][0]["name"] == "IKEA Outlet"


@pytest.mark.asyncio
async def test_device_classification_and_discovery_correlation(
    interview_controller, device_classifier, auto_discovery_service
):
    """Test correlating user mentions with discovery results."""
    interview_id = 1
    user_message = "I have Philips Hue lights"

    # Mock interview session
    mock_session = InterviewSession(
        id=interview_id, house_id=1, status="active", current_phase="introduction"
    )

    interview_controller.session.get = AsyncMock(return_value=mock_session)
    interview_controller.device_classifier = device_classifier
    interview_controller.auto_discovery = auto_discovery_service

    # Mock device classification
    device_classifier.extract_device_mentions = AsyncMock(
        return_value=[
            {
                "description": "Philips Hue lights",
                "brand": "Philips",
                "function": "lighting",
                "keywords": ["philips", "hue", "lights"],
                "confidence": 0.95,
            }
        ]
    )

    device_classifier.match_integrations = AsyncMock(
        return_value=[
            {
                "integration": "hue",
                "score": 0.95,
                "requires_hub": True,
                "discovery_protocols": ["mdns"],
            }
        ]
    )

    # Mock auto-discovery
    auto_discovery_service.discover_for_integration = AsyncMock(
        return_value=[
            {
                "name": "Philips Hue Bridge",
                "address": "192.168.1.100",
                "type": "_hue._tcp.local.",
                "integration_match": "hue",
                "confidence": 0.90,
            }
        ]
    )

    # Mock candidate creation
    mock_candidate = DeviceCandidate(
        id=1,
        interview_session_id=interview_id,
        detected_brand="Philips",
        detected_function="lighting",
        confidence=0.95,
        auto_discovery_successful=True,
    )

    interview_controller.session.merge = AsyncMock(return_value=mock_candidate)
    interview_controller.session.commit = AsyncMock()

    # Process user message
    result = await interview_controller.process_user_message(interview_id, user_message)

    assert result["success"] is True
    assert result["phase"] == "classification"
    assert len(result["candidates"]) == 1

    candidate = result["candidates"][0]
    assert candidate["detected_brand"] == "Philips"
    assert candidate["detected_function"] == "lighting"
    assert candidate["auto_discovery_successful"] is True
    assert "auto_discovery_results" in candidate


@pytest.mark.asyncio
async def test_interview_flow_multiple_devices(interview_controller):
    """Test complete interview flow with multiple devices."""
    interview_id = 1
    house_id = 1

    # Mock interview session
    mock_session = InterviewSession(
        id=interview_id,
        house_id=house_id,
        status="active",
        current_phase="introduction",
    )
    interview_controller.session.get = AsyncMock(return_value=mock_session)

    # Phase 1: User mentions multiple devices
    user_input_1 = (
        "I have Philips Hue lights, a Nest thermostat, and some TP-Link smart plugs"
    )

    # Mock device extraction for multiple devices
    interview_controller.device_classifier.extract_device_mentions = AsyncMock(
        return_value=[
            {
                "description": "Philips Hue lights",
                "brand": "Philips",
                "function": "lighting",
                "confidence": 0.95,
            },
            {
                "description": "Nest thermostat",
                "brand": "Google/Nest",
                "function": "climate_control",
                "confidence": 0.90,
            },
            {
                "description": "TP-Link smart plugs",
                "brand": "TP-Link",
                "function": "power_control",
                "confidence": 0.85,
            },
        ]
    )

    # Mock integration matching
    interview_controller.device_classifier.match_integrations = AsyncMock(
        side_effect=[
            [{"integration": "hue", "score": 0.95}],
            [{"integration": "nest", "score": 0.90}],
            [{"integration": "tplink", "score": 0.85}],
        ]
    )

    # Mock auto-discovery results
    interview_controller.auto_discovery.discover_for_integration = AsyncMock(
        side_effect=[
            [{"name": "Philips Hue Bridge", "address": "192.168.1.100"}],
            [{"name": "Nest Thermostat", "address": "192.168.1.101"}],
            [{"name": "TP-Link Plug", "address": "192.168.1.102"}],
        ]
    )

    # Mock candidate creation
    candidates = [
        DeviceCandidate(
            id=i + 1,
            interview_session_id=interview_id,
            detected_brand=brand,
            detected_function=func,
        )
        for i, (brand, func) in enumerate(
            [
                ("Philips", "lighting"),
                ("Google/Nest", "climate_control"),
                ("TP-Link", "power_control"),
            ]
        )
    ]

    interview_controller.session.merge = AsyncMock(side_effect=candidates)
    interview_controller.session.commit = AsyncMock()

    # Process first message
    result_1 = await interview_controller.process_user_message(
        interview_id, user_input_1
    )

    assert result_1["success"] is True
    assert len(result_1["candidates"]) == 3
    assert result_1["phase"] == "classification"

    # Phase 2: User confirms devices
    confirmation_data = {
        "confirmed_candidates": [
            {"candidate_id": 1, "integration_type": "hue", "location": "living_room"},
            {"candidate_id": 2, "integration_type": "nest", "location": "main_floor"},
            {"candidate_id": 3, "integration_type": "tplink", "location": "kitchen"},
        ]
    }

    # Mock device creation
    from consciousness.models.entities import Device

    created_devices = [
        Device(id=f"device_{i+1}", name=f"Device {i+1}", device_type=dtype)
        for i, dtype in enumerate(["smart_light", "thermostat", "smart_plug"])
    ]

    interview_controller.session.merge = AsyncMock(side_effect=created_devices)

    confirmation_result = await interview_controller.confirm_devices(
        interview_id, confirmation_data
    )

    assert confirmation_result["success"] is True
    assert len(confirmation_result["created_devices"]) == 3
    assert confirmation_result["phase"] == "configuration"


@pytest.mark.asyncio
async def test_ambiguous_device_handling(interview_controller, device_classifier):
    """Test handling of ambiguous device descriptions."""
    interview_id = 1
    user_input = "I have some smart lights in the bedroom"

    # Mock session
    mock_session = InterviewSession(id=interview_id, house_id=1, status="active")
    interview_controller.session.get = AsyncMock(return_value=mock_session)
    interview_controller.device_classifier = device_classifier

    # Mock ambiguous device classification
    device_classifier.extract_device_mentions = AsyncMock(
        return_value=[
            {
                "description": "smart lights",
                "brand": None,  # Unknown brand
                "function": "lighting",
                "keywords": ["smart", "lights"],
                "confidence": 0.6,  # Lower confidence
                "ambiguous": True,
            }
        ]
    )

    # Mock multiple possible integrations
    device_classifier.match_integrations = AsyncMock(
        return_value=[
            {"integration": "hue", "score": 0.7, "likelihood": "possible"},
            {"integration": "lifx", "score": 0.65, "likelihood": "possible"},
            {"integration": "tplink", "score": 0.6, "likelihood": "possible"},
            {"integration": "tuya", "score": 0.55, "likelihood": "less_likely"},
        ]
    )

    # Mock discovery attempts for multiple integrations
    interview_controller.auto_discovery.discover_for_integration = AsyncMock(
        side_effect=[
            [],  # No Hue bridge found
            [{"name": "LIFX Bulb", "address": "192.168.1.103"}],  # LIFX found
            [],  # No TP-Link found
            [],  # No Tuya found
        ]
    )

    mock_candidate = DeviceCandidate(
        id=1,
        interview_session_id=interview_id,
        detected_brand=None,
        detected_function="lighting",
        confidence=0.6,
        requires_clarification=True,
    )

    interview_controller.session.merge = AsyncMock(return_value=mock_candidate)
    interview_controller.session.commit = AsyncMock()

    result = await interview_controller.process_user_message(interview_id, user_input)

    assert result["success"] is True
    assert result["requires_clarification"] is True
    assert len(result["possible_integrations"]) > 1
    assert result["clarification_question"] is not None
    assert "which brand" in result["clarification_question"].lower()


@pytest.mark.asyncio
async def test_discovery_failure_handling(auto_discovery_service):
    """Test handling of discovery failures gracefully."""
    # Mock network/protocol failures
    auto_discovery_service.mdns_discovery.discover = AsyncMock(
        side_effect=Exception("Network timeout")
    )
    auto_discovery_service.upnp_discovery.discover = AsyncMock(
        return_value=[]
    )  # No devices
    auto_discovery_service.bluetooth_discovery.discover = AsyncMock(
        side_effect=Exception("Bluetooth adapter not found")
    )
    auto_discovery_service.zigbee_discovery.discover = AsyncMock(
        return_value=[{"name": "Zigbee Device", "address": "0x1234"}]
    )

    results = await auto_discovery_service.discover_all_protocols()

    # Should handle failures gracefully
    assert "mdns" in results
    assert "upnp" in results
    assert "bluetooth" in results
    assert "zigbee" in results

    # Failed protocols should return empty lists
    assert results["mdns"] == []
    assert results["upnp"] == []
    assert results["bluetooth"] == []

    # Working protocol should return results
    assert len(results["zigbee"]) == 1
    assert results["zigbee"][0]["name"] == "Zigbee Device"


@pytest.mark.asyncio
async def test_interview_session_recovery(interview_controller):
    """Test recovery of interrupted interview sessions."""
    house_id = 1

    # Mock existing incomplete session
    existing_session = InterviewSession(
        id=1,
        house_id=house_id,
        status="active",
        current_phase="classification",
        created_at=datetime.now(),
    )

    interview_controller.session.scalar = AsyncMock(return_value=existing_session)

    # Mock existing candidates
    existing_candidates = [
        DeviceCandidate(
            id=1,
            interview_session_id=1,
            detected_brand="Philips",
            detected_function="lighting",
            status="pending_confirmation",
        )
    ]

    interview_controller.session.execute = AsyncMock()
    interview_controller.session.scalars = AsyncMock(return_value=existing_candidates)

    # Start interview (should recover existing session)
    recovered_session = await interview_controller.start_interview(house_id)

    assert recovered_session.id == existing_session.id
    assert recovered_session.status == "active"
    assert recovered_session.current_phase == "classification"

    # Get session status with existing candidates
    status = await interview_controller.get_interview_status(1)

    assert status["interview_id"] == 1
    assert status["phase"] == "classification"
    assert len(status["pending_candidates"]) == 1
    assert status["pending_candidates"][0]["detected_brand"] == "Philips"


@pytest.mark.asyncio
async def test_interview_completion_flow(interview_controller):
    """Test complete interview session from start to finish."""
    house_id = 1

    # Start new interview
    interview_controller.session.scalar = AsyncMock(
        return_value=None
    )  # No existing session

    new_session = InterviewSession(
        id=1, house_id=house_id, status="active", current_phase="introduction"
    )
    interview_controller.session.merge = AsyncMock(return_value=new_session)
    interview_controller.session.commit = AsyncMock()

    # Step 1: Start interview
    session = await interview_controller.start_interview(house_id)
    assert session.current_phase == "introduction"

    # Step 2: Process device mentions
    new_session.current_phase = "classification"
    interview_controller.device_classifier.extract_device_mentions = AsyncMock(
        return_value=[
            {
                "description": "Hue lights",
                "brand": "Philips",
                "function": "lighting",
                "confidence": 0.9,
            }
        ]
    )
    interview_controller.device_classifier.match_integrations = AsyncMock(
        return_value=[{"integration": "hue", "score": 0.9}]
    )
    interview_controller.auto_discovery.discover_for_integration = AsyncMock(
        return_value=[{"name": "Hue Bridge", "address": "192.168.1.100"}]
    )

    candidate = DeviceCandidate(id=1, interview_session_id=1, detected_brand="Philips")
    interview_controller.session.merge = AsyncMock(return_value=candidate)

    classification_result = await interview_controller.process_user_message(
        1, "I have Hue lights"
    )
    assert classification_result["phase"] == "classification"

    # Step 3: Confirm devices
    new_session.current_phase = "configuration"
    from consciousness.models.entities import Device

    device = Device(id="device_1", name="Hue Lights", device_type="smart_light")
    interview_controller.session.merge = AsyncMock(return_value=device)

    confirmation_result = await interview_controller.confirm_devices(
        1, {"confirmed_candidates": [{"candidate_id": 1, "integration_type": "hue"}]}
    )
    assert confirmation_result["phase"] == "configuration"

    # Step 4: Complete interview
    new_session.status = "completed"
    new_session.current_phase = "completed"

    completion_result = await interview_controller.complete_interview(1)
    assert completion_result["status"] == "completed"
    assert completion_result["total_devices_added"] > 0
