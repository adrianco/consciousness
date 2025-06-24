"""
Base simulator classes for device emulation.
"""

import asyncio
import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import json
import logging


logger = logging.getLogger(__name__)


class SimulatorEventType(Enum):
    """Types of events that can occur in simulation."""
    STATE_CHANGE = "state_change"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    BATTERY_LOW = "battery_low"
    SENSOR_TRIGGERED = "sensor_triggered"
    ERROR_OCCURRED = "error_occurred"
    MAINTENANCE_REQUIRED = "maintenance_required"
    FIRMWARE_UPDATE = "firmware_update"
    ENVIRONMENTAL_CHANGE = "environmental_change"
    USER_INTERACTION = "user_interaction"


class DeviceEvent:
    """Represents an event from a simulated device."""
    
    def __init__(
        self,
        device_id: str,
        event_type: SimulatorEventType,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ):
        self.id = str(uuid.uuid4())
        self.device_id = device_id
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class BaseSimulatedDevice(ABC):
    """Abstract base class for all simulated devices."""
    
    def __init__(
        self,
        device_id: Optional[str] = None,
        name: str = "Simulated Device",
        brand: str = "Generic",
        model: str = "Model-X",
        device_class: str = "generic",
        integration_type: str = "simulator",
        location: str = "Unknown",
        connection_method: str = "wifi",
        response_delay: float = 0.1,
        failure_rate: float = 0.01,
        enable_random_events: bool = True
    ):
        self.device_id = device_id or str(uuid.uuid4())
        self.name = name
        self.brand = brand
        self.model = model
        self.device_class = device_class
        self.integration_type = integration_type
        self.location = location
        self.connection_method = connection_method
        
        # Simulation parameters
        self.response_delay = response_delay  # Seconds
        self.failure_rate = failure_rate  # Probability of failure per operation
        self.enable_random_events = enable_random_events
        
        # State management
        self.is_online = True
        self.is_enabled = True
        self.last_seen = datetime.utcnow()
        self.last_error = None
        self._state: Dict[str, Any] = {}
        self._attributes: Dict[str, Any] = {}
        
        # Event handling
        self._event_listeners: List[Callable[[DeviceEvent], None]] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._tasks: Set[asyncio.Task] = set()
        
        # Environmental factors
        self.environmental_factors = {
            "temperature": 20.0,  # Celsius
            "humidity": 50.0,     # Percentage
            "light_level": 100.0, # Lux
            "motion": False,
            "time_of_day": "day"  # day, evening, night
        }
        
        # Initialize device-specific state
        self._initialize_state()
    
    @abstractmethod
    def _initialize_state(self) -> None:
        """Initialize device-specific state."""
        pass
    
    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Return list of supported features."""
        pass
    
    @abstractmethod
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        pass
    
    async def start(self) -> None:
        """Start the device simulator."""
        self._running = True
        logger.info(f"Starting simulator for device {self.device_id} ({self.name})")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._random_event_generator()),
            asyncio.create_task(self._state_updater())
        ]
        
        for task in tasks:
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)
    
    async def stop(self) -> None:
        """Stop the device simulator."""
        logger.info(f"Stopping simulator for device {self.device_id}")
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
    
    async def _event_processor(self) -> None:
        """Process events from the event queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Notify all listeners
                for listener in self._event_listeners:
                    try:
                        await asyncio.create_task(
                            self._notify_listener(listener, event)
                        )
                    except Exception as e:
                        logger.error(f"Error notifying listener: {e}")
                        
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
    
    async def _notify_listener(
        self,
        listener: Callable[[DeviceEvent], None],
        event: DeviceEvent
    ) -> None:
        """Notify a listener about an event."""
        if asyncio.iscoroutinefunction(listener):
            await listener(event)
        else:
            listener(event)
    
    async def _random_event_generator(self) -> None:
        """Generate random events to simulate real device behavior."""
        while self._running and self.enable_random_events:
            try:
                # Wait random interval
                await asyncio.sleep(random.uniform(30, 300))  # 30s to 5min
                
                if not self.is_online:
                    continue
                
                # Generate random event based on device type
                await self._generate_random_event()
                
            except Exception as e:
                logger.error(f"Error in random event generator: {e}")
    
    @abstractmethod
    async def _generate_random_event(self) -> None:
        """Generate device-specific random events."""
        pass
    
    @abstractmethod
    async def _state_updater(self) -> None:
        """Update device state based on environmental factors."""
        pass
    
    def add_event_listener(self, listener: Callable[[DeviceEvent], None]) -> None:
        """Add an event listener."""
        self._event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[DeviceEvent], None]) -> None:
        """Remove an event listener."""
        if listener in self._event_listeners:
            self._event_listeners.remove(listener)
    
    async def emit_event(
        self,
        event_type: SimulatorEventType,
        data: Dict[str, Any]
    ) -> None:
        """Emit an event."""
        event = DeviceEvent(
            device_id=self.device_id,
            event_type=event_type,
            data=data
        )
        await self._event_queue.put(event)
    
    async def simulate_response_delay(self) -> None:
        """Simulate network/processing delay."""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)
    
    async def simulate_failure(self) -> bool:
        """Simulate random device failure."""
        if random.random() < self.failure_rate:
            self.last_error = f"Random failure at {datetime.utcnow().isoformat()}"
            await self.emit_event(
                SimulatorEventType.ERROR_OCCURRED,
                {"error": self.last_error}
            )
            return True
        return False
    
    async def set_connection_status(self, online: bool) -> None:
        """Set device connection status."""
        if self.is_online != online:
            self.is_online = online
            event_type = (
                SimulatorEventType.CONNECTION_RESTORED
                if online
                else SimulatorEventType.CONNECTION_LOST
            )
            await self.emit_event(event_type, {"online": online})
    
    def update_environmental_factor(self, factor: str, value: Any) -> None:
        """Update an environmental factor."""
        if factor in self.environmental_factors:
            self.environmental_factors[factor] = value
            logger.debug(
                f"Updated {factor} to {value} for device {self.device_id}"
            )
    
    def get_state(self) -> Dict[str, Any]:
        """Get current device state."""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "online": self.is_online,
            "enabled": self.is_enabled,
            "last_seen": self.last_seen.isoformat(),
            "state": self._state.copy(),
            "attributes": self._attributes.copy(),
            "last_error": self.last_error
        }
    
    @abstractmethod
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle a command sent to the device."""
        pass
    
    async def _execute_command(
        self,
        command_handler: Callable,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a command with common error handling."""
        try:
            # Check if device is online
            if not self.is_online:
                return {
                    "success": False,
                    "error": "Device is offline"
                }
            
            # Simulate response delay
            await self.simulate_response_delay()
            
            # Check for random failure
            if await self.simulate_failure():
                return {
                    "success": False,
                    "error": "Device failure occurred"
                }
            
            # Execute the command
            result = await command_handler(parameters or {})
            
            # Update last seen
            self.last_seen = datetime.utcnow()
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            self.last_error = str(e)
            return {
                "success": False,
                "error": str(e)
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary representation."""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "brand": self.brand,
            "model": self.model,
            "device_class": self.device_class,
            "integration_type": self.integration_type,
            "location": self.location,
            "connection_method": self.connection_method,
            "supported_features": self.get_supported_features(),
            "device_info": self.get_device_info(),
            "state": self.get_state()
        }