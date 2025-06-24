"""
Device Integration Layer

Provides unified interface for both real and simulated devices.
Enables seamless switching between real hardware and digital twin simulation.
"""

from typing import Dict, List, Any, Optional, Union, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from enum import Enum, auto
import asyncio
import json
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from consciousness.models.entities import Device, DeviceEntity
from consciousness.core.logging import get_logger
from consciousness.exceptions import DeviceNotFoundError, IntegrationError
from consciousness.utils.config import get_config

logger = get_logger(__name__)


class DeviceMode(Enum):
    """Operating modes for the device integration layer."""
    REAL = auto()        # Use real physical devices
    SIMULATED = auto()   # Use simulated devices (digital twin)
    HYBRID = auto()      # Mix of real and simulated devices


class DeviceCapability(Enum):
    """Standard device capabilities."""
    POWER = "power"
    BRIGHTNESS = "brightness"
    COLOR = "color"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    MOTION = "motion"
    LOCK = "lock"
    CAMERA = "camera"
    ENERGY = "energy"
    CUSTOM = "custom"


@runtime_checkable
class IDeviceAdapter(Protocol):
    """Protocol for device adapters."""
    
    async def connect(self) -> bool:
        """Connect to the device."""
        ...
    
    async def disconnect(self) -> None:
        """Disconnect from the device."""
        ...
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current device state."""
        ...
    
    async def set_state(self, state: Dict[str, Any]) -> bool:
        """Set device state."""
        ...
    
    async def get_capabilities(self) -> List[DeviceCapability]:
        """Get device capabilities."""
        ...
    
    async def subscribe_to_events(self, callback: callable) -> None:
        """Subscribe to device events."""
        ...


class BaseDeviceAdapter(ABC):
    """Base class for all device adapters."""
    
    def __init__(self, device: Device, config: Dict[str, Any]):
        self.device = device
        self.config = config
        self.is_connected = False
        self.event_callbacks = []
        self.last_state = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the device."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Get current device state."""
        pass
    
    @abstractmethod
    async def set_state(self, state: Dict[str, Any]) -> bool:
        """Set device state."""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[DeviceCapability]:
        """Get device capabilities."""
        pass
    
    async def subscribe_to_events(self, callback: callable) -> None:
        """Subscribe to device events."""
        self.event_callbacks.append(callback)
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit event to all subscribers."""
        event = {
            "device_id": str(self.device.id),
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for callback in self.event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")


class RealDeviceAdapter(BaseDeviceAdapter):
    """Adapter for real physical devices."""
    
    async def connect(self) -> bool:
        """Connect to real device using appropriate protocol."""
        try:
            # Determine connection method
            if self.device.connection_method == "wifi":
                return await self._connect_wifi()
            elif self.device.connection_method == "zigbee":
                return await self._connect_zigbee()
            elif self.device.connection_method == "bluetooth":
                return await self._connect_bluetooth()
            elif self.device.connection_method == "cloud":
                return await self._connect_cloud()
            else:
                logger.warning(f"Unknown connection method: {self.device.connection_method}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to device {self.device.id}: {e}")
            return False
    
    async def _connect_wifi(self) -> bool:
        """Connect to WiFi device."""
        # Implementation would use appropriate library based on device type
        # For example: aiohttp for REST APIs, specific SDKs for proprietary protocols
        endpoint = self.device.api_endpoint
        if endpoint:
            # Test connection
            logger.info(f"Connecting to WiFi device at {endpoint}")
            self.is_connected = True
            return True
        return False
    
    async def _connect_zigbee(self) -> bool:
        """Connect to Zigbee device through hub."""
        if self.device.hub_id:
            logger.info(f"Connecting to Zigbee device through hub {self.device.hub_id}")
            self.is_connected = True
            return True
        return False
    
    async def _connect_bluetooth(self) -> bool:
        """Connect to Bluetooth device."""
        logger.info(f"Connecting to Bluetooth device {self.device.detected_model}")
        self.is_connected = True
        return True
    
    async def _connect_cloud(self) -> bool:
        """Connect to cloud-based device."""
        if self.device.credentials:
            logger.info(f"Connecting to cloud service for {self.device.detected_brand}")
            self.is_connected = True
            return True
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from device."""
        self.is_connected = False
        logger.info(f"Disconnected from device {self.device.id}")
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current device state from real hardware."""
        if not self.is_connected:
            raise IntegrationError("Device not connected")
        
        # Implementation would query actual device
        # This is a placeholder that returns last known state
        return self.last_state
    
    async def set_state(self, state: Dict[str, Any]) -> bool:
        """Set device state on real hardware."""
        if not self.is_connected:
            raise IntegrationError("Device not connected")
        
        # Implementation would send commands to actual device
        self.last_state.update(state)
        await self._emit_event("state_change", state)
        return True
    
    async def get_capabilities(self) -> List[DeviceCapability]:
        """Get device capabilities from configuration."""
        capabilities = []
        
        if self.device.device_class == "light":
            capabilities.extend([DeviceCapability.POWER, DeviceCapability.BRIGHTNESS])
            if "color" in self.device.supported_features:
                capabilities.append(DeviceCapability.COLOR)
                
        elif self.device.device_class == "climate":
            capabilities.extend([DeviceCapability.POWER, DeviceCapability.TEMPERATURE])
            
        elif self.device.device_class == "sensor":
            sensor_type = self.device.capabilities.get("sensor_type", "")
            if sensor_type == "temperature":
                capabilities.append(DeviceCapability.TEMPERATURE)
            elif sensor_type == "humidity":
                capabilities.append(DeviceCapability.HUMIDITY)
            elif sensor_type == "motion":
                capabilities.append(DeviceCapability.MOTION)
                
        elif self.device.device_class == "lock":
            capabilities.append(DeviceCapability.LOCK)
            
        elif self.device.device_class == "camera":
            capabilities.append(DeviceCapability.CAMERA)
            
        return capabilities


class SimulatedDeviceAdapter(BaseDeviceAdapter):
    """Adapter for simulated devices (digital twin)."""
    
    def __init__(self, device: Device, config: Dict[str, Any], simulator):
        super().__init__(device, config)
        self.simulator = simulator
        
    async def connect(self) -> bool:
        """Connect to simulated device."""
        try:
            # Connect to the simulator instance
            self.is_connected = await self.simulator.connect()
            
            if self.is_connected:
                # Subscribe to simulator events
                await self.simulator.subscribe(self._handle_simulator_event)
                logger.info(f"Connected to simulated device {self.device.id}")
                
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Failed to connect to simulator: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from simulated device."""
        if self.simulator:
            await self.simulator.disconnect()
        self.is_connected = False
        logger.info(f"Disconnected from simulated device {self.device.id}")
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current state from simulator."""
        if not self.is_connected:
            raise IntegrationError("Simulator not connected")
        
        return await self.simulator.get_state()
    
    async def set_state(self, state: Dict[str, Any]) -> bool:
        """Set state in simulator."""
        if not self.is_connected:
            raise IntegrationError("Simulator not connected")
        
        success = await self.simulator.set_state(state)
        if success:
            await self._emit_event("state_change", state)
        return success
    
    async def get_capabilities(self) -> List[DeviceCapability]:
        """Get capabilities from simulator."""
        if not self.is_connected:
            return []
        
        return await self.simulator.get_capabilities()
    
    async def _handle_simulator_event(self, event: Dict[str, Any]) -> None:
        """Handle events from simulator."""
        await self._emit_event(event["type"], event["data"])


class DeviceIntegrationManager:
    """Manages device integration with support for real and simulated modes."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.mode = self._get_mode_from_config()
        self.device_adapters: Dict[str, Union[RealDeviceAdapter, SimulatedDeviceAdapter]] = {}
        self.simulator_manager = None
        
        logger.info(f"Device Integration Manager initialized in {self.mode.name} mode")
    
    def _get_mode_from_config(self) -> DeviceMode:
        """Get device mode from configuration."""
        mode_str = os.getenv("DEVICE_MODE", "real").lower()
        
        if mode_str == "simulated" or mode_str == "simulation":
            return DeviceMode.SIMULATED
        elif mode_str == "hybrid":
            return DeviceMode.HYBRID
        else:
            return DeviceMode.REAL
    
    async def initialize(self) -> None:
        """Initialize the integration manager."""
        if self.mode in [DeviceMode.SIMULATED, DeviceMode.HYBRID]:
            # Initialize simulator manager
            from consciousness.simulators.manager import SimulatorManager
            self.simulator_manager = SimulatorManager(self.session)
            await self.simulator_manager.initialize()
            
            # Load simulation configuration
            await self._load_simulation_config()
    
    async def _load_simulation_config(self) -> None:
        """Load simulation configuration from file."""
        config_path = os.getenv("SIMULATION_CONFIG", "config/simulation.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                
            if self.simulator_manager:
                await self.simulator_manager.load_configuration(config)
                logger.info(f"Loaded simulation configuration from {config_path}")
    
    async def discover_devices(self) -> List[Device]:
        """Discover devices based on current mode."""
        discovered = []
        
        if self.mode == DeviceMode.REAL:
            # Use real device discovery
            discovered = await self._discover_real_devices()
            
        elif self.mode == DeviceMode.SIMULATED:
            # Use simulated device discovery
            discovered = await self._discover_simulated_devices()
            
        elif self.mode == DeviceMode.HYBRID:
            # Discover both real and simulated
            real_devices = await self._discover_real_devices()
            sim_devices = await self._discover_simulated_devices()
            
            # Merge lists, preferring simulated for specific devices if configured
            discovered = self._merge_device_lists(real_devices, sim_devices)
        
        logger.info(f"Discovered {len(discovered)} devices in {self.mode.name} mode")
        return discovered
    
    async def _discover_real_devices(self) -> List[Device]:
        """Discover real physical devices."""
        from consciousness.discovery.auto_discovery import AutoDiscoveryService
        
        discovery_service = AutoDiscoveryService()
        results = await discovery_service.discover_all_protocols()
        
        # Convert discovery results to Device objects
        devices = []
        for protocol, discovered in results.items():
            for device_data in discovered:
                # Create Device object from discovery data
                # This would map discovery data to Device model
                pass
        
        return devices
    
    async def _discover_simulated_devices(self) -> List[Device]:
        """Discover simulated devices from configuration."""
        if not self.simulator_manager:
            return []
        
        return await self.simulator_manager.get_available_devices()
    
    def _merge_device_lists(self, real: List[Device], simulated: List[Device]) -> List[Device]:
        """Merge real and simulated device lists for hybrid mode."""
        # Configuration determines which devices to simulate
        simulate_config = os.getenv("HYBRID_SIMULATE_DEVICES", "").split(",")
        
        merged = []
        sim_dict = {d.user_name: d for d in simulated}
        
        for device in real:
            if device.user_name in simulate_config and device.user_name in sim_dict:
                # Use simulated version
                merged.append(sim_dict[device.user_name])
            else:
                # Use real device
                merged.append(device)
        
        # Add any simulated-only devices
        real_names = {d.user_name for d in real}
        for sim_device in simulated:
            if sim_device.user_name not in real_names:
                merged.append(sim_device)
        
        return merged
    
    async def get_device_adapter(self, device_id: str) -> Union[RealDeviceAdapter, SimulatedDeviceAdapter]:
        """Get or create device adapter."""
        if device_id in self.device_adapters:
            return self.device_adapters[device_id]
        
        # Load device from database
        device = await self._get_device(device_id)
        if not device:
            raise DeviceNotFoundError(f"Device {device_id} not found")
        
        # Create appropriate adapter
        adapter = await self._create_adapter(device)
        self.device_adapters[device_id] = adapter
        
        return adapter
    
    async def _create_adapter(self, device: Device) -> Union[RealDeviceAdapter, SimulatedDeviceAdapter]:
        """Create appropriate adapter based on mode and device."""
        config = device.config_data or {}
        
        if self.mode == DeviceMode.SIMULATED:
            # Always use simulated
            simulator = await self.simulator_manager.get_simulator(device)
            return SimulatedDeviceAdapter(device, config, simulator)
            
        elif self.mode == DeviceMode.REAL:
            # Always use real
            return RealDeviceAdapter(device, config)
            
        elif self.mode == DeviceMode.HYBRID:
            # Check if this specific device should be simulated
            simulate_devices = os.getenv("HYBRID_SIMULATE_DEVICES", "").split(",")
            
            if device.user_name in simulate_devices:
                simulator = await self.simulator_manager.get_simulator(device)
                return SimulatedDeviceAdapter(device, config, simulator)
            else:
                return RealDeviceAdapter(device, config)
    
    async def _get_device(self, device_id: str) -> Optional[Device]:
        """Get device from database."""
        # Implementation would query database
        # This is a placeholder
        return None
    
    async def execute_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> bool:
        """Execute command on device through appropriate adapter."""
        adapter = await self.get_device_adapter(device_id)
        
        if not adapter.is_connected:
            connected = await adapter.connect()
            if not connected:
                raise IntegrationError(f"Failed to connect to device {device_id}")
        
        # Map command to state change
        state_change = self._command_to_state(command, parameters)
        
        return await adapter.set_state(state_change)
    
    def _command_to_state(self, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert command to state change."""
        state = {}
        
        if command == "turn_on":
            state["power"] = True
        elif command == "turn_off":
            state["power"] = False
        elif command == "set_brightness":
            state["brightness"] = parameters.get("brightness", 100)
        elif command == "set_temperature":
            state["temperature"] = parameters.get("temperature", 20)
        elif command == "set_color":
            state["color"] = parameters.get("color", {"r": 255, "g": 255, "b": 255})
        
        return state
    
    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current device state."""
        adapter = await self.get_device_adapter(device_id)
        
        if not adapter.is_connected:
            connected = await adapter.connect()
            if not connected:
                raise IntegrationError(f"Failed to connect to device {device_id}")
        
        return await adapter.get_state()
    
    async def subscribe_to_device_events(self, device_id: str, callback: callable) -> None:
        """Subscribe to device events."""
        adapter = await self.get_device_adapter(device_id)
        await adapter.subscribe_to_events(callback)
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Disconnect all adapters
        for adapter in self.device_adapters.values():
            await adapter.disconnect()
        
        # Clean up simulator manager
        if self.simulator_manager:
            await self.simulator_manager.cleanup()
        
        self.device_adapters.clear()
        logger.info("Device Integration Manager cleaned up")


# Factory function for creating integration manager
def create_integration_manager(session: AsyncSession) -> DeviceIntegrationManager:
    """Create device integration manager with appropriate configuration."""
    return DeviceIntegrationManager(session)