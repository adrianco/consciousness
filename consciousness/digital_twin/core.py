"""Core digital twin management system."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..models.entities import Device, House, Person, Room
from ..models.events import Event
from .models import (
    DeviceState,
    DigitalTwinDevice,
    DigitalTwinFloor,
    DigitalTwinHouse,
    DigitalTwinRoom,
    Dimensions3D,
    Position3D,
    SyncStatus,
)
from .simulation import EnvironmentalSimulator
from .synchronization import StateSynchronizer


class DigitalTwinManager:
    """Manages digital twin instances and their synchronization with real systems."""
    
    def __init__(self):
        self.houses: Dict[str, DigitalTwinHouse] = {}
        self.synchronizer = StateSynchronizer()
        self.simulators: Dict[str, EnvironmentalSimulator] = {}
        self.is_running = False
        
        # Event tracking
        self.event_handlers: Dict[str, callable] = {}
        
    async def initialize(self):
        """Initialize the digital twin manager."""
        await self.synchronizer.start()
        print("🏠 Digital Twin Manager initialized")
        
    async def start(self):
        """Start the digital twin system."""
        if not self.is_running:
            await self.initialize()
            
        self.is_running = True
        
        # Start simulators for all houses
        for house_id, simulator in self.simulators.items():
            await simulator.start()
            
        print("🚀 Digital Twin system started")
        
    async def stop(self):
        """Stop the digital twin system."""
        self.is_running = False
        
        # Stop all simulators
        for simulator in self.simulators.values():
            await simulator.stop()
            
        await self.synchronizer.stop()
        print("⏹️ Digital Twin system stopped")
        
    async def create_house_twin(self, house_id: int) -> Optional[DigitalTwinHouse]:
        """Create a digital twin for a real house."""
        async with get_async_session() as session:
            # Get house data
            house = await session.get(House, house_id)
            if not house:
                return None
                
            # Create digital twin house
            twin_house = DigitalTwinHouse(
                id=f"house_{house.id}",
                name=house.name,
                address=house.address or "",
                position=Position3D(0, 0, 0),  # Could be GPS coordinates
                timezone=house.timezone,
                preferences=house.preferences,
                capabilities=house.capabilities,
            )
            
            # Load rooms
            await self._load_house_rooms(session, house, twin_house)
            
            # Load devices
            await self._load_house_devices(session, house, twin_house)
            
            # Load residents
            await self._load_house_residents(session, house, twin_house)
            
            # Store the twin
            self.houses[twin_house.id] = twin_house
            
            # Create and start simulator
            simulator = EnvironmentalSimulator(twin_house)
            self.simulators[twin_house.id] = simulator
            if self.is_running:
                await simulator.start()
                
            # Log creation event
            await self._log_event(
                session,
                "twin_created",
                f"Digital twin created for house: {house.name}",
                {"house_id": house.id, "twin_id": twin_house.id},
            )
            
            return twin_house
            
    async def _load_house_rooms(
        self, session: AsyncSession, house: House, twin_house: DigitalTwinHouse
    ):
        """Load rooms for the house twin."""
        floor_rooms: Dict[int, List[Room]] = {}
        
        # Group rooms by floor
        for room in house.rooms:
            floor_num = room.floor or 0
            if floor_num not in floor_rooms:
                floor_rooms[floor_num] = []
            floor_rooms[floor_num].append(room)
            
        # Create floors and rooms
        for floor_num, rooms in floor_rooms.items():
            # Create floor
            floor_id = f"floor_{floor_num}_{house.id}"
            twin_floor = DigitalTwinFloor(
                id=floor_id,
                name=f"Floor {floor_num}",
                level=floor_num,
                house_id=twin_house.id,
                height=2.5,  # Default ceiling height
            )
            
            # Add rooms to floor
            for i, room in enumerate(rooms):
                # Position rooms in a simple grid layout
                grid_x = (i % 3) * 5  # 5 meter spacing
                grid_y = (i // 3) * 5
                
                twin_room = DigitalTwinRoom(
                    id=f"room_{room.id}",
                    name=room.name,
                    room_type=room.room_type,
                    floor_id=floor_id,
                    position=Position3D(grid_x, grid_y, floor_num * 2.5),
                    dimensions=Dimensions3D(
                        width=room.square_footage ** 0.5 if room.square_footage else 4.0,
                        depth=room.square_footage ** 0.5 if room.square_footage else 4.0,
                        height=room.ceiling_height or 2.5,
                    ),
                    windows=[{"area": 2.0}] * (room.windows or 1),
                    doors=[{"area": 2.0}] * (room.doors or 1),
                )
                
                # Set preferred environmental conditions
                if room.preferred_temperature:
                    twin_room.environmental_state.temperature = room.preferred_temperature
                if room.preferred_humidity:
                    twin_room.environmental_state.humidity = room.preferred_humidity
                    
                twin_floor.add_room(twin_room)
                
            twin_house.add_floor(twin_floor)
            
    async def _load_house_devices(
        self, session: AsyncSession, house: House, twin_house: DigitalTwinHouse
    ):
        """Load devices for the house twin."""
        for device in house.devices:
            # Find the room for this device
            room_id = f"room_{device.room_id}" if device.room_id else None
            
            # Create twin device
            twin_device = DigitalTwinDevice(
                id=f"device_{device.id}",
                name=device.user_name,
                device_type=device.integration_type,
                device_class=device.device_class,
                position=Position3D(0, 0, 1),  # Default position
                dimensions=Dimensions3D(0.3, 0.3, 0.3),  # Default size
                room_id=room_id or "",
                capabilities=device.supported_features,
                metadata={
                    "brand": device.detected_brand,
                    "model": device.detected_model,
                    "connection": device.connection_method,
                },
                real_device_id=device.id,
            )
            
            # Set initial state
            if device.current_state:
                twin_device.update_state(device.current_state)
                
            # Determine sync status
            if device.status == "online":
                twin_device.sync_status = SyncStatus.SYNCHRONIZED
                twin_device.state = DeviceState.ONLINE
            else:
                twin_device.sync_status = SyncStatus.OUT_OF_SYNC
                twin_device.state = DeviceState.OFFLINE
                
            # Add to house
            if room_id:
                twin_house.add_device(twin_device, room_id)
            else:
                twin_house.all_devices[twin_device.id] = twin_device
                
            # Register with synchronizer
            self.synchronizer.register_device_mapping(device.id, twin_device.id)
            
    async def _load_house_residents(
        self, session: AsyncSession, house: House, twin_house: DigitalTwinHouse
    ):
        """Load residents for the house twin."""
        for person in house.people:
            twin_house.residents[str(person.id)] = {
                "name": person.name,
                "role": person.role,
                "preferences": person.preferences,
                "is_present": person.is_present,
                "last_seen": person.last_seen.isoformat() if person.last_seen else None,
            }
            
            # If person is present, add to a default room
            if person.is_present:
                rooms = twin_house.get_all_rooms()
                if rooms:
                    # Add to first living room, or first room if no living room
                    living_rooms = [r for r in rooms if "living" in r.room_type.lower()]
                    default_room = living_rooms[0] if living_rooms else rooms[0]
                    twin_house.update_occupancy(str(person.id), default_room.id)
                    
    async def get_house_twin(self, house_id: str) -> Optional[DigitalTwinHouse]:
        """Get a house digital twin."""
        return self.houses.get(house_id)
        
    async def update_device_state(
        self, house_id: str, device_id: str, state_changes: Dict[str, Any]
    ) -> bool:
        """Update device state in digital twin."""
        house = self.houses.get(house_id)
        if not house:
            return False
            
        device = house.all_devices.get(device_id)
        if not device:
            return False
            
        # Update virtual state
        old_state = device.get_state()
        device.update_state(state_changes)
        
        # Sync to real device if needed
        if device.real_device_id:
            await self.synchronizer.sync_from_twin(device, state_changes)
            
        # Log state change event
        async with get_async_session() as session:
            await self._log_event(
                session,
                "device_state_changed",
                f"Device state updated: {device.name}",
                {
                    "house_id": house_id,
                    "device_id": device_id,
                    "old_state": old_state,
                    "new_state": device.get_state(),
                    "changes": state_changes,
                },
            )
            
        return True
        
    async def update_occupancy(
        self, house_id: str, person_id: str, room_id: Optional[str] = None
    ) -> bool:
        """Update person's location in the house."""
        house = self.houses.get(house_id)
        if not house:
            return False
            
        house.update_occupancy(person_id, room_id)
        
        # Log occupancy change
        async with get_async_session() as session:
            await self._log_event(
                session,
                "occupancy_changed",
                f"Person moved: {person_id}",
                {
                    "house_id": house_id,
                    "person_id": person_id,
                    "room_id": room_id,
                    "total_occupancy": house.current_occupancy,
                },
            )
            
        return True
        
    async def get_house_state(self, house_id: str) -> Optional[Dict[str, Any]]:
        """Get complete house state snapshot."""
        house = self.houses.get(house_id)
        if not house:
            return None
            
        return house.get_state_snapshot()
        
    async def get_room_state(self, house_id: str, room_id: str) -> Optional[Dict[str, Any]]:
        """Get room state snapshot."""
        house = self.houses.get(house_id)
        if not house:
            return None
            
        room = house.find_room_by_id(room_id)
        if not room:
            return None
            
        return {
            "id": room.id,
            "name": room.name,
            "type": room.room_type,
            "environmental": {
                "temperature": room.environmental_state.temperature,
                "humidity": room.environmental_state.humidity,
                "light_level": room.environmental_state.light_level,
                "co2_level": room.environmental_state.co2_level,
                "noise_level": room.environmental_state.noise_level,
                "air_quality": room.environmental_state.air_quality_index,
                "comfort_score": room.environmental_state.comfort_score(),
            },
            "occupancy": {
                "occupants": list(room.occupants),
                "count": len(room.occupants),
            },
            "devices": {
                device_id: device.get_state()
                for device_id, device in room.devices.items()
            },
            "energy": {
                "power_consumption": room.get_total_power_consumption(),
                "heat_generation": room.get_total_heat_generation(),
            },
        }
        
    async def get_device_state(
        self, house_id: str, device_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get device state snapshot."""
        house = self.houses.get(house_id)
        if not house:
            return None
            
        device = house.all_devices.get(device_id)
        if not device:
            return None
            
        state = device.get_state()
        
        # Add sync information
        sync_state = self.synchronizer.get_sync_state(device_id)
        if sync_state:
            state["sync"] = {
                "status": sync_state.sync_status.value,
                "last_sync": sync_state.last_sync.isoformat(),
                "errors": sync_state.sync_errors,
                "divergence": sync_state.get_divergence(),
            }
            
        return state
        
    async def set_simulation_rate(self, house_id: str, rate: float) -> bool:
        """Set simulation speed for a house."""
        simulator = self.simulators.get(house_id)
        if not simulator:
            return False
            
        simulator.set_simulation_rate(rate)
        return True
        
    async def add_weather_event(
        self, house_id: str, event_type: str, duration_hours: float, intensity: float
    ) -> bool:
        """Add a weather event to house simulation."""
        simulator = self.simulators.get(house_id)
        if not simulator:
            return False
            
        simulator.add_weather_event(event_type, duration_hours, intensity)
        
        # Log weather event
        async with get_async_session() as session:
            await self._log_event(
                session,
                "weather_event_added",
                f"Weather event added: {event_type}",
                {
                    "house_id": house_id,
                    "event_type": event_type,
                    "duration_hours": duration_hours,
                    "intensity": intensity,
                },
            )
            
        return True
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        sync_metrics = await self.synchronizer.get_sync_metrics()
        
        house_statuses = {}
        for house_id, house in self.houses.items():
            simulator = self.simulators.get(house_id)
            house_statuses[house_id] = {
                "name": house.name,
                "rooms": len(house.get_all_rooms()),
                "devices": len(house.all_devices),
                "occupancy": house.current_occupancy,
                "power_consumption": house.total_power_consumption,
                "simulation": simulator.get_simulation_status() if simulator else None,
            }
            
        return {
            "is_running": self.is_running,
            "houses": house_statuses,
            "synchronization": sync_metrics,
            "total_houses": len(self.houses),
            "total_devices": sum(len(h.all_devices) for h in self.houses.values()),
        }
        
    async def _log_event(
        self,
        session: AsyncSession,
        event_type: str,
        title: str,
        event_data: Dict[str, Any],
    ):
        """Log an event to the database."""
        event = Event(
            event_type=event_type,
            category="digital_twin",
            severity="low",
            title=title,
            description=f"Digital twin event: {title}",
            source="digital_twin_manager",
            event_data=event_data,
        )
        session.add(event)
        await session.commit()
        
    # Event handling
    def register_event_handler(self, event_type: str, handler: callable):
        """Register an event handler."""
        self.event_handlers[event_type] = handler
        
    async def handle_real_device_event(self, device_id: int, event_data: Dict[str, Any]):
        """Handle events from real devices."""
        # Find corresponding twin device
        twin_id = self.synchronizer.device_mappings.get(device_id)
        if not twin_id:
            return
            
        # Update synchronizer
        await self.synchronizer.handle_real_device_update(device_id, event_data)
        
        # Find the house and device
        for house in self.houses.values():
            if twin_id in house.all_devices:
                device = house.all_devices[twin_id]
                
                # Update device state
                if "state" in event_data:
                    device.update_state(event_data["state"])
                    
                # Call event handlers
                if "device_update" in self.event_handlers:
                    await self.event_handlers["device_update"](house.id, device, event_data)
                    
                break