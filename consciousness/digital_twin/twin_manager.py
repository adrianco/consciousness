"""
Enhanced digital twin manager with interview system integration.

This module extends the existing digital twin system to work seamlessly with
the conversational device discovery interview system, enabling automatic
twin creation during the device setup process.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from consciousness.digital_twin.core import DigitalTwinManager as CoreTwinManager
from consciousness.digital_twin.models import (
    DeviceState,
    DigitalTwinDevice,
    DigitalTwinHouse,
    Dimensions3D,
    Position3D,
    SyncStatus,
)

logger = logging.getLogger(__name__)


class TwinSpecification:
    """Specification for creating a digital twin."""

    def __init__(
        self,
        device_id: str,
        twin_type: str,
        fidelity_level: str = "basic",
        sync_frequency: int = 60,
        enable_predictions: bool = True,
        enable_scenarios: bool = False,
        enable_learning: bool = False,
        physics_modeling: bool = False,
        simulation_models: Optional[List[Dict[str, Any]]] = None,
        prediction_capabilities: Optional[List[str]] = None,
        environmental_factors: Optional[List[str]] = None,
    ):
        self.device_id = device_id
        self.twin_type = twin_type
        self.fidelity_level = fidelity_level
        self.sync_frequency = sync_frequency
        self.enable_predictions = enable_predictions
        self.enable_scenarios = enable_scenarios
        self.enable_learning = enable_learning
        self.physics_modeling = physics_modeling
        self.simulation_models = simulation_models or []
        self.prediction_capabilities = prediction_capabilities or []
        self.environmental_factors = environmental_factors or []

        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert specification to dictionary."""
        return {
            "device_id": self.device_id,
            "twin_type": self.twin_type,
            "fidelity_level": self.fidelity_level,
            "sync_frequency": self.sync_frequency,
            "enable_predictions": self.enable_predictions,
            "enable_scenarios": self.enable_scenarios,
            "enable_learning": self.enable_learning,
            "physics_modeling": self.physics_modeling,
            "simulation_models": self.simulation_models,
            "prediction_capabilities": self.prediction_capabilities,
            "environmental_factors": self.environmental_factors,
            "created_at": self.created_at.isoformat(),
        }


class SyncConfig:
    """Configuration for twin-device synchronization."""

    def __init__(
        self,
        frequency: int = 60,
        bidirectional: bool = True,
        conflict_resolution: str = "device_wins",
        safe_mode: bool = True,
        retry_attempts: int = 3,
        timeout: int = 30,
    ):
        self.frequency = frequency  # Seconds
        self.bidirectional = bidirectional
        self.conflict_resolution = (
            conflict_resolution  # "device_wins", "twin_wins", "manual"
        )
        self.safe_mode = safe_mode  # Validate changes before applying
        self.retry_attempts = retry_attempts
        self.timeout = timeout


class DigitalTwin:
    """Enhanced digital twin with interview system integration."""

    def __init__(
        self,
        twin_id: str,
        device_config: Dict[str, Any],
        twin_spec: TwinSpecification,
        twin_device: DigitalTwinDevice,
    ):
        self.id = twin_id
        self.device_config = device_config
        self.specification = twin_spec
        self.twin_device = twin_device
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()

        # Sync configuration
        self.sync_config: Optional[SyncConfig] = None
        self.sync_active = False

        # Performance metrics
        self.prediction_accuracy: Dict[str, float] = {}
        self.sync_errors: List[Dict[str, Any]] = []
        self.usage_statistics: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert twin to dictionary representation."""
        return {
            "id": self.id,
            "device_config": self.device_config,
            "specification": self.specification.to_dict(),
            "twin_device": self.twin_device.get_state(),
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "sync_active": self.sync_active,
            "prediction_accuracy": self.prediction_accuracy,
            "usage_statistics": self.usage_statistics,
        }


class DigitalTwinManager:
    """Enhanced digital twin manager with interview system integration."""

    def __init__(self):
        # Use the existing core twin manager
        self.core_manager = CoreTwinManager()

        # Twin registry for interview-created twins
        self.interview_twins: Dict[str, DigitalTwin] = {}

        # Twin templates for different device types
        self._initialize_twin_templates()

        # Active sync tasks
        self.sync_tasks: Dict[str, asyncio.Task] = {}

    def _initialize_twin_templates(self) -> None:
        """Initialize twin templates for different device types."""

        self.twin_templates = {
            "hue_light": {
                "simulation_models": [
                    {
                        "type": "thermal_model",
                        "heat_output_per_watt": 0.9,
                        "cooling_rate": 0.1,
                    },
                    {
                        "type": "power_consumption_model",
                        "base_consumption": 0.5,
                        "max_consumption": 10.0,
                        "efficiency_curve": "led_standard",
                    },
                    {
                        "type": "lifespan_model",
                        "rated_hours": 25000,
                        "degradation_factors": ["heat", "cycles", "time"],
                    },
                ],
                "prediction_capabilities": [
                    "energy_usage",
                    "lifespan_prediction",
                    "optimal_scheduling",
                ],
                "environmental_factors": [
                    "ambient_temperature",
                    "humidity",
                    "occupancy",
                ],
            },
            "smart_thermostat": {
                "simulation_models": [
                    {
                        "type": "thermal_dynamics_model",
                        "thermal_mass": 50000,
                        "insulation_factor": 0.3,
                        "hvac_capacity": 3000,
                        "efficiency_rating": 0.95,
                    },
                    {
                        "type": "occupancy_model",
                        "occupant_heat_output": 100,
                        "schedule_learning": True,
                    },
                    {
                        "type": "weather_integration_model",
                        "external_temp_source": "weather_api",
                        "solar_gain_modeling": True,
                    },
                ],
                "prediction_capabilities": [
                    "temperature_forecast",
                    "energy_optimization",
                    "comfort_prediction",
                    "cost_analysis",
                ],
                "scenario_capabilities": [
                    "vacation_mode",
                    "weather_events",
                    "schedule_changes",
                ],
            },
            "security_camera": {
                "simulation_models": [
                    {
                        "type": "detection_model",
                        "detection_accuracy": 0.95,
                        "false_positive_rate": 0.02,
                        "environment_factors": ["lighting", "weather"],
                    },
                    {
                        "type": "storage_model",
                        "storage_capacity": 1000,  # GB
                        "retention_days": 30,
                        "compression_ratio": 0.3,
                    },
                ],
                "prediction_capabilities": [
                    "storage_usage",
                    "detection_patterns",
                    "maintenance_needs",
                ],
            },
            "smart_speaker": {
                "simulation_models": [
                    {
                        "type": "usage_pattern_model",
                        "command_frequency": 50,  # commands per day
                        "peak_hours": [7, 8, 18, 19, 20],
                        "learning_rate": 0.1,
                    },
                    {
                        "type": "audio_model",
                        "noise_reduction": 0.8,
                        "voice_recognition_accuracy": 0.95,
                    },
                ],
                "prediction_capabilities": [
                    "usage_patterns",
                    "command_prediction",
                    "preference_learning",
                ],
            },
        }

    async def initialize(self):
        """Initialize the enhanced twin manager."""
        await self.core_manager.initialize()
        logger.info("Enhanced Digital Twin Manager initialized")

    async def start(self):
        """Start the enhanced twin system."""
        await self.core_manager.start()
        logger.info("Enhanced Digital Twin system started")

    async def stop(self):
        """Stop the enhanced twin system."""
        # Stop all sync tasks
        for task in self.sync_tasks.values():
            task.cancel()

        await asyncio.gather(*self.sync_tasks.values(), return_exceptions=True)
        self.sync_tasks.clear()

        await self.core_manager.stop()
        logger.info("Enhanced Digital Twin system stopped")

    async def create_device_twin(
        self,
        device_config: Dict[str, Any],
        twin_config: Dict[str, Any],
        house_id: Optional[str] = None,
    ) -> DigitalTwin:
        """Create a digital twin for a device discovered through the interview system."""

        logger.info(f"Creating digital twin for device: {device_config.get('name')}")

        # Generate twin ID
        twin_id = (
            f"twin_{device_config['id']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        # Create twin specification
        twin_spec = self._create_twin_specification(device_config, twin_config)

        # Create the digital twin device
        twin_device = self._create_twin_device(device_config, twin_spec)

        # Create the digital twin wrapper
        digital_twin = DigitalTwin(
            twin_id=twin_id,
            device_config=device_config,
            twin_spec=twin_spec,
            twin_device=twin_device,
        )

        # Store in registry
        self.interview_twins[twin_id] = digital_twin

        # If house_id provided, add to house twin
        if house_id:
            await self._add_twin_to_house(digital_twin, house_id)

        logger.info(f"Digital twin created: {twin_id}")
        return digital_twin

    def _create_twin_specification(
        self, device_config: Dict[str, Any], twin_config: Dict[str, Any]
    ) -> TwinSpecification:
        """Create twin specification from device and user preferences."""

        device_type = device_config.get("function", "unknown")
        integration_type = device_config.get("integration_type", "generic")

        # Map device type to twin type
        twin_type = self._map_device_to_twin_type(device_type, integration_type)

        # Get template if available
        template = self.twin_templates.get(twin_type, {})

        # Create specification
        spec = TwinSpecification(
            device_id=device_config["id"],
            twin_type=twin_type,
            fidelity_level=twin_config.get("fidelity_level", "basic"),
            sync_frequency=twin_config.get("sync_frequency", 60),
            enable_predictions=twin_config.get("enable_predictions", True),
            enable_scenarios=twin_config.get("enable_scenarios", False),
            enable_learning=twin_config.get("enable_learning", False),
            physics_modeling=twin_config.get("physics_modeling", False),
            simulation_models=template.get("simulation_models", []),
            prediction_capabilities=template.get("prediction_capabilities", []),
            environmental_factors=template.get("environmental_factors", []),
        )

        return spec

    def _map_device_to_twin_type(self, device_type: str, integration_type: str) -> str:
        """Map device type and integration to twin type."""

        # Integration-specific mapping
        if integration_type == "hue" and device_type == "lighting":
            return "hue_light"
        elif integration_type == "nest" and device_type == "climate":
            return "smart_thermostat"
        elif integration_type == "ring" and device_type == "security":
            return "security_camera"
        elif integration_type in ["sonos", "alexa", "google_home"]:
            return "smart_speaker"

        # Generic mapping
        type_mapping = {
            "lighting": "smart_light",
            "climate": "smart_thermostat",
            "security": "security_device",
            "sensor": "smart_sensor",
            "switch": "smart_switch",
            "lock": "smart_lock",
            "media": "media_device",
        }

        return type_mapping.get(device_type, "generic_device")

    def _create_twin_device(
        self, device_config: Dict[str, Any], twin_spec: TwinSpecification
    ) -> DigitalTwinDevice:
        """Create the core digital twin device."""

        # Extract device information
        device_name = device_config.get("name", "Unknown Device")
        device_brand = device_config.get("brand", "Unknown")
        device_model = device_config.get("model", "Unknown")
        device_function = device_config.get("function", "unknown")

        # Create twin device
        twin_device = DigitalTwinDevice(
            id=f"twin_device_{device_config['id']}",
            name=device_name,
            device_type=twin_spec.twin_type,
            device_class=device_function,
            position=Position3D(0, 0, 1),  # Default position
            dimensions=Dimensions3D(0.3, 0.3, 0.3),  # Default dimensions
            room_id="",  # Will be set when added to room
            capabilities=device_config.get("supported_features", []),
            metadata={
                "brand": device_brand,
                "model": device_model,
                "integration_type": device_config.get("integration_type"),
                "twin_spec": twin_spec.to_dict(),
                "fidelity_level": twin_spec.fidelity_level,
            },
            real_device_id=device_config.get("created_device_id"),
            sync_status=SyncStatus.NO_REAL_DEVICE,
        )

        # Set initial state based on device type
        self._initialize_twin_device_state(twin_device, twin_spec)

        return twin_device

    def _initialize_twin_device_state(
        self, twin_device: DigitalTwinDevice, twin_spec: TwinSpecification
    ) -> None:
        """Initialize twin device state based on device type and spec."""

        if twin_spec.twin_type == "hue_light":
            twin_device.update_state(
                {
                    "power": False,
                    "brightness": 0,
                    "color_temp": 4000,
                    "rgb_color": [255, 255, 255],
                    "transition_time": 0.5,
                }
            )
        elif twin_spec.twin_type == "smart_thermostat":
            twin_device.update_state(
                {
                    "power": True,
                    "mode": "auto",
                    "target_temperature": 22.0,
                    "current_temperature": 21.5,
                    "current_humidity": 50,
                    "fan_mode": "auto",
                }
            )
        elif twin_spec.twin_type == "security_camera":
            twin_device.update_state(
                {
                    "power": True,
                    "recording": False,
                    "streaming": False,
                    "motion_detection": True,
                    "night_vision": "auto",
                }
            )
        elif twin_spec.twin_type == "smart_speaker":
            twin_device.update_state(
                {
                    "power": True,
                    "volume": 50,
                    "muted": False,
                    "playing": False,
                    "voice_control": True,
                }
            )
        else:
            # Generic device
            twin_device.update_state({"power": False, "status": "idle"})

        twin_device.state = DeviceState.SIMULATED

    async def _add_twin_to_house(
        self, digital_twin: DigitalTwin, house_id: str
    ) -> None:
        """Add digital twin to a house twin."""

        # Get or create house twin
        house_twin = await self.core_manager.get_house_twin(house_id)

        if not house_twin:
            # Create house twin if it doesn't exist
            house_id_int = (
                int(house_id.split("_")[-1]) if "_" in house_id else int(house_id)
            )
            house_twin = await self.core_manager.create_house_twin(house_id_int)

        if house_twin:
            # Find appropriate room for the device
            room_id = self._find_suitable_room(digital_twin, house_twin)

            if room_id:
                house_twin.add_device(digital_twin.twin_device, room_id)
                logger.info(f"Added twin {digital_twin.id} to room {room_id}")
            else:
                # Add to house without specific room
                house_twin.all_devices[
                    digital_twin.twin_device.id
                ] = digital_twin.twin_device
                logger.info(f"Added twin {digital_twin.id} to house (no specific room)")

    def _find_suitable_room(
        self, digital_twin: DigitalTwin, house_twin: DigitalTwinHouse
    ) -> Optional[str]:
        """Find the most suitable room for a device twin."""

        device_type = digital_twin.specification.twin_type
        all_rooms = house_twin.get_all_rooms()

        if not all_rooms:
            return None

        # Room preferences by device type
        room_preferences = {
            "hue_light": ["living_room", "bedroom", "kitchen"],
            "smart_thermostat": ["living_room", "hallway"],
            "security_camera": ["living_room", "entrance", "outdoor"],
            "smart_speaker": ["living_room", "kitchen", "bedroom"],
            "smart_lock": ["entrance", "front_door"],
            "smart_switch": ["any"],
        }

        preferred_types = room_preferences.get(device_type, ["living_room"])

        # Find matching room
        for pref_type in preferred_types:
            if pref_type == "any":
                return all_rooms[0].id

            matching_rooms = [
                room
                for room in all_rooms
                if pref_type.replace("_", " ") in room.room_type.lower()
            ]

            if matching_rooms:
                return matching_rooms[0].id

        # Default to first room
        return all_rooms[0].id

    async def setup_synchronization(
        self, twin_id: str, device_id: str, sync_config: SyncConfig
    ) -> bool:
        """Set up synchronization between twin and physical device."""

        digital_twin = self.interview_twins.get(twin_id)
        if not digital_twin:
            logger.error(f"Twin {twin_id} not found")
            return False

        # Store sync configuration
        digital_twin.sync_config = sync_config

        # Register device mapping with core synchronizer
        if hasattr(self.core_manager, "synchronizer"):
            self.core_manager.synchronizer.register_device_mapping(
                device_id, digital_twin.twin_device.id
            )

        # Start sync task if bidirectional
        if sync_config.bidirectional:
            task = asyncio.create_task(self._sync_loop(twin_id, device_id, sync_config))
            self.sync_tasks[twin_id] = task

        digital_twin.sync_active = True
        logger.info(f"Synchronization setup for twin {twin_id}")
        return True

    async def _sync_loop(
        self, twin_id: str, device_id: str, sync_config: SyncConfig
    ) -> None:
        """Continuous synchronization loop between twin and device."""

        logger.info(f"Starting sync loop for twin {twin_id}")

        try:
            while True:
                await asyncio.sleep(sync_config.frequency)

                digital_twin = self.interview_twins.get(twin_id)
                if not digital_twin:
                    break

                try:
                    # Sync from device to twin
                    await self._sync_device_to_twin(digital_twin, device_id)

                    # Sync from twin to device (if safe)
                    if sync_config.safe_mode:
                        await self._sync_twin_to_device_safe(digital_twin, device_id)
                    else:
                        await self._sync_twin_to_device(digital_twin, device_id)

                    digital_twin.last_updated = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Sync error for twin {twin_id}: {e}")
                    digital_twin.sync_errors.append(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "error": str(e),
                            "device_id": device_id,
                        }
                    )

                    # Keep only last 10 errors
                    digital_twin.sync_errors = digital_twin.sync_errors[-10:]

        except asyncio.CancelledError:
            logger.info(f"Sync loop cancelled for twin {twin_id}")
        except Exception as e:
            logger.error(f"Sync loop error for twin {twin_id}: {e}")

    async def _sync_device_to_twin(
        self, digital_twin: DigitalTwin, device_id: str
    ) -> None:
        """Sync state from physical device to twin."""

        # This would interface with the actual device integration
        # For now, simulate getting device state
        logger.debug(f"Syncing device {device_id} to twin {digital_twin.id}")

        # In real implementation, this would:
        # 1. Get current device state from integration
        # 2. Update twin device state
        # 3. Check for conflicts

    async def _sync_twin_to_device(
        self, digital_twin: DigitalTwin, device_id: str
    ) -> None:
        """Sync state from twin to physical device."""

        # This would interface with the actual device integration
        # For now, simulate sending commands to device
        logger.debug(f"Syncing twin {digital_twin.id} to device {device_id}")

        # In real implementation, this would:
        # 1. Check for twin state changes
        # 2. Validate changes are safe
        # 3. Send commands to physical device
        # 4. Verify command execution

    async def _sync_twin_to_device_safe(
        self, digital_twin: DigitalTwin, device_id: str
    ) -> None:
        """Safely sync state from twin to device with validation."""

        # Additional safety checks would be implemented here
        await self._sync_twin_to_device(digital_twin, device_id)

    async def twin_exists(self, twin_id: str) -> bool:
        """Check if a twin exists."""
        return twin_id in self.interview_twins

    async def update_twin_state(
        self, twin_id: str, state_changes: Dict[str, Any]
    ) -> bool:
        """Update twin state."""

        digital_twin = self.interview_twins.get(twin_id)
        if not digital_twin:
            return False

        digital_twin.twin_device.update_state(state_changes)
        digital_twin.last_updated = datetime.utcnow()

        logger.debug(f"Updated twin {twin_id} state: {state_changes}")
        return True

    def get_twin(self, twin_id: str) -> Optional[DigitalTwin]:
        """Get a digital twin by ID."""
        return self.interview_twins.get(twin_id)

    def get_all_twins(self) -> List[DigitalTwin]:
        """Get all interview-created twins."""
        return list(self.interview_twins.values())

    async def get_twin_statistics(self) -> Dict[str, Any]:
        """Get statistics about the twin system."""

        total_twins = len(self.interview_twins)
        active_syncs = len(self.sync_tasks)

        twin_types = {}
        fidelity_levels = {}

        for twin in self.interview_twins.values():
            twin_type = twin.specification.twin_type
            fidelity = twin.specification.fidelity_level

            twin_types[twin_type] = twin_types.get(twin_type, 0) + 1
            fidelity_levels[fidelity] = fidelity_levels.get(fidelity, 0) + 1

        return {
            "total_twins": total_twins,
            "active_synchronizations": active_syncs,
            "twin_types": twin_types,
            "fidelity_levels": fidelity_levels,
            "templates_available": len(self.twin_templates),
        }
