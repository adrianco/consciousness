"""
Simulator Manager for orchestrating multiple device simulators.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type, Callable, Set
import uuid
import random
from pathlib import Path

from .base import BaseSimulatedDevice, DeviceEvent, SimulatorEventType
from .devices import (
    SimulatedLight,
    SimulatedThermostat,
    SimulatedSensor,
    SimulatedCamera,
    SimulatedLock,
    SimulatedSwitch,
    SimulatedHub
)


logger = logging.getLogger(__name__)


class SimulatorConfig:
    """Configuration for the simulator manager."""
    
    def __init__(
        self,
        auto_start: bool = True,
        enable_random_events: bool = True,
        global_failure_rate: float = 0.01,
        response_delay_range: tuple = (0.1, 0.5),
        environmental_updates: bool = True,
        save_events: bool = True,
        event_log_path: Optional[str] = None
    ):
        self.auto_start = auto_start
        self.enable_random_events = enable_random_events
        self.global_failure_rate = global_failure_rate
        self.response_delay_range = response_delay_range
        self.environmental_updates = environmental_updates
        self.save_events = save_events
        self.event_log_path = event_log_path or "simulator_events.json"


class EnvironmentalSimulator:
    """Simulates environmental conditions that affect devices."""
    
    def __init__(self):
        self.conditions = {
            "temperature": 22.0,  # Celsius
            "humidity": 50.0,     # Percentage
            "light_level": 100.0, # Lux
            "motion": False,
            "time_of_day": "day",  # day, evening, night
            "occupancy": True,     # Is anyone home
            "weather": "clear"     # clear, cloudy, rain, storm
        }
        
        self._running = False
        self._update_task = None
    
    async def start(self) -> None:
        """Start environmental simulation."""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Environmental simulator started")
    
    async def stop(self) -> None:
        """Stop environmental simulation."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Environmental simulator stopped")
    
    async def _update_loop(self) -> None:
        """Main environmental update loop."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_conditions()
            except Exception as e:
                logger.error(f"Error in environmental update loop: {e}")
    
    async def _update_conditions(self) -> None:
        """Update environmental conditions."""
        # Time-based updates
        hour = datetime.now().hour
        
        if 6 <= hour <= 18:
            self.conditions["time_of_day"] = "day"
            self.conditions["light_level"] = random.uniform(200, 1000)
        elif 19 <= hour <= 22:
            self.conditions["time_of_day"] = "evening"
            self.conditions["light_level"] = random.uniform(50, 200)
        else:
            self.conditions["time_of_day"] = "night"
            self.conditions["light_level"] = random.uniform(0, 50)
        
        # Temperature variations
        base_temp = 22.0
        if self.conditions["time_of_day"] == "night":
            base_temp -= 2
        elif self.conditions["time_of_day"] == "day":
            base_temp += 1
        
        # Add random variation
        self.conditions["temperature"] = base_temp + random.uniform(-3, 3)
        
        # Humidity variations
        self.conditions["humidity"] = max(30, min(70, 
            self.conditions["humidity"] + random.uniform(-2, 2)))
        
        # Motion simulation (random occupancy patterns)
        if self.conditions["occupancy"]:
            # More motion during day/evening
            motion_probability = {
                "day": 0.3,
                "evening": 0.4,
                "night": 0.1
            }
            self.conditions["motion"] = random.random() < motion_probability.get(
                self.conditions["time_of_day"], 0.2
            )
        else:
            self.conditions["motion"] = False
        
        # Weather changes (slow)
        if random.random() < 0.05:  # 5% chance of weather change
            weather_options = ["clear", "cloudy", "rain", "storm"]
            self.conditions["weather"] = random.choice(weather_options)
    
    def get_conditions(self) -> Dict[str, Any]:
        """Get current environmental conditions."""
        return self.conditions.copy()
    
    def set_condition(self, condition: str, value: Any) -> None:
        """Manually set an environmental condition."""
        if condition in self.conditions:
            self.conditions[condition] = value
            logger.info(f"Set {condition} to {value}")
    
    def simulate_scenario(self, scenario: str) -> None:
        """Apply a predefined scenario."""
        scenarios = {
            "morning": {
                "time_of_day": "day",
                "light_level": 300,
                "temperature": 20,
                "occupancy": True,
                "motion": True
            },
            "evening": {
                "time_of_day": "evening",
                "light_level": 100,
                "temperature": 22,
                "occupancy": True,
                "motion": True
            },
            "night": {
                "time_of_day": "night",
                "light_level": 5,
                "temperature": 18,
                "motion": False
            },
            "away": {
                "occupancy": False,
                "motion": False,
                "temperature": 16
            },
            "storm": {
                "weather": "storm",
                "light_level": 50,
                "humidity": 80
            }
        }
        
        if scenario in scenarios:
            self.conditions.update(scenarios[scenario])
            logger.info(f"Applied scenario: {scenario}")


class SimulatorManager:
    """Manages multiple device simulators and orchestrates their behavior."""
    
    DEVICE_TYPES = {
        "light": SimulatedLight,
        "thermostat": SimulatedThermostat,
        "sensor": SimulatedSensor,
        "camera": SimulatedCamera,
        "lock": SimulatedLock,
        "switch": SimulatedSwitch,
        "hub": SimulatedHub
    }
    
    def __init__(self, config: Optional[SimulatorConfig] = None):
        self.config = config or SimulatorConfig()
        self.devices: Dict[str, BaseSimulatedDevice] = {}
        self.environmental_sim = EnvironmentalSimulator()
        
        # Event handling
        self.event_listeners: List[Callable[[DeviceEvent], None]] = []
        self.event_log: List[Dict[str, Any]] = []
        
        # Orchestration
        self._running = False
        self._orchestration_task = None
        self._event_logger_task = None
        
        # Performance tracking
        self.stats = {
            "devices_created": 0,
            "events_processed": 0,
            "commands_executed": 0,
            "failures_simulated": 0,
            "uptime": 0
        }
        self._start_time = None
    
    async def start(self) -> None:
        """Start the simulator manager."""
        if self._running:
            logger.warning("Simulator manager is already running")
            return
        
        self._running = True
        self._start_time = datetime.utcnow()
        
        logger.info("Starting simulator manager")
        
        # Start environmental simulation
        await self.environmental_sim.start()
        
        # Start all devices
        if self.config.auto_start:
            for device in self.devices.values():
                await device.start()
        
        # Start orchestration tasks
        self._orchestration_task = asyncio.create_task(self._orchestrate())
        if self.config.save_events:
            self._event_logger_task = asyncio.create_task(self._log_events())
        
        logger.info(f"Simulator manager started with {len(self.devices)} devices")
    
    async def stop(self) -> None:
        """Stop the simulator manager."""
        if not self._running:
            return
        
        logger.info("Stopping simulator manager")
        self._running = False
        
        # Stop orchestration tasks
        if self._orchestration_task:
            self._orchestration_task.cancel()
        if self._event_logger_task:
            self._event_logger_task.cancel()
        
        # Stop all devices
        tasks = []
        for device in self.devices.values():
            tasks.append(device.stop())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop environmental simulation
        await self.environmental_sim.stop()
        
        # Save final event log
        if self.config.save_events and self.event_log:
            await self._save_event_log()
        
        # Update stats
        if self._start_time:
            self.stats["uptime"] = (datetime.utcnow() - self._start_time).total_seconds()
        
        logger.info("Simulator manager stopped")
    
    def create_device(
        self,
        device_type: str,
        name: str,
        **kwargs
    ) -> BaseSimulatedDevice:
        """Create a new simulated device."""
        if device_type not in self.DEVICE_TYPES:
            raise ValueError(f"Unknown device type: {device_type}")
        
        device_class = self.DEVICE_TYPES[device_type]
        
        # Apply global configuration
        device_kwargs = {
            "name": name,
            "enable_random_events": self.config.enable_random_events,
            "failure_rate": self.config.global_failure_rate,
            "response_delay": random.uniform(*self.config.response_delay_range),
            **kwargs
        }
        
        # Special handling for sensors
        if device_type == "sensor":
            sensor_type = kwargs.get("sensor_type", "motion")
            device = device_class(sensor_type=sensor_type, **device_kwargs)
        else:
            device = device_class(**device_kwargs)
        
        # Add event listener
        device.add_event_listener(self._handle_device_event)
        
        # Register device
        self.devices[device.device_id] = device
        self.stats["devices_created"] += 1
        
        # Update environmental factors
        if self.config.environmental_updates:
            self._update_device_environment(device)
        
        logger.info(f"Created {device_type} device: {name} ({device.device_id})")
        
        # Auto-start if manager is running
        if self._running and self.config.auto_start:
            asyncio.create_task(device.start())
        
        return device
    
    def get_device(self, device_id: str) -> Optional[BaseSimulatedDevice]:
        """Get a device by ID."""
        return self.devices.get(device_id)
    
    def get_devices_by_type(self, device_type: str) -> List[BaseSimulatedDevice]:
        """Get all devices of a specific type."""
        return [
            device for device in self.devices.values()
            if device.device_class == device_type or device_type in device.device_class
        ]
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all devices with their basic information."""
        return [
            {
                "id": device.device_id,
                "name": device.name,
                "type": device.device_class,
                "brand": device.brand,
                "model": device.model,
                "online": device.is_online,
                "location": device.location
            }
            for device in self.devices.values()
        ]
    
    async def remove_device(self, device_id: str) -> bool:
        """Remove a device from the simulator."""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        # Stop the device
        await device.stop()
        
        # Remove from registry
        del self.devices[device_id]
        
        logger.info(f"Removed device: {device.name} ({device_id})")
        return True
    
    async def send_command(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a command to a specific device."""
        device = self.devices.get(device_id)
        if not device:
            return {
                "success": False,
                "error": f"Device not found: {device_id}"
            }
        
        try:
            result = await device.handle_command(command, parameters)
            self.stats["commands_executed"] += 1
            
            logger.debug(f"Command '{command}' sent to {device.name}: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    async def broadcast_command(
        self,
        device_type: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Send a command to all devices of a specific type."""
        devices = self.get_devices_by_type(device_type)
        results = []
        
        for device in devices:
            result = await self.send_command(device.device_id, command, parameters)
            results.append({
                "device_id": device.device_id,
                "device_name": device.name,
                "result": result
            })
        
        return {"results": results, "count": len(results)}
    
    def simulate_failure(self, device_id: str, failure_type: str = "random") -> bool:
        """Manually trigger a device failure."""
        device = self.devices.get(device_id)
        if not device:
            return False
        
        # Simulate different types of failures
        if failure_type == "offline":
            asyncio.create_task(device.set_connection_status(False))
        elif failure_type == "error":
            device.last_error = f"Simulated error at {datetime.utcnow().isoformat()}"
            asyncio.create_task(device.emit_event(
                SimulatorEventType.ERROR_OCCURRED,
                {"error": device.last_error, "simulated": True}
            ))
        elif failure_type == "random":
            # Temporarily increase failure rate
            old_rate = device.failure_rate
            device.failure_rate = 1.0  # 100% failure on next operation
            
            # Reset after a short delay
            async def reset_failure_rate():
                await asyncio.sleep(1)
                device.failure_rate = old_rate
            
            asyncio.create_task(reset_failure_rate())
        
        self.stats["failures_simulated"] += 1
        logger.info(f"Triggered {failure_type} failure for device {device.name}")
        return True
    
    def set_environmental_condition(self, condition: str, value: Any) -> None:
        """Set an environmental condition."""
        self.environmental_sim.set_condition(condition, value)
        
        # Update all devices
        if self.config.environmental_updates:
            for device in self.devices.values():
                self._update_device_environment(device)
    
    def apply_scenario(self, scenario: str) -> None:
        """Apply a predefined environmental scenario."""
        self.environmental_sim.simulate_scenario(scenario)
        
        # Update all devices
        if self.config.environmental_updates:
            for device in self.devices.values():
                self._update_device_environment(device)
        
        logger.info(f"Applied scenario: {scenario}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get simulator statistics."""
        current_uptime = 0
        if self._start_time:
            current_uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            **self.stats,
            "current_uptime": current_uptime,
            "active_devices": len([d for d in self.devices.values() if d.is_online]),
            "total_devices": len(self.devices),
            "environmental_conditions": self.environmental_sim.get_conditions(),
            "event_log_size": len(self.event_log)
        }
    
    def add_event_listener(self, listener: Callable[[DeviceEvent], None]) -> None:
        """Add a global event listener."""
        self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[DeviceEvent], None]) -> None:
        """Remove a global event listener."""
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    async def create_test_environment(self, scenario: str = "default") -> None:
        """Create a comprehensive test environment."""
        logger.info(f"Creating test environment: {scenario}")
        
        if scenario == "default":
            # Create a typical smart home setup
            devices_to_create = [
                ("light", "Living Room Light", {"location": "Living Room"}),
                ("light", "Bedroom Light", {"location": "Bedroom"}),
                ("thermostat", "Main Thermostat", {"location": "Living Room"}),
                ("sensor", "Front Door Sensor", {
                    "sensor_type": "door", "location": "Front Door"}),
                ("sensor", "Motion Sensor", {
                    "sensor_type": "motion", "location": "Living Room"}),
                ("camera", "Security Camera", {"location": "Front Door"}),
                ("lock", "Front Door Lock", {"location": "Front Door"}),
                ("switch", "Coffee Maker", {"location": "Kitchen"}),
                ("hub", "Smart Hub", {"location": "Living Room"})
            ]
            
        elif scenario == "security":
            # Security-focused setup
            devices_to_create = [
                ("camera", "Front Camera", {"location": "Front Door"}),
                ("camera", "Back Camera", {"location": "Back Yard"}),
                ("lock", "Front Lock", {"location": "Front Door"}),
                ("lock", "Back Lock", {"location": "Back Door"}),
                ("sensor", "Front Motion", {
                    "sensor_type": "motion", "location": "Front Door"}),
                ("sensor", "Back Motion", {
                    "sensor_type": "motion", "location": "Back Yard"}),
                ("sensor", "Window Sensor", {
                    "sensor_type": "door", "location": "Living Room Window"}),
            ]
            
        elif scenario == "comfort":
            # Comfort and automation focused
            devices_to_create = [
                ("thermostat", "Living Room Thermostat", {"location": "Living Room"}),
                ("thermostat", "Bedroom Thermostat", {"location": "Bedroom"}),
                ("light", "Living Room Lights", {"location": "Living Room"}),
                ("light", "Bedroom Lights", {"location": "Bedroom"}),
                ("light", "Kitchen Lights", {"location": "Kitchen"}),
                ("sensor", "Temperature Sensor", {
                    "sensor_type": "temperature", "location": "Living Room"}),
                ("sensor", "Humidity Sensor", {
                    "sensor_type": "humidity", "location": "Bedroom"}),
                ("switch", "Fan", {"location": "Bedroom"}),
            ]
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        # Create devices
        created_devices = []
        for device_type, name, kwargs in devices_to_create:
            device = self.create_device(device_type, name, **kwargs)
            created_devices.append(device)
        
        # If there's a hub, connect other devices to it
        hubs = [d for d in created_devices if isinstance(d, SimulatedHub)]
        if hubs:
            hub = hubs[0]
            for device in created_devices:
                if device != hub:
                    hub.add_connected_device(device)
        
        logger.info(f"Created {len(created_devices)} devices for scenario '{scenario}'")
        return created_devices
    
    def _update_device_environment(self, device: BaseSimulatedDevice) -> None:
        """Update a device's environmental factors."""
        conditions = self.environmental_sim.get_conditions()
        
        for factor, value in conditions.items():
            device.update_environmental_factor(factor, value)
    
    async def _handle_device_event(self, event: DeviceEvent) -> None:
        """Handle events from devices."""
        self.stats["events_processed"] += 1
        
        # Add to event log
        self.event_log.append(event.to_dict())
        
        # Notify listeners
        for listener in self.event_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
    
    async def _orchestrate(self) -> None:
        """Main orchestration loop."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Orchestrate every 30 seconds
                
                # Update environmental factors for all devices
                if self.config.environmental_updates:
                    for device in self.devices.values():
                        self._update_device_environment(device)
                
                # Perform periodic maintenance
                await self._perform_maintenance()
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
    
    async def _perform_maintenance(self) -> None:
        """Perform periodic maintenance tasks."""
        # Clean up old events (keep last 1000)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]
        
        # Update uptime statistic
        if self._start_time:
            self.stats["uptime"] = (datetime.utcnow() - self._start_time).total_seconds()
    
    async def _log_events(self) -> None:
        """Periodically save events to file."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Save every 5 minutes
                await self._save_event_log()
            except Exception as e:
                logger.error(f"Error in event logger: {e}")
    
    async def _save_event_log(self) -> None:
        """Save event log to file."""
        if not self.event_log or not self.config.event_log_path:
            return
        
        try:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "stats": self.get_statistics(),
                "events": self.event_log[-100:]  # Save last 100 events
            }
            
            log_path = Path(self.config.event_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
                
            logger.debug(f"Saved event log to {log_path}")
            
        except Exception as e:
            logger.error(f"Failed to save event log: {e}")
    
    async def export_configuration(self, file_path: str) -> None:
        """Export current simulator configuration."""
        config_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "environmental_conditions": self.environmental_sim.get_conditions(),
            "devices": [
                {
                    "id": device.device_id,
                    "type": device.device_class,
                    "name": device.name,
                    "brand": device.brand,
                    "model": device.model,
                    "location": device.location,
                    "configuration": device.to_dict()
                }
                for device in self.devices.values()
            ],
            "statistics": self.get_statistics()
        }
        
        config_path = Path(file_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        logger.info(f"Exported configuration to {config_path}")
    
    async def import_configuration(self, file_path: str) -> None:
        """Import simulator configuration from file."""
        config_path = Path(file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Clear existing devices
        for device_id in list(self.devices.keys()):
            await self.remove_device(device_id)
        
        # Apply environmental conditions
        if "environmental_conditions" in config_data:
            for condition, value in config_data["environmental_conditions"].items():
                self.environmental_sim.set_condition(condition, value)
        
        # Recreate devices
        for device_config in config_data.get("devices", []):
            device_type = device_config["type"]
            if "sensor_" in device_type:
                device_type = "sensor"
                sensor_type = device_config["type"].replace("sensor_", "")
                device_config["sensor_type"] = sensor_type
            
            self.create_device(
                device_type=device_type,
                name=device_config["name"],
                brand=device_config.get("brand", "Generic"),
                model=device_config.get("model", "Model-X"),
                location=device_config.get("location", "Unknown")
            )
        
        logger.info(f"Imported configuration from {file_path}")
        logger.info(f"Created {len(self.devices)} devices")