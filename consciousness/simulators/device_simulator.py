"""Device simulator for creating realistic IoT device behaviors."""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from consciousness.models.entities import Device, DeviceEntity
from consciousness.models.events import SensorReading


class DeviceSimulator:
    """Simulates various IoT device behaviors."""

    def __init__(self, device: Device):
        self.device = device
        self.running = False
        self.state = {}
        self.callbacks = {}
        self.simulation_speed = 1.0  # 1.0 = real-time, 2.0 = 2x speed
        
    async def start(self):
        """Start the device simulation."""
        self.running = True
        await self._initialize_state()
        
        # Start simulation based on device class
        if self.device.device_class == "climate":
            await self._simulate_climate_device()
        elif self.device.device_class == "light":
            await self._simulate_light_device()
        elif self.device.device_class == "sensor":
            await self._simulate_sensor_device()
        elif self.device.device_class == "security":
            await self._simulate_security_device()
        elif self.device.device_class == "energy":
            await self._simulate_energy_device()
            
    async def stop(self):
        """Stop the device simulation."""
        self.running = False
        
    async def set_state(self, state: Dict[str, Any]):
        """Set device state."""
        self.state.update(state)
        await self._trigger_callback("state_changed", self.state)
        
    def on(self, event: str, callback: Callable):
        """Register event callback."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        
    async def _trigger_callback(self, event: str, data: Any):
        """Trigger registered callbacks."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                await callback(self.device, data)
                
    async def _initialize_state(self):
        """Initialize device state based on device class."""
        if self.device.device_class == "climate":
            self.state = {
                "temperature": 72.0,
                "target_temperature": 72.0,
                "humidity": 45.0,
                "mode": "auto",
                "fan_speed": "auto",
                "is_on": True
            }
        elif self.device.device_class == "light":
            self.state = {
                "is_on": False,
                "brightness": 100,
                "color_temp": 4000,
                "rgb_color": None
            }
        elif self.device.device_class == "sensor":
            sensor_type = self.device.capabilities.get("sensor_type", "temperature")
            if sensor_type == "motion":
                self.state = {"motion_detected": False, "last_motion": None}
            elif sensor_type == "door":
                self.state = {"is_open": False, "last_opened": None}
            elif sensor_type == "temperature":
                self.state = {"temperature": 72.0, "humidity": 45.0}
        elif self.device.device_class == "security":
            self.state = {
                "armed": False,
                "mode": "home",
                "alerts": [],
                "camera_active": True
            }
        elif self.device.device_class == "energy":
            self.state = {
                "current_power": 0.0,
                "total_energy": 0.0,
                "solar_production": 0.0,
                "battery_level": 85.0,
                "grid_status": "connected"
            }
            
    async def _simulate_climate_device(self):
        """Simulate HVAC/thermostat behavior."""
        while self.running:
            # Simulate temperature changes
            current_temp = self.state["temperature"]
            target_temp = self.state["target_temperature"]
            
            if self.state["is_on"]:
                # Move towards target temperature
                if current_temp < target_temp - 0.5:
                    current_temp += random.uniform(0.1, 0.3)
                elif current_temp > target_temp + 0.5:
                    current_temp -= random.uniform(0.1, 0.3)
                    
            # Add some random fluctuation
            current_temp += random.uniform(-0.1, 0.1)
            
            # Update humidity
            humidity = self.state["humidity"] + random.uniform(-1, 1)
            humidity = max(20, min(80, humidity))
            
            self.state.update({
                "temperature": round(current_temp, 1),
                "humidity": round(humidity, 1)
            })
            
            await self._trigger_callback("sensor_reading", {
                "sensor_type": "temperature",
                "value": current_temp,
                "unit": "°F"
            })
            
            await self._trigger_callback("sensor_reading", {
                "sensor_type": "humidity",
                "value": humidity,
                "unit": "%"
            })
            
            await asyncio.sleep(30 / self.simulation_speed)  # Update every 30 seconds
            
    async def _simulate_light_device(self):
        """Simulate smart light behavior."""
        while self.running:
            if self.state["is_on"]:
                # Simulate slight power fluctuations
                power_usage = (self.state["brightness"] / 100) * 10  # 10W max
                power_usage += random.uniform(-0.5, 0.5)
                
                await self._trigger_callback("sensor_reading", {
                    "sensor_type": "power",
                    "value": power_usage,
                    "unit": "W"
                })
                
            await asyncio.sleep(60 / self.simulation_speed)  # Update every minute
            
    async def _simulate_sensor_device(self):
        """Simulate various sensor behaviors."""
        sensor_type = self.device.capabilities.get("sensor_type", "temperature")
        
        while self.running:
            if sensor_type == "motion":
                # Random motion events
                if random.random() < 0.1:  # 10% chance of motion
                    self.state["motion_detected"] = True
                    self.state["last_motion"] = datetime.now()
                    await self._trigger_callback("motion_detected", True)
                    
                    # Clear motion after a few seconds
                    await asyncio.sleep(5 / self.simulation_speed)
                    self.state["motion_detected"] = False
                    await self._trigger_callback("motion_cleared", False)
                    
            elif sensor_type == "door":
                # Random door open/close events
                if random.random() < 0.05:  # 5% chance of state change
                    self.state["is_open"] = not self.state["is_open"]
                    self.state["last_opened"] = datetime.now() if self.state["is_open"] else self.state["last_opened"]
                    await self._trigger_callback("door_state_changed", self.state["is_open"])
                    
            elif sensor_type == "temperature":
                # Ambient temperature sensor
                temp = self.state["temperature"] + random.uniform(-0.5, 0.5)
                self.state["temperature"] = round(temp, 1)
                
                await self._trigger_callback("sensor_reading", {
                    "sensor_type": "temperature",
                    "value": temp,
                    "unit": "°F"
                })
                
            await asyncio.sleep(10 / self.simulation_speed)  # Update every 10 seconds
            
    async def _simulate_security_device(self):
        """Simulate security system behavior."""
        while self.running:
            if self.state["armed"]:
                # Simulate random security events (very low probability)
                if random.random() < 0.001:  # 0.1% chance
                    alert = {
                        "type": "motion",
                        "location": self.device.location,
                        "timestamp": datetime.now(),
                        "severity": "high"
                    }
                    self.state["alerts"].append(alert)
                    await self._trigger_callback("security_alert", alert)
                    
            await asyncio.sleep(5 / self.simulation_speed)  # Check every 5 seconds
            
    async def _simulate_energy_device(self):
        """Simulate energy monitoring/solar system."""
        while self.running:
            # Simulate power consumption based on time of day
            hour = datetime.now().hour
            base_load = 1.5  # kW base load
            
            # Higher usage during day
            if 6 <= hour <= 22:
                power = base_load + random.uniform(0.5, 2.0)
            else:
                power = base_load + random.uniform(-0.5, 0.5)
                
            # Solar production (peaks at noon)
            if 6 <= hour <= 18:
                solar_factor = 1 - abs(12 - hour) / 6
                solar = solar_factor * 5.0 + random.uniform(-0.5, 0.5)  # 5kW peak
            else:
                solar = 0.0
                
            # Battery charging/discharging
            battery = self.state["battery_level"]
            if solar > power and battery < 100:
                battery += 0.1  # Charging
            elif solar < power and battery > 0:
                battery -= 0.1  # Discharging
                
            self.state.update({
                "current_power": round(power, 2),
                "solar_production": round(solar, 2),
                "battery_level": round(max(0, min(100, battery)), 1),
                "total_energy": self.state["total_energy"] + (power / 60)  # kWh
            })
            
            await self._trigger_callback("energy_update", self.state)
            
            await asyncio.sleep(60 / self.simulation_speed)  # Update every minute


class HouseSimulator:
    """Orchestrates multiple device simulators to create a complete house simulation."""
    
    def __init__(self):
        self.devices: Dict[int, DeviceSimulator] = {}
        self.running = False
        self.scenarios = {}
        self.current_scenario = None
        
    def add_device(self, device: Device) -> DeviceSimulator:
        """Add a device to the simulation."""
        simulator = DeviceSimulator(device)
        self.devices[device.id] = simulator
        return simulator
        
    async def start(self):
        """Start all device simulations."""
        self.running = True
        tasks = []
        for simulator in self.devices.values():
            tasks.append(asyncio.create_task(simulator.start()))
        await asyncio.gather(*tasks)
        
    async def stop(self):
        """Stop all device simulations."""
        self.running = False
        for simulator in self.devices.values():
            await simulator.stop()
            
    async def run_scenario(self, scenario_name: str):
        """Run a predefined scenario."""
        if scenario_name in self.scenarios:
            self.current_scenario = scenario_name
            await self.scenarios[scenario_name](self)
            
    def get_device_by_class(self, device_class: str) -> List[DeviceSimulator]:
        """Get all devices of a specific class."""
        return [sim for sim in self.devices.values() 
                if sim.device.device_class == device_class]
                
    def get_device_by_location(self, location: str) -> List[DeviceSimulator]:
        """Get all devices in a specific location."""
        return [sim for sim in self.devices.values() 
                if sim.device.location == location]