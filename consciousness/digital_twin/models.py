"""Digital Twin models for house representation."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

import numpy as np


class DeviceState(Enum):
    """Device states in the digital twin."""
    
    OFFLINE = "offline"
    ONLINE = "online"
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    SIMULATED = "simulated"
    SYNCING = "syncing"


class SyncStatus(Enum):
    """Synchronization status between real and virtual."""
    
    SYNCHRONIZED = "synchronized"
    OUT_OF_SYNC = "out_of_sync"
    SYNCING = "syncing"
    NO_REAL_DEVICE = "no_real_device"
    ERROR = "error"


@dataclass
class Position3D:
    """3D position representation."""
    
    x: float
    y: float
    z: float
    
    def distance_to(self, other: "Position3D") -> float:
        """Calculate Euclidean distance to another position."""
        return np.sqrt(
            (self.x - other.x) ** 2 + 
            (self.y - other.y) ** 2 + 
            (self.z - other.z) ** 2
        )


@dataclass
class Dimensions3D:
    """3D dimensions for objects."""
    
    width: float  # x-axis
    depth: float  # y-axis 
    height: float  # z-axis
    
    @property
    def volume(self) -> float:
        """Calculate volume."""
        return self.width * self.depth * self.height
    
    @property
    def floor_area(self) -> float:
        """Calculate floor area."""
        return self.width * self.depth


@dataclass
class EnvironmentalState:
    """Environmental conditions in a space."""
    
    temperature: float  # Celsius
    humidity: float  # Percentage
    light_level: float  # Lux
    co2_level: float  # PPM
    noise_level: float  # Decibels
    air_quality_index: float  # 0-500 scale
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def comfort_score(self) -> float:
        """Calculate overall comfort score (0-1)."""
        # Ideal ranges
        temp_ideal = 21.0  # Celsius
        humidity_ideal = 45.0  # Percentage
        
        # Calculate deviations
        temp_score = max(0, 1 - abs(self.temperature - temp_ideal) / 10)
        humidity_score = max(0, 1 - abs(self.humidity - humidity_ideal) / 30)
        light_score = min(1, self.light_level / 500) if self.light_level > 0 else 0
        co2_score = max(0, 1 - (self.co2_level - 400) / 1000)
        noise_score = max(0, 1 - self.noise_level / 80)
        air_score = max(0, 1 - self.air_quality_index / 200)
        
        # Weighted average
        weights = [0.3, 0.2, 0.15, 0.15, 0.1, 0.1]
        scores = [temp_score, humidity_score, light_score, co2_score, noise_score, air_score]
        
        return sum(w * s for w, s in zip(weights, scores))


@dataclass
class TwinState:
    """State representation for digital twin entities."""
    
    entity_id: str
    entity_type: str
    sync_status: SyncStatus
    real_state: Dict[str, Any]
    virtual_state: Dict[str, Any]
    last_sync: datetime
    sync_errors: List[str] = field(default_factory=list)
    
    def get_divergence(self) -> Dict[str, Tuple[Any, Any]]:
        """Get differences between real and virtual states."""
        divergence = {}
        all_keys = set(self.real_state.keys()) | set(self.virtual_state.keys())
        
        for key in all_keys:
            real_val = self.real_state.get(key)
            virtual_val = self.virtual_state.get(key)
            if real_val != virtual_val:
                divergence[key] = (real_val, virtual_val)
                
        return divergence
    
    def is_synchronized(self) -> bool:
        """Check if states are synchronized."""
        return len(self.get_divergence()) == 0


class IDigitalTwinEntity(Protocol):
    """Protocol for digital twin entities."""
    
    id: str
    name: str
    position: Position3D
    dimensions: Dimensions3D
    metadata: Dict[str, Any]
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """Update entity state."""
        ...
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state."""
        ...
    
    def simulate_tick(self, delta_time: float) -> None:
        """Simulate one time step."""
        ...


@dataclass
class DigitalTwinDevice:
    """Digital twin representation of a device."""
    
    id: str
    name: str
    device_type: str
    device_class: str
    position: Position3D
    dimensions: Dimensions3D
    room_id: str
    
    # State management
    state: DeviceState = DeviceState.OFFLINE
    current_values: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Simulation properties
    power_consumption: float = 0.0  # Watts
    heat_generation: float = 0.0  # Watts
    noise_generation: float = 0.0  # Decibels
    
    # Real device mapping
    real_device_id: Optional[int] = None
    last_sync_time: Optional[datetime] = None
    sync_status: SyncStatus = SyncStatus.NO_REAL_DEVICE
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """Update device state."""
        self.current_values.update(state)
        if "power" in state:
            self.state = DeviceState.ACTIVE if state["power"] else DeviceState.IDLE
            
    def get_state(self) -> Dict[str, Any]:
        """Get current device state."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.device_type,
            "state": self.state.value,
            "values": self.current_values.copy(),
            "position": {
                "x": self.position.x,
                "y": self.position.y,
                "z": self.position.z,
            },
            "power_consumption": self.power_consumption,
            "sync_status": self.sync_status.value,
        }
    
    def simulate_tick(self, delta_time: float) -> None:
        """Simulate device behavior for one time step."""
        # Update power consumption based on state
        if self.state == DeviceState.ACTIVE:
            # Simulate device-specific behavior
            if self.device_class == "light":
                brightness = self.current_values.get("brightness", 0)
                self.power_consumption = 10 * (brightness / 100)  # 10W max
                self.heat_generation = self.power_consumption * 0.9  # 90% heat
            elif self.device_class == "climate":
                if self.current_values.get("hvac_mode") == "heat":
                    self.power_consumption = 2000  # 2kW heating
                    self.heat_generation = 2000
                elif self.current_values.get("hvac_mode") == "cool":
                    self.power_consumption = 1500  # 1.5kW cooling
                    self.heat_generation = -1000  # Cooling effect
        else:
            self.power_consumption = 0.5  # Standby power
            self.heat_generation = 0.5


@dataclass
class DigitalTwinRoom:
    """Digital twin representation of a room."""
    
    id: str
    name: str
    room_type: str
    floor_id: str
    position: Position3D  # Corner position
    dimensions: Dimensions3D
    
    # Environmental state
    environmental_state: EnvironmentalState = field(
        default_factory=lambda: EnvironmentalState(
            temperature=20.0,
            humidity=50.0,
            light_level=0.0,
            co2_level=400.0,
            noise_level=30.0,
            air_quality_index=50.0,
        )
    )
    
    # Room properties
    windows: List[Dict[str, Any]] = field(default_factory=list)
    doors: List[Dict[str, Any]] = field(default_factory=list)
    thermal_mass: float = 50000.0  # J/K - heat capacity
    
    # Devices in room
    devices: Dict[str, DigitalTwinDevice] = field(default_factory=dict)
    
    # Occupancy
    occupants: Set[str] = field(default_factory=set)
    max_occupancy: int = 4
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_device(self, device: DigitalTwinDevice) -> None:
        """Add a device to the room."""
        self.devices[device.id] = device
        device.room_id = self.id
        
    def remove_device(self, device_id: str) -> None:
        """Remove a device from the room."""
        if device_id in self.devices:
            del self.devices[device_id]
            
    def get_total_power_consumption(self) -> float:
        """Calculate total power consumption of all devices."""
        return sum(device.power_consumption for device in self.devices.values())
    
    def get_total_heat_generation(self) -> float:
        """Calculate total heat generation from all devices."""
        return sum(device.heat_generation for device in self.devices.values())
    
    def update_environmental_state(self, state: EnvironmentalState) -> None:
        """Update room environmental state."""
        self.environmental_state = state
        
    def simulate_tick(self, delta_time: float, external_temp: float = 15.0) -> None:
        """Simulate room environment for one time step."""
        # Simulate devices
        for device in self.devices.values():
            device.simulate_tick(delta_time)
            
        # Simple thermal model
        heat_from_devices = self.get_total_heat_generation()
        heat_from_occupants = len(self.occupants) * 100  # 100W per person
        
        # Heat transfer through walls (simplified)
        wall_area = 2 * (self.dimensions.width + self.dimensions.depth) * self.dimensions.height
        u_value = 0.3  # W/m²K - typical insulated wall
        heat_loss = u_value * wall_area * (self.environmental_state.temperature - external_temp)
        
        # Temperature change
        total_heat = heat_from_devices + heat_from_occupants - heat_loss
        temp_change = (total_heat * delta_time) / self.thermal_mass
        self.environmental_state.temperature += temp_change
        
        # Update CO2 from occupants
        co2_generation = len(self.occupants) * 20  # 20 PPM/hour per person
        room_volume = self.dimensions.volume
        air_changes = 0.5  # Air changes per hour
        
        co2_change = (co2_generation - self.environmental_state.co2_level * air_changes) * delta_time / 3600
        self.environmental_state.co2_level += co2_change
        
        # Update light level based on lights
        total_lumens = 0
        for device in self.devices.values():
            if device.device_class == "light" and device.state == DeviceState.ACTIVE:
                brightness = device.current_values.get("brightness", 0) / 100
                total_lumens += 800 * brightness  # Assume 800 lumens per bulb
                
        self.environmental_state.light_level = total_lumens / self.dimensions.floor_area
        
        # Update timestamp
        self.environmental_state.timestamp = datetime.utcnow()


@dataclass
class DigitalTwinFloor:
    """Digital twin representation of a floor."""
    
    id: str
    name: str
    level: int  # 0 = ground floor, 1 = first floor, etc.
    house_id: str
    height: float  # Floor height in meters
    
    # Rooms on this floor
    rooms: Dict[str, DigitalTwinRoom] = field(default_factory=dict)
    
    # Floor plan
    floor_plan: Optional[Dict[str, Any]] = None
    total_area: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_room(self, room: DigitalTwinRoom) -> None:
        """Add a room to the floor."""
        self.rooms[room.id] = room
        room.floor_id = self.id
        self._update_total_area()
        
    def remove_room(self, room_id: str) -> None:
        """Remove a room from the floor."""
        if room_id in self.rooms:
            del self.rooms[room_id]
            self._update_total_area()
            
    def _update_total_area(self) -> None:
        """Update total floor area."""
        self.total_area = sum(room.dimensions.floor_area for room in self.rooms.values())
        
    def get_average_temperature(self) -> float:
        """Calculate average temperature across all rooms."""
        if not self.rooms:
            return 20.0
        return np.mean([room.environmental_state.temperature for room in self.rooms.values()])
    
    def get_occupancy(self) -> Dict[str, int]:
        """Get occupancy per room."""
        return {room_id: len(room.occupants) for room_id, room in self.rooms.items()}
    
    def simulate_tick(self, delta_time: float, external_temp: float = 15.0) -> None:
        """Simulate floor for one time step."""
        # Simulate each room
        for room in self.rooms.values():
            room.simulate_tick(delta_time, external_temp)
            
        # Heat transfer between adjacent rooms (simplified)
        room_list = list(self.rooms.values())
        for i, room1 in enumerate(room_list):
            for room2 in room_list[i+1:]:
                # Check if rooms are adjacent (simplified - just check if they share a wall)
                if self._are_rooms_adjacent(room1, room2):
                    # Heat transfer
                    temp_diff = room1.environmental_state.temperature - room2.environmental_state.temperature
                    heat_transfer = 50 * temp_diff * delta_time / 3600  # Simplified model
                    
                    # Update temperatures
                    room1.environmental_state.temperature -= heat_transfer / room1.thermal_mass
                    room2.environmental_state.temperature += heat_transfer / room2.thermal_mass
    
    def _are_rooms_adjacent(self, room1: DigitalTwinRoom, room2: DigitalTwinRoom) -> bool:
        """Check if two rooms share a wall (simplified)."""
        # Simplified check - rooms are adjacent if they're close enough
        distance = room1.position.distance_to(room2.position)
        max_dimension = max(room1.dimensions.width, room1.dimensions.depth, 
                          room2.dimensions.width, room2.dimensions.depth)
        return distance < max_dimension * 1.5


@dataclass
class DigitalTwinHouse:
    """Digital twin representation of an entire house."""
    
    id: str
    name: str
    address: str
    position: Position3D  # GPS coordinates or relative position
    
    # Structure
    floors: Dict[str, DigitalTwinFloor] = field(default_factory=dict)
    total_floors: int = 1
    total_area: float = 0.0
    
    # Systems
    all_devices: Dict[str, DigitalTwinDevice] = field(default_factory=dict)
    
    # Environmental
    external_temperature: float = 15.0
    external_humidity: float = 60.0
    weather_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Energy
    total_power_consumption: float = 0.0
    energy_sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Occupancy
    residents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    current_occupancy: int = 0
    
    # Metadata
    timezone: str = "UTC"
    preferences: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_floor(self, floor: DigitalTwinFloor) -> None:
        """Add a floor to the house."""
        self.floors[floor.id] = floor
        floor.house_id = self.id
        self._update_totals()
        
    def add_device(self, device: DigitalTwinDevice, room_id: str) -> None:
        """Add a device to a specific room."""
        self.all_devices[device.id] = device
        
        # Find the room and add device
        for floor in self.floors.values():
            if room_id in floor.rooms:
                floor.rooms[room_id].add_device(device)
                break
                
    def remove_device(self, device_id: str) -> None:
        """Remove a device from the house."""
        if device_id in self.all_devices:
            device = self.all_devices[device_id]
            
            # Remove from room
            for floor in self.floors.values():
                for room in floor.rooms.values():
                    if device_id in room.devices:
                        room.remove_device(device_id)
                        break
                        
            del self.all_devices[device_id]
            
    def _update_totals(self) -> None:
        """Update total area and other aggregates."""
        self.total_area = sum(floor.total_area for floor in self.floors.values())
        self.total_floors = len(self.floors)
        
    def get_all_rooms(self) -> List[DigitalTwinRoom]:
        """Get all rooms in the house."""
        rooms = []
        for floor in self.floors.values():
            rooms.extend(floor.rooms.values())
        return rooms
    
    def find_room_by_id(self, room_id: str) -> Optional[DigitalTwinRoom]:
        """Find a room by its ID."""
        for floor in self.floors.values():
            if room_id in floor.rooms:
                return floor.rooms[room_id]
        return None
    
    def get_environmental_summary(self) -> Dict[str, Any]:
        """Get summary of environmental conditions."""
        all_rooms = self.get_all_rooms()
        if not all_rooms:
            return {}
            
        return {
            "average_temperature": np.mean([r.environmental_state.temperature for r in all_rooms]),
            "average_humidity": np.mean([r.environmental_state.humidity for r in all_rooms]),
            "average_co2": np.mean([r.environmental_state.co2_level for r in all_rooms]),
            "total_light_level": sum(r.environmental_state.light_level for r in all_rooms),
            "comfort_scores": {r.id: r.environmental_state.comfort_score() for r in all_rooms},
        }
    
    def update_occupancy(self, person_id: str, room_id: Optional[str] = None) -> None:
        """Update person's location in the house."""
        # Remove person from all rooms
        for room in self.get_all_rooms():
            room.occupants.discard(person_id)
            
        # Add to new room if specified
        if room_id:
            room = self.find_room_by_id(room_id)
            if room:
                room.occupants.add(person_id)
                
        # Update total occupancy
        self.current_occupancy = sum(len(r.occupants) for r in self.get_all_rooms())
        
    def simulate_tick(self, delta_time: float) -> None:
        """Simulate entire house for one time step."""
        # Update external conditions (could be connected to weather service)
        self._update_external_conditions()
        
        # Simulate each floor
        for floor in self.floors.values():
            floor.simulate_tick(delta_time, self.external_temperature)
            
        # Update totals
        self.total_power_consumption = sum(
            device.power_consumption for device in self.all_devices.values()
        )
        
    def _update_external_conditions(self) -> None:
        """Update external environmental conditions."""
        # This would normally connect to a weather service
        # For now, simple daily temperature variation
        hour = datetime.utcnow().hour
        self.external_temperature = 15 + 5 * np.sin((hour - 6) * np.pi / 12)
        
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get complete state snapshot of the house."""
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": datetime.utcnow().isoformat(),
            "structure": {
                "floors": self.total_floors,
                "total_area": self.total_area,
                "rooms": len(self.get_all_rooms()),
                "devices": len(self.all_devices),
            },
            "environmental": self.get_environmental_summary(),
            "energy": {
                "total_power_consumption": self.total_power_consumption,
                "devices_active": sum(1 for d in self.all_devices.values() if d.state == DeviceState.ACTIVE),
            },
            "occupancy": {
                "current": self.current_occupancy,
                "by_room": {floor.id: floor.get_occupancy() for floor in self.floors.values()},
            },
            "external": {
                "temperature": self.external_temperature,
                "humidity": self.external_humidity,
                "weather": self.weather_conditions,
            },
        }