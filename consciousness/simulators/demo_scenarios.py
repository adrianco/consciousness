"""Demonstration scenarios for the consciousness system."""

import asyncio
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from consciousness.simulators.device_simulator import HouseSimulator


class DemoScenarios:
    """Collection of demonstration scenarios for the consciousness system."""

    @staticmethod
    async def smart_morning_routine(simulator: "HouseSimulator"):
        """
        Smart Morning Routine - Automated wake-up sequence.

        This scenario demonstrates:
        - Gradual lighting adjustment
        - Climate control optimization
        - Security system disarming
        - Energy management
        - Predictive behavior based on patterns
        """
        print("🌅 Starting Smart Morning Routine...")

        # Get relevant devices
        bedroom_lights = [
            d
            for d in simulator.get_device_by_location("bedroom")
            if d.device.device_class == "light"
        ]
        kitchen_lights = [
            d
            for d in simulator.get_device_by_location("kitchen")
            if d.device.device_class == "light"
        ]
        climate_devices = simulator.get_device_by_class("climate")
        security_devices = simulator.get_device_by_class("security")

        # Phase 1: Gentle wake-up (6:30 AM)
        print("Phase 1: Gentle wake-up sequence initiated")

        # Gradually increase bedroom lights
        for light in bedroom_lights:
            await light.set_state({"is_on": True, "brightness": 10, "color_temp": 2700})

        # Start warming the house
        for climate in climate_devices:
            current_temp = climate.state["current_temperature"]
            await climate.set_state(
                {
                    "target_temperature": 72.0,
                    "mode": "heat" if current_temp < 70 else "cool",
                }
            )

        # Simulate 5 minutes passing
        await asyncio.sleep(5)

        # Phase 2: Full wake-up (6:35 AM)
        print("Phase 2: Full wake-up sequence")

        # Increase bedroom lights to 50%
        for light in bedroom_lights:
            await light.set_state({"brightness": 50, "color_temp": 3500})

        # Turn on kitchen lights
        for light in kitchen_lights:
            await light.set_state({"is_on": True, "brightness": 80, "color_temp": 4000})

        # Disarm security system
        for security in security_devices:
            await security.set_state({"armed": False, "mode": "home"})

        await asyncio.sleep(3)

        # Phase 3: Morning activities (6:38 AM)
        print("Phase 3: Preparing for morning activities")

        # Simulate motion in bedroom
        motion_sensors = [
            d
            for d in simulator.get_device_by_class("sensor")
            if d.device.capabilities.get("sensor_type") == "motion"
        ]
        for sensor in motion_sensors:
            if sensor.device.location == "bedroom":
                sensor.state["motion_detected"] = True
                await sensor._trigger_callback("motion_detected", True)

        # Full brightness in active areas
        for light in bedroom_lights + kitchen_lights:
            await light.set_state({"brightness": 100, "color_temp": 5000})

        # Check energy status
        energy_devices = simulator.get_device_by_class("energy")
        for energy in energy_devices:
            print(
                f"Energy Status - Solar: {energy.state['solar_production']}kW, "
                f"Battery: {energy.state['battery_level']}%"
            )

        print("✅ Smart Morning Routine completed")

    @staticmethod
    async def security_alert_scenario(simulator: "HouseSimulator"):
        """
        Security Alert - Intrusion detection simulation.

        This scenario demonstrates:
        - Motion detection triggering
        - Security system response
        - Lighting deterrent activation
        - Notification system
        - Recording and logging
        """
        print("🚨 Starting Security Alert Scenario...")

        # Get relevant devices
        security_devices = simulator.get_device_by_class("security")
        all_lights = simulator.get_device_by_class("light")
        motion_sensors = [
            d
            for d in simulator.get_device_by_class("sensor")
            if d.device.capabilities.get("sensor_type") == "motion"
        ]
        door_sensors = [
            d
            for d in simulator.get_device_by_class("sensor")
            if d.device.capabilities.get("sensor_type") == "door"
        ]

        # Phase 1: Arm security system
        print("Phase 1: Arming security system")
        for security in security_devices:
            await security.set_state({"armed": True, "mode": "away"})

        # Turn off all lights (simulating night/away)
        for light in all_lights:
            await light.set_state({"is_on": False})

        await asyncio.sleep(3)

        # Phase 2: Trigger intrusion
        print("Phase 2: Intrusion detected!")

        # Simulate door opening
        if door_sensors:
            door = door_sensors[0]
            door.state["is_open"] = True
            await door._trigger_callback("door_state_changed", True)

        # Trigger motion sensor
        if motion_sensors:
            motion = motion_sensors[0]
            motion.state["motion_detected"] = True
            await motion._trigger_callback("motion_detected", True)

        # Phase 3: Security response
        print("Phase 3: Executing security response")

        # Create security alert
        for security in security_devices:
            alert = {
                "type": "intrusion",
                "location": motion_sensors[0].device.location
                if motion_sensors
                else "unknown",
                "timestamp": datetime.now(),
                "severity": "critical",
            }
            security.state["alerts"].append(alert)
            await security._trigger_callback("security_alert", alert)

        # Flash all lights as deterrent
        for _ in range(3):
            for light in all_lights:
                await light.set_state({"is_on": True, "brightness": 100})
            await asyncio.sleep(0.5)
            for light in all_lights:
                await light.set_state({"is_on": False})
            await asyncio.sleep(0.5)

        # Leave exterior lights on
        exterior_lights = [
            l for l in all_lights if "exterior" in l.device.location.lower()
        ]
        for light in exterior_lights:
            await light.set_state({"is_on": True, "brightness": 100})

        print("✅ Security Alert Scenario completed - Authorities notified")

    @staticmethod
    async def energy_optimization_scenario(simulator: "HouseSimulator"):
        """
        Energy Optimization - Adaptive device control for efficiency.

        This scenario demonstrates:
        - Peak demand management
        - Solar production utilization
        - Battery optimization
        - Smart device scheduling
        - Cost-aware operation
        """
        print("⚡ Starting Energy Optimization Scenario...")

        # Get relevant devices
        energy_devices = simulator.get_device_by_class("energy")
        climate_devices = simulator.get_device_by_class("climate")
        all_lights = simulator.get_device_by_class("light")

        if not energy_devices:
            print("No energy devices found")
            return

        energy = energy_devices[0]

        # Phase 1: Morning optimization
        print("Phase 1: Morning energy optimization")

        # Simulate low solar production
        await energy.set_state({"solar_production": 0.5, "current_power": 3.5})

        # Reduce non-essential loads
        for light in all_lights:
            if light.state["is_on"] and "bedroom" not in light.device.location:
                await light.set_state({"brightness": 70})  # Dim non-essential lights

        await asyncio.sleep(3)

        # Phase 2: Peak solar production
        print("Phase 2: Maximizing solar utilization")

        # Simulate high solar production
        await energy.set_state({"solar_production": 4.8, "current_power": 2.5})

        # Pre-cool house during solar peak
        for climate in climate_devices:
            await climate.set_state(
                {"target_temperature": 70.0, "fan_speed": "high"}  # Pre-cool
            )

        # Charge battery
        battery_level = energy.state["battery_level"]
        await energy.set_state({"battery_level": min(100, battery_level + 10)})

        await asyncio.sleep(3)

        # Phase 3: Evening peak avoidance
        print("Phase 3: Evening peak demand management")

        # Simulate evening peak rates
        await energy.set_state({"solar_production": 0.2, "current_power": 4.5})

        # Switch to battery power
        battery_level = energy.state["battery_level"]
        await energy.set_state({"battery_level": max(20, battery_level - 5)})

        # Optimize climate settings
        for climate in climate_devices:
            await climate.set_state(
                {
                    "target_temperature": 74.0,  # Allow temperature to drift
                    "fan_speed": "low",
                }
            )

        # Dim lights in unoccupied rooms
        occupied_rooms = ["living_room", "kitchen"]
        for light in all_lights:
            if light.state["is_on"] and light.device.location not in occupied_rooms:
                await light.set_state({"is_on": False})

        print(
            f"✅ Energy Optimization completed - Saved ${random.uniform(2.5, 5.0):.2f} today"
        )

    @staticmethod
    async def party_mode_scenario(simulator: "HouseSimulator"):
        """
        Party Mode - Entertainment scenario with dynamic lighting and climate.

        This scenario demonstrates:
        - Synchronized lighting effects
        - Climate adjustment for crowds
        - Music system integration
        - Energy monitoring
        - Security awareness
        """
        print("🎉 Starting Party Mode...")

        # Get relevant devices
        all_lights = simulator.get_device_by_class("light")
        climate_devices = simulator.get_device_by_class("climate")
        security_devices = simulator.get_device_by_class("security")

        # Phase 1: Setup
        print("Phase 1: Setting up party atmosphere")

        # Set security to home mode
        for security in security_devices:
            await security.set_state({"armed": True, "mode": "home"})

        # Adjust climate for more people
        for climate in climate_devices:
            await climate.set_state(
                {"target_temperature": 68.0, "fan_speed": "high"}  # Cooler for crowds
            )

        # Phase 2: Dynamic lighting
        print("Phase 2: Activating dynamic lighting")

        # Create lighting zones
        living_lights = [l for l in all_lights if "living" in l.device.location.lower()]
        kitchen_lights = [
            l for l in all_lights if "kitchen" in l.device.location.lower()
        ]

        # Simulate party lighting effects
        for _ in range(5):
            # Living room: color cycling
            for light in living_lights:
                if "rgb_color" in light.state:
                    color = random.choice(
                        [
                            (255, 0, 0),
                            (0, 255, 0),
                            (0, 0, 255),
                            (255, 255, 0),
                            (255, 0, 255),
                        ]
                    )
                    await light.set_state(
                        {
                            "is_on": True,
                            "brightness": random.randint(50, 100),
                            "rgb_color": color,
                        }
                    )

            # Kitchen: bright for food/drinks
            for light in kitchen_lights:
                await light.set_state(
                    {"is_on": True, "brightness": 100, "color_temp": 4000}
                )

            await asyncio.sleep(2)

        # Phase 3: Monitor and adjust
        print("Phase 3: Monitoring party conditions")

        # Simulate increased temperature from guests
        for climate in climate_devices:
            current_temp = climate.state["temperature"] + 3
            climate.state["temperature"] = current_temp

        # Adjust cooling
        for climate in climate_devices:
            await climate.set_state({"target_temperature": 66.0})

        print("✅ Party Mode active - System monitoring crowd comfort")

    @staticmethod
    async def vacation_mode_scenario(simulator: "HouseSimulator"):
        """
        Vacation Mode - Security and energy saving while away.

        This scenario demonstrates:
        - Enhanced security monitoring
        - Minimal energy usage
        - Presence simulation
        - Remote monitoring
        - Smart scheduling
        """
        print("✈️ Starting Vacation Mode...")

        # Get all devices
        all_lights = simulator.get_device_by_class("light")
        climate_devices = simulator.get_device_by_class("climate")
        security_devices = simulator.get_device_by_class("security")
        energy_devices = simulator.get_device_by_class("energy")

        # Phase 1: Secure the house
        print("Phase 1: Securing the house")

        # Arm all security
        for security in security_devices:
            await security.set_state({"armed": True, "mode": "vacation", "alerts": []})

        # Turn off all lights
        for light in all_lights:
            await light.set_state({"is_on": False})

        # Set climate to away mode
        for climate in climate_devices:
            await climate.set_state(
                {
                    "target_temperature": 85.0,  # Summer away setting
                    "mode": "auto",
                    "fan_speed": "low",
                }
            )

        await asyncio.sleep(2)

        # Phase 2: Presence simulation
        print("Phase 2: Running presence simulation")

        # Simulate evening presence
        for day in range(3):  # Simulate 3 days
            print(f"  Day {day + 1} evening simulation")

            # Turn on random lights in evening pattern
            living_lights = [
                l for l in all_lights if "living" in l.device.location.lower()
            ]
            bedroom_lights = [
                l for l in all_lights if "bedroom" in l.device.location.lower()
            ]

            # 7 PM - Living room lights
            if living_lights:
                await living_lights[0].set_state(
                    {"is_on": True, "brightness": 80, "color_temp": 3000}
                )

            await asyncio.sleep(1)

            # 9 PM - Bedroom lights
            if bedroom_lights:
                await bedroom_lights[0].set_state(
                    {"is_on": True, "brightness": 60, "color_temp": 2700}
                )

            # 10 PM - Living room off
            if living_lights:
                await living_lights[0].set_state({"is_on": False})

            await asyncio.sleep(1)

            # 11 PM - All lights off
            for light in all_lights:
                await light.set_state({"is_on": False})

            await asyncio.sleep(1)

        # Phase 3: Energy report
        print("Phase 3: Vacation energy savings")

        if energy_devices:
            energy = energy_devices[0]
            # Simulate reduced consumption
            await energy.set_state(
                {
                    "current_power": 0.5,  # Minimal baseline
                    "total_energy": energy.state["total_energy"]
                    + 12,  # 3 days minimal usage
                }
            )

            print(f"  Energy saved: ~{random.uniform(15, 25):.1f} kWh")
            print(f"  Cost saved: ~${random.uniform(3, 5):.2f}")

        print("✅ Vacation Mode active - House secured and monitored")


def register_scenarios(simulator: "HouseSimulator"):
    """Register all demo scenarios with the simulator."""
    simulator.scenarios = {
        "smart_morning": DemoScenarios.smart_morning_routine,
        "security_alert": DemoScenarios.security_alert_scenario,
        "energy_optimization": DemoScenarios.energy_optimization_scenario,
        "party_mode": DemoScenarios.party_mode_scenario,
        "vacation_mode": DemoScenarios.vacation_mode_scenario,
    }
