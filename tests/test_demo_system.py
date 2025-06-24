"""Comprehensive test suite for the demo and simulation system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

from consciousness.models.entities import Device, House, Room
from consciousness.simulators.device_simulator import DeviceSimulator, HouseSimulator
from consciousness.simulators.demo_scenarios import DemoScenarios, register_scenarios


class TestDeviceSimulator:
    """Test suite for individual device simulators."""
    
    @pytest.fixture
    def mock_device(self):
        """Create a mock device for testing."""
        device = Mock(spec=Device)
        device.id = 1
        device.device_class = "climate"
        device.location = "living_room"
        device.capabilities = {}
        return device
    
    @pytest.fixture
    def light_device(self):
        """Create a mock light device."""
        device = Mock(spec=Device)
        device.id = 2
        device.device_class = "light"
        device.location = "bedroom"
        device.capabilities = {}
        return device
    
    @pytest.fixture
    def sensor_device(self):
        """Create a mock sensor device."""
        device = Mock(spec=Device)
        device.id = 3
        device.device_class = "sensor"
        device.location = "hallway"
        device.capabilities = {"sensor_type": "motion"}
        return device
    
    def test_device_simulator_initialization(self, mock_device):
        """Test device simulator initialization."""
        simulator = DeviceSimulator(mock_device)
        
        assert simulator.device == mock_device
        assert not simulator.running
        assert simulator.state == {}
        assert simulator.callbacks == {}
        assert simulator.simulation_speed == 1.0
    
    @pytest.mark.asyncio
    async def test_climate_device_initialization(self, mock_device):
        """Test climate device state initialization."""
        simulator = DeviceSimulator(mock_device)
        await simulator._initialize_state()
        
        assert "temperature" in simulator.state
        assert "target_temperature" in simulator.state
        assert "humidity" in simulator.state
        assert simulator.state["mode"] == "auto"
        assert simulator.state["is_on"] is True
    
    @pytest.mark.asyncio
    async def test_light_device_initialization(self, light_device):
        """Test light device state initialization."""
        simulator = DeviceSimulator(light_device)
        await simulator._initialize_state()
        
        assert simulator.state["is_on"] is False
        assert simulator.state["brightness"] == 100
        assert "color_temp" in simulator.state
    
    @pytest.mark.asyncio
    async def test_motion_sensor_initialization(self, sensor_device):
        """Test motion sensor state initialization."""
        simulator = DeviceSimulator(sensor_device)
        await simulator._initialize_state()
        
        assert simulator.state["motion_detected"] is False
        assert "last_motion" in simulator.state
    
    @pytest.mark.asyncio
    async def test_state_update_triggers_callback(self, mock_device):
        """Test that state updates trigger callbacks."""
        simulator = DeviceSimulator(mock_device)
        callback_called = False
        
        async def test_callback(device, data):
            nonlocal callback_called
            callback_called = True
            assert device == mock_device
            assert data == {"test": "value"}
        
        simulator.on("state_changed", test_callback)
        await simulator.set_state({"test": "value"})
        
        assert callback_called
        assert simulator.state["test"] == "value"
    
    @pytest.mark.asyncio
    async def test_device_simulation_lifecycle(self, mock_device):
        """Test device simulation start/stop lifecycle."""
        simulator = DeviceSimulator(mock_device)
        
        # Mock the climate simulation method to avoid infinite loop
        simulator._simulate_climate_device = AsyncMock()
        
        start_task = asyncio.create_task(simulator.start())
        await asyncio.sleep(0.1)  # Let initialization happen
        
        assert simulator.running
        simulator._simulate_climate_device.assert_called_once()
        
        await simulator.stop()
        assert not simulator.running
        
        start_task.cancel()
        try:
            await start_task
        except asyncio.CancelledError:
            pass


class TestHouseSimulator:
    """Test suite for house-wide simulation orchestration."""
    
    @pytest.fixture
    def house_simulator(self):
        """Create a house simulator for testing."""
        return HouseSimulator()
    
    @pytest.fixture
    def sample_devices(self):
        """Create sample devices for testing."""
        devices = []
        
        # Climate device
        climate = Mock(spec=Device)
        climate.id = 1
        climate.device_class = "climate"
        climate.location = "living_room"
        climate.capabilities = {}
        devices.append(climate)
        
        # Light device
        light = Mock(spec=Device)
        light.id = 2
        light.device_class = "light"
        light.location = "bedroom"
        light.capabilities = {}
        devices.append(light)
        
        # Motion sensor
        sensor = Mock(spec=Device)
        sensor.id = 3
        sensor.device_class = "sensor"
        sensor.location = "hallway"
        sensor.capabilities = {"sensor_type": "motion"}
        devices.append(sensor)
        
        return devices
    
    def test_house_simulator_initialization(self, house_simulator):
        """Test house simulator initialization."""
        assert house_simulator.devices == {}
        assert not house_simulator.running
        assert house_simulator.scenarios == {}
        assert house_simulator.current_scenario is None
    
    def test_add_device(self, house_simulator, sample_devices):
        """Test adding devices to house simulator."""
        device = sample_devices[0]
        simulator = house_simulator.add_device(device)
        
        assert isinstance(simulator, DeviceSimulator)
        assert house_simulator.devices[device.id] == simulator
        assert simulator.device == device
    
    def test_get_device_by_class(self, house_simulator, sample_devices):
        """Test filtering devices by class."""
        for device in sample_devices:
            house_simulator.add_device(device)
        
        climate_devices = house_simulator.get_device_by_class("climate")
        light_devices = house_simulator.get_device_by_class("light")
        sensor_devices = house_simulator.get_device_by_class("sensor")
        
        assert len(climate_devices) == 1
        assert len(light_devices) == 1
        assert len(sensor_devices) == 1
        assert climate_devices[0].device.device_class == "climate"
    
    def test_get_device_by_location(self, house_simulator, sample_devices):
        """Test filtering devices by location."""
        for device in sample_devices:
            house_simulator.add_device(device)
        
        living_room_devices = house_simulator.get_device_by_location("living_room")
        bedroom_devices = house_simulator.get_device_by_location("bedroom")
        
        assert len(living_room_devices) == 1
        assert len(bedroom_devices) == 1
        assert living_room_devices[0].device.location == "living_room"
    
    @pytest.mark.asyncio
    async def test_scenario_registration_and_execution(self, house_simulator, sample_devices):
        """Test scenario registration and execution."""
        for device in sample_devices:
            house_simulator.add_device(device)
        
        # Register scenarios
        register_scenarios(house_simulator)
        
        assert "smart_morning" in house_simulator.scenarios
        assert "security_alert" in house_simulator.scenarios
        
        # Mock scenario execution to avoid actual device simulation
        with patch.object(DemoScenarios, 'smart_morning_routine', new_callable=AsyncMock) as mock_scenario:
            await house_simulator.run_scenario("smart_morning")
            mock_scenario.assert_called_once_with(house_simulator)


class TestDemoScenarios:
    """Test suite for demonstration scenarios."""
    
    @pytest.fixture
    def mock_house_simulator(self):
        """Create a mock house simulator with sample devices."""
        simulator = Mock(spec=HouseSimulator)
        
        # Mock devices
        bedroom_light = Mock()
        bedroom_light.device.device_class = "light"
        bedroom_light.device.location = "bedroom"
        bedroom_light.state = {"is_on": False, "brightness": 100}
        bedroom_light.set_state = AsyncMock()
        
        climate_device = Mock()
        climate_device.device.device_class = "climate"
        climate_device.state = {"temperature": 70.0, "target_temperature": 72.0}
        climate_device.set_state = AsyncMock()
        
        security_device = Mock()
        security_device.device.device_class = "security"
        security_device.state = {"armed": False, "mode": "home", "alerts": []}
        security_device.set_state = AsyncMock()
        
        # Setup mock methods
        simulator.get_device_by_location.return_value = [bedroom_light]
        simulator.get_device_by_class.side_effect = lambda class_type: {
            "light": [bedroom_light],
            "climate": [climate_device],
            "security": [security_device],
            "sensor": [],
            "energy": []
        }.get(class_type, [])
        
        return simulator
    
    @pytest.mark.asyncio
    async def test_smart_morning_routine(self, mock_house_simulator):
        """Test smart morning routine scenario."""
        await DemoScenarios.smart_morning_routine(mock_house_simulator)
        
        # Verify devices were called
        mock_house_simulator.get_device_by_location.assert_called()
        mock_house_simulator.get_device_by_class.assert_called()
    
    @pytest.mark.asyncio
    async def test_security_alert_scenario(self, mock_house_simulator):
        """Test security alert scenario."""
        # Add motion sensor for this test
        motion_sensor = Mock()
        motion_sensor.device.capabilities = {"sensor_type": "motion"}
        motion_sensor.device.location = "hallway"
        motion_sensor.state = {"motion_detected": False}
        motion_sensor._trigger_callback = AsyncMock()
        
        def mock_get_device_by_class(class_type):
            if class_type == "sensor":
                return [motion_sensor]
            return mock_house_simulator.get_device_by_class(class_type)
        
        mock_house_simulator.get_device_by_class.side_effect = mock_get_device_by_class
        
        await DemoScenarios.security_alert_scenario(mock_house_simulator)
        
        # Verify security alert was triggered
        assert motion_sensor.state["motion_detected"] is True
    
    @pytest.mark.asyncio
    async def test_energy_optimization_scenario(self, mock_house_simulator):
        """Test energy optimization scenario."""
        # Add energy device
        energy_device = Mock()
        energy_device.device.device_class = "energy"
        energy_device.state = {
            "solar_production": 2.0,
            "current_power": 3.0,
            "battery_level": 50.0
        }
        energy_device.set_state = AsyncMock()
        
        def mock_get_device_by_class(class_type):
            if class_type == "energy":
                return [energy_device]
            return mock_house_simulator.get_device_by_class(class_type)
        
        mock_house_simulator.get_device_by_class.side_effect = mock_get_device_by_class
        
        await DemoScenarios.energy_optimization_scenario(mock_house_simulator)
        
        # Verify energy device was controlled
        energy_device.set_state.assert_called()
    
    @pytest.mark.asyncio
    async def test_party_mode_scenario(self, mock_house_simulator):
        """Test party mode scenario."""
        await DemoScenarios.party_mode_scenario(mock_house_simulator)
        
        # Verify devices were controlled for party mode
        mock_house_simulator.get_device_by_class.assert_called()
    
    @pytest.mark.asyncio
    async def test_vacation_mode_scenario(self, mock_house_simulator):
        """Test vacation mode scenario."""
        await DemoScenarios.vacation_mode_scenario(mock_house_simulator)
        
        # Verify security was armed
        security_devices = mock_house_simulator.get_device_by_class("security")
        if security_devices:
            security_devices[0].set_state.assert_called()


class TestSystemIntegration:
    """Integration tests for the complete demo system."""
    
    @pytest.mark.asyncio
    async def test_complete_demo_workflow(self):
        """Test complete workflow from device setup to scenario execution."""
        # Create house simulator
        house_sim = HouseSimulator()
        
        # Create test devices
        devices = []
        
        # Climate device
        climate = Mock(spec=Device)
        climate.id = 1
        climate.device_class = "climate"
        climate.location = "living_room"
        climate.capabilities = {}
        devices.append(climate)
        
        # Light device
        light = Mock(spec=Device)
        light.id = 2
        light.device_class = "light"
        light.location = "bedroom"
        light.capabilities = {}
        devices.append(light)
        
        # Add devices to simulator
        for device in devices:
            house_sim.add_device(device)
        
        # Register scenarios
        register_scenarios(house_sim)
        
        # Verify setup
        assert len(house_sim.devices) == 2
        assert len(house_sim.scenarios) == 5
        
        # Test scenario execution with mocked methods
        with patch.object(DemoScenarios, 'smart_morning_routine', new_callable=AsyncMock) as mock_scenario:
            await house_sim.run_scenario("smart_morning")
            mock_scenario.assert_called_once_with(house_sim)
    
    @pytest.mark.asyncio 
    async def test_performance_under_load(self):
        """Test system performance with many devices."""
        house_sim = HouseSimulator()
        
        # Create many devices
        for i in range(100):
            device = Mock(spec=Device)
            device.id = i
            device.device_class = ["climate", "light", "sensor"][i % 3]
            device.location = f"room_{i // 10}"
            device.capabilities = {}
            house_sim.add_device(device)
        
        assert len(house_sim.devices) == 100
        
        # Test device filtering performance
        start_time = datetime.now()
        climate_devices = house_sim.get_device_by_class("climate")
        end_time = datetime.now()
        
        assert len(climate_devices) > 30  # Should have ~33 devices
        assert (end_time - start_time).total_seconds() < 0.1  # Should be fast
    
    @pytest.mark.asyncio
    async def test_error_handling_in_scenarios(self, mock_house_simulator):
        """Test error handling during scenario execution."""
        # Mock a device that raises an exception
        faulty_device = Mock()
        faulty_device.set_state = AsyncMock(side_effect=Exception("Device error"))
        mock_house_simulator.get_device_by_class.return_value = [faulty_device]
        
        # Scenario should handle errors gracefully
        try:
            await DemoScenarios.smart_morning_routine(mock_house_simulator)
            # If we get here, the scenario handled the error
            assert True
        except Exception as e:
            # If the scenario doesn't handle errors, this test will help identify that
            pytest.fail(f"Scenario should handle device errors gracefully: {e}")
    
    def test_scenario_registration(self):
        """Test that all required scenarios are registered."""
        house_sim = HouseSimulator()
        register_scenarios(house_sim)
        
        required_scenarios = [
            "smart_morning",
            "security_alert", 
            "energy_optimization",
            "party_mode",
            "vacation_mode"
        ]
        
        for scenario in required_scenarios:
            assert scenario in house_sim.scenarios
            assert callable(house_sim.scenarios[scenario])


class TestDigitalTwinSynchronization:
    """Test digital twin state synchronization."""
    
    @pytest.mark.asyncio
    async def test_device_state_sync(self):
        """Test that device state changes are synchronized."""
        device = Mock(spec=Device)
        device.id = 1
        device.device_class = "light"
        device.location = "bedroom"
        device.capabilities = {}
        
        simulator = DeviceSimulator(device)
        await simulator._initialize_state()
        
        # Simulate state change
        new_state = {"is_on": True, "brightness": 75}
        await simulator.set_state(new_state)
        
        # Verify state is updated
        assert simulator.state["is_on"] is True
        assert simulator.state["brightness"] == 75
    
    @pytest.mark.asyncio
    async def test_sensor_reading_generation(self):
        """Test that sensor readings are generated correctly."""
        device = Mock(spec=Device)
        device.id = 1
        device.device_class = "sensor"
        device.location = "living_room"
        device.capabilities = {"sensor_type": "temperature"}
        
        simulator = DeviceSimulator(device)
        await simulator._initialize_state()
        
        # Track sensor readings
        readings = []
        
        async def capture_reading(device, data):
            readings.append(data)
        
        simulator.on("sensor_reading", capture_reading)
        
        # Simulate sensor reading
        await simulator._trigger_callback("sensor_reading", {
            "sensor_type": "temperature",
            "value": 72.5,
            "unit": "°F"
        })
        
        assert len(readings) == 1
        assert readings[0]["sensor_type"] == "temperature"
        assert readings[0]["value"] == 72.5