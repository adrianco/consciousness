"""Demo runner script to showcase the consciousness system."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.database import get_async_session, init_db
from consciousness.interfaces.demo_dashboard import create_demo_dashboard
from consciousness.models.entities import Device, House, Room
from consciousness.simulators.device_simulator import HouseSimulator
from consciousness.simulators.demo_scenarios import register_scenarios

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemoRunner:
    """Main demo runner for the consciousness system."""
    
    def __init__(self):
        self.consciousness = None
        self.house_simulator = None
        self.dashboard = None
        
    async def initialize(self):
        """Initialize the demo system."""
        logger.info("🚀 Initializing Consciousness Demo System...")
        
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Initialize consciousness engine
        async with get_async_session() as session:
            self.consciousness = ConsciousnessEngine(session)
            await self.consciousness.initialize()
            logger.info("✅ Consciousness engine initialized")
        
        # Setup demo house and devices
        await self._setup_demo_house()
        logger.info("✅ Demo house setup complete")
        
        # Create dashboard
        self.dashboard = create_demo_dashboard(self.consciousness)
        self.house_simulator = self.dashboard.house_simulator
        logger.info("✅ Demo dashboard created")
        
    async def _setup_demo_house(self):
        """Setup a complete demo house with various devices."""
        async with get_async_session() as session:
            # Create demo house
            house = House(
                name="Demo Smart Home",
                address="123 AI Street, Future City",
                square_footage=2500.0,
                num_rooms=8,
                num_floors=2,
                timezone="America/Los_Angeles",
                preferences={
                    "temperature_range": [68, 75],
                    "energy_saving": True,
                    "security_level": "high"
                },
                capabilities=[
                    "climate_control",
                    "lighting_automation", 
                    "security_monitoring",
                    "energy_management",
                    "voice_control"
                ]
            )
            session.add(house)
            await session.flush()  # Get the house ID
            
            # Create rooms
            rooms_data = [
                {"name": "Living Room", "room_type": "living_room", "floor": 1, "square_footage": 400.0},
                {"name": "Kitchen", "room_type": "kitchen", "floor": 1, "square_footage": 200.0},
                {"name": "Master Bedroom", "room_type": "bedroom", "floor": 2, "square_footage": 300.0},
                {"name": "Guest Bedroom", "room_type": "bedroom", "floor": 2, "square_footage": 200.0},
                {"name": "Home Office", "room_type": "office", "floor": 2, "square_footage": 150.0},
                {"name": "Hallway", "room_type": "hallway", "floor": 1, "square_footage": 100.0},
                {"name": "Garage", "room_type": "garage", "floor": 1, "square_footage": 400.0},
                {"name": "Exterior", "room_type": "exterior", "floor": 0, "square_footage": 0.0}
            ]
            
            rooms = {}
            for room_data in rooms_data:
                room = Room(
                    house_id=house.id,
                    **room_data,
                    windows=2 if room_data["room_type"] != "garage" else 0,
                    preferred_temperature=72.0,
                    lighting_preferences={"default_brightness": 80, "color_temp": 4000}
                )
                session.add(room)
                await session.flush()
                rooms[room.name] = room
            
            # Create demo devices
            devices_data = [
                # Climate devices
                {
                    "user_name": "Main Thermostat",
                    "location": "Living Room",
                    "device_class": "climate",
                    "integration_type": "nest",
                    "capabilities": {"heating": True, "cooling": True, "auto_mode": True}
                },
                {
                    "user_name": "Bedroom Climate Control",
                    "location": "Master Bedroom", 
                    "device_class": "climate",
                    "integration_type": "ecobee",
                    "capabilities": {"heating": True, "cooling": True, "humidity_control": True}
                },
                
                # Lighting devices
                {
                    "user_name": "Living Room Lights",
                    "location": "Living Room",
                    "device_class": "light",
                    "integration_type": "hue",
                    "capabilities": {"dimming": True, "color_changing": True}
                },
                {
                    "user_name": "Kitchen Lights",
                    "location": "Kitchen",
                    "device_class": "light", 
                    "integration_type": "hue",
                    "capabilities": {"dimming": True, "color_temp": True}
                },
                {
                    "user_name": "Bedroom Lights",
                    "location": "Master Bedroom",
                    "device_class": "light",
                    "integration_type": "hue",
                    "capabilities": {"dimming": True, "color_temp": True}
                },
                {
                    "user_name": "Exterior Lights",
                    "location": "Exterior",
                    "device_class": "light",
                    "integration_type": "hue",
                    "capabilities": {"dimming": True, "motion_sensor": True}
                },
                
                # Sensors
                {
                    "user_name": "Living Room Motion",
                    "location": "Living Room",
                    "device_class": "sensor",
                    "integration_type": "smartthings",
                    "capabilities": {"sensor_type": "motion"}
                },
                {
                    "user_name": "Front Door Sensor",
                    "location": "Hallway",
                    "device_class": "sensor",
                    "integration_type": "smartthings", 
                    "capabilities": {"sensor_type": "door"}
                },
                {
                    "user_name": "Kitchen Temperature",
                    "location": "Kitchen",
                    "device_class": "sensor",
                    "integration_type": "smartthings",
                    "capabilities": {"sensor_type": "temperature"}
                },
                
                # Security
                {
                    "user_name": "Security System",
                    "location": "Hallway",
                    "device_class": "security",
                    "integration_type": "ring",
                    "capabilities": {"arming": True, "cameras": True, "alerts": True}
                },
                
                # Energy
                {
                    "user_name": "Solar & Battery System",
                    "location": "Garage", 
                    "device_class": "energy",
                    "integration_type": "tesla",
                    "capabilities": {"solar": True, "battery": True, "grid_tie": True}
                }
            ]
            
            devices = []
            for device_data in devices_data:
                device = Device(
                    house_id=house.id,
                    room_id=next((r.id for r in rooms.values() if r.name == device_data["location"]), None),
                    user_description=f"Demo {device_data['user_name']}",
                    detected_brand=device_data["integration_type"].title(),
                    integration_type=device_data["integration_type"],
                    supported_features=list(device_data["capabilities"].keys()),
                    capabilities=device_data["capabilities"],
                    status="online",
                    discovery_method="demo",
                    discovery_confidence=1.0,
                    **{k: v for k, v in device_data.items() if k not in ["capabilities"]}
                )
                session.add(device)
                devices.append(device)
            
            await session.commit()
            logger.info(f"✅ Created demo house with {len(rooms)} rooms and {len(devices)} devices")
            
            # Add devices to simulator
            for device in devices:
                simulator = self.dashboard.house_simulator.add_device(device)
                logger.info(f"   📱 Added {device.user_name} ({device.device_class}) to simulator")
    
    async def run_interactive_demo(self):
        """Run an interactive demo session."""
        logger.info("🎭 Starting Interactive Demo Session")
        
        print("\n" + "="*60)
        print("🧠 CONSCIOUSNESS SYSTEM DEMO")
        print("="*60)
        print("\nAvailable commands:")
        print("  1. status    - Show system status")
        print("  2. scenarios - List available scenarios")
        print("  3. run <scenario> - Run a demo scenario")
        print("  4. query <question> - Ask the consciousness system")
        print("  5. devices   - Show device status")
        print("  6. dashboard - Start web dashboard")
        print("  7. quit      - Exit demo")
        print("\nScenario options:")
        for name, description in [
            ("smart_morning", "Smart Morning Routine"),
            ("security_alert", "Security Alert Simulation"),
            ("energy_optimization", "Energy Optimization"),
            ("party_mode", "Party Mode Entertainment"),
            ("vacation_mode", "Vacation Security & Savings")
        ]:
            print(f"  - {name}: {description}")
        
        while True:
            try:
                command = input("\n🤖 Enter command: ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "status":
                    await self._show_status()
                elif command == "scenarios":
                    await self._list_scenarios()
                elif command.startswith("run "):
                    scenario = command[4:].strip()
                    await self._run_scenario(scenario)
                elif command.startswith("query "):
                    question = command[6:].strip()
                    await self._query_consciousness(question)
                elif command == "devices":
                    await self._show_devices()
                elif command == "dashboard":
                    await self._start_dashboard()
                else:
                    print("❓ Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in demo: {e}")
                print(f"❌ Error: {e}")
        
        print("\n👋 Demo session ended")
    
    async def _show_status(self):
        """Show consciousness system status."""
        print("\n📊 SYSTEM STATUS")
        print("-" * 40)
        
        try:
            status = await self.consciousness.get_status()
            print(f"Emotional State: {status.get('emotional_state', 'unknown')}")
            print(f"Mood: {status.get('mood', 'stable')}")
            print(f"Active Concerns: {', '.join(status.get('active_concerns', [])) or 'None'}")
            print(f"Last Activity: {status.get('last_activity', 'Never')}")
        except Exception as e:
            print(f"❌ Could not get status: {e}")
        
        device_count = len(self.house_simulator.devices)
        active_count = sum(1 for sim in self.house_simulator.devices.values() if sim.running)
        print(f"Devices: {active_count}/{device_count} active")
        print(f"Current Scenario: {self.house_simulator.current_scenario or 'None'}")
    
    async def _list_scenarios(self):
        """List available demo scenarios."""
        print("\n🎭 AVAILABLE SCENARIOS")
        print("-" * 40)
        scenarios = [
            ("smart_morning", "🌅 Smart Morning Routine - Automated wake-up sequence"),
            ("security_alert", "🚨 Security Alert - Intrusion detection simulation"),
            ("energy_optimization", "⚡ Energy Optimization - Adaptive device control"),
            ("party_mode", "🎉 Party Mode - Entertainment scenario"),
            ("vacation_mode", "✈️  Vacation Mode - Security and energy saving")
        ]
        
        for name, description in scenarios:
            print(f"  {description}")
    
    async def _run_scenario(self, scenario_name: str):
        """Run a specific demo scenario."""
        if scenario_name in self.house_simulator.scenarios:
            print(f"\n🎬 Running scenario: {scenario_name}")
            print("-" * 40)
            try:
                await self.house_simulator.run_scenario(scenario_name)
                print(f"✅ Scenario '{scenario_name}' completed successfully")
            except Exception as e:
                print(f"❌ Scenario failed: {e}")
        else:
            print(f"❌ Unknown scenario: {scenario_name}")
            print("Available scenarios: smart_morning, security_alert, energy_optimization, party_mode, vacation_mode")
    
    async def _query_consciousness(self, question: str):
        """Query the consciousness system."""
        print(f"\n🤔 Asking: {question}")
        print("-" * 40)
        try:
            response = await self.consciousness.process_query(question)
            print(f"🧠 Response: {response}")
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    async def _show_devices(self):
        """Show device status."""
        print("\n📱 DEVICE STATUS")
        print("-" * 40)
        
        if not self.house_simulator.devices:
            print("No devices found")
            return
        
        for device_id, simulator in self.house_simulator.devices.items():
            device = simulator.device
            status_icon = "🟢" if simulator.running else "🔴"
            print(f"{status_icon} {device.user_name} ({device.device_class})")
            print(f"   Location: {device.location}")
            print(f"   State: {simulator.state}")
            print()
    
    async def _start_dashboard(self):
        """Start the web dashboard."""
        print("\n🌐 Starting Web Dashboard...")
        print("-" * 40)
        print("Dashboard will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop the dashboard and return to demo")
        
        try:
            import uvicorn
            config = uvicorn.Config(
                app=self.dashboard.app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        except KeyboardInterrupt:
            print("\n📱 Dashboard stopped")
        except ImportError:
            print("❌ uvicorn not installed. Install with: pip install uvicorn")
        except Exception as e:
            print(f"❌ Dashboard failed to start: {e}")


async def main():
    """Main demo entry point."""
    runner = DemoRunner()
    
    try:
        await runner.initialize()
        await runner.run_interactive_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
    finally:
        # Cleanup
        if runner.house_simulator:
            await runner.house_simulator.stop()
        print("🧹 Cleanup completed")


if __name__ == "__main__":
    print("🚀 Consciousness System Demo")
    print("Setting up the AI-powered home automation demonstration...")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)