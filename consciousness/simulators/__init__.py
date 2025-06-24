"""
Device Simulator Package

Provides realistic device simulation for testing without hardware.
"""

from .base import BaseSimulatedDevice, DeviceEvent, SimulatorEventType
from .demo_scenarios import DemoScenarios, register_scenarios
from .devices import (
    SimulatedCamera,
    SimulatedHub,
    SimulatedLight,
    SimulatedLock,
    SimulatedSensor,
    SimulatedSwitch,
    SimulatedThermostat,
)
from .manager import SimulatorManager
from .scenarios import ScenarioEngine

__all__ = [
    "BaseSimulatedDevice",
    "SimulatorEventType",
    "DeviceEvent",
    "SimulatedLight",
    "SimulatedThermostat",
    "SimulatedSensor",
    "SimulatedCamera",
    "SimulatedLock",
    "SimulatedSwitch",
    "SimulatedHub",
    "SimulatorManager",
    "DemoScenarios",
    "register_scenarios",
    "ScenarioEngine",
]
