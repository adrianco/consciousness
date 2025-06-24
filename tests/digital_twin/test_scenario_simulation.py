"""
Digital Twin Scenario Simulation Testing
Tests complex scenario simulations using digital twins for predictive analysis.
"""
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from consciousness.digital_twin.physics_models import EnergyModel, ThermalModel
from consciousness.digital_twin.scenario_engine import ScenarioEngine
from consciousness.digital_twin.twin_manager import DigitalTwinManager
from consciousness.models.entities import Device, House


@pytest.fixture
async def scenario_engine():
    """Create scenario engine for testing."""
    mock_session = AsyncMock()
    engine = ScenarioEngine(mock_session)
    await engine.initialize()
    return engine


@pytest.fixture
async def test_house_setup():
    """Create a test house with multiple devices for scenarios."""
    house = House(
        id="test_house_001",
        name="Test Smart Home",
        timezone="America/New_York",
        location={"latitude": 40.7128, "longitude": -74.0060},
    )

    devices = [
        Device(id="hvac_001", device_type="thermostat", location="living_room"),
        Device(id="light_001", device_type="smart_light", location="living_room"),
        Device(id="light_002", device_type="smart_light", location="bedroom"),
        Device(id="motion_001", device_type="motion_sensor", location="living_room"),
        Device(id="temp_001", device_type="temperature_sensor", location="bedroom"),
        Device(id="door_001", device_type="smart_lock", location="front_door"),
        Device(id="window_001", device_type="smart_blinds", location="living_room"),
    ]

    # Mock device interfaces
    for device in devices:
        device.interface = AsyncMock()
        if device.device_type == "thermostat":
            device.interface.get_state.return_value = {
                "temperature": 22.0,
                "target": 21.0,
                "mode": "auto",
            }
        elif device.device_type == "smart_light":
            device.interface.get_state.return_value = {
                "brightness": 75,
                "color_temp": 3000,
                "status": "on",
            }
        elif device.device_type == "motion_sensor":
            device.interface.get_state.return_value = {
                "motion_detected": False,
                "last_motion": None,
            }
        elif device.device_type == "temperature_sensor":
            device.interface.get_state.return_value = {
                "temperature": 21.8,
                "humidity": 45,
            }
        elif device.device_type == "smart_lock":
            device.interface.get_state.return_value = {
                "locked": True,
                "last_access": None,
            }
        elif device.device_type == "smart_blinds":
            device.interface.get_state.return_value = {"position": 50, "tilt": 0}

    return house, devices


@pytest.mark.asyncio
async def test_power_outage_scenario(scenario_engine, test_house_setup):
    """Test power outage scenario simulation."""
    house, devices = test_house_setup

    # Define power outage scenario
    scenario = {
        "name": "power_outage_30min",
        "description": "30-minute power outage during evening",
        "duration_minutes": 30,
        "start_time": "19:00",
        "events": [
            {
                "time_offset": 0,
                "type": "power_loss",
                "affected_circuits": ["main"],
                "backup_power": {"available": True, "capacity": 0.3},
            },
            {
                "time_offset": 1800,  # 30 minutes
                "type": "power_restore",
                "affected_circuits": ["main"],
            },
        ],
        "initial_conditions": {
            "occupancy": True,
            "external_temperature": 85,  # Hot day
            "time_of_day": "evening",
            "hvac_load": "high",
        },
    }

    # Run scenario simulation
    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True
    assert simulation_result.duration_minutes == 30
    assert len(simulation_result.timeline) > 10  # Should have multiple timeline events

    # Verify power outage effects
    outage_events = [
        event
        for event in simulation_result.timeline
        if event.time_offset > 0 and event.time_offset < 1800
    ]

    # During outage, most devices should be offline
    for event in outage_events[:5]:  # Check first 5 events during outage
        hvac_state = next(
            (d for d in event.device_states if d.device_id == "hvac_001"), None
        )
        if hvac_state:
            assert hvac_state.powered is False or hvac_state.backup_power is True

    # After power restore, devices should come back online
    restore_events = [
        event for event in simulation_result.timeline if event.time_offset >= 1800
    ]

    final_event = restore_events[-1]
    hvac_final = next(
        (d for d in final_event.device_states if d.device_id == "hvac_001"), None
    )
    assert hvac_final.powered is True


@pytest.mark.asyncio
async def test_vacation_mode_scenario(scenario_engine, test_house_setup):
    """Test vacation mode energy optimization scenario."""
    house, devices = test_house_setup

    scenario = {
        "name": "vacation_7_days",
        "description": "7-day vacation with energy optimization",
        "duration_minutes": 7 * 24 * 60,  # 7 days
        "events": [
            {
                "time_offset": 0,
                "type": "occupancy_change",
                "occupancy": False,
                "duration": 7 * 24 * 60,
            }
        ],
        "automation_rules": {
            "energy_optimization": True,
            "security_mode": True,
            "presence_simulation": True,
            "temperature_setback": 5,  # 5 degree setback
        },
        "environmental_conditions": {
            "weather_pattern": "seasonal_normal",
            "external_temperature_range": [15, 25],
        },
    }

    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True

    # Verify energy optimization
    baseline_energy = await scenario_engine.calculate_baseline_energy_usage(
        devices, duration_minutes=7 * 24 * 60
    )
    vacation_energy = simulation_result.metrics.total_energy_usage

    energy_savings = (baseline_energy - vacation_energy) / baseline_energy
    assert energy_savings > 0.15  # At least 15% energy savings

    # Verify presence simulation
    lighting_events = [
        event
        for event in simulation_result.timeline
        if any(
            d.device_id.startswith("light_") and d.state_changes
            for d in event.device_states
        )
    ]

    assert (
        len(lighting_events) > 5
    )  # Should have some lighting activity for presence simulation

    # Verify temperature setback
    hvac_events = [
        event
        for event in simulation_result.timeline
        if any(d.device_id == "hvac_001" for d in event.device_states)
    ]

    # Find setback temperature
    setback_event = next(
        event
        for event in hvac_events
        if any(
            d.device_id == "hvac_001"
            and abs(d.current_state.get("target_temperature", 21) - 16)
            < 1  # 5 degree setback
            for d in event.device_states
        )
    )
    assert setback_event is not None


@pytest.mark.asyncio
async def test_extreme_weather_scenario(scenario_engine, test_house_setup):
    """Test extreme weather event scenario."""
    house, devices = test_house_setup

    scenario = {
        "name": "heatwave_72_hours",
        "description": "72-hour heatwave with high energy demand",
        "duration_minutes": 72 * 60,
        "environmental_conditions": {
            "external_temperature": {
                "pattern": "heatwave",
                "peak_temperature": 105,  # 105°F
                "base_temperature": 95,
                "peak_time": "15:00",
            },
            "humidity": {"base": 60, "peak": 85},
            "grid_conditions": {"stress_level": "high", "peak_demand_surcharge": True},
        },
        "events": [
            {
                "time_offset": 24 * 60,  # Day 2
                "type": "grid_emergency",
                "description": "Grid asks for demand reduction",
                "demand_reduction_request": 0.3,  # 30% reduction
            }
        ],
    }

    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True

    # Verify HVAC response to extreme heat
    hvac_operations = [
        event
        for event in simulation_result.timeline
        if any(
            d.device_id == "hvac_001" and d.current_state.get("mode") == "cooling"
            for d in event.device_states
        )
    ]

    assert len(hvac_operations) > 20  # Should be cooling frequently

    # Verify demand response
    grid_emergency_time = 24 * 60
    post_emergency_events = [
        event
        for event in simulation_result.timeline
        if event.time_offset > grid_emergency_time
        and event.time_offset < grid_emergency_time + 60
    ]

    # Should show reduced energy consumption after grid emergency
    pre_emergency_usage = simulation_result.metrics.energy_usage_by_hour[
        23
    ]  # Hour before
    post_emergency_usage = simulation_result.metrics.energy_usage_by_hour[
        25
    ]  # Hour after

    reduction = (pre_emergency_usage - post_emergency_usage) / pre_emergency_usage
    assert reduction > 0.2  # At least 20% reduction


@pytest.mark.asyncio
async def test_guest_arrival_automation_scenario(scenario_engine, test_house_setup):
    """Test guest arrival automation scenario."""
    house, devices = test_house_setup

    scenario = {
        "name": "guest_arrival_evening",
        "description": "Evening guest arrival with automated welcome sequence",
        "duration_minutes": 120,  # 2 hours
        "events": [
            {
                "time_offset": 30,
                "type": "occupancy_change",
                "occupancy": True,
                "guest_count": 3,
                "arrival_mode": "expected",
            }
        ],
        "automation_sequences": {
            "guest_welcome": {
                "pre_arrival": [
                    {"device": "light_001", "action": "set_brightness", "value": 80},
                    {
                        "device": "hvac_001",
                        "action": "adjust_for_occupancy",
                        "guest_count": 3,
                    },
                ],
                "on_arrival": [
                    {"device": "door_001", "action": "unlock", "duration": 10},
                    {"device": "light_001", "action": "welcome_scene"},
                    {"device": "window_001", "action": "adjust_for_privacy"},
                ],
                "post_arrival": [
                    {"device": "hvac_001", "action": "optimize_for_group_comfort"},
                    {"device": "light_002", "action": "ambient_lighting"},
                ],
            }
        },
        "initial_conditions": {
            "time": "18:30",
            "occupancy": False,
            "external_temperature": 75,
        },
    }

    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True

    # Verify welcome sequence execution
    arrival_time = 30
    welcome_events = [
        event
        for event in simulation_result.timeline
        if arrival_time
        <= event.time_offset
        <= arrival_time + 15  # 15 minutes after arrival
    ]

    # Check that welcome actions were executed
    door_unlocked = any(
        any(
            d.device_id == "door_001" and d.current_state.get("locked") is False
            for d in event.device_states
        )
        for event in welcome_events
    )
    assert door_unlocked is True

    # Verify lighting adjustment
    lighting_adjusted = any(
        any(
            d.device_id == "light_001" and d.current_state.get("brightness", 0) > 75
            for d in event.device_states
        )
        for event in welcome_events
    )
    assert lighting_adjusted is True

    # Verify HVAC adjustment for additional occupancy
    hvac_adjusted = any(
        any(
            d.device_id == "hvac_001" and "guest_count" in d.current_state
            for d in event.device_states
        )
        for event in welcome_events
    )
    assert hvac_adjusted is True


@pytest.mark.asyncio
async def test_security_incident_response_scenario(scenario_engine, test_house_setup):
    """Test security incident response scenario."""
    house, devices = test_house_setup

    scenario = {
        "name": "security_breach_response",
        "description": "Unauthorized entry detection and response",
        "duration_minutes": 60,
        "events": [
            {
                "time_offset": 10,
                "type": "motion_detection",
                "device": "motion_001",
                "unexpected": True,
                "occupancy_expected": False,
            },
            {
                "time_offset": 12,
                "type": "door_access",
                "device": "door_001",
                "access_method": "unknown",
                "authorized": False,
            },
        ],
        "security_protocols": {
            "alert_authorities": True,
            "activate_recording": True,
            "secure_mode": True,
            "emergency_lighting": True,
        },
        "initial_conditions": {
            "time": "02:30",  # Late night
            "occupancy": False,
            "security_armed": True,
        },
    }

    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True

    # Verify security response
    security_events = [
        event
        for event in simulation_result.timeline
        if 10 <= event.time_offset <= 20  # Response window
    ]

    # Check emergency lighting activation
    emergency_lighting = any(
        any(
            d.device_id.startswith("light_")
            and d.current_state.get("brightness", 0) == 100  # Full brightness
            for d in event.device_states
        )
        for event in security_events
    )
    assert emergency_lighting is True

    # Verify alert generation
    alerts_generated = [
        event
        for event in simulation_result.timeline
        if hasattr(event, "alerts") and event.alerts
    ]
    assert len(alerts_generated) > 0

    # Check that door was secured
    door_secured = any(
        any(
            d.device_id == "door_001" and d.current_state.get("locked") is True
            for d in event.device_states
        )
        for event in security_events
    )
    assert door_secured is True


@pytest.mark.asyncio
async def test_morning_routine_optimization_scenario(scenario_engine, test_house_setup):
    """Test morning routine optimization scenario."""
    house, devices = test_house_setup

    scenario = {
        "name": "morning_routine_optimization",
        "description": "Optimize morning routine based on learned patterns",
        "duration_minutes": 180,  # 3 hours
        "user_patterns": {
            "wake_time": "06:30",
            "shower_duration": 15,
            "breakfast_time": 20,
            "departure_time": "08:00",
            "preferences": {
                "gradual_lighting": True,
                "pre_heat_shower": True,
                "coffee_preparation": True,
            },
        },
        "optimization_goals": {
            "energy_efficiency": 0.8,
            "comfort_priority": 0.9,
            "time_efficiency": 0.7,
        },
        "events": [
            {
                "time_offset": 30,  # 06:30
                "type": "wake_up_detected",
                "confidence": 0.95,
            },
            {"time_offset": 45, "type": "shower_start"},
            {"time_offset": 75, "type": "kitchen_activity"},
            {"time_offset": 150, "type": "departure_preparation"},
        ],
    }

    simulation_result = await scenario_engine.run_scenario(scenario, devices)

    assert simulation_result.success is True

    # Verify gradual lighting
    wake_time = 30
    lighting_events = [
        event
        for event in simulation_result.timeline
        if wake_time - 15 <= event.time_offset <= wake_time + 30
    ]

    brightness_progression = []
    for event in lighting_events:
        for device_state in event.device_states:
            if device_state.device_id == "light_002":  # Bedroom light
                brightness = device_state.current_state.get("brightness", 0)
                brightness_progression.append(brightness)

    # Should show gradual increase in brightness
    if len(brightness_progression) >= 3:
        assert brightness_progression[0] < brightness_progression[-1]
        assert max(brightness_progression) - min(brightness_progression) > 30

    # Verify pre-heating for shower
    shower_time = 45
    hvac_pre_shower = [
        event
        for event in simulation_result.timeline
        if shower_time - 10 <= event.time_offset <= shower_time
    ]

    bathroom_temp_raised = any(
        any(
            d.device_id == "hvac_001"
            and d.current_state.get("target_temperature", 21) > 22
            for d in event.device_states
        )
        for event in hvac_pre_shower
    )
    assert bathroom_temp_raised is True


@pytest.mark.asyncio
async def test_scenario_prediction_accuracy(scenario_engine, test_house_setup):
    """Test the accuracy of scenario predictions."""
    house, devices = test_house_setup

    # Create a scenario with known outcomes
    known_scenario = {
        "name": "temperature_response_test",
        "description": "Test HVAC response to temperature changes",
        "duration_minutes": 120,
        "environmental_conditions": {
            "external_temperature": 85,
            "starting_internal_temp": 75,
            "target_temp": 72,
        },
        "initial_conditions": {
            "hvac_efficiency": 0.8,
            "insulation_quality": "good",
            "occupancy": True,
        },
    }

    # Run actual simulation
    actual_result = await scenario_engine.run_scenario(known_scenario, devices)

    # Run prediction without full simulation
    predicted_result = await scenario_engine.predict_scenario_outcome(
        known_scenario, devices
    )

    # Compare actual vs predicted outcomes
    actual_final_temp = actual_result.final_state["hvac_001"]["temperature"]
    predicted_final_temp = predicted_result.predicted_final_state["hvac_001"][
        "temperature"
    ]

    temp_prediction_error = abs(actual_final_temp - predicted_final_temp)
    assert temp_prediction_error < 2.0  # Within 2 degrees

    # Compare energy usage predictions
    actual_energy = actual_result.metrics.total_energy_usage
    predicted_energy = predicted_result.predicted_energy_usage

    energy_prediction_error = abs(actual_energy - predicted_energy) / actual_energy
    assert energy_prediction_error < 0.15  # Within 15%

    # Verify prediction confidence
    assert predicted_result.confidence > 0.75


@pytest.mark.asyncio
async def test_multi_scenario_comparison(scenario_engine, test_house_setup):
    """Test comparison between multiple scenario alternatives."""
    house, devices = test_house_setup

    scenarios = [
        {
            "name": "aggressive_cooling",
            "hvac_strategy": "aggressive",
            "target_temp": 70,
            "energy_priority": 0.2,
        },
        {
            "name": "balanced_cooling",
            "hvac_strategy": "balanced",
            "target_temp": 72,
            "energy_priority": 0.6,
        },
        {
            "name": "eco_cooling",
            "hvac_strategy": "eco",
            "target_temp": 74,
            "energy_priority": 0.9,
        },
    ]

    comparison_results = []

    for scenario_config in scenarios:
        scenario = {
            "name": scenario_config["name"],
            "duration_minutes": 240,  # 4 hours
            "environmental_conditions": {"external_temperature": 90, "humidity": 60},
            "hvac_configuration": scenario_config,
        }

        result = await scenario_engine.run_scenario(scenario, devices)
        comparison_results.append(
            {
                "name": scenario_config["name"],
                "energy_usage": result.metrics.total_energy_usage,
                "comfort_score": result.metrics.comfort_score,
                "target_achievement": result.metrics.target_achievement_time,
            }
        )

    # Verify expected trade-offs
    aggressive = next(
        r for r in comparison_results if r["name"] == "aggressive_cooling"
    )
    eco = next(r for r in comparison_results if r["name"] == "eco_cooling")

    # Aggressive should use more energy but achieve comfort faster
    assert aggressive["energy_usage"] > eco["energy_usage"]
    assert aggressive["target_achievement"] < eco["target_achievement"]

    # Eco should have lower energy usage
    energy_savings = (aggressive["energy_usage"] - eco["energy_usage"]) / aggressive[
        "energy_usage"
    ]
    assert energy_savings > 0.2  # At least 20% energy savings
