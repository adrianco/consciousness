"""Integration layer connecting digital twin to consciousness engine."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.consciousness_engine import ConsciousnessEngine
from .core import DigitalTwinManager
from .models import DigitalTwinDevice, DigitalTwinHouse


class DigitalTwinConsciousnessIntegration:
    """Integrates digital twin with consciousness engine for intelligent automation."""
    
    def __init__(self, consciousness_engine: ConsciousnessEngine):
        self.consciousness_engine = consciousness_engine
        self.digital_twin_manager = DigitalTwinManager()
        self.is_running = False
        
        # Monitoring intervals
        self.monitoring_interval = 30.0  # seconds
        self.decision_threshold = 0.7  # Confidence threshold for autonomous decisions
        
        # Register event handlers
        self._register_event_handlers()
        
    async def start(self):
        """Start the integrated system."""
        await self.digital_twin_manager.start()
        self.is_running = True
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
        
        print("🔗 Digital Twin - Consciousness Integration started")
        
    async def stop(self):
        """Stop the integrated system."""
        self.is_running = False
        await self.digital_twin_manager.stop()
        
        print("⏹️ Digital Twin - Consciousness Integration stopped")
        
    def _register_event_handlers(self):
        """Register event handlers for digital twin events."""
        self.digital_twin_manager.register_event_handler(
            "device_update", self._handle_device_update
        )
        
    async def _monitoring_loop(self):
        """Main monitoring loop for intelligent automation."""
        while self.is_running:
            try:
                await self._monitor_and_decide()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
                
    async def _monitor_and_decide(self):
        """Monitor digital twin state and make consciousness-driven decisions."""
        for house_id, house in self.digital_twin_manager.houses.items():
            # Analyze house state
            house_analysis = await self._analyze_house_state(house)
            
            # Check for decision triggers
            decisions_needed = self._identify_decision_triggers(house_analysis)
            
            # Process decisions through consciousness engine
            for decision_context in decisions_needed:
                await self._process_decision(house_id, decision_context)
                
    async def _analyze_house_state(self, house: DigitalTwinHouse) -> Dict[str, Any]:
        """Analyze current house state for decision making."""
        environmental_summary = house.get_environmental_summary()
        
        # Comfort analysis
        comfort_issues = []
        if environmental_summary.get("average_temperature", 20) < 18:
            comfort_issues.append("temperature_too_low")
        elif environmental_summary.get("average_temperature", 20) > 26:
            comfort_issues.append("temperature_too_high")
            
        if environmental_summary.get("average_humidity", 50) < 30:
            comfort_issues.append("humidity_too_low")
        elif environmental_summary.get("average_humidity", 50) > 70:
            comfort_issues.append("humidity_too_high")
            
        if environmental_summary.get("average_co2", 400) > 1000:
            comfort_issues.append("co2_high")
            
        # Energy analysis
        high_consumption_devices = [
            device for device in house.all_devices.values()
            if device.power_consumption > 500  # > 500W
        ]
        
        # Occupancy analysis
        rooms_with_people = [
            room for room in house.get_all_rooms()
            if len(room.occupants) > 0
        ]
        
        empty_rooms_with_lights = [
            room for room in house.get_all_rooms()
            if len(room.occupants) == 0 and any(
                device.device_class == "light" and device.current_values.get("power")
                for device in room.devices.values()
            )
        ]
        
        return {
            "house_id": house.id,
            "timestamp": datetime.utcnow().isoformat(),
            "environmental": environmental_summary,
            "comfort_issues": comfort_issues,
            "energy": {
                "total_consumption": house.total_power_consumption,
                "high_consumption_devices": [d.id for d in high_consumption_devices],
                "efficiency_score": self._calculate_energy_efficiency(house),
            },
            "occupancy": {
                "total_occupants": house.current_occupancy,
                "occupied_rooms": [r.id for r in rooms_with_people],
                "wasteful_rooms": [r.id for r in empty_rooms_with_lights],
            },
            "security": {
                "doors_unlocked": self._count_unlocked_doors(house),
                "windows_open": self._count_open_windows(house),
            },
        }
        
    def _identify_decision_triggers(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify situations that require decisions."""
        triggers = []
        
        # Comfort-related decisions
        if "temperature_too_low" in analysis["comfort_issues"]:
            triggers.append({
                "type": "comfort_adjustment",
                "subtype": "heating",
                "urgency": "medium",
                "context": analysis,
                "options": [
                    {"action": "increase_heating", "target_temp": 21},
                    {"action": "turn_on_space_heater", "rooms": analysis["occupancy"]["occupied_rooms"]},
                    {"action": "close_windows", "reason": "retain_heat"},
                ]
            })
            
        if "temperature_too_high" in analysis["comfort_issues"]:
            triggers.append({
                "type": "comfort_adjustment",
                "subtype": "cooling",
                "urgency": "medium",
                "context": analysis,
                "options": [
                    {"action": "increase_cooling", "target_temp": 23},
                    {"action": "turn_on_fans", "rooms": analysis["occupancy"]["occupied_rooms"]},
                    {"action": "open_windows", "reason": "natural_cooling"},
                ]
            })
            
        # Energy efficiency decisions
        if analysis["occupancy"]["wasteful_rooms"]:
            triggers.append({
                "type": "energy_optimization",
                "subtype": "lighting",
                "urgency": "low",
                "context": analysis,
                "options": [
                    {"action": "turn_off_lights", "rooms": analysis["occupancy"]["wasteful_rooms"]},
                    {"action": "dim_lights", "rooms": analysis["occupancy"]["wasteful_rooms"], "level": 20},
                ]
            })
            
        # Air quality decisions
        if "co2_high" in analysis["comfort_issues"]:
            triggers.append({
                "type": "air_quality",
                "subtype": "ventilation",
                "urgency": "high",
                "context": analysis,
                "options": [
                    {"action": "increase_ventilation", "duration": 30},
                    {"action": "open_windows", "reason": "air_exchange"},
                    {"action": "turn_on_air_purifier", "rooms": analysis["occupancy"]["occupied_rooms"]},
                ]
            })
            
        return triggers
        
    async def _process_decision(self, house_id: str, decision_context: Dict[str, Any]):
        """Process a decision through the consciousness engine."""
        # Prepare decision for consciousness engine
        decision_type = f"{decision_context['type']}_{decision_context['subtype']}"
        
        # Make decision
        decision_result = await self.consciousness_engine.make_decision(
            decision_type=decision_type,
            context=decision_context["context"],
            options=decision_context["options"],
            urgency=decision_context["urgency"],
        )
        
        # Execute decision if confidence is high enough
        if (decision_result.get("confidence", 0) >= self.decision_threshold and
            decision_result.get("chosen_option")):
            
            await self._execute_decision(house_id, decision_result)
            
            # Store memory of decision
            await self.consciousness_engine.store_memory(
                title=f"Automated house decision: {decision_type}",
                description=f"Made decision for {house_id}: {decision_result.get('reasoning', '')}",
                memory_type="procedural",
                category="home_automation",
                importance=0.6,
                tags=["automation", "decision", decision_type],
                related_entities=[house_id],
            )
            
    async def _execute_decision(self, house_id: str, decision: Dict[str, Any]):
        """Execute a decision in the digital twin."""
        chosen_option = decision.get("chosen_option", {})
        action = chosen_option.get("action")
        
        if not action:
            return
            
        try:
            if action == "turn_off_lights":
                await self._turn_off_lights(house_id, chosen_option.get("rooms", []))
            elif action == "dim_lights":
                await self._dim_lights(
                    house_id, 
                    chosen_option.get("rooms", []),
                    chosen_option.get("level", 50)
                )
            elif action == "increase_heating":
                await self._adjust_heating(house_id, chosen_option.get("target_temp", 21))
            elif action == "increase_cooling":
                await self._adjust_cooling(house_id, chosen_option.get("target_temp", 23))
            elif action == "turn_on_fans":
                await self._turn_on_fans(house_id, chosen_option.get("rooms", []))
            elif action == "increase_ventilation":
                await self._increase_ventilation(house_id, chosen_option.get("duration", 30))
                
            print(f"✅ Executed decision: {action} for house {house_id}")
            
        except Exception as e:
            print(f"❌ Failed to execute decision {action}: {e}")
            
            # Learn from failure
            await self.consciousness_engine.learn_from_feedback(
                action=action,
                outcome=f"execution_failed: {str(e)}",
                feedback_score=-0.8,
                context={"house_id": house_id, "decision": decision},
            )
            
    async def _turn_off_lights(self, house_id: str, room_ids: List[str]):
        """Turn off lights in specified rooms."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for room_id in room_ids:
            room = house.find_room_by_id(room_id)
            if not room:
                continue
                
            for device in room.devices.values():
                if device.device_class == "light":
                    await self.digital_twin_manager.update_device_state(
                        house_id, device.id, {"power": False, "brightness": 0}
                    )
                    
    async def _dim_lights(self, house_id: str, room_ids: List[str], level: int):
        """Dim lights in specified rooms."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for room_id in room_ids:
            room = house.find_room_by_id(room_id)
            if not room:
                continue
                
            for device in room.devices.values():
                if device.device_class == "light":
                    await self.digital_twin_manager.update_device_state(
                        house_id, device.id, {"brightness": level}
                    )
                    
    async def _adjust_heating(self, house_id: str, target_temp: float):
        """Adjust heating to target temperature."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for device in house.all_devices.values():
            if device.device_class == "climate":
                await self.digital_twin_manager.update_device_state(
                    house_id, device.id, {
                        "hvac_mode": "heat",
                        "temperature": target_temp,
                    }
                )
                
    async def _adjust_cooling(self, house_id: str, target_temp: float):
        """Adjust cooling to target temperature."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for device in house.all_devices.values():
            if device.device_class == "climate":
                await self.digital_twin_manager.update_device_state(
                    house_id, device.id, {
                        "hvac_mode": "cool",
                        "temperature": target_temp,
                    }
                )
                
    async def _turn_on_fans(self, house_id: str, room_ids: List[str]):
        """Turn on fans in specified rooms."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for room_id in room_ids:
            room = house.find_room_by_id(room_id)
            if not room:
                continue
                
            for device in room.devices.values():
                if device.device_class == "fan":
                    await self.digital_twin_manager.update_device_state(
                        house_id, device.id, {"power": True, "speed": "medium"}
                    )
                    
    async def _increase_ventilation(self, house_id: str, duration: int):
        """Increase ventilation for specified duration."""
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for device in house.all_devices.values():
            if device.device_class == "fan" and "ventilation" in device.capabilities:
                await self.digital_twin_manager.update_device_state(
                    house_id, device.id, {"power": True, "speed": "high"}
                )
                
        # Schedule to turn off after duration
        asyncio.create_task(self._schedule_ventilation_off(house_id, duration))
        
    async def _schedule_ventilation_off(self, house_id: str, duration: int):
        """Schedule ventilation to turn off after duration."""
        await asyncio.sleep(duration * 60)  # Convert to seconds
        
        house = await self.digital_twin_manager.get_house_twin(house_id)
        if not house:
            return
            
        for device in house.all_devices.values():
            if device.device_class == "fan" and "ventilation" in device.capabilities:
                await self.digital_twin_manager.update_device_state(
                    house_id, device.id, {"speed": "low"}
                )
                
    def _calculate_energy_efficiency(self, house: DigitalTwinHouse) -> float:
        """Calculate energy efficiency score (0-1)."""
        if house.total_power_consumption == 0:
            return 1.0
            
        # Factors affecting efficiency:
        # 1. Power consumption vs occupancy
        # 2. Lights in unoccupied rooms
        # 3. Heating/cooling efficiency
        
        occupied_rooms = sum(1 for room in house.get_all_rooms() if len(room.occupants) > 0)
        total_rooms = len(house.get_all_rooms())
        
        # Base efficiency on occupancy ratio
        occupancy_efficiency = occupied_rooms / max(1, total_rooms)
        
        # Penalty for lights in empty rooms
        empty_rooms_with_lights = sum(1 for room in house.get_all_rooms()
                                    if len(room.occupants) == 0 and any(
                                        device.device_class == "light" and device.current_values.get("power")
                                        for device in room.devices.values()
                                    ))
        light_penalty = empty_rooms_with_lights / max(1, total_rooms)
        
        # Power per person metric
        power_per_person = house.total_power_consumption / max(1, house.current_occupancy)
        power_efficiency = max(0, 1 - (power_per_person - 500) / 1000)  # Normalize around 500W per person
        
        # Weighted average
        efficiency = (occupancy_efficiency * 0.4 + 
                     (1 - light_penalty) * 0.3 + 
                     power_efficiency * 0.3)
        
        return max(0, min(1, efficiency))
        
    def _count_unlocked_doors(self, house: DigitalTwinHouse) -> int:
        """Count unlocked doors in the house."""
        count = 0
        for device in house.all_devices.values():
            if (device.device_class == "lock" and 
                not device.current_values.get("locked", True)):
                count += 1
        return count
        
    def _count_open_windows(self, house: DigitalTwinHouse) -> int:
        """Count open windows in the house."""
        count = 0
        for device in house.all_devices.values():
            if (device.device_class == "window" and 
                device.current_values.get("open", False)):
                count += 1
        return count
        
    async def _handle_device_update(self, house_id: str, device: DigitalTwinDevice, event_data: Dict[str, Any]):
        """Handle device update events."""
        # Log significant device changes
        if event_data.get("state_change"):
            await self.consciousness_engine.store_memory(
                title=f"Device state change: {device.name}",
                description=f"Device {device.name} changed state in {house_id}",
                memory_type="episodic",
                category="device_activity",
                importance=0.3,
                tags=["device", "state_change", device.device_class],
                related_entities=[house_id, device.id],
            )
            
        # Check if this triggers any immediate decisions
        if device.device_class == "sensor":
            # Sensor updates might trigger environmental decisions
            asyncio.create_task(self._check_sensor_triggers(house_id, device, event_data))
            
    async def _check_sensor_triggers(self, house_id: str, device: DigitalTwinDevice, event_data: Dict[str, Any]):
        """Check if sensor updates trigger immediate decisions."""
        # Example: Smoke detector
        if device.device_type == "smoke_detector" and event_data.get("state", {}).get("smoke_detected"):
            await self._handle_emergency(house_id, "smoke_detected", device.id)
            
    async def _handle_emergency(self, house_id: str, emergency_type: str, device_id: str):
        """Handle emergency situations."""
        # Emergency decisions have highest priority
        decision_result = await self.consciousness_engine.make_decision(
            decision_type=f"emergency_{emergency_type}",
            context={
                "house_id": house_id,
                "device_id": device_id,
                "emergency_type": emergency_type,
                "timestamp": datetime.utcnow().isoformat(),
            },
            options=[
                {"action": "alert_authorities", "priority": "high"},
                {"action": "notify_residents", "priority": "high"},
                {"action": "activate_safety_systems", "priority": "high"},
            ],
            urgency="critical",
        )
        
        # Execute emergency response immediately
        await self._execute_decision(house_id, decision_result)
        
        # Store critical memory
        await self.consciousness_engine.store_memory(
            title=f"Emergency handled: {emergency_type}",
            description=f"Handled {emergency_type} emergency in {house_id}",
            memory_type="episodic",
            category="emergency",
            importance=1.0,
            tags=["emergency", emergency_type, "critical"],
            related_entities=[house_id, device_id],
        )
        
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get integration status."""
        consciousness_status = await self.consciousness_engine.get_status()
        digital_twin_status = await self.digital_twin_manager.get_system_status()
        
        return {
            "is_running": self.is_running,
            "consciousness_engine": consciousness_status,
            "digital_twin": digital_twin_status,
            "monitoring_interval": self.monitoring_interval,
            "decision_threshold": self.decision_threshold,
        }