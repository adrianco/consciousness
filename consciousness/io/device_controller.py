"""
Device Controller with Integration Layer Support

Unified controller for managing both real and simulated devices through
the device integration layer.
"""

from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from consciousness.models.entities import Device, DeviceEntity
from consciousness.io.device_integration import DeviceIntegrationManager, DeviceMode
from consciousness.digital_twin.core import DigitalTwin, TwinSyncMode
from consciousness.config.device_config import get_device_config_manager
from consciousness.core.logging import get_logger
from consciousness.exceptions import DeviceNotFoundError, IntegrationError

logger = get_logger(__name__)


class DeviceController:
    """Unified device controller supporting real and simulated devices."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.integration_manager = DeviceIntegrationManager(session)
        self.digital_twins: Dict[str, DigitalTwin] = {}
        self.config_manager = get_device_config_manager()
        self.event_callbacks: List[callable] = []
        
        # Task management
        self.discovery_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("Device Controller initialized")
    
    async def initialize(self):
        """Initialize the device controller."""
        try:
            # Initialize integration manager
            await self.integration_manager.initialize()
            
            # Load existing devices from database
            await self._load_existing_devices()
            
            # Start monitoring
            self.monitoring_task = asyncio.create_task(self._monitor_devices())
            
            logger.info("Device Controller initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize Device Controller: {e}")
            raise
    
    async def discover_devices(self, force_refresh: bool = False) -> List[Device]:
        """Discover available devices."""
        try:
            logger.info("Starting device discovery")
            
            # Use integration manager for discovery
            devices = await self.integration_manager.discover_devices()
            
            # Store discovered devices
            for device in devices:
                await self._register_device(device)
            
            logger.info(f"Discovered {len(devices)} devices")
            return devices
            
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            raise
    
    async def _register_device(self, device: Device):
        """Register a discovered device."""
        try:
            # Check if device already exists
            existing = await self._get_device_by_name(device.user_name)
            if existing:
                logger.debug(f"Device {device.user_name} already registered")
                return existing
            
            # Save to database
            device.created_at = datetime.utcnow()
            device.updated_at = datetime.utcnow()
            
            # Add to session (actual database save would happen here)
            logger.info(f"Registered device: {device.user_name}")
            
            # Create digital twin if in simulated or hybrid mode
            mode = self.config_manager.get_device_mode()
            should_simulate = self.config_manager.should_simulate_device(device.user_name)
            
            if mode == DeviceMode.SIMULATED or should_simulate:
                await self._create_digital_twin(device)
            
            return device
            
        except Exception as e:
            logger.error(f"Failed to register device {device.user_name}: {e}")
            raise
    
    async def _create_digital_twin(self, device: Device):
        """Create digital twin for device."""
        try:
            # Determine sync mode based on configuration
            mode = self.config_manager.get_device_mode()
            
            if mode == DeviceMode.SIMULATED:
                sync_mode = TwinSyncMode.PERIODIC
            elif mode == DeviceMode.HYBRID:
                sync_mode = TwinSyncMode.REAL_TIME
            else:
                sync_mode = TwinSyncMode.ON_DEMAND
            
            # Create digital twin
            twin = DigitalTwin(device, sync_mode)
            
            # Subscribe to twin events
            twin.subscribe_to_state_changes(self._handle_twin_state_change)
            
            # Start twin
            await twin.start()
            
            # Store twin
            self.digital_twins[str(device.id)] = twin
            
            logger.info(f"Created digital twin for {device.user_name}")
            
        except Exception as e:
            logger.error(f"Failed to create digital twin for {device.user_name}: {e}")
    
    async def _handle_twin_state_change(self, twin: DigitalTwin, 
                                       old_state: Dict[str, Any], 
                                       new_state: Dict[str, Any]):
        """Handle digital twin state changes."""
        try:
            # Emit device event
            event = {
                "device_id": str(twin.device.id),
                "device_name": twin.device.user_name,
                "event_type": "state_change",
                "old_state": old_state,
                "new_state": new_state,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "digital_twin"
            }
            
            await self._emit_event(event)
            
        except Exception as e:
            logger.error(f"Error handling twin state change: {e}")
    
    async def get_device_state(self, device_id: str) -> Dict[str, Any]:
        """Get current device state."""
        try:
            # Check if we have a digital twin
            if device_id in self.digital_twins:
                twin = self.digital_twins[device_id]
                return await twin.get_state()
            
            # Use integration manager
            return await self.integration_manager.get_device_state(device_id)
            
        except Exception as e:
            logger.error(f"Failed to get state for device {device_id}: {e}")
            raise
    
    async def set_device_state(self, device_id: str, state: Dict[str, Any]) -> bool:
        """Set device state."""
        try:
            # Update digital twin if exists
            if device_id in self.digital_twins:
                twin = self.digital_twins[device_id]
                await twin.set_state(state, trigger="user_command")
            
            # Send to integration manager (which handles real/simulated routing)
            success = await self.integration_manager.execute_command(
                device_id, "set_state", state
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to set state for device {device_id}: {e}")
            raise
    
    async def execute_device_command(self, device_id: str, command: str, 
                                   parameters: Dict[str, Any] = None) -> bool:
        """Execute a command on a device."""
        try:
            parameters = parameters or {}
            
            # Log command
            logger.info(f"Executing command '{command}' on device {device_id}")
            
            # Execute through integration manager
            success = await self.integration_manager.execute_command(
                device_id, command, parameters
            )
            
            # Emit event
            event = {
                "device_id": device_id,
                "event_type": "command_executed",
                "command": command,
                "parameters": parameters,
                "success": success,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._emit_event(event)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to execute command '{command}' on device {device_id}: {e}")
            raise
    
    async def get_device_list(self) -> List[Dict[str, Any]]:
        """Get list of all registered devices."""
        try:
            # In real implementation, this would query the database
            devices = []
            
            # Get devices from config
            device_configs = self.config_manager.get_all_device_configs()
            
            for name, config in device_configs.items():
                device_info = {
                    "id": name,  # Using name as ID for now
                    "name": config.name,
                    "type": config.device_type,
                    "class": config.device_class,
                    "brand": config.brand,
                    "model": config.model,
                    "location": config.location,
                    "online": config.is_online,
                    "capabilities": config.capabilities,
                    "is_simulated": self.config_manager.should_simulate_device(name),
                    "has_digital_twin": name in self.digital_twins
                }
                
                # Add current state if available
                try:
                    if name in self.digital_twins:
                        device_info["current_state"] = await self.digital_twins[name].get_state()
                    else:
                        # Try to get state from integration manager
                        device_info["current_state"] = await self.integration_manager.get_device_state(name)
                except:
                    device_info["current_state"] = {"available": False}
                
                devices.append(device_info)
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get device list: {e}")
            return []
    
    async def get_device_capabilities(self, device_id: str) -> List[str]:
        """Get device capabilities."""
        try:
            # Get from integration manager
            adapter = await self.integration_manager.get_device_adapter(device_id)
            capabilities = await adapter.get_capabilities()
            
            return [cap.value for cap in capabilities]
            
        except Exception as e:
            logger.error(f"Failed to get capabilities for device {device_id}: {e}")
            return []
    
    async def predict_device_state(self, device_id: str, 
                                  future_time: datetime) -> Optional[Dict[str, Any]]:
        """Predict device state at future time using digital twin."""
        try:
            if device_id in self.digital_twins:
                twin = self.digital_twins[device_id]
                return await twin.predict_future_state(future_time)
            
            logger.warning(f"No digital twin available for device {device_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to predict state for device {device_id}: {e}")
            return None
    
    async def get_device_insights(self, device_id: str) -> Dict[str, Any]:
        """Get behavioral insights from digital twin."""
        try:
            if device_id in self.digital_twins:
                twin = self.digital_twins[device_id]
                return {
                    "metrics": twin.get_metrics(),
                    "behavior_insights": twin.get_behavior_insights(),
                    "prediction_accuracy": twin.metrics.accuracy_rate
                }
            
            return {"error": "No digital twin available"}
            
        except Exception as e:
            logger.error(f"Failed to get insights for device {device_id}: {e}")
            return {"error": str(e)}
    
    async def run_simulation_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Run a simulation scenario."""
        try:
            scenario = self.config_manager.get_simulation_scenario(scenario_name)
            if not scenario:
                raise ValueError(f"Scenario '{scenario_name}' not found")
            
            logger.info(f"Running simulation scenario: {scenario_name}")
            
            # Set initial states
            for device_name, initial_state in scenario.initial_states.items():
                if device_name in self.digital_twins:
                    twin = self.digital_twins[device_name]
                    await twin.set_state(initial_state, trigger="scenario_init")
            
            # Execute scheduled events
            start_time = datetime.utcnow()
            
            for event in sorted(scenario.events, key=lambda x: x.get("time", 0)):
                # Wait for event time
                event_time = event.get("time", 0)
                wait_time = event_time - (datetime.utcnow() - start_time).total_seconds()
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                
                # Execute event
                device_name = event["device"]
                action = event["action"]
                
                # Prepare parameters
                params = {k: v for k, v in event.items() 
                         if k not in ["time", "device", "action"]}
                
                try:
                    await self.execute_device_command(device_name, action, params)
                    logger.debug(f"Executed scenario event: {action} on {device_name}")
                except Exception as e:
                    logger.error(f"Failed to execute scenario event: {e}")
            
            return {
                "scenario": scenario_name,
                "status": "completed",
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "events_executed": len(scenario.events)
            }
            
        except Exception as e:
            logger.error(f"Failed to run simulation scenario: {e}")
            return {
                "scenario": scenario_name,
                "status": "failed",
                "error": str(e)
            }
    
    async def _monitor_devices(self):
        """Monitor device health and connectivity."""
        while True:
            try:
                # Check device health
                for device_id, twin in self.digital_twins.items():
                    metrics = twin.get_metrics()
                    
                    # Log metrics periodically
                    if metrics.sync_count % 100 == 0:  # Every 100 syncs
                        logger.debug(f"Device {device_id} metrics: "
                                   f"syncs={metrics.sync_count}, "
                                   f"accuracy={metrics.accuracy_rate:.2f}")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in device monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _load_existing_devices(self):
        """Load existing devices from database."""
        try:
            # In real implementation, this would query the database
            # For now, we'll use configuration
            pass
            
        except Exception as e:
            logger.error(f"Failed to load existing devices: {e}")
    
    async def _get_device_by_name(self, name: str) -> Optional[Device]:
        """Get device by name from database."""
        # In real implementation, this would query the database
        return None
    
    async def subscribe_to_events(self, callback: callable):
        """Subscribe to device events."""
        self.event_callbacks.append(callback)
    
    async def _emit_event(self, event: Dict[str, Any]):
        """Emit event to all subscribers."""
        for callback in self.event_callbacks:
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        try:
            # Stop monitoring
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Stop digital twins
            for twin in self.digital_twins.values():
                await twin.stop()
            
            # Clean up integration manager
            await self.integration_manager.cleanup()
            
            self.digital_twins.clear()
            self.event_callbacks.clear()
            
            logger.info("Device Controller cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Factory function
def create_device_controller(session: AsyncSession) -> DeviceController:
    """Create device controller with proper initialization."""
    return DeviceController(session)