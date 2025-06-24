"""
Device Configuration System

Manages configuration for device integration modes, simulation settings,
and environment-specific device behaviors.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import os
import json
import yaml
from pathlib import Path

from consciousness.core.logging import get_logger

logger = get_logger(__name__)


class DeviceMode(Enum):
    """Device operation modes."""
    REAL = "real"
    SIMULATED = "simulated"
    HYBRID = "hybrid"


class DiscoveryProtocol(Enum):
    """Device discovery protocols."""
    DHCP = "dhcp"
    MDNS = "mdns"
    UPNP = "upnp"
    BLUETOOTH = "bluetooth"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    MATTER = "matter"
    HOMEKIT = "homekit"


@dataclass
class DeviceConfig:
    """Configuration for a single device."""
    name: str
    device_type: str
    device_class: str
    brand: str = ""
    model: str = ""
    location: str = ""
    
    # Connection settings
    connection_method: str = "wifi"
    endpoint: str = ""
    port: int = 0
    requires_hub: bool = False
    hub_name: str = ""
    
    # Authentication
    requires_auth: bool = False
    auth_method: str = "none"
    username: str = ""
    password: str = ""
    api_key: str = ""
    
    # Capabilities
    capabilities: List[str] = field(default_factory=list)
    supported_features: List[str] = field(default_factory=list)
    
    # Simulation settings
    simulate: bool = False
    simulation_config: Dict[str, Any] = field(default_factory=dict)
    
    # Runtime state
    is_online: bool = True
    last_seen: str = ""


@dataclass
class RoomConfig:
    """Configuration for a room."""
    name: str
    devices: List[str] = field(default_factory=list)
    automation_rules: List[Dict[str, Any]] = field(default_factory=list)
    environmental_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HouseConfig:
    """Configuration for entire house."""
    name: str
    address: str = ""
    timezone: str = "UTC"
    rooms: List[RoomConfig] = field(default_factory=list)
    global_automation: List[Dict[str, Any]] = field(default_factory=list)
    security_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationScenario:
    """Configuration for simulation scenarios."""
    name: str
    description: str
    duration: int  # seconds
    
    # Scenario events
    events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Environmental conditions
    weather: Dict[str, Any] = field(default_factory=dict)
    time_of_day: str = "day"
    occupancy: List[str] = field(default_factory=list)  # Who's home
    
    # Device states
    initial_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    scheduled_changes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IntegrationSettings:
    """Settings for device integrations."""
    mode: DeviceMode = DeviceMode.REAL
    discovery_enabled: bool = True
    discovery_protocols: List[DiscoveryProtocol] = field(
        default_factory=lambda: [DiscoveryProtocol.MDNS, DiscoveryProtocol.DHCP]
    )
    
    # Simulation settings
    simulation_mode: str = "realistic"  # realistic, fast, debug
    auto_populate_devices: bool = True
    sync_interval_seconds: int = 30
    
    # Hybrid mode settings
    hybrid_simulate_devices: List[str] = field(default_factory=list)
    hybrid_fallback_to_simulation: bool = True
    
    # Performance settings
    max_concurrent_connections: int = 50
    connection_timeout_seconds: int = 10
    retry_attempts: int = 3
    
    # Logging
    debug_mode: bool = False
    log_device_events: bool = True
    log_state_changes: bool = False


class DeviceConfigurationManager:
    """Manages device configuration and modes."""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.getenv("DEVICE_CONFIG_DIR", "config/devices"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration data
        self.integration_settings: Optional[IntegrationSettings] = None
        self.house_config: Optional[HouseConfig] = None
        self.device_configs: Dict[str, DeviceConfig] = {}
        self.simulation_scenarios: Dict[str, SimulationScenario] = {}
        
        # Load configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files."""
        try:
            # Load integration settings
            self._load_integration_settings()
            
            # Load house configuration
            self._load_house_config()
            
            # Load device configurations
            self._load_device_configs()
            
            # Load simulation scenarios
            self._load_simulation_scenarios()
            
            logger.info("Device configurations loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {e}")
            self._create_default_configurations()
    
    def _load_integration_settings(self):
        """Load integration settings."""
        settings_file = self.config_dir / "integration.yaml"
        
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                data = yaml.safe_load(f)
                
            # Convert enum strings
            if 'mode' in data:
                data['mode'] = DeviceMode(data['mode'])
            
            if 'discovery_protocols' in data:
                data['discovery_protocols'] = [
                    DiscoveryProtocol(p) for p in data['discovery_protocols']
                ]
            
            self.integration_settings = IntegrationSettings(**data)
        else:
            self.integration_settings = IntegrationSettings()
            self._save_integration_settings()
    
    def _load_house_config(self):
        """Load house configuration."""
        house_file = self.config_dir / "house.yaml"
        
        if house_file.exists():
            with open(house_file, 'r') as f:
                data = yaml.safe_load(f)
            
            # Convert room data
            rooms = []
            for room_data in data.get('rooms', []):
                rooms.append(RoomConfig(**room_data))
            
            data['rooms'] = rooms
            self.house_config = HouseConfig(**data)
        else:
            self.house_config = self._create_default_house_config()
            self._save_house_config()
    
    def _load_device_configs(self):
        """Load device configurations."""
        devices_file = self.config_dir / "devices.yaml"
        
        if devices_file.exists():
            with open(devices_file, 'r') as f:
                data = yaml.safe_load(f)
            
            for device_name, device_data in data.get('devices', {}).items():
                self.device_configs[device_name] = DeviceConfig(
                    name=device_name, **device_data
                )
        else:
            self._create_default_device_configs()
            self._save_device_configs()
    
    def _load_simulation_scenarios(self):
        """Load simulation scenarios."""
        scenarios_file = self.config_dir / "scenarios.yaml"
        
        if scenarios_file.exists():
            with open(scenarios_file, 'r') as f:
                data = yaml.safe_load(f)
            
            for scenario_name, scenario_data in data.get('scenarios', {}).items():
                self.simulation_scenarios[scenario_name] = SimulationScenario(
                    name=scenario_name, **scenario_data
                )
        else:
            self._create_default_simulation_scenarios()
            self._save_simulation_scenarios()
    
    def _create_default_configurations(self):
        """Create default configurations."""
        self.integration_settings = IntegrationSettings()
        self.house_config = self._create_default_house_config()
        self._create_default_device_configs()
        self._create_default_simulation_scenarios()
        
        # Save all defaults
        self._save_integration_settings()
        self._save_house_config()
        self._save_device_configs()
        self._save_simulation_scenarios()
    
    def _create_default_house_config(self) -> HouseConfig:
        """Create default house configuration."""
        return HouseConfig(
            name="Smart Home",
            address="123 Main St",
            timezone="America/New_York",
            rooms=[
                RoomConfig(
                    name="Living Room",
                    devices=["living_room_lights", "smart_tv"],
                    environmental_factors={"natural_light": True, "traffic": "medium"}
                ),
                RoomConfig(
                    name="Bedroom",
                    devices=["bedroom_lights", "smart_thermostat"],
                    environmental_factors={"natural_light": False, "privacy": "high"}
                ),
                RoomConfig(
                    name="Kitchen",
                    devices=["kitchen_lights", "smart_fridge"],
                    environmental_factors={"humidity": "high", "temperature_variance": "high"}
                )
            ]
        )
    
    def _create_default_device_configs(self):
        """Create default device configurations."""
        default_devices = [
            DeviceConfig(
                name="living_room_lights",
                device_type="hue",
                device_class="light",
                brand="Philips",
                model="Hue Color Bulb",
                location="Living Room",
                connection_method="wifi",
                requires_hub=True,
                hub_name="hue_bridge",
                capabilities=["power", "brightness", "color"],
                supported_features=["brightness", "color", "effects"],
                simulate=False,
                simulation_config={
                    "response_time": 0.5,
                    "failure_rate": 0.01,
                    "power_consumption": {"on": 9, "off": 0.5}
                }
            ),
            DeviceConfig(
                name="smart_thermostat",
                device_type="nest",
                device_class="climate",
                brand="Google",
                model="Nest Learning Thermostat",
                location="Hallway",
                connection_method="wifi",
                requires_auth=True,
                auth_method="oauth",
                capabilities=["temperature", "humidity", "scheduling"],
                supported_features=["temperature", "mode", "fan_speed"],
                simulate=False,
                simulation_config={
                    "temperature_range": [15, 30],
                    "response_time": 2.0,
                    "thermal_mass": 5.0  # Minutes to change 1 degree
                }
            ),
            DeviceConfig(
                name="smart_lock",
                device_type="august",
                device_class="lock",
                brand="August",
                model="Smart Lock Pro",
                location="Front Door",
                connection_method="bluetooth",
                requires_auth=True,
                auth_method="api_key",
                capabilities=["lock", "unlock", "status"],
                supported_features=["remote_unlock", "auto_lock"],
                simulate=True,  # Often simulate locks for security
                simulation_config={
                    "lock_time": 1.0,
                    "unlock_time": 0.5,
                    "battery_drain_rate": 0.1  # Percent per day
                }
            )
        ]
        
        for device in default_devices:
            self.device_configs[device.name] = device
    
    def _create_default_simulation_scenarios(self):
        """Create default simulation scenarios."""
        scenarios = [
            SimulationScenario(
                name="morning_routine",
                description="Typical morning routine simulation",
                duration=3600,  # 1 hour
                events=[
                    {"time": 0, "device": "bedroom_lights", "action": "turn_on", "brightness": 30},
                    {"time": 300, "device": "smart_thermostat", "action": "set_temperature", "temperature": 22},
                    {"time": 600, "device": "kitchen_lights", "action": "turn_on"},
                    {"time": 1800, "device": "smart_lock", "action": "unlock"},
                    {"time": 1820, "device": "smart_lock", "action": "lock"}
                ],
                weather={"condition": "clear", "temperature": 15, "humidity": 60},
                time_of_day="morning",
                occupancy=["person1"],
                initial_states={
                    "bedroom_lights": {"power": False},
                    "smart_thermostat": {"temperature": 18, "mode": "heat"},
                    "smart_lock": {"locked": True}
                }
            ),
            SimulationScenario(
                name="evening_routine",
                description="Evening relaxation and security routine",
                duration=7200,  # 2 hours
                events=[
                    {"time": 0, "device": "living_room_lights", "action": "turn_on", "brightness": 80},
                    {"time": 1800, "device": "living_room_lights", "action": "set_brightness", "brightness": 40},
                    {"time": 3600, "device": "smart_thermostat", "action": "set_temperature", "temperature": 20},
                    {"time": 6000, "device": "living_room_lights", "action": "turn_off"},
                    {"time": 6300, "device": "smart_lock", "action": "verify_locked"}
                ],
                weather={"condition": "cloudy", "temperature": 8, "humidity": 70},
                time_of_day="evening",
                occupancy=["person1", "person2"]
            )
        ]
        
        for scenario in scenarios:
            self.simulation_scenarios[scenario.name] = scenario
    
    def _save_integration_settings(self):
        """Save integration settings."""
        settings_file = self.config_dir / "integration.yaml"
        
        data = asdict(self.integration_settings)
        
        # Convert enums to strings
        data['mode'] = data['mode'].value
        data['discovery_protocols'] = [p.value for p in data['discovery_protocols']]
        
        with open(settings_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def _save_house_config(self):
        """Save house configuration."""
        house_file = self.config_dir / "house.yaml"
        
        with open(house_file, 'w') as f:
            yaml.dump(asdict(self.house_config), f, default_flow_style=False, sort_keys=False)
    
    def _save_device_configs(self):
        """Save device configurations."""
        devices_file = self.config_dir / "devices.yaml"
        
        data = {
            "devices": {
                name: {k: v for k, v in asdict(config).items() if k != 'name'}
                for name, config in self.device_configs.items()
            }
        }
        
        with open(devices_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def _save_simulation_scenarios(self):
        """Save simulation scenarios."""
        scenarios_file = self.config_dir / "scenarios.yaml"
        
        data = {
            "scenarios": {
                name: {k: v for k, v in asdict(scenario).items() if k != 'name'}
                for name, scenario in self.simulation_scenarios.items()
            }
        }
        
        with open(scenarios_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    # Public API methods
    
    def get_device_mode(self) -> DeviceMode:
        """Get current device mode."""
        return self.integration_settings.mode
    
    def set_device_mode(self, mode: DeviceMode):
        """Set device mode."""
        self.integration_settings.mode = mode
        self._save_integration_settings()
        logger.info(f"Device mode changed to {mode.value}")
    
    def get_device_config(self, device_name: str) -> Optional[DeviceConfig]:
        """Get configuration for a specific device."""
        return self.device_configs.get(device_name)
    
    def should_simulate_device(self, device_name: str) -> bool:
        """Check if a device should be simulated."""
        config = self.get_device_config(device_name)
        if not config:
            return False
        
        mode = self.get_device_mode()
        
        if mode == DeviceMode.SIMULATED:
            return True
        elif mode == DeviceMode.REAL:
            return False
        elif mode == DeviceMode.HYBRID:
            return (config.simulate or 
                   device_name in self.integration_settings.hybrid_simulate_devices)
        
        return False
    
    def get_simulation_scenario(self, scenario_name: str) -> Optional[SimulationScenario]:
        """Get simulation scenario by name."""
        return self.simulation_scenarios.get(scenario_name)
    
    def list_available_scenarios(self) -> List[str]:
        """List all available simulation scenarios."""
        return list(self.simulation_scenarios.keys())
    
    def add_device_config(self, device_config: DeviceConfig):
        """Add or update device configuration."""
        self.device_configs[device_config.name] = device_config
        self._save_device_configs()
        logger.info(f"Device configuration updated: {device_config.name}")
    
    def remove_device_config(self, device_name: str) -> bool:
        """Remove device configuration."""
        if device_name in self.device_configs:
            del self.device_configs[device_name]
            self._save_device_configs()
            logger.info(f"Device configuration removed: {device_name}")
            return True
        return False
    
    def get_devices_by_room(self, room_name: str) -> List[DeviceConfig]:
        """Get all devices in a specific room."""
        devices = []
        
        # Find room
        if self.house_config:
            for room in self.house_config.rooms:
                if room.name == room_name:
                    for device_name in room.devices:
                        if device_name in self.device_configs:
                            devices.append(self.device_configs[device_name])
                    break
        
        return devices
    
    def get_all_device_configs(self) -> Dict[str, DeviceConfig]:
        """Get all device configurations."""
        return self.device_configs.copy()
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check device references in rooms
        if self.house_config:
            for room in self.house_config.rooms:
                for device_name in room.devices:
                    if device_name not in self.device_configs:
                        issues.append(f"Room '{room.name}' references unknown device '{device_name}'")
        
        # Check hub dependencies
        for device_name, device_config in self.device_configs.items():
            if device_config.requires_hub and device_config.hub_name:
                if device_config.hub_name not in self.device_configs:
                    issues.append(f"Device '{device_name}' requires unknown hub '{device_config.hub_name}'")
        
        # Check authentication requirements
        for device_name, device_config in self.device_configs.items():
            if device_config.requires_auth:
                if device_config.auth_method == "none":
                    issues.append(f"Device '{device_name}' requires auth but method is 'none'")
                elif device_config.auth_method == "api_key" and not device_config.api_key:
                    issues.append(f"Device '{device_name}' requires API key but none provided")
                elif device_config.auth_method == "username_password" and (not device_config.username or not device_config.password):
                    issues.append(f"Device '{device_name}' requires username/password but not provided")
        
        return issues
    
    def reload(self):
        """Reload all configuration files."""
        self._load_configurations()
        logger.info("Configuration reloaded")


# Global configuration manager instance
_config_manager: Optional[DeviceConfigurationManager] = None


def get_device_config_manager() -> DeviceConfigurationManager:
    """Get global device configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = DeviceConfigurationManager()
    return _config_manager


def initialize_device_config(config_dir: str = None) -> DeviceConfigurationManager:
    """Initialize device configuration manager."""
    global _config_manager
    _config_manager = DeviceConfigurationManager(config_dir)
    return _config_manager