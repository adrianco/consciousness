"""
Demo device simulator for the House Consciousness System.
Provides simulated smart home devices when real devices aren't available.
"""

import random
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SimulatedDevice:
    """Represents a simulated smart home device."""

    id: str
    name: str
    type: str
    status: str
    location: str
    properties: Dict[str, Any]
    last_seen: str
    discovery_method: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return asdict(self)


class DeviceSimulator:
    """Manages simulated smart home devices for demo purposes."""

    def __init__(self):
        self.devices: Dict[str, SimulatedDevice] = {}
        self.demo_mode = False
        self._initialize_demo_devices()

    def enable_demo_mode(self):
        """Enable demo mode with simulated devices."""
        self.demo_mode = True
        self._initialize_demo_devices()

    def disable_demo_mode(self):
        """Disable demo mode and clear simulated devices."""
        self.demo_mode = False
        self.devices.clear()

    def _initialize_demo_devices(self):
        """Create initial set of demo devices."""
        demo_devices = [
            SimulatedDevice(
                id="thermostat-main",
                name="Main Thermostat",
                type="thermostat",
                status="online",
                location="living_room",
                properties={
                    "current_temp": 72,
                    "target_temp": 72,
                    "mode": "auto",
                    "humidity": 45,
                    "battery": 100,
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="upnp",
            ),
            SimulatedDevice(
                id="lights-kitchen",
                name="Kitchen Smart Lights",
                type="smart_light",
                status="online",
                location="kitchen",
                properties={
                    "brightness": 80,
                    "color": "warm_white",
                    "power": True,
                    "energy_usage": 12.5,
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="mdns",
            ),
            SimulatedDevice(
                id="camera-front-door",
                name="Front Door Camera",
                type="security_camera",
                status="online",
                location="front_door",
                properties={
                    "recording": True,
                    "motion_detection": True,
                    "night_vision": True,
                    "wifi_signal": -45,
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="upnp",
            ),
            SimulatedDevice(
                id="sensor-living-room",
                name="Living Room Motion Sensor",
                type="motion_sensor",
                status="online",
                location="living_room",
                properties={
                    "motion_detected": False,
                    "battery": 85,
                    "sensitivity": "medium",
                    "last_motion": "2025-06-24T22:30:00",
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="bluetooth",
            ),
            SimulatedDevice(
                id="speaker-bedroom",
                name="Bedroom Smart Speaker",
                type="smart_speaker",
                status="online",
                location="bedroom",
                properties={
                    "volume": 30,
                    "playing": False,
                    "current_track": "None",
                    "wifi_signal": -38,
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="mdns",
            ),
            SimulatedDevice(
                id="lock-front-door",
                name="Smart Door Lock",
                type="smart_lock",
                status="online",
                location="front_door",
                properties={
                    "locked": True,
                    "battery": 78,
                    "auto_lock": True,
                    "unlock_methods": ["key", "code", "app"],
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="bluetooth",
            ),
            SimulatedDevice(
                id="garage-door",
                name="Garage Door Opener",
                type="garage_door",
                status="online",
                location="garage",
                properties={
                    "open": False,
                    "wifi_signal": -52,
                    "last_operation": "2025-06-24T18:45:00",
                    "remote_access": True,
                },
                last_seen=datetime.now().isoformat(),
                discovery_method="upnp",
            ),
        ]

        for device in demo_devices:
            self.devices[device.id] = device

    def get_all_devices(self) -> List[Dict[str, Any]]:
        """Get all discovered devices."""
        return [device.to_dict() for device in self.devices.values()]

    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get a specific device by ID."""
        device = self.devices.get(device_id)
        if device:
            return device.to_dict()
        return {}

    def add_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new simulated device."""
        device_id = device_data.get("id", f"device-{len(self.devices) + 1}")

        device = SimulatedDevice(
            id=device_id,
            name=device_data.get("name", f"Device {device_id}"),
            type=device_data.get("type", "unknown"),
            status=device_data.get("status", "online"),
            location=device_data.get("location", "unknown"),
            properties=device_data.get("properties", {}),
            last_seen=datetime.now().isoformat(),
            discovery_method=device_data.get("discovery_method", "manual"),
        )

        self.devices[device_id] = device
        return device.to_dict()

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing device."""
        if device_id in self.devices:
            device = self.devices[device_id]

            # Update basic properties
            if "name" in updates:
                device.name = updates["name"]
            if "status" in updates:
                device.status = updates["status"]
            if "location" in updates:
                device.location = updates["location"]
            if "properties" in updates:
                device.properties.update(updates["properties"])

            device.last_seen = datetime.now().isoformat()
            return device.to_dict()

        return {}

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the simulator."""
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False

    def simulate_device_activity(self):
        """Simulate realistic device activity and property changes."""
        for device in self.devices.values():
            # Update last_seen for all online devices
            if device.status == "online":
                device.last_seen = datetime.now().isoformat()

            # Device-specific activity simulation
            if device.type == "thermostat":
                # Slightly vary temperature
                current = device.properties.get("current_temp", 72)
                device.properties["current_temp"] = current + random.uniform(-0.5, 0.5)
                device.properties["humidity"] = random.randint(40, 60)

            elif device.type == "motion_sensor":
                # Randomly trigger motion
                if random.random() < 0.1:  # 10% chance
                    device.properties["motion_detected"] = True
                    device.properties["last_motion"] = datetime.now().isoformat()
                else:
                    device.properties["motion_detected"] = False

            elif device.type == "smart_light":
                # Slightly vary energy usage based on brightness
                brightness = device.properties.get("brightness", 80)
                device.properties["energy_usage"] = round(brightness * 0.15, 1)

    def get_device_count(self) -> int:
        """Get total number of devices."""
        return len(self.devices)

    def get_device_summary(self) -> Dict[str, Any]:
        """Get summary statistics about devices."""
        online_count = sum(1 for d in self.devices.values() if d.status == "online")
        offline_count = len(self.devices) - online_count

        types = {}
        locations = {}
        discovery_methods = {}

        for device in self.devices.values():
            types[device.type] = types.get(device.type, 0) + 1
            locations[device.location] = locations.get(device.location, 0) + 1
            discovery_methods[device.discovery_method] = (
                discovery_methods.get(device.discovery_method, 0) + 1
            )

        return {
            "total_devices": len(self.devices),
            "online_devices": online_count,
            "offline_devices": offline_count,
            "device_types": types,
            "locations": locations,
            "discovery_methods": discovery_methods,
            "demo_mode": self.demo_mode,
        }


# Global device simulator instance
device_simulator = DeviceSimulator()
