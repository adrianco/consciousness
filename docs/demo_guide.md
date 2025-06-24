# Demo & Test System Guide

## Overview

The Consciousness Demo & Test System provides comprehensive demonstration scenarios and test suites for the AI-powered home automation system. It includes device simulators, realistic scenarios, a web dashboard, and extensive test coverage.

## 🎯 Components

### 1. Device Simulator (`consciousness/simulators/device_simulator.py`)

Simulates realistic IoT device behaviors including:

- **Climate Devices**: Temperature control, humidity management, HVAC systems
- **Lighting**: Smart bulbs, dimmers, color control, brightness adjustment
- **Sensors**: Motion detection, door/window sensors, environmental monitoring
- **Security**: Alarm systems, cameras, intrusion detection
- **Energy**: Solar panels, battery systems, power monitoring

#### Device Simulator Features:
- Realistic state transitions
- Configurable simulation speed
- Event-driven callbacks
- Async/await support
- Error simulation capabilities

### 2. Demo Scenarios (`consciousness/simulators/demo_scenarios.py`)

Five comprehensive demonstration scenarios:

#### 🌅 Smart Morning Routine
- **Phase 1**: Gentle wake-up with gradual lighting
- **Phase 2**: Full wake-up sequence with security disarming
- **Phase 3**: Morning activity preparation with climate optimization

#### 🚨 Security Alert
- **Phase 1**: Security system arming
- **Phase 2**: Intrusion detection and motion triggering
- **Phase 3**: Automated response with lighting deterrents

#### ⚡ Energy Optimization
- **Phase 1**: Morning energy conservation
- **Phase 2**: Solar production maximization
- **Phase 3**: Peak demand avoidance

#### 🎉 Party Mode
- **Phase 1**: Atmosphere setup with security adjustment
- **Phase 2**: Dynamic lighting effects
- **Phase 3**: Crowd comfort monitoring

#### ✈️ Vacation Mode
- **Phase 1**: House security and energy saving
- **Phase 2**: Presence simulation over multiple days
- **Phase 3**: Energy savings reporting

### 3. Web Dashboard (`consciousness/interfaces/demo_dashboard.py`)

Real-time visualization dashboard featuring:

- **Consciousness Status**: Emotional state, mood, concerns
- **System Overview**: Device counts, active scenarios
- **Scenario Controls**: One-click scenario launching
- **Device Grid**: Real-time device state monitoring
- **Event Log**: Live system activity feed
- **WebSocket Integration**: Real-time updates

### 4. Test Suites (`tests/test_demo_system.py`)

Comprehensive test coverage including:

#### Device Simulator Tests:
- State initialization verification
- Lifecycle management
- Callback triggering
- Async behavior validation

#### House Simulator Tests:
- Device orchestration
- Scenario execution
- Performance under load
- Error handling

#### Integration Tests:
- Digital twin synchronization
- Sensor reading generation
- Complete demo workflow
- Performance benchmarking

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/migrate.py

# Install web dashboard dependencies (optional)
pip install uvicorn
```

### 2. Running the Demo

```bash
# Start interactive demo
python scripts/run_demo.py
```

### 3. Available Commands

In the interactive demo:

- `status` - Show system status
- `scenarios` - List available scenarios  
- `run <scenario>` - Execute a scenario
- `query <question>` - Ask the consciousness system
- `devices` - Show device status
- `dashboard` - Start web dashboard
- `quit` - Exit demo

### 4. Web Dashboard

Access the dashboard at `http://localhost:8000` when running the dashboard command.

## 🎭 Demo Scenarios

### Smart Morning Routine

```bash
# In demo shell
run smart_morning
```

**What it demonstrates:**
- Gradual lighting adjustment (10% → 50% → 100%)
- Climate pre-conditioning
- Security system disarming
- Motion-triggered responses
- Energy-aware operation

**Timeline:**
- 6:30 AM: Gentle wake-up (dim lights, warming start)
- 6:35 AM: Full wake-up (brighter lights, kitchen activation)
- 6:38 AM: Activity preparation (motion detection, full brightness)

### Security Alert Simulation

```bash
run security_alert
```

**What it demonstrates:**
- Security system arming
- Motion and door sensor triggering
- Automated deterrent responses
- Alert generation and logging
- Coordinated device responses

**Sequence:**
1. Arm security system
2. Trigger door sensor
3. Activate motion detection
4. Flash lights as deterrent
5. Log security event

### Energy Optimization

```bash
run energy_optimization
```

**What it demonstrates:**
- Peak demand management
- Solar production utilization
- Battery optimization
- Smart device scheduling
- Cost-aware operation

**Phases:**
- Morning: Reduce non-essential loads
- Midday: Maximize solar utilization
- Evening: Battery power, peak avoidance

### Party Mode

```bash
run party_mode
```

**What it demonstrates:**
- Synchronized lighting effects
- Climate adjustment for crowds
- Color-changing light sequences
- Enhanced monitoring mode
- Entertainment system integration

### Vacation Mode

```bash
run vacation_mode
```

**What it demonstrates:**
- Enhanced security settings
- Minimal energy consumption
- Presence simulation patterns
- Multi-day scheduling
- Savings calculations

## 🧪 Testing

### Running Tests

```bash
# Run all demo tests
pytest tests/test_demo_system.py -v

# Run specific test categories
pytest tests/test_demo_system.py::TestDeviceSimulator -v
pytest tests/test_demo_system.py::TestDemoScenarios -v

# Run with coverage
pytest tests/test_demo_system.py --cov=consciousness.simulators
```

### Test Categories

#### Unit Tests (70% of coverage)
- Device simulator behavior
- State management
- Callback mechanisms
- Error handling

#### Integration Tests (25% of coverage)
- Multi-device coordination
- Scenario execution
- Dashboard integration
- Database persistence

#### End-to-End Tests (5% of coverage)
- Complete workflow validation
- Performance benchmarking
- Real-time updates
- Error recovery

### Performance Testing

```bash
# Test with 100 simulated devices
pytest tests/test_demo_system.py::TestSystemIntegration::test_performance_under_load -v

# Memory usage analysis
python -m memory_profiler scripts/run_demo.py
```

## 🔧 Configuration

### Simulation Speed

Adjust simulation speed in device simulators:

```python
simulator.simulation_speed = 2.0  # 2x real-time
simulator.simulation_speed = 0.5  # Half real-time
```

### Device Capabilities

Configure device capabilities:

```python
device.capabilities = {
    "sensor_type": "motion",
    "detection_range": 10,  # meters
    "sensitivity": 0.8
}
```

### Scenario Customization

Create custom scenarios:

```python
@staticmethod
async def custom_scenario(simulator: "HouseSimulator"):
    """Custom demonstration scenario."""
    lights = simulator.get_device_by_class("light")
    for light in lights:
        await light.set_state({"is_on": True, "brightness": 50})
```

## 📊 Monitoring & Metrics

### Real-time Monitoring

The dashboard provides:

- **Device Status**: Live state updates
- **System Health**: Performance metrics
- **Scenario Progress**: Execution tracking
- **Event Timeline**: Activity logging

### Performance Metrics

Key metrics tracked:

- **Response Time**: Device command execution
- **Throughput**: Messages per second
- **Memory Usage**: System resource consumption
- **Error Rate**: Failed operations percentage

### Logging

Configure logging levels:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Specific component logging
logging.getLogger('consciousness.simulators').setLevel(logging.DEBUG)
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Reset database
python scripts/migrate.py --reset

# Check database status
python scripts/migrate.py --status
```

#### 2. Device Simulation Not Starting
```python
# Check device initialization
await simulator._initialize_state()
print(f"Device state: {simulator.state}")
```

#### 3. WebSocket Connection Issues
- Ensure port 8000 is available
- Check firewall settings
- Verify uvicorn installation

#### 4. Scenario Execution Failures
```python
# Enable debug logging
logging.getLogger('consciousness.simulators.demo_scenarios').setLevel(logging.DEBUG)
```

### Debug Commands

```bash
# Verbose test output
pytest tests/test_demo_system.py -v -s

# Debug device states
python -c "from consciousness.simulators.device_simulator import DeviceSimulator; print('Debug info')"

# Check database schema
python scripts/migrate.py --schema
```

## 🎨 Customization

### Adding New Device Types

1. Extend DeviceSimulator:

```python
async def _simulate_custom_device(self):
    """Simulate custom device behavior."""
    while self.running:
        # Custom simulation logic
        await asyncio.sleep(60)
```

2. Add device class mapping:

```python
if self.device.device_class == "custom":
    await self._simulate_custom_device()
```

### Creating New Scenarios

1. Add scenario method to DemoScenarios:

```python
@staticmethod
async def my_custom_scenario(simulator: "HouseSimulator"):
    """Custom scenario description."""
    # Scenario implementation
    pass
```

2. Register scenario:

```python
simulator.scenarios["my_custom"] = DemoScenarios.my_custom_scenario
```

### Dashboard Customization

Modify the HTML template in `demo_dashboard.py`:

```html
<!-- Add custom dashboard sections -->
<div class="custom-section">
    <h3>Custom Metrics</h3>
    <div id="customMetrics"></div>
</div>
```

## 🔍 API Reference

### Device Simulator API

```python
class DeviceSimulator:
    async def start()                          # Start simulation
    async def stop()                           # Stop simulation
    async def set_state(state: Dict)           # Update device state
    def on(event: str, callback: Callable)     # Register callback
```

### House Simulator API

```python
class HouseSimulator:
    def add_device(device: Device) -> DeviceSimulator
    async def run_scenario(scenario_name: str)
    def get_device_by_class(device_class: str) -> List[DeviceSimulator]
    def get_device_by_location(location: str) -> List[DeviceSimulator]
```

### Dashboard API Endpoints

- `GET /` - Dashboard HTML
- `GET /api/status` - System status
- `GET /api/devices` - Device list
- `POST /api/scenarios/{name}/run` - Run scenario
- `POST /api/scenarios/stop` - Stop scenarios
- `WebSocket /ws` - Real-time updates

## 📈 Performance Optimization

### Simulation Performance

```python
# Optimize update frequency
simulator.simulation_speed = 5.0  # 5x speed for testing

# Batch device updates
await asyncio.gather(*[device.update() for device in devices])
```

### Memory Management

```python
# Limit event history
max_events = 1000
if len(event_log) > max_events:
    event_log = event_log[-max_events:]
```

### Database Optimization

```python
# Use async sessions
async with get_async_session() as session:
    # Batch database operations
    await session.execute(bulk_insert_mappings(...))
```

## 🎯 Best Practices

### 1. Device Simulation
- Keep state transitions realistic
- Implement proper error handling
- Use appropriate timing intervals
- Test edge cases

### 2. Scenario Design
- Break complex scenarios into phases
- Provide clear progress indicators
- Handle device failures gracefully
- Document expected outcomes

### 3. Testing Strategy
- Test individual components first
- Use mocks for external dependencies
- Validate realistic scenarios
- Monitor performance metrics

### 4. Dashboard Usage
- Use real-time updates judiciously
- Implement proper error boundaries
- Provide clear user feedback
- Optimize for mobile devices

## 📚 Additional Resources

- [Consciousness Engine Guide](./consciousness-engine-guide.md)
- [API Documentation](./api-reference.md)
- [Testing Best Practices](./testing-guide.md)
- [Deployment Guide](./deployment.md)

## 🤝 Contributing

To contribute to the demo system:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Document public methods
- Write comprehensive tests

## 📝 Changelog

### v1.0.0
- Initial demo system implementation
- Five core scenarios
- Web dashboard
- Comprehensive test suite
- Performance optimization

### v1.1.0 (Planned)
- Additional device types
- Custom scenario builder
- Advanced analytics
- Mobile dashboard optimization

---

*This guide provides comprehensive documentation for the Consciousness Demo & Test System. For questions or issues, please refer to the project's GitHub repository.*