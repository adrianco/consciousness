"""
Specific device simulator implementations.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

from .base import BaseSimulatedDevice, SimulatorEventType


logger = logging.getLogger(__name__)


class SimulatedLight(BaseSimulatedDevice):
    """Simulated smart light device."""
    
    def _initialize_state(self) -> None:
        """Initialize light-specific state."""
        self._state = {
            "power": False,
            "brightness": 0,  # 0-100
            "color_temp": 4000,  # Kelvin (2700-6500)
            "rgb_color": [255, 255, 255],  # RGB values
            "effect": None,  # None, "rainbow", "pulse", "strobe"
            "transition_time": 0.5  # Seconds
        }
        
        self._attributes = {
            "min_brightness": 1,
            "max_brightness": 100,
            "min_color_temp": 2700,
            "max_color_temp": 6500,
            "supports_color": True,
            "supports_effects": True,
            "available_effects": ["rainbow", "pulse", "strobe", "fireplace"]
        }
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        return [
            "brightness",
            "color_temp",
            "rgb_color",
            "effects",
            "transition"
        ]
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": "1.2.3",
            "hw_version": "2.0",
            "capabilities": {
                "brightness": True,
                "color": True,
                "color_temp": True,
                "effects": True
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle light-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "turn_on": self._turn_on,
            "turn_off": self._turn_off,
            "set_brightness": self._set_brightness,
            "set_color": self._set_color,
            "set_color_temp": self._set_color_temp,
            "set_effect": self._set_effect,
            "toggle": self._toggle
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _turn_on(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn on the light."""
        old_state = self._state["power"]
        self._state["power"] = True
        
        # Apply optional parameters
        if "brightness" in params:
            self._state["brightness"] = max(1, min(100, params["brightness"]))
        elif self._state["brightness"] == 0:
            self._state["brightness"] = 100
        
        if "color" in params:
            self._state["rgb_color"] = params["color"]
        
        if "color_temp" in params:
            self._state["color_temp"] = max(2700, min(6500, params["color_temp"]))
        
        if "effect" in params:
            self._state["effect"] = params["effect"]
        
        # Emit state change event
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"power": old_state},
                "new_state": {"power": True, "brightness": self._state["brightness"]}
            }
        )
        
        return {"power": True, "brightness": self._state["brightness"]}
    
    async def _turn_off(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn off the light."""
        old_state = self._state["power"]
        self._state["power"] = False
        self._state["effect"] = None
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"power": old_state},
                "new_state": {"power": False}
            }
        )
        
        return {"power": False}
    
    async def _set_brightness(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set light brightness."""
        if "brightness" not in params:
            raise ValueError("Missing brightness parameter")
        
        old_brightness = self._state["brightness"]
        new_brightness = max(1, min(100, params["brightness"]))
        self._state["brightness"] = new_brightness
        
        # Turn on if setting brightness while off
        if not self._state["power"] and new_brightness > 0:
            self._state["power"] = True
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"brightness": old_brightness},
                "new_state": {"brightness": new_brightness}
            }
        )
        
        return {"brightness": new_brightness}
    
    async def _set_color(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set light color."""
        if "color" not in params:
            raise ValueError("Missing color parameter")
        
        old_color = self._state["rgb_color"]
        self._state["rgb_color"] = params["color"]
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"rgb_color": old_color},
                "new_state": {"rgb_color": self._state["rgb_color"]}
            }
        )
        
        return {"rgb_color": self._state["rgb_color"]}
    
    async def _set_color_temp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set color temperature."""
        if "color_temp" not in params:
            raise ValueError("Missing color_temp parameter")
        
        old_temp = self._state["color_temp"]
        new_temp = max(2700, min(6500, params["color_temp"]))
        self._state["color_temp"] = new_temp
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"color_temp": old_temp},
                "new_state": {"color_temp": new_temp}
            }
        )
        
        return {"color_temp": new_temp}
    
    async def _set_effect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set light effect."""
        effect = params.get("effect")
        if effect and effect not in self._attributes["available_effects"]:
            raise ValueError(f"Invalid effect: {effect}")
        
        old_effect = self._state["effect"]
        self._state["effect"] = effect
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"effect": old_effect},
                "new_state": {"effect": effect}
            }
        )
        
        return {"effect": effect}
    
    async def _toggle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle light power."""
        if self._state["power"]:
            return await self._turn_off(params)
        else:
            return await self._turn_on(params)
    
    async def _generate_random_event(self) -> None:
        """Generate light-specific random events."""
        if not self._state["power"]:
            return
        
        event_choices = [
            ("flicker", 0.1),
            ("color_drift", 0.2),
            ("brightness_fluctuation", 0.15),
            None
        ]
        
        event = random.choice(event_choices)
        if event and isinstance(event, tuple):
            event_type, _ = event
            
            if event_type == "flicker":
                # Simulate brief power fluctuation
                await self.emit_event(
                    SimulatorEventType.STATE_CHANGE,
                    {"event": "flicker", "duration": random.uniform(0.1, 0.5)}
                )
            
            elif event_type == "color_drift":
                # Simulate slight color temperature drift
                drift = random.randint(-100, 100)
                new_temp = max(2700, min(6500, self._state["color_temp"] + drift))
                self._state["color_temp"] = new_temp
                
            elif event_type == "brightness_fluctuation":
                # Simulate brightness fluctuation
                change = random.randint(-5, 5)
                new_brightness = max(1, min(100, self._state["brightness"] + change))
                self._state["brightness"] = new_brightness
    
    async def _state_updater(self) -> None:
        """Update light state based on environmental factors."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Auto-adjust based on time of day if enabled
                if self._state["power"] and self.environmental_factors.get("auto_adjust", False):
                    time_of_day = self.environmental_factors["time_of_day"]
                    
                    if time_of_day == "evening":
                        # Warm light in evening
                        self._state["color_temp"] = 3000
                        self._state["brightness"] = 70
                    elif time_of_day == "night":
                        # Dim warm light at night
                        self._state["color_temp"] = 2700
                        self._state["brightness"] = 30
                    else:
                        # Bright cool light during day
                        self._state["color_temp"] = 5000
                        self._state["brightness"] = 100
                
            except Exception as e:
                logger.error(f"Error in state updater: {e}")


class SimulatedThermostat(BaseSimulatedDevice):
    """Simulated smart thermostat device."""
    
    def _initialize_state(self) -> None:
        """Initialize thermostat-specific state."""
        self._state = {
            "power": True,
            "mode": "auto",  # off, heat, cool, auto
            "target_temperature": 22.0,  # Celsius
            "current_temperature": 21.5,
            "current_humidity": 50,
            "fan_mode": "auto",  # auto, low, medium, high
            "swing_mode": "off",  # off, vertical, horizontal, both
            "preset_mode": "comfort",  # comfort, eco, away, sleep
            "is_heating": False,
            "is_cooling": False
        }
        
        self._attributes = {
            "min_temp": 16,
            "max_temp": 30,
            "temp_step": 0.5,
            "supported_modes": ["off", "heat", "cool", "auto"],
            "supported_fan_modes": ["auto", "low", "medium", "high"],
            "supported_swing_modes": ["off", "vertical", "horizontal", "both"],
            "supported_presets": ["comfort", "eco", "away", "sleep"],
            "supports_humidity": True
        }
        
        # Internal state for simulation
        self._last_temp_update = datetime.utcnow()
        self._temp_trend = 0.0  # Rate of temperature change
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        return [
            "temperature",
            "humidity",
            "mode",
            "fan_mode",
            "swing_mode",
            "preset_mode"
        ]
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": "3.1.0",
            "hw_version": "1.5",
            "capabilities": {
                "heating": True,
                "cooling": True,
                "humidity_control": True,
                "scheduling": True
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle thermostat-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "set_temperature": self._set_temperature,
            "set_mode": self._set_mode,
            "set_fan_mode": self._set_fan_mode,
            "set_swing_mode": self._set_swing_mode,
            "set_preset": self._set_preset,
            "turn_on": self._turn_on,
            "turn_off": self._turn_off
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _set_temperature(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set target temperature."""
        if "temperature" not in params:
            raise ValueError("Missing temperature parameter")
        
        old_temp = self._state["target_temperature"]
        new_temp = max(16, min(30, params["temperature"]))
        self._state["target_temperature"] = new_temp
        
        # Update heating/cooling state
        self._update_hvac_state()
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"target_temperature": old_temp},
                "new_state": {"target_temperature": new_temp}
            }
        )
        
        return {"target_temperature": new_temp}
    
    async def _set_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set HVAC mode."""
        if "mode" not in params:
            raise ValueError("Missing mode parameter")
        
        mode = params["mode"]
        if mode not in self._attributes["supported_modes"]:
            raise ValueError(f"Invalid mode: {mode}")
        
        old_mode = self._state["mode"]
        self._state["mode"] = mode
        
        # Turn off if mode is "off"
        if mode == "off":
            self._state["power"] = False
            self._state["is_heating"] = False
            self._state["is_cooling"] = False
        else:
            self._state["power"] = True
            self._update_hvac_state()
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"mode": old_mode},
                "new_state": {"mode": mode}
            }
        )
        
        return {"mode": mode}
    
    async def _set_fan_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set fan mode."""
        if "fan_mode" not in params:
            raise ValueError("Missing fan_mode parameter")
        
        fan_mode = params["fan_mode"]
        if fan_mode not in self._attributes["supported_fan_modes"]:
            raise ValueError(f"Invalid fan mode: {fan_mode}")
        
        self._state["fan_mode"] = fan_mode
        return {"fan_mode": fan_mode}
    
    async def _set_swing_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set swing mode."""
        if "swing_mode" not in params:
            raise ValueError("Missing swing_mode parameter")
        
        swing_mode = params["swing_mode"]
        if swing_mode not in self._attributes["supported_swing_modes"]:
            raise ValueError(f"Invalid swing mode: {swing_mode}")
        
        self._state["swing_mode"] = swing_mode
        return {"swing_mode": swing_mode}
    
    async def _set_preset(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set preset mode."""
        if "preset" not in params:
            raise ValueError("Missing preset parameter")
        
        preset = params["preset"]
        if preset not in self._attributes["supported_presets"]:
            raise ValueError(f"Invalid preset: {preset}")
        
        self._state["preset_mode"] = preset
        
        # Adjust target temperature based on preset
        preset_temps = {
            "comfort": 22,
            "eco": 20,
            "away": 18,
            "sleep": 21
        }
        
        if preset in preset_temps:
            self._state["target_temperature"] = preset_temps[preset]
            self._update_hvac_state()
        
        return {"preset": preset}
    
    async def _turn_on(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn on thermostat."""
        self._state["power"] = True
        if self._state["mode"] == "off":
            self._state["mode"] = "auto"
        self._update_hvac_state()
        return {"power": True}
    
    async def _turn_off(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn off thermostat."""
        self._state["power"] = False
        self._state["mode"] = "off"
        self._state["is_heating"] = False
        self._state["is_cooling"] = False
        return {"power": False}
    
    def _update_hvac_state(self) -> None:
        """Update heating/cooling state based on current conditions."""
        if not self._state["power"] or self._state["mode"] == "off":
            self._state["is_heating"] = False
            self._state["is_cooling"] = False
            return
        
        current = self._state["current_temperature"]
        target = self._state["target_temperature"]
        mode = self._state["mode"]
        
        # Hysteresis to prevent rapid switching
        hysteresis = 0.5
        
        if mode == "heat":
            self._state["is_heating"] = current < target - hysteresis
            self._state["is_cooling"] = False
        elif mode == "cool":
            self._state["is_heating"] = False
            self._state["is_cooling"] = current > target + hysteresis
        elif mode == "auto":
            self._state["is_heating"] = current < target - hysteresis
            self._state["is_cooling"] = current > target + hysteresis
    
    async def _generate_random_event(self) -> None:
        """Generate thermostat-specific random events."""
        if not self._state["power"]:
            return
        
        # Simulate temperature sensor drift
        if random.random() < 0.3:
            drift = random.uniform(-0.2, 0.2)
            self._state["current_temperature"] += drift
            
        # Simulate humidity changes
        if random.random() < 0.2:
            change = random.randint(-2, 2)
            self._state["current_humidity"] = max(30, min(70, 
                self._state["current_humidity"] + change))
    
    async def _state_updater(self) -> None:
        """Update thermostat state - simulate temperature changes."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                now = datetime.utcnow()
                time_delta = (now - self._last_temp_update).total_seconds() / 60  # Minutes
                self._last_temp_update = now
                
                # Calculate temperature change based on HVAC state
                temp_change_rate = 0.0  # Degrees per minute
                
                if self._state["is_heating"]:
                    temp_change_rate = 0.1
                elif self._state["is_cooling"]:
                    temp_change_rate = -0.1
                else:
                    # Natural drift towards ambient
                    ambient_temp = self.environmental_factors["temperature"]
                    diff = ambient_temp - self._state["current_temperature"]
                    temp_change_rate = diff * 0.01  # Slow natural drift
                
                # Apply temperature change
                temp_change = temp_change_rate * time_delta
                self._state["current_temperature"] += temp_change
                
                # Update HVAC state
                self._update_hvac_state()
                
                # Emit temperature change event if significant
                if abs(temp_change) > 0.1:
                    await self.emit_event(
                        SimulatorEventType.STATE_CHANGE,
                        {
                            "current_temperature": self._state["current_temperature"],
                            "is_heating": self._state["is_heating"],
                            "is_cooling": self._state["is_cooling"]
                        }
                    )
                
            except Exception as e:
                logger.error(f"Error in thermostat state updater: {e}")


class SimulatedSensor(BaseSimulatedDevice):
    """Simulated sensor device (motion, door/window, temperature, etc.)."""
    
    def __init__(self, sensor_type: str = "motion", **kwargs):
        self.sensor_type = sensor_type
        super().__init__(**kwargs)
        self.device_class = f"sensor_{sensor_type}"
    
    def _initialize_state(self) -> None:
        """Initialize sensor-specific state."""
        if self.sensor_type == "motion":
            self._state = {
                "detected": False,
                "last_motion": None,
                "sensitivity": "medium",  # low, medium, high
                "detection_delay": 30  # Seconds before clearing
            }
        elif self.sensor_type == "door":
            self._state = {
                "open": False,
                "last_opened": None,
                "last_closed": None
            }
        elif self.sensor_type == "temperature":
            self._state = {
                "temperature": 22.0,
                "unit": "celsius"
            }
        elif self.sensor_type == "humidity":
            self._state = {
                "humidity": 50.0,
                "unit": "percent"
            }
        elif self.sensor_type == "light":
            self._state = {
                "illuminance": 100.0,
                "unit": "lux"
            }
        else:
            self._state = {"value": None}
        
        self._attributes = {
            "sensor_type": self.sensor_type,
            "battery_powered": True,
            "battery_level": 85
        }
        
        # Internal state
        self._last_trigger = None
        self._motion_clear_task = None
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        features = ["battery_level"]
        
        if self.sensor_type == "motion":
            features.extend(["sensitivity", "detection_delay"])
        
        return features
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": f"{self.model} {self.sensor_type.title()} Sensor",
            "sw_version": "2.0.1",
            "hw_version": "1.0",
            "sensor_type": self.sensor_type,
            "battery_powered": True
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle sensor-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "trigger": self._trigger_sensor,
            "set_sensitivity": self._set_sensitivity,
            "get_battery": self._get_battery
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _trigger_sensor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manually trigger the sensor (for testing)."""
        if self.sensor_type == "motion":
            return await self._trigger_motion()
        elif self.sensor_type == "door":
            return await self._trigger_door()
        else:
            return {"success": False, "error": "Sensor type doesn't support manual trigger"}
    
    async def _trigger_motion(self) -> Dict[str, Any]:
        """Trigger motion detection."""
        self._state["detected"] = True
        self._state["last_motion"] = datetime.utcnow().isoformat()
        self._last_trigger = datetime.utcnow()
        
        # Cancel existing clear task
        if self._motion_clear_task:
            self._motion_clear_task.cancel()
        
        # Schedule motion clear
        self._motion_clear_task = asyncio.create_task(
            self._clear_motion_after_delay()
        )
        
        await self.emit_event(
            SimulatorEventType.SENSOR_TRIGGERED,
            {
                "sensor_type": "motion",
                "detected": True,
                "timestamp": self._state["last_motion"]
            }
        )
        
        return {"detected": True}
    
    async def _clear_motion_after_delay(self) -> None:
        """Clear motion detection after delay."""
        await asyncio.sleep(self._state["detection_delay"])
        self._state["detected"] = False
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "sensor_type": "motion",
                "detected": False
            }
        )
    
    async def _trigger_door(self) -> Dict[str, Any]:
        """Toggle door state."""
        old_state = self._state["open"]
        self._state["open"] = not old_state
        
        if self._state["open"]:
            self._state["last_opened"] = datetime.utcnow().isoformat()
        else:
            self._state["last_closed"] = datetime.utcnow().isoformat()
        
        await self.emit_event(
            SimulatorEventType.SENSOR_TRIGGERED,
            {
                "sensor_type": "door",
                "open": self._state["open"],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {"open": self._state["open"]}
    
    async def _set_sensitivity(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set motion sensor sensitivity."""
        if self.sensor_type != "motion":
            return {"success": False, "error": "Not a motion sensor"}
        
        if "sensitivity" not in params:
            raise ValueError("Missing sensitivity parameter")
        
        sensitivity = params["sensitivity"]
        if sensitivity not in ["low", "medium", "high"]:
            raise ValueError(f"Invalid sensitivity: {sensitivity}")
        
        self._state["sensitivity"] = sensitivity
        
        # Adjust detection parameters based on sensitivity
        sensitivity_delays = {
            "low": 60,
            "medium": 30,
            "high": 10
        }
        self._state["detection_delay"] = sensitivity_delays[sensitivity]
        
        return {"sensitivity": sensitivity}
    
    async def _get_battery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get battery level."""
        return {"battery_level": self._attributes["battery_level"]}
    
    async def _generate_random_event(self) -> None:
        """Generate sensor-specific random events."""
        # Battery drain simulation
        if self._attributes.get("battery_powered", False) and random.random() < 0.1:
            self._attributes["battery_level"] = max(0, 
                self._attributes["battery_level"] - random.randint(1, 3))
            
            if self._attributes["battery_level"] < 20:
                await self.emit_event(
                    SimulatorEventType.BATTERY_LOW,
                    {"battery_level": self._attributes["battery_level"]}
                )
        
        # Sensor-specific random triggers
        if self.sensor_type == "motion" and self.environmental_factors.get("motion", False):
            if random.random() < 0.3:  # 30% chance when motion is present
                await self._trigger_motion()
        
        elif self.sensor_type == "door" and random.random() < 0.05:
            # Random door open/close (5% chance)
            await self._trigger_door()
    
    async def _state_updater(self) -> None:
        """Update sensor state based on environmental factors."""
        while self._running:
            try:
                await asyncio.sleep(10)  # Update every 10 seconds
                
                if self.sensor_type == "temperature":
                    # Follow environmental temperature with some lag
                    env_temp = self.environmental_factors["temperature"]
                    current = self._state["temperature"]
                    
                    # Gradual change towards environmental temperature
                    diff = env_temp - current
                    self._state["temperature"] = current + (diff * 0.1)
                    
                elif self.sensor_type == "humidity":
                    # Follow environmental humidity
                    env_humidity = self.environmental_factors["humidity"]
                    current = self._state["humidity"]
                    
                    diff = env_humidity - current
                    self._state["humidity"] = current + (diff * 0.1)
                    
                elif self.sensor_type == "light":
                    # Follow environmental light level
                    self._state["illuminance"] = self.environmental_factors["light_level"]
                
            except Exception as e:
                logger.error(f"Error in sensor state updater: {e}")


class SimulatedCamera(BaseSimulatedDevice):
    """Simulated security camera device."""
    
    def _initialize_state(self) -> None:
        """Initialize camera-specific state."""
        self._state = {
            "power": True,
            "recording": False,
            "streaming": False,
            "motion_detection": True,
            "night_vision": "auto",  # off, on, auto
            "resolution": "1080p",  # 720p, 1080p, 4k
            "fps": 30,
            "privacy_mode": False,
            "last_motion": None,
            "last_snapshot": None
        }
        
        self._attributes = {
            "supported_resolutions": ["720p", "1080p", "4k"],
            "supported_fps": [15, 24, 30, 60],
            "has_night_vision": True,
            "has_ptz": True,  # Pan, Tilt, Zoom
            "has_audio": True,
            "storage_type": "cloud",  # local, cloud, both
            "max_recordings": 100
        }
        
        # PTZ position
        self._ptz_position = {
            "pan": 0,    # -180 to 180
            "tilt": 0,   # -90 to 90
            "zoom": 1    # 1 to 10
        }
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        return [
            "recording",
            "streaming",
            "motion_detection",
            "night_vision",
            "ptz",
            "privacy_mode",
            "snapshots"
        ]
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": "4.2.1",
            "hw_version": "2.1",
            "capabilities": {
                "video": True,
                "audio": self._attributes["has_audio"],
                "ptz": self._attributes["has_ptz"],
                "night_vision": self._attributes["has_night_vision"]
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle camera-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "start_recording": self._start_recording,
            "stop_recording": self._stop_recording,
            "start_streaming": self._start_streaming,
            "stop_streaming": self._stop_streaming,
            "take_snapshot": self._take_snapshot,
            "set_privacy": self._set_privacy,
            "set_night_vision": self._set_night_vision,
            "set_resolution": self._set_resolution,
            "ptz_control": self._ptz_control,
            "enable_motion_detection": self._enable_motion_detection,
            "disable_motion_detection": self._disable_motion_detection
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _start_recording(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start recording."""
        if self._state["privacy_mode"]:
            return {"success": False, "error": "Cannot record in privacy mode"}
        
        self._state["recording"] = True
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"recording": True}
        )
        
        return {"recording": True}
    
    async def _stop_recording(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop recording."""
        self._state["recording"] = False
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"recording": False}
        )
        
        return {"recording": False}
    
    async def _start_streaming(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Start streaming."""
        if self._state["privacy_mode"]:
            return {"success": False, "error": "Cannot stream in privacy mode"}
        
        self._state["streaming"] = True
        stream_url = f"rtsp://{self.device_id}.local:554/stream"
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"streaming": True, "stream_url": stream_url}
        )
        
        return {"streaming": True, "stream_url": stream_url}
    
    async def _stop_streaming(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Stop streaming."""
        self._state["streaming"] = False
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"streaming": False}
        )
        
        return {"streaming": False}
    
    async def _take_snapshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a snapshot."""
        if self._state["privacy_mode"]:
            return {"success": False, "error": "Cannot take snapshot in privacy mode"}
        
        snapshot_id = f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self._state["last_snapshot"] = snapshot_id
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"snapshot_taken": True, "snapshot_id": snapshot_id}
        )
        
        return {"snapshot_id": snapshot_id, "url": f"/snapshots/{snapshot_id}.jpg"}
    
    async def _set_privacy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set privacy mode."""
        if "enabled" not in params:
            raise ValueError("Missing enabled parameter")
        
        enabled = params["enabled"]
        self._state["privacy_mode"] = enabled
        
        # Stop recording/streaming if enabling privacy
        if enabled:
            self._state["recording"] = False
            self._state["streaming"] = False
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"privacy_mode": enabled}
        )
        
        return {"privacy_mode": enabled}
    
    async def _set_night_vision(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set night vision mode."""
        if "mode" not in params:
            raise ValueError("Missing mode parameter")
        
        mode = params["mode"]
        if mode not in ["off", "on", "auto"]:
            raise ValueError(f"Invalid night vision mode: {mode}")
        
        self._state["night_vision"] = mode
        return {"night_vision": mode}
    
    async def _set_resolution(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set camera resolution."""
        if "resolution" not in params:
            raise ValueError("Missing resolution parameter")
        
        resolution = params["resolution"]
        if resolution not in self._attributes["supported_resolutions"]:
            raise ValueError(f"Invalid resolution: {resolution}")
        
        self._state["resolution"] = resolution
        return {"resolution": resolution}
    
    async def _ptz_control(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Control PTZ (Pan, Tilt, Zoom)."""
        if not self._attributes["has_ptz"]:
            return {"success": False, "error": "Camera doesn't support PTZ"}
        
        if "pan" in params:
            self._ptz_position["pan"] = max(-180, min(180, params["pan"]))
        
        if "tilt" in params:
            self._ptz_position["tilt"] = max(-90, min(90, params["tilt"]))
        
        if "zoom" in params:
            self._ptz_position["zoom"] = max(1, min(10, params["zoom"]))
        
        return {"ptz_position": self._ptz_position.copy()}
    
    async def _enable_motion_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enable motion detection."""
        self._state["motion_detection"] = True
        return {"motion_detection": True}
    
    async def _disable_motion_detection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Disable motion detection."""
        self._state["motion_detection"] = False
        return {"motion_detection": False}
    
    async def _generate_random_event(self) -> None:
        """Generate camera-specific random events."""
        # Motion detection events
        if (self._state["motion_detection"] and 
            not self._state["privacy_mode"] and
            self.environmental_factors.get("motion", False)):
            
            if random.random() < 0.4:  # 40% chance when motion present
                self._state["last_motion"] = datetime.utcnow().isoformat()
                
                await self.emit_event(
                    SimulatorEventType.SENSOR_TRIGGERED,
                    {
                        "type": "motion_detected",
                        "timestamp": self._state["last_motion"],
                        "confidence": random.uniform(0.7, 0.95)
                    }
                )
        
        # Night vision auto-switching
        if self._state["night_vision"] == "auto":
            light_level = self.environmental_factors["light_level"]
            
            # Switch to night vision in low light
            should_enable = light_level < 10
            current_enabled = self._state.get("_night_vision_active", False)
            
            if should_enable != current_enabled:
                self._state["_night_vision_active"] = should_enable
                await self.emit_event(
                    SimulatorEventType.STATE_CHANGE,
                    {"night_vision_active": should_enable}
                )
    
    async def _state_updater(self) -> None:
        """Update camera state periodically."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Simulate storage usage if recording
                if self._state["recording"]:
                    # Emit storage event occasionally
                    if random.random() < 0.1:
                        await self.emit_event(
                            SimulatorEventType.STATE_CHANGE,
                            {
                                "storage_used": random.randint(10, 90),
                                "storage_unit": "percent"
                            }
                        )
                
            except Exception as e:
                logger.error(f"Error in camera state updater: {e}")


class SimulatedLock(BaseSimulatedDevice):
    """Simulated smart lock device."""
    
    def _initialize_state(self) -> None:
        """Initialize lock-specific state."""
        self._state = {
            "locked": True,
            "jammed": False,
            "battery_level": 75,
            "last_user": None,
            "last_action": None,
            "last_action_time": None,
            "auto_lock_enabled": True,
            "auto_lock_delay": 30,  # Seconds
            "vacation_mode": False
        }
        
        self._attributes = {
            "supports_codes": True,
            "max_codes": 10,
            "supports_fingerprint": True,
            "supports_keypad": True,
            "supports_remote": True,
            "has_doorbell": True
        }
        
        # User codes (simplified for simulation)
        self._user_codes = {
            "1234": "User 1",
            "5678": "User 2",
            "0000": "Master"
        }
        
        # Auto-lock task
        self._auto_lock_task = None
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        return [
            "remote_control",
            "user_codes",
            "auto_lock",
            "vacation_mode",
            "battery_status",
            "jam_detection"
        ]
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": "5.1.2",
            "hw_version": "3.0",
            "capabilities": {
                "codes": self._attributes["supports_codes"],
                "fingerprint": self._attributes["supports_fingerprint"],
                "keypad": self._attributes["supports_keypad"],
                "remote": self._attributes["supports_remote"]
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle lock-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "lock": self._lock,
            "unlock": self._unlock,
            "set_auto_lock": self._set_auto_lock,
            "set_vacation_mode": self._set_vacation_mode,
            "add_code": self._add_code,
            "remove_code": self._remove_code,
            "get_battery": self._get_battery_status
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _lock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lock the door."""
        if self._state["jammed"]:
            return {"success": False, "error": "Lock is jammed"}
        
        old_state = self._state["locked"]
        self._state["locked"] = True
        self._state["last_action"] = "locked"
        self._state["last_action_time"] = datetime.utcnow().isoformat()
        self._state["last_user"] = params.get("user", "remote")
        
        # Cancel auto-lock if running
        if self._auto_lock_task:
            self._auto_lock_task.cancel()
            self._auto_lock_task = None
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"locked": old_state},
                "new_state": {"locked": True},
                "user": self._state["last_user"]
            }
        )
        
        return {"locked": True}
    
    async def _unlock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock the door."""
        if self._state["jammed"]:
            return {"success": False, "error": "Lock is jammed"}
        
        # Verify code if provided
        if "code" in params:
            code = params["code"]
            if code not in self._user_codes:
                await self.emit_event(
                    SimulatorEventType.ERROR_OCCURRED,
                    {"error": "Invalid code attempt", "code": code}
                )
                return {"success": False, "error": "Invalid code"}
            
            user = self._user_codes[code]
        else:
            user = params.get("user", "remote")
        
        old_state = self._state["locked"]
        self._state["locked"] = False
        self._state["last_action"] = "unlocked"
        self._state["last_action_time"] = datetime.utcnow().isoformat()
        self._state["last_user"] = user
        
        # Schedule auto-lock if enabled
        if self._state["auto_lock_enabled"]:
            self._auto_lock_task = asyncio.create_task(
                self._auto_lock_after_delay()
            )
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"locked": old_state},
                "new_state": {"locked": False},
                "user": user
            }
        )
        
        return {"locked": False, "user": user}
    
    async def _auto_lock_after_delay(self) -> None:
        """Auto-lock after configured delay."""
        await asyncio.sleep(self._state["auto_lock_delay"])
        
        if not self._state["locked"]:
            await self._lock({"user": "auto"})
    
    async def _set_auto_lock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Configure auto-lock settings."""
        if "enabled" in params:
            self._state["auto_lock_enabled"] = params["enabled"]
        
        if "delay" in params:
            self._state["auto_lock_delay"] = max(10, min(300, params["delay"]))
        
        return {
            "auto_lock_enabled": self._state["auto_lock_enabled"],
            "auto_lock_delay": self._state["auto_lock_delay"]
        }
    
    async def _set_vacation_mode(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set vacation mode."""
        if "enabled" not in params:
            raise ValueError("Missing enabled parameter")
        
        self._state["vacation_mode"] = params["enabled"]
        
        # Lock immediately if enabling vacation mode
        if params["enabled"] and not self._state["locked"]:
            await self._lock({"user": "vacation_mode"})
        
        return {"vacation_mode": self._state["vacation_mode"]}
    
    async def _add_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a user code."""
        if "code" not in params or "user" not in params:
            raise ValueError("Missing code or user parameter")
        
        if len(self._user_codes) >= self._attributes["max_codes"]:
            return {"success": False, "error": "Maximum codes reached"}
        
        self._user_codes[params["code"]] = params["user"]
        return {"success": True, "user": params["user"]}
    
    async def _remove_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a user code."""
        if "code" not in params:
            raise ValueError("Missing code parameter")
        
        if params["code"] in self._user_codes:
            user = self._user_codes.pop(params["code"])
            return {"success": True, "user": user}
        
        return {"success": False, "error": "Code not found"}
    
    async def _get_battery_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get battery status."""
        return {
            "battery_level": self._state["battery_level"],
            "low_battery": self._state["battery_level"] < 20
        }
    
    async def _generate_random_event(self) -> None:
        """Generate lock-specific random events."""
        # Battery drain
        if random.random() < 0.05:
            self._state["battery_level"] = max(0, 
                self._state["battery_level"] - random.randint(1, 3))
            
            if self._state["battery_level"] < 20:
                await self.emit_event(
                    SimulatorEventType.BATTERY_LOW,
                    {"battery_level": self._state["battery_level"]}
                )
        
        # Rare jam simulation
        if random.random() < 0.001:  # 0.1% chance
            self._state["jammed"] = True
            await self.emit_event(
                SimulatorEventType.ERROR_OCCURRED,
                {"error": "Lock mechanism jammed"}
            )
        
        # Clear jam after some time
        if self._state["jammed"] and random.random() < 0.1:
            self._state["jammed"] = False
            await self.emit_event(
                SimulatorEventType.STATE_CHANGE,
                {"jammed": False}
            )
    
    async def _state_updater(self) -> None:
        """Update lock state periodically."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Update every 5 minutes
                
                # Simulate very slow battery drain
                if random.random() < 0.3:
                    self._state["battery_level"] = max(0,
                        self._state["battery_level"] - 1)
                
            except Exception as e:
                logger.error(f"Error in lock state updater: {e}")


class SimulatedSwitch(BaseSimulatedDevice):
    """Simulated smart switch/outlet device."""
    
    def _initialize_state(self) -> None:
        """Initialize switch-specific state."""
        self._state = {
            "on": False,
            "power_consumption": 0.0,  # Watts
            "energy_today": 0.0,  # kWh
            "voltage": 120.0,  # Volts
            "current": 0.0,  # Amps
            "overload_protection": True,
            "child_lock": False,
            "led_indicator": True
        }
        
        self._attributes = {
            "supports_power_monitoring": True,
            "max_load": 1800,  # Watts
            "outlet_count": 1,
            "supports_dimming": False,
            "supports_usb": False
        }
        
        # Internal state for power simulation
        self._base_consumption = 0.0
        self._last_energy_update = datetime.utcnow()
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        features = ["on_off", "led_indicator"]
        
        if self._attributes["supports_power_monitoring"]:
            features.extend(["power_monitoring", "energy_tracking"])
        
        if self._attributes["outlet_count"] > 1:
            features.append("multi_outlet")
        
        return features
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": "2.4.1",
            "hw_version": "1.2",
            "capabilities": {
                "power_monitoring": self._attributes["supports_power_monitoring"],
                "max_load": self._attributes["max_load"],
                "outlets": self._attributes["outlet_count"]
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle switch-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "turn_on": self._turn_on,
            "turn_off": self._turn_off,
            "toggle": self._toggle,
            "get_power": self._get_power,
            "get_energy": self._get_energy,
            "set_child_lock": self._set_child_lock,
            "set_led": self._set_led,
            "reset_energy": self._reset_energy
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    async def _turn_on(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn on the switch."""
        if self._state["child_lock"]:
            return {"success": False, "error": "Child lock is active"}
        
        old_state = self._state["on"]
        self._state["on"] = True
        
        # Simulate power draw
        self._base_consumption = random.uniform(50, 200)  # Base load
        self._update_power_readings()
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"on": old_state},
                "new_state": {"on": True}
            }
        )
        
        return {"on": True, "power": self._state["power_consumption"]}
    
    async def _turn_off(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Turn off the switch."""
        if self._state["child_lock"]:
            return {"success": False, "error": "Child lock is active"}
        
        old_state = self._state["on"]
        self._state["on"] = False
        
        # No power draw when off
        self._base_consumption = 0.0
        self._update_power_readings()
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {
                "old_state": {"on": old_state},
                "new_state": {"on": False}
            }
        )
        
        return {"on": False}
    
    async def _toggle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Toggle switch state."""
        if self._state["on"]:
            return await self._turn_off(params)
        else:
            return await self._turn_on(params)
    
    async def _get_power(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current power consumption."""
        return {
            "power": self._state["power_consumption"],
            "voltage": self._state["voltage"],
            "current": self._state["current"]
        }
    
    async def _get_energy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get energy consumption."""
        return {
            "energy_today": self._state["energy_today"],
            "unit": "kWh"
        }
    
    async def _set_child_lock(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set child lock."""
        if "enabled" not in params:
            raise ValueError("Missing enabled parameter")
        
        self._state["child_lock"] = params["enabled"]
        return {"child_lock": self._state["child_lock"]}
    
    async def _set_led(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set LED indicator."""
        if "enabled" not in params:
            raise ValueError("Missing enabled parameter")
        
        self._state["led_indicator"] = params["enabled"]
        return {"led_indicator": self._state["led_indicator"]}
    
    async def _reset_energy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset energy counter."""
        self._state["energy_today"] = 0.0
        self._last_energy_update = datetime.utcnow()
        return {"energy_today": 0.0}
    
    def _update_power_readings(self) -> None:
        """Update power-related readings."""
        if self._state["on"]:
            # Add some variation to base consumption
            variation = random.uniform(-10, 10)
            self._state["power_consumption"] = max(0, self._base_consumption + variation)
            
            # Calculate current from power and voltage
            self._state["current"] = self._state["power_consumption"] / self._state["voltage"]
            
            # Check for overload
            if (self._state["power_consumption"] > self._attributes["max_load"] and
                self._state["overload_protection"]):
                # Trip the switch
                self._state["on"] = False
                self._state["power_consumption"] = 0.0
                self._state["current"] = 0.0
                asyncio.create_task(self.emit_event(
                    SimulatorEventType.ERROR_OCCURRED,
                    {"error": "Overload protection triggered"}
                ))
        else:
            self._state["power_consumption"] = 0.0
            self._state["current"] = 0.0
    
    async def _generate_random_event(self) -> None:
        """Generate switch-specific random events."""
        if self._state["on"]:
            # Power fluctuation
            if random.random() < 0.1:
                old_power = self._state["power_consumption"]
                self._update_power_readings()
                
                # Significant change triggers event
                if abs(old_power - self._state["power_consumption"]) > 20:
                    await self.emit_event(
                        SimulatorEventType.STATE_CHANGE,
                        {
                            "power_consumption": self._state["power_consumption"],
                            "change": "fluctuation"
                        }
                    )
    
    async def _state_updater(self) -> None:
        """Update switch state and track energy."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                if self._state["on"]:
                    # Update energy consumption
                    now = datetime.utcnow()
                    time_delta = (now - self._last_energy_update).total_seconds() / 3600  # Hours
                    
                    # Energy = Power * Time
                    energy_consumed = (self._state["power_consumption"] / 1000) * time_delta  # kWh
                    self._state["energy_today"] += energy_consumed
                    
                    self._last_energy_update = now
                    
                    # Update power readings with variation
                    self._update_power_readings()
                
            except Exception as e:
                logger.error(f"Error in switch state updater: {e}")


class SimulatedHub(BaseSimulatedDevice):
    """Simulated smart home hub device."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device_class = "hub"
        self.connected_devices: Dict[str, BaseSimulatedDevice] = {}
    
    def _initialize_state(self) -> None:
        """Initialize hub-specific state."""
        self._state = {
            "online": True,
            "connected_devices": 0,
            "cpu_usage": 15.0,
            "memory_usage": 30.0,
            "temperature": 45.0,  # Celsius
            "uptime": 0,  # Seconds
            "firmware_version": "2.1.0",
            "auto_update": True
        }
        
        self._attributes = {
            "max_devices": 50,
            "supported_protocols": ["zigbee", "zwave", "wifi", "bluetooth"],
            "has_backup_battery": True,
            "battery_runtime": 4,  # Hours
            "storage_capacity": 16  # GB
        }
        
        self._start_time = datetime.utcnow()
    
    def get_supported_features(self) -> List[str]:
        """Return supported features."""
        return [
            "device_management",
            "protocol_bridge",
            "backup_battery",
            "system_monitoring",
            "firmware_update"
        ]
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information."""
        return {
            "manufacturer": self.brand,
            "model": self.model,
            "sw_version": self._state["firmware_version"],
            "hw_version": "1.0",
            "capabilities": {
                "max_devices": self._attributes["max_devices"],
                "protocols": self._attributes["supported_protocols"],
                "backup_battery": self._attributes["has_backup_battery"]
            }
        }
    
    async def handle_command(
        self,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle hub-specific commands."""
        params = parameters or {}
        
        command_handlers = {
            "get_devices": self._get_devices,
            "add_device": self._add_device,
            "remove_device": self._remove_device,
            "get_system_info": self._get_system_info,
            "restart": self._restart,
            "update_firmware": self._update_firmware
        }
        
        handler = command_handlers.get(command)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {command}"
            }
        
        return await self._execute_command(handler, params)
    
    def add_connected_device(self, device: BaseSimulatedDevice) -> None:
        """Add a device to the hub."""
        self.connected_devices[device.device_id] = device
        self._state["connected_devices"] = len(self.connected_devices)
    
    def remove_connected_device(self, device_id: str) -> None:
        """Remove a device from the hub."""
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
            self._state["connected_devices"] = len(self.connected_devices)
    
    async def _get_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get list of connected devices."""
        devices = []
        for device_id, device in self.connected_devices.items():
            devices.append({
                "id": device_id,
                "name": device.name,
                "type": device.device_class,
                "online": device.is_online
            })
        
        return {"devices": devices, "count": len(devices)}
    
    async def _add_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new device (simulation)."""
        if len(self.connected_devices) >= self._attributes["max_devices"]:
            return {"success": False, "error": "Maximum devices reached"}
        
        # In real implementation, this would initiate pairing
        return {"success": True, "pairing_mode": "active"}
    
    async def _remove_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a device."""
        if "device_id" not in params:
            raise ValueError("Missing device_id parameter")
        
        device_id = params["device_id"]
        if device_id in self.connected_devices:
            self.remove_connected_device(device_id)
            return {"success": True, "removed": device_id}
        
        return {"success": False, "error": "Device not found"}
    
    async def _get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system information."""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            "cpu_usage": self._state["cpu_usage"],
            "memory_usage": self._state["memory_usage"],
            "temperature": self._state["temperature"],
            "uptime": uptime,
            "firmware_version": self._state["firmware_version"],
            "connected_devices": self._state["connected_devices"]
        }
    
    async def _restart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restart the hub."""
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"restarting": True}
        )
        
        # Simulate restart delay
        await asyncio.sleep(5)
        
        # Reset state
        self._start_time = datetime.utcnow()
        self._state["cpu_usage"] = 15.0
        self._state["memory_usage"] = 30.0
        
        await self.emit_event(
            SimulatorEventType.STATE_CHANGE,
            {"restarted": True}
        )
        
        return {"success": True, "status": "restarted"}
    
    async def _update_firmware(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update firmware (simulation)."""
        if "version" not in params:
            # Check for updates
            return {
                "current_version": self._state["firmware_version"],
                "available_version": "2.2.0",
                "update_available": True
            }
        
        # Simulate firmware update
        await self.emit_event(
            SimulatorEventType.FIRMWARE_UPDATE,
            {
                "status": "downloading",
                "version": params["version"]
            }
        )
        
        await asyncio.sleep(3)  # Simulate download
        
        await self.emit_event(
            SimulatorEventType.FIRMWARE_UPDATE,
            {
                "status": "installing",
                "version": params["version"]
            }
        )
        
        await asyncio.sleep(2)  # Simulate installation
        
        self._state["firmware_version"] = params["version"]
        
        return {"success": True, "version": params["version"]}
    
    async def _generate_random_event(self) -> None:
        """Generate hub-specific random events."""
        # System resource fluctuation
        if random.random() < 0.2:
            self._state["cpu_usage"] = random.uniform(10, 40)
            self._state["memory_usage"] = random.uniform(25, 50)
            self._state["temperature"] = random.uniform(40, 55)
        
        # Device connection events
        for device in self.connected_devices.values():
            if random.random() < 0.01:  # 1% chance per device
                # Simulate brief disconnection
                old_status = device.is_online
                device.is_online = False
                
                await self.emit_event(
                    SimulatorEventType.CONNECTION_LOST,
                    {"device_id": device.device_id}
                )
                
                # Restore after brief delay
                await asyncio.sleep(random.uniform(1, 5))
                device.is_online = old_status
                
                await self.emit_event(
                    SimulatorEventType.CONNECTION_RESTORED,
                    {"device_id": device.device_id}
                )
    
    async def _state_updater(self) -> None:
        """Update hub state periodically."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Update uptime
                self._state["uptime"] = (
                    datetime.utcnow() - self._start_time
                ).total_seconds()
                
                # Gradual resource usage changes
                self._state["cpu_usage"] += random.uniform(-2, 2)
                self._state["cpu_usage"] = max(5, min(60, self._state["cpu_usage"]))
                
                self._state["memory_usage"] += random.uniform(-1, 1)
                self._state["memory_usage"] = max(20, min(70, self._state["memory_usage"]))
                
                # Temperature based on load
                base_temp = 40 + (self._state["cpu_usage"] / 10)
                self._state["temperature"] = base_temp + random.uniform(-2, 2)
                
            except Exception as e:
                logger.error(f"Error in hub state updater: {e}")