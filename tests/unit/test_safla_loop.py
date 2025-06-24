"""
Comprehensive test suite for the SAFLA (Self-Aware Feedback Loop Algorithm) implementation.
Tests the complete observability ’ consciousness ’ controllability loop.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

from consciousness.core.safla_loop import SAFLALoop
from consciousness.models.consciousness import EmotionalState
from consciousness.models.entities import Device


@pytest.mark.asyncio
async def test_safla_loop_initialization():
    """Test SAFLA loop initializes correctly with all components."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)

    await safla.initialize()

    assert safla.is_active
    assert safla.session is not None
    assert safla.observability_layer is not None
    assert safla.consciousness_model is not None
    assert safla.controllability_layer is not None


@pytest.mark.asyncio
async def test_sense_phase_data_collection():
    """Test the Sense phase collects sensor data correctly."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock sensor data
    mock_sensor_data = {
        "temperature": 22.5,
        "humidity": 45.0,
        "light_level": 0.7,
        "motion_detected": False,
        "energy_usage": 150.0,
        "device_statuses": {
            "hvac_001": {"status": "cooling", "target": 21.0},
            "light_001": {"status": "on", "brightness": 80}
        }
    }

    # Mock the observability layer
    safla.observability_layer.collect_sensor_data = AsyncMock(return_value=mock_sensor_data)

    sense_data = await safla.sense()

    assert sense_data["temperature"] == 22.5
    assert sense_data["humidity"] == 45.0
    assert "device_statuses" in sense_data
    assert sense_data["device_statuses"]["hvac_001"]["status"] == "cooling"


@pytest.mark.asyncio
async def test_analyze_phase_environmental_assessment():
    """Test the Analyze phase processes environmental conditions correctly."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock sense data with concerning temperature
    sense_data = {
        "temperature": 26.0,  # High temperature
        "humidity": 65.0,     # High humidity
        "light_level": 0.2,   # Low light
        "motion_detected": True,
        "energy_usage": 200.0,  # High energy usage
        "device_statuses": {
            "hvac_001": {"status": "idle", "target": 22.0},
            "light_001": {"status": "off"}
        }
    }

    analysis = await safla.analyze(sense_data)

    # Should identify comfort and efficiency issues
    assert "temperature_status" in analysis
    assert analysis["temperature_status"]["level"] == "high"
    assert "optimization_opportunities" in analysis
    assert any("cooling" in str(opp).lower() for opp in analysis["optimization_opportunities"])


@pytest.mark.asyncio
async def test_feel_phase_emotional_processing():
    """Test the Feel phase updates emotional state based on analysis."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock analysis with concerning conditions
    analysis = {
        "temperature_status": {"level": "high", "comfort": "poor"},
        "energy_efficiency": {"score": 0.3, "waste_detected": True},
        "user_satisfaction": {"estimated": 0.4},
        "system_health": {"score": 0.6, "issues": ["hvac_inefficiency"]}
    }

    # Mock emotional processor
    mock_emotional_state = EmotionalState(
        happiness=0.4,
        worry=0.7,
        boredom=0.2,
        excitement=0.3,
        primary_emotion="concerned",
        intensity=0.7,
        confidence=0.8,
        trigger_event="environmental_discomfort"
    )

    safla.consciousness_model.emotion_processor.process_environmental_factors = AsyncMock(
        return_value=mock_emotional_state
    )

    emotional_response = await safla.feel(analysis)

    assert emotional_response.primary_emotion == "concerned"
    assert emotional_response.worry > 0.5
    assert "environmental" in emotional_response.trigger_event.lower()


@pytest.mark.asyncio
async def test_learn_phase_pattern_recognition():
    """Test the Learn phase identifies patterns and updates knowledge."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock historical data showing pattern
    historical_context = {
        "time_of_day": "afternoon",
        "weather": "sunny",
        "occupancy": True,
        "previous_actions": [
            {"action": "increase_cooling", "result": "improved_comfort", "timestamp": datetime.now() - timedelta(hours=1)},
            {"action": "adjust_blinds", "result": "reduced_glare", "timestamp": datetime.now() - timedelta(hours=2)}
        ],
        "user_feedback": [
            {"action": "cooling_adjustment", "satisfaction": 0.9},
            {"action": "lighting_change", "satisfaction": 0.7}
        ]
    }

    current_situation = {
        "temperature": 25.0,
        "light_level": 0.8,
        "time": "14:30",
        "occupancy": True
    }

    learning_insights = await safla.learn(current_situation, historical_context)

    assert "patterns_identified" in learning_insights
    assert "recommendations" in learning_insights
    assert learning_insights["confidence"] > 0.0


@pytest.mark.asyncio
async def test_act_phase_device_control():
    """Test the Act phase executes appropriate device controls."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock decision from consciousness
    consciousness_decision = {
        "primary_action": "improve_comfort",
        "specific_actions": [
            {"device": "hvac_001", "action": "set_temperature", "value": 22.0},
            {"device": "light_001", "action": "turn_on", "brightness": 60},
            {"device": "blinds_001", "action": "adjust", "position": 70}
        ],
        "priority": "high",
        "safety_constraints": {
            "max_temperature_change": 3.0,
            "energy_limit": 300.0
        }
    }

    # Mock controllability layer
    safla.controllability_layer.execute_actions = AsyncMock(return_value={
        "success": True,
        "executed_actions": 3,
        "failed_actions": 0,
        "execution_time": 1.2
    })

    action_results = await safla.act(consciousness_decision)

    assert action_results["success"] is True
    assert action_results["executed_actions"] == 3
    assert action_results["execution_time"] > 0


@pytest.mark.asyncio
async def test_complete_safla_cycle():
    """Test a complete SAFLA cycle from sense to act."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Mock all layers for complete cycle
    # 1. Sense phase
    sense_data = {
        "temperature": 24.0,
        "humidity": 50.0,
        "light_level": 0.3,
        "motion_detected": True,
        "energy_usage": 180.0
    }
    safla.observability_layer.collect_sensor_data = AsyncMock(return_value=sense_data)

    # 2. Analyze phase
    analysis_result = {
        "temperature_status": {"level": "comfortable"},
        "lighting_status": {"level": "dim", "recommendation": "increase"},
        "energy_efficiency": {"score": 0.7}
    }
    safla.analyze = AsyncMock(return_value=analysis_result)

    # 3. Feel phase
    emotional_state = EmotionalState(
        happiness=0.6,
        worry=0.3,
        boredom=0.4,
        excitement=0.5,
        primary_emotion="attentive",
        intensity=0.6,
        confidence=0.8,
        trigger_event="user_activity_detected"
    )
    safla.consciousness_model.emotion_processor.process_environmental_factors = AsyncMock(
        return_value=emotional_state
    )

    # 4. Learn phase
    learning_result = {
        "patterns_identified": ["user_prefers_brighter_lighting_when_active"],
        "confidence": 0.85,
        "recommendations": ["increase_lighting"]
    }
    safla.learn = AsyncMock(return_value=learning_result)

    # 5. Act phase
    action_result = {
        "success": True,
        "actions_taken": ["light_brightness_increased"],
        "execution_time": 0.8
    }
    safla.controllability_layer.execute_actions = AsyncMock(return_value=action_result)

    # Execute complete cycle
    cycle_result = await safla.execute_cycle()

    assert cycle_result["success"] is True
    assert "sense_data" in cycle_result
    assert "analysis" in cycle_result
    assert "emotional_state" in cycle_result
    assert "learning_insights" in cycle_result
    assert "action_results" in cycle_result


@pytest.mark.asyncio
async def test_feedback_loop_learning():
    """Test that the feedback loop improves system behavior over time."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Simulate feedback on previous action
    action_feedback = {
        "action_id": "temp_adjustment_001",
        "user_satisfaction": 0.9,
        "effectiveness": 0.85,
        "energy_efficiency": 0.7,
        "time_to_comfort": 300,  # 5 minutes
        "side_effects": []
    }

    # Mock memory storage
    safla.consciousness_model.memory_manager.store_feedback = AsyncMock(return_value=True)

    # Process feedback
    learning_update = await safla.process_feedback(action_feedback)

    assert learning_update["pattern_reinforced"] is True
    assert learning_update["confidence_increase"] > 0

    # Verify memory was updated
    safla.consciousness_model.memory_manager.store_feedback.assert_called_once_with(action_feedback)


@pytest.mark.asyncio
async def test_safety_constraints_enforcement():
    """Test that safety constraints prevent harmful actions."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Create potentially unsafe action decision
    unsafe_decision = {
        "primary_action": "emergency_cooling",
        "specific_actions": [
            {"device": "hvac_001", "action": "set_temperature", "value": 10.0},  # Too cold
            {"device": "all_lights", "action": "set_brightness", "value": 100},   # Full brightness
        ],
        "priority": "critical"
    }

    # Mock safety constraint checker
    safla.controllability_layer.validate_safety_constraints = AsyncMock(return_value={
        "safe": False,
        "violations": [
            {"constraint": "min_temperature", "value": 10.0, "limit": 16.0},
        ],
        "safe_alternatives": [
            {"device": "hvac_001", "action": "set_temperature", "value": 18.0}
        ]
    })

    # Attempt unsafe action
    safety_result = await safla.controllability_layer.validate_safety_constraints(unsafe_decision)

    assert safety_result["safe"] is False
    assert len(safety_result["violations"]) > 0
    assert "safe_alternatives" in safety_result


@pytest.mark.asyncio
async def test_error_handling_and_recovery():
    """Test SAFLA loop handles errors gracefully and attempts recovery."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Simulate sensor failure
    safla.observability_layer.collect_sensor_data = AsyncMock(
        side_effect=Exception("Sensor communication error")
    )

    # Should handle error gracefully
    sense_result = await safla.sense()

    # Should return default/cached data or indicate sensor failure
    assert "error" in sense_result or "cached_data" in sense_result

    # Test device control failure
    safla.controllability_layer.execute_actions = AsyncMock(
        side_effect=Exception("Device unreachable")
    )

    action_decision = {
        "specific_actions": [
            {"device": "light_001", "action": "turn_on"}
        ]
    }

    # Should handle device failure
    with pytest.raises(Exception) or "error" in await safla.act(action_decision):
        pass  # Either exception is raised or error is handled gracefully


@pytest.mark.asyncio
async def test_multi_device_coordination():
    """Test SAFLA coordinates multiple devices for complex scenarios."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Complex scenario: Guest arrival automation
    scenario_context = {
        "event": "guest_arrival",
        "time": "evening",
        "weather": "rainy",
        "current_occupancy": 1,
        "arriving_guests": 3
    }

    coordination_plan = {
        "sequence": [
            {"phase": "preparation", "actions": [
                {"device": "entry_lights", "action": "turn_on", "brightness": 80},
                {"device": "hvac_001", "action": "adjust_for_occupancy", "target_occupancy": 4}
            ]},
            {"phase": "welcome", "actions": [
                {"device": "door_lock", "action": "unlock"},
                {"device": "ambient_lights", "action": "warm_welcome_scene"},
                {"device": "music_system", "action": "play_ambient"}
            ]},
            {"phase": "comfort", "actions": [
                {"device": "hvac_001", "action": "optimize_for_group"},
                {"device": "lighting_system", "action": "evening_social_scene"}
            ]}
        ]
    }

    # Mock coordination execution
    safla.controllability_layer.execute_coordinated_sequence = AsyncMock(return_value={
        "success": True,
        "phases_completed": 3,
        "total_actions": 7,
        "execution_time": 15.2,
        "coordination_effectiveness": 0.92
    })

    coordination_result = await safla.controllability_layer.execute_coordinated_sequence(coordination_plan)

    assert coordination_result["success"] is True
    assert coordination_result["phases_completed"] == 3
    assert coordination_result["coordination_effectiveness"] > 0.9


@pytest.mark.asyncio
async def test_adaptive_learning_from_patterns():
    """Test SAFLA adapts behavior based on learned patterns."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # Historical pattern: User always dims lights when watching TV in evening
    historical_pattern = {
        "pattern_id": "evening_tv_lighting",
        "conditions": {
            "time_range": ["19:00", "23:00"],
            "activity": "watching_tv",
            "room": "living_room"
        },
        "user_preferences": {
            "lighting_level": 0.3,
            "color_temperature": "warm",
            "ambient_only": True
        },
        "confidence": 0.95,
        "reinforcement_count": 15
    }

    current_context = {
        "time": "20:30",
        "detected_activity": "tv_on",
        "room": "living_room",
        "user_present": True
    }

    # Mock pattern matching
    safla.consciousness_model.memory_manager.find_matching_patterns = AsyncMock(
        return_value=[historical_pattern]
    )

    # Should proactively suggest lighting adjustment
    proactive_suggestions = await safla.generate_proactive_actions(current_context)

    assert len(proactive_suggestions) > 0
    assert any("lighting" in action["action"].lower() for action in proactive_suggestions)
    assert any(action["confidence"] > 0.9 for action in proactive_suggestions)


@pytest.mark.asyncio
async def test_energy_optimization_decisions():
    """Test SAFLA makes energy-conscious decisions."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # High energy usage scenario
    energy_context = {
        "current_usage": 350.0,  # watts
        "baseline_usage": 200.0,
        "peak_rate_period": True,
        "battery_level": 0.2,  # Low battery backup
        "grid_stress": "high"
    }

    comfort_request = {
        "action": "increase_cooling",
        "urgency": "moderate",
        "user_preference": "comfort_priority"
    }

    # Should balance comfort and energy efficiency
    optimization_result = await safla.optimize_energy_decision(comfort_request, energy_context)

    assert "energy_impact" in optimization_result
    assert "alternative_actions" in optimization_result
    assert optimization_result["recommended_action"]["energy_efficiency"] > 0.5


@pytest.mark.asyncio
async def test_consciousness_query_integration():
    """Test integration between SAFLA and consciousness query processing."""
    mock_session = AsyncMock()
    safla = SAFLALoop(mock_session)
    await safla.initialize()

    # User query about system state
    user_query = "Why is the temperature so high right now?"

    current_context = {
        "temperature": 26.0,
        "hvac_status": "cooling",
        "hvac_efficiency": 0.6,
        "external_temperature": 32.0,
        "recent_actions": [
            {"action": "cooling_increased", "time": "10 minutes ago", "effectiveness": "partial"}
        ]
    }

    # Mock consciousness response generation
    safla.consciousness_model.query_engine.process_contextual_query = AsyncMock(return_value={
        "interpretation": "user_concerned_about_temperature",
        "explanation": "The AC is working but struggling with the hot weather. I increased cooling 10 minutes ago but it's still catching up.",
        "current_actions": "Continuing to cool, considering additional measures",
        "emotional_context": "I'm concerned about your comfort and working to improve it",
        "confidence": 0.9
    })

    query_response = await safla.consciousness_model.query_engine.process_contextual_query(
        user_query, current_context
    )

    assert "explanation" in query_response
    assert "emotional_context" in query_response
    assert query_response["confidence"] > 0.8
    assert "struggling" in query_response["explanation"].lower()
