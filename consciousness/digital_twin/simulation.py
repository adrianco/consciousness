"""Environmental simulation engine for digital twin."""

import asyncio
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .models import (
    DigitalTwinDevice,
    DigitalTwinFloor,
    DigitalTwinHouse,
    DigitalTwinRoom,
    EnvironmentalState,
)


class EnvironmentalSimulator:
    """Simulates environmental conditions in the digital twin house."""
    
    def __init__(self, house: DigitalTwinHouse, simulation_rate: float = 1.0):
        self.house = house
        self.simulation_rate = simulation_rate  # Real-time multiplier
        self.time_step = 60.0  # Seconds per simulation step
        self.is_running = False
        
        # Weather model parameters
        self.weather_model = WeatherModel()
        
        # Thermal models for each room
        self.thermal_models: Dict[str, RoomThermalModel] = {}
        
        # Initialize room models
        self._initialize_room_models()
        
    def _initialize_room_models(self):
        """Initialize thermal models for all rooms."""
        for room in self.house.get_all_rooms():
            self.thermal_models[room.id] = RoomThermalModel(room)
            
    async def start(self):
        """Start the environmental simulation."""
        self.is_running = True
        asyncio.create_task(self._simulation_loop())
        
    async def stop(self):
        """Stop the environmental simulation."""
        self.is_running = False
        
    async def _simulation_loop(self):
        """Main simulation loop."""
        while self.is_running:
            try:
                start_time = datetime.utcnow()
                
                # Run one simulation step
                await self._simulate_step()
                
                # Calculate time to next step
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                sleep_time = max(0, (self.time_step / self.simulation_rate) - elapsed)
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)
                
    async def _simulate_step(self):
        """Execute one simulation time step."""
        delta_time = self.time_step  # seconds
        
        # Update weather conditions
        self.weather_model.update(delta_time)
        self.house.external_temperature = self.weather_model.temperature
        self.house.external_humidity = self.weather_model.humidity
        self.house.weather_conditions = self.weather_model.get_conditions()
        
        # Simulate each room
        for room in self.house.get_all_rooms():
            thermal_model = self.thermal_models[room.id]
            
            # Get neighboring rooms for heat transfer
            neighbors = self._get_neighboring_rooms(room)
            
            # Simulate room environment
            new_state = thermal_model.simulate_step(
                delta_time,
                external_temp=self.house.external_temperature,
                external_humidity=self.house.external_humidity,
                neighboring_rooms=neighbors,
            )
            
            room.update_environmental_state(new_state)
            
        # Update house totals
        self.house.simulate_tick(delta_time)
        
    def _get_neighboring_rooms(self, room: DigitalTwinRoom) -> List[DigitalTwinRoom]:
        """Get rooms that share walls with the given room."""
        neighbors = []
        
        # Find rooms on the same floor
        current_floor = None
        for floor in self.house.floors.values():
            if room.id in floor.rooms:
                current_floor = floor
                break
                
        if not current_floor:
            return neighbors
            
        # Simple adjacency check based on position
        for other_id, other_room in current_floor.rooms.items():
            if other_id != room.id and self._are_rooms_adjacent(room, other_room):
                neighbors.append(other_room)
                
        return neighbors
        
    def _are_rooms_adjacent(self, room1: DigitalTwinRoom, room2: DigitalTwinRoom) -> bool:
        """Check if two rooms share a wall."""
        # Calculate if rooms share a wall based on position and dimensions
        r1_min_x = room1.position.x
        r1_max_x = room1.position.x + room1.dimensions.width
        r1_min_y = room1.position.y
        r1_max_y = room1.position.y + room1.dimensions.depth
        
        r2_min_x = room2.position.x
        r2_max_x = room2.position.x + room2.dimensions.width
        r2_min_y = room2.position.y
        r2_max_y = room2.position.y + room2.dimensions.depth
        
        # Check for shared walls
        # Vertical wall (same x-coordinate)
        if (abs(r1_max_x - r2_min_x) < 0.1 or abs(r1_min_x - r2_max_x) < 0.1):
            return not (r1_max_y <= r2_min_y or r1_min_y >= r2_max_y)
            
        # Horizontal wall (same y-coordinate)
        if (abs(r1_max_y - r2_min_y) < 0.1 or abs(r1_min_y - r2_max_y) < 0.1):
            return not (r1_max_x <= r2_min_x or r1_min_x >= r2_max_x)
            
        return False
        
    def set_simulation_rate(self, rate: float):
        """Set simulation speed multiplier."""
        self.simulation_rate = max(0.1, min(10.0, rate))  # Limit between 0.1x and 10x
        
    def add_weather_event(self, event_type: str, duration_hours: float, intensity: float):
        """Add a weather event to the simulation."""
        self.weather_model.add_event(event_type, duration_hours, intensity)
        
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "is_running": self.is_running,
            "simulation_rate": self.simulation_rate,
            "time_step": self.time_step,
            "weather": self.weather_model.get_conditions(),
            "rooms_simulated": len(self.thermal_models),
            "total_devices": len(self.house.all_devices),
        }


class WeatherModel:
    """Simulates weather conditions."""
    
    def __init__(self):
        self.temperature = 20.0  # Celsius
        self.humidity = 50.0  # Percentage
        self.wind_speed = 5.0  # m/s
        self.cloud_cover = 0.3  # 0-1
        self.precipitation = 0.0  # mm/hour
        
        # Base conditions (daily averages)
        self.base_temperature = 20.0
        self.base_humidity = 50.0
        
        # Weather events
        self.active_events: List[Dict[str, Any]] = []
        
        # Time tracking
        self.current_time = 0.0  # Seconds since start
        
    def update(self, delta_time: float):
        """Update weather conditions."""
        self.current_time += delta_time
        
        # Daily temperature cycle
        hour_of_day = (self.current_time / 3600) % 24
        daily_temp_variation = 8 * math.sin((hour_of_day - 6) * math.pi / 12)
        self.temperature = self.base_temperature + daily_temp_variation
        
        # Daily humidity cycle (inverse of temperature)
        daily_humidity_variation = -15 * math.sin((hour_of_day - 6) * math.pi / 12)
        self.humidity = max(20, min(90, self.base_humidity + daily_humidity_variation))
        
        # Process weather events
        self._process_weather_events(delta_time)
        
        # Random weather variations
        self.temperature += np.random.normal(0, 0.5)
        self.humidity += np.random.normal(0, 2)
        self.wind_speed = max(0, self.wind_speed + np.random.normal(0, 0.5))
        
        # Keep values in reasonable ranges
        self.temperature = max(-30, min(50, self.temperature))
        self.humidity = max(0, min(100, self.humidity))
        self.wind_speed = max(0, min(30, self.wind_speed))
        
    def _process_weather_events(self, delta_time: float):
        """Process active weather events."""
        active_events = []
        
        for event in self.active_events:
            event["remaining_duration"] -= delta_time
            
            if event["remaining_duration"] > 0:
                # Apply event effects
                if event["type"] == "storm":
                    self.temperature -= event["intensity"] * 5
                    self.humidity += event["intensity"] * 20
                    self.wind_speed += event["intensity"] * 10
                    self.precipitation = event["intensity"] * 15
                elif event["type"] == "heatwave":
                    self.temperature += event["intensity"] * 10
                    self.humidity -= event["intensity"] * 15
                elif event["type"] == "cold_snap":
                    self.temperature -= event["intensity"] * 15
                    
                active_events.append(event)
            else:
                # Event expired, reset effects
                self.precipitation = 0.0
                
        self.active_events = active_events
        
    def add_event(self, event_type: str, duration_hours: float, intensity: float):
        """Add a weather event."""
        event = {
            "type": event_type,
            "remaining_duration": duration_hours * 3600,  # Convert to seconds
            "intensity": max(0, min(1, intensity)),  # Clamp 0-1
        }
        self.active_events.append(event)
        
    def get_conditions(self) -> Dict[str, Any]:
        """Get current weather conditions."""
        return {
            "temperature": round(self.temperature, 1),
            "humidity": round(self.humidity, 1),
            "wind_speed": round(self.wind_speed, 1),
            "cloud_cover": round(self.cloud_cover, 2),
            "precipitation": round(self.precipitation, 1),
            "active_events": [e["type"] for e in self.active_events],
        }


class RoomThermalModel:
    """Thermal simulation model for a room."""
    
    def __init__(self, room: DigitalTwinRoom):
        self.room = room
        
        # Thermal properties
        self.thermal_mass = room.thermal_mass  # J/K
        self.wall_u_value = 0.3  # W/m²K - thermal transmittance
        self.window_u_value = 2.0  # W/m²K - windows are less insulated
        self.air_changes_per_hour = 0.5  # Natural ventilation
        
        # Calculate surface areas
        self._calculate_surfaces()
        
    def _calculate_surfaces(self):
        """Calculate wall and window areas."""
        # Total wall area (simplified - assumes rectangular room)
        wall_height = self.room.dimensions.height
        perimeter = 2 * (self.room.dimensions.width + self.room.dimensions.depth)
        self.wall_area = perimeter * wall_height
        
        # Window area (from room windows list)
        self.window_area = sum(
            window.get("area", 2.0) for window in self.room.windows
        )
        
        # Adjust wall area for windows
        self.wall_area -= self.window_area
        
    def simulate_step(
        self,
        delta_time: float,
        external_temp: float,
        external_humidity: float,
        neighboring_rooms: List[DigitalTwinRoom],
    ) -> EnvironmentalState:
        """Simulate one time step for the room."""
        current_temp = self.room.environmental_state.temperature
        current_humidity = self.room.environmental_state.humidity
        current_co2 = self.room.environmental_state.co2_level
        
        # Heat sources
        device_heat = sum(
            device.heat_generation for device in self.room.devices.values()
        )
        occupant_heat = len(self.room.occupants) * 100  # 100W per person
        
        # Heat losses
        # 1. Through walls
        wall_heat_loss = (
            self.wall_u_value * self.wall_area * (current_temp - external_temp)
        )
        
        # 2. Through windows
        window_heat_loss = (
            self.window_u_value * self.window_area * (current_temp - external_temp)
        )
        
        # 3. Through ventilation
        room_volume = self.room.dimensions.volume
        air_mass = room_volume * 1.2  # kg (air density)
        specific_heat_air = 1005  # J/kg·K
        ventilation_heat_loss = (
            self.air_changes_per_hour / 3600 * air_mass * specific_heat_air *
            (current_temp - external_temp)
        )
        
        # 4. Heat transfer to neighboring rooms
        neighbor_heat_transfer = 0
        for neighbor in neighboring_rooms:
            temp_diff = current_temp - neighbor.environmental_state.temperature
            # Simplified internal wall heat transfer
            shared_wall_area = 20.0  # Assume 20 m² shared wall
            internal_u_value = 0.5  # W/m²K for internal walls
            neighbor_heat_transfer += internal_u_value * shared_wall_area * temp_diff
            
        # Total heat balance
        total_heat_gain = device_heat + occupant_heat
        total_heat_loss = (
            wall_heat_loss + window_heat_loss + 
            ventilation_heat_loss + neighbor_heat_transfer
        )
        
        net_heat = total_heat_gain - total_heat_loss
        
        # Temperature change
        temp_change = (net_heat * delta_time) / self.thermal_mass
        new_temperature = current_temp + temp_change
        
        # Humidity changes
        # Occupants add humidity
        humidity_generation = len(self.room.occupants) * 50  # g/hour per person
        
        # Ventilation removes humidity
        humidity_removal = (
            self.air_changes_per_hour * room_volume * 
            (current_humidity - external_humidity) / 100
        )
        
        net_humidity_change = (humidity_generation - humidity_removal) * delta_time / 3600
        # Convert to percentage change
        humidity_change_percent = net_humidity_change / (room_volume * 12.0) * 100
        new_humidity = max(20, min(90, current_humidity + humidity_change_percent))
        
        # CO2 changes
        co2_generation = len(self.room.occupants) * 20000  # mg/hour per person
        co2_removal = (
            self.air_changes_per_hour * room_volume * 
            (current_co2 - 400) / 1000000  # Convert ppm to fraction
        ) * 1800000  # Air density factor
        
        co2_change = (co2_generation - co2_removal) * delta_time / 3600
        new_co2 = max(400, current_co2 + co2_change / room_volume * 1000)  # Convert to ppm
        
        # Light level from devices
        total_lumens = 0
        for device in self.room.devices.values():
            if device.device_class == "light" and device.current_values.get("power"):
                brightness = device.current_values.get("brightness", 0) / 100
                lumens_per_watt = 80  # Typical LED efficiency
                device_lumens = device.power_consumption * lumens_per_watt * brightness
                total_lumens += device_lumens
                
        new_light_level = total_lumens / self.room.dimensions.floor_area
        
        # Noise level (simplified)
        device_noise = max(
            (device.noise_generation for device in self.room.devices.values()),
            default=30
        )
        occupant_noise = len(self.room.occupants) * 5  # Additional noise per person
        new_noise_level = device_noise + occupant_noise
        
        # Air quality (simplified - mainly CO2 based)
        if new_co2 < 600:
            air_quality = 50  # Good
        elif new_co2 < 1000:
            air_quality = 100  # Moderate
        else:
            air_quality = min(300, 50 + (new_co2 - 600) / 10)  # Poor to very poor
            
        return EnvironmentalState(
            temperature=round(new_temperature, 1),
            humidity=round(new_humidity, 1),
            light_level=round(new_light_level, 1),
            co2_level=round(new_co2, 1),
            noise_level=round(new_noise_level, 1),
            air_quality_index=round(air_quality, 1),
            timestamp=datetime.utcnow(),
        )