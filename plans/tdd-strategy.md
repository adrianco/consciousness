# TDD Strategy for Consciousness Framework

## Executive Summary

This document defines a comprehensive Test-Driven Development (TDD) strategy for the consciousness framework, focusing on testability of SAFLA (Self Aware Feedback Loop Algorithm) components, STPA control loops, and emotional state management systems.

## Test Architecture Overview

### Test Pyramid for SAFLA Components

```
    /\
   /  \  E2E Tests (5%)
  /____\ - Full consciousness scenarios
 /      \ - Human-system conversations 
/__UI___\ - Emotional state transitions

/________\ Integration Tests (25%)
           - SAFLA loop integration
           - Device API integration  
           - SQLite persistence layer
           - STPA control flow testing

/__________\ Unit Tests (70%)
             - Individual component logic
             - State management functions
             - Query processing algorithms
             - Emotional state calculations
```

## Test Categories & Structure

### 1. Unit Tests (70% of test suite)

#### 1.1 Consciousness Model Components
- **State Management**
  - Emotional state calculations (happy, worried, bored, excited)
  - State persistence and retrieval
  - State transition validations
  - Memory accumulation over time

- **Query Processing**
  - Natural language query parsing
  - Intent classification
  - Response generation
  - Context awareness

- **Device Interface Logic**
  - API abstraction layers
  - Data normalization
  - Error handling
  - Credential management

#### 1.2 SAFLA Loop Components
- **Observability Layer**
  - Sensor data collection
  - Data validation and sanitization
  - Metric aggregation
  - Threshold detection

- **Control Layer**
  - Action execution
  - Safety constraint validation
  - Rollback mechanisms
  - Command queuing

### 2. Integration Tests (25% of test suite)

#### 2.1 SAFLA Integration
- Complete observability → consciousness → controllability loops
- Multi-device coordination scenarios
- Database transaction consistency
- Event-driven architecture validation

#### 2.2 STPA Control Flow Testing
- Three-layer control validation:
  - Business function layer
  - Control system layer  
  - Human operator layer
- Failure cascade prevention
- Safety constraint enforcement

#### 2.3 Database Integration
- SQLite schema validation
- CRUD operations for all entities
- Performance under load
- Backup and recovery scenarios

### 3. System/E2E Tests (5% of test suite)

#### 3.1 Consciousness Scenarios
- Full conversation workflows
- Complex emotional state transitions
- Multi-device orchestration
- Real-time response validation

#### 3.2 Failure Mode Testing
- FMEA scenario validation
- Graceful degradation
- Recovery procedures
- Alert escalation

## Test Naming Conventions

### Unit Tests
```
test_[component]_[action]_[expected_outcome]()
test_[component]_[action]_when_[condition]_then_[outcome]()

Examples:
test_emotional_state_calculate_happiness_when_all_systems_ok()
test_query_processor_parse_intent_when_asking_about_temperature()
test_device_interface_authenticate_when_credentials_invalid_then_raise_error()
```

### Integration Tests
```
test_integration_[system1]_[system2]_[scenario]()
test_safla_loop_[component]_to_[component]_[scenario]()

Examples:
test_integration_observability_consciousness_temperature_alert()
test_safla_loop_sensor_to_action_hvac_adjustment()
test_stpa_business_to_control_safety_constraint_violation()
```

### E2E Tests
```
test_e2e_[user_story]_[scenario]()
test_conversation_[topic]_[expected_behavior]()

Examples:
test_e2e_morning_routine_blind_and_light_automation()
test_conversation_weather_concern_when_storm_approaching()
test_e2e_energy_management_guest_arrival_scenario()
```

## Test Data Strategies for SQLite

### 1. Test Database Management
```python
# Separate test database per test run
TEST_DB_PATH = ":memory:"  # In-memory for unit tests
TEST_DB_FILE = "test_consciousness.db"  # File-based for integration tests

@pytest.fixture(scope="function")
def test_db():
    """Fresh database for each test"""
    db = sqlite3.connect(":memory:")
    setup_schema(db)
    yield db
    db.close()

@pytest.fixture(scope="session")  
def integration_db():
    """Persistent database for integration tests"""
    db_path = f"test_integration_{uuid4()}.db"
    db = sqlite3.connect(db_path)
    setup_schema(db)
    yield db
    db.close()
    os.unlink(db_path)
```

### 2. Test Data Builders
```python
class DeviceDataBuilder:
    def with_temperature_sensor(self, location="living_room"):
        return self
    
    def with_hvac_system(self, zones=["main", "guest"]):
        return self
        
    def build(self):
        return device_data

class EmotionalStateBuilder:
    def happy(self, level=0.8):
        return self
        
    def worried(self, about="weather", level=0.6):
        return self
        
    def build(self):
        return emotional_state
```

### 3. Fixture Data Management
```python
# fixtures/consciousness_scenarios.json
{
  "morning_routine": {
    "time": "07:00",
    "devices": {...},
    "expected_actions": [...],
    "expected_queries": [...]
  },
  "storm_preparation": {
    "weather_forecast": {...},
    "device_states": {...},
    "expected_emotions": "worried",
    "expected_actions": [...]
  }
}
```

## Mock Strategies for SAFLA Components

### 1. Device Interface Mocking
```python
class MockDeviceInterface:
    """Mock for external device APIs"""
    
    def __init__(self):
        self.call_history = []
        self.responses = {}
        
    def setup_response(self, device_id, action, response):
        self.responses[(device_id, action)] = response
        
    def execute_action(self, device_id, action, params):
        self.call_history.append((device_id, action, params))
        return self.responses.get((device_id, action), {"success": True})

@pytest.fixture
def mock_homekit():
    return MockDeviceInterface()

@pytest.fixture
def mock_weather_api():
    mock = MockDeviceInterface()
    mock.setup_response("weather", "current", {
        "temperature": 72,
        "conditions": "sunny",
        "forecast": "rain_later"
    })
    return mock
```

### 2. Time and Environment Mocking
```python
@pytest.fixture
def mock_datetime():
    with patch('consciousness.utils.datetime') as mock:
        mock.now.return_value = datetime(2024, 6, 15, 7, 0, 0)  # Morning
        yield mock

@pytest.fixture
def mock_environmental_conditions():
    return {
        "external_temperature": 75,
        "humidity": 60,
        "wind_speed": 5,
        "forecast": "sunny"
    }
```

### 3. SAFLA Loop Component Mocking
```python
class MockObservabilityLayer:
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        
    def add_metric(self, name, value, timestamp=None):
        self.metrics[name] = value
        
    def get_current_state(self):
        return {"metrics": self.metrics, "alerts": self.alerts}

class MockConsciousnessModel:
    def __init__(self):
        self.emotional_state = "neutral"
        self.queries = []
        
    def process_observations(self, observations):
        # Mock consciousness processing
        pass
        
    def query(self, question):
        self.queries.append(question)
        return f"Mock response to: {question}"
```

## Database Testing Patterns

### 1. Schema Validation Tests
```python
def test_database_schema_creation():
    """Ensure all required tables and indexes exist"""
    db = sqlite3.connect(":memory:")
    setup_schema(db)
    
    # Verify tables exist
    tables = get_table_names(db)
    assert "devices" in tables
    assert "emotional_states" in tables
    assert "conversations" in tables
    assert "system_events" in tables
    
    # Verify indexes for performance
    indexes = get_index_names(db)
    assert "idx_emotional_states_timestamp" in indexes
    assert "idx_conversations_timestamp" in indexes

def test_database_constraints():
    """Test foreign key and check constraints"""
    db = sqlite3.connect(":memory:")
    setup_schema(db)
    
    # Test foreign key constraints
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("""
            INSERT INTO device_actions (device_id, action)
            VALUES ('nonexistent_device', 'turn_on')
        """)
```

### 2. Performance Testing
```python
def test_query_performance():
    """Ensure queries perform within acceptable limits"""
    db = create_test_db_with_sample_data(1000)  # 1000 records
    
    start_time = time.time()
    result = db.execute("""
        SELECT * FROM emotional_states 
        WHERE timestamp > ? 
        ORDER BY timestamp DESC 
        LIMIT 10
    """, (datetime.now() - timedelta(hours=24),))
    query_time = time.time() - start_time
    
    assert query_time < 0.1  # Should complete in under 100ms
    assert len(result.fetchall()) <= 10
```

### 3. Migration Testing
```python
def test_database_migration():
    """Test schema migrations work correctly"""
    # Create old schema
    db = sqlite3.connect(":memory:")
    create_schema_v1(db)
    insert_sample_data_v1(db)
    
    # Apply migration
    migrate_to_v2(db)
    
    # Verify data integrity
    assert get_schema_version(db) == 2
    assert count_records(db, "devices") > 0  # Data preserved
    assert column_exists(db, "devices", "new_column")  # New schema applied
```

## Coverage Requirements

### Minimum Coverage Targets
- **Unit Tests**: 90% line coverage, 85% branch coverage
- **Integration Tests**: 80% of critical paths covered
- **E2E Tests**: 100% of user-facing workflows covered

### Critical Components (95% coverage required)
- Safety constraint validation
- Emotional state calculations
- Device action execution
- Database transaction handling
- Query processing pipeline

### Coverage Exclusions
- Third-party library integrations (mocked)
- Configuration file parsing
- Logging statements
- Development/debug code paths

## TDD Workflow Documentation

### Red-Green-Refactor Cycle for Consciousness Components

#### Phase 1: Red (Write Failing Test)
```python
def test_consciousness_responds_to_temperature_query():
    """Test that consciousness can answer temperature questions"""
    # Arrange
    consciousness = ConsciousnessModel()
    mock_sensors = {"living_room_temp": 72, "outside_temp": 85}
    consciousness.update_observations(mock_sensors)
    
    # Act
    response = consciousness.query("What's the temperature inside?")
    
    # Assert
    assert "72" in response
    assert "living room" in response.lower()
```

#### Phase 2: Green (Make Test Pass)
```python
class ConsciousnessModel:
    def __init__(self):
        self.observations = {}
        
    def update_observations(self, sensor_data):
        self.observations.update(sensor_data)
        
    def query(self, question):
        if "temperature" in question.lower() and "inside" in question.lower():
            temp = self.observations.get("living_room_temp")
            return f"The temperature in the living room is {temp} degrees."
        return "I don't understand that question."
```

#### Phase 3: Refactor (Improve Design)
```python
class ConsciousnessModel:
    def __init__(self, query_processor, sensor_manager):
        self.query_processor = query_processor
        self.sensor_manager = sensor_manager
        
    def query(self, question):
        intent = self.query_processor.parse_intent(question)
        return self.sensor_manager.handle_query(intent)
```

### TDD for SAFLA Loop Integration
```python
class TestSaflaLoop:
    def test_observability_to_consciousness_flow(self):
        """Test complete flow from observation to consciousness update"""
        # Red: Write test for behavior that doesn't exist yet
        safla = SaflaLoop()
        
        # Simulate device observations
        observations = {
            "hvac_status": "cooling",
            "target_temp": 72,
            "actual_temp": 78,
            "efficiency": 0.7
        }
        
        safla.process_observations(observations)
        
        # Consciousness should detect inefficiency and become concerned
        emotional_state = safla.get_emotional_state()
        assert emotional_state["primary"] == "concerned"
        assert "hvac" in emotional_state["concerns"]
        
        # Green: Implement minimal code to pass
        # Refactor: Extract concerns, improve efficiency detection
```

### TDD for Database Interactions
```python
def test_emotional_state_persistence():
    """Test that emotional states are correctly saved and retrieved"""
    # Red: Write test for database persistence
    db = create_test_db()
    state_manager = EmotionalStateManager(db)
    
    initial_state = EmotionalState(
        primary="happy",
        level=0.8,
        timestamp=datetime.now(),
        context={"reason": "all_systems_optimal"}
    )
    
    # Save state
    state_id = state_manager.save_state(initial_state)
    
    # Retrieve and verify
    retrieved_state = state_manager.get_state(state_id)
    assert retrieved_state.primary == "happy"
    assert retrieved_state.level == 0.8
    assert retrieved_state.context["reason"] == "all_systems_optimal"
```

## CI/CD Integration Approach

### 1. Test Pipeline Structure
```yaml
# .github/workflows/consciousness-tests.yml
name: Consciousness Framework Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ --cov=consciousness --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - name: Run integration tests
        run: |
          pytest tests/integration/ --timeout=300
      - name: Test database migrations
        run: |
          python scripts/test_migrations.py

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - name: Setup test environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
      - name: Run E2E tests
        run: |
          pytest tests/e2e/ --timeout=600
      - name: Cleanup
        run: |
          docker-compose -f docker-compose.test.yml down
```

### 2. Quality Gates
- **Unit tests must pass** with >90% coverage
- **Integration tests must pass** within 5 minutes
- **E2E tests must pass** within 10 minutes
- **No security vulnerabilities** in dependencies
- **Code quality checks** (flake8, mypy, black)

### 3. Test Data Management in CI
```python
# conftest.py for CI environment
@pytest.fixture(scope="session")
def ci_test_db():
    """Database fixture optimized for CI environment"""
    if os.getenv("CI"):
        # Use faster in-memory database for CI
        db_path = ":memory:"
    else:
        # Use file-based database for local development
        db_path = "test_local.db"
    
    db = sqlite3.connect(db_path)
    setup_schema(db)
    seed_test_data(db)
    yield db
    db.close()
```

### 4. Parallel Test Execution
```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=consciousness
    --cov-branch
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --numprocesses=auto  # Run tests in parallel
    --timeout=60  # Timeout individual tests after 60s
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take more than 1 second
    database: Tests that require database
```

## Mock Strategies for Complex Scenarios

### 1. Weather and Environmental Mocking
```python
class WeatherScenarioMock:
    """Mock complex weather scenarios for testing"""
    
    SCENARIOS = {
        "approaching_storm": {
            "current": {"condition": "cloudy", "wind": 15, "pressure": 29.8},
            "forecast": {"condition": "thunderstorm", "wind": 35, "arrival": "2 hours"},
            "expected_emotion": "worried",
            "expected_actions": ["secure_outdoor_furniture", "close_windows"]
        },
        "heat_wave": {
            "current": {"temperature": 105, "humidity": 85, "air_quality": "poor"},
            "forecast": {"temperature": [106, 107, 104], "duration": "3 days"}, 
            "expected_emotion": "concerned",
            "expected_actions": ["increase_cooling", "close_blinds", "air_quality_alert"]
        }
    }
    
    def setup_scenario(self, scenario_name):
        scenario = self.SCENARIOS[scenario_name]
        # Setup mock APIs to return scenario data
        return scenario
```

### 2. Device Coordination Mocking
```python
class DeviceOrchestrationMock:
    """Mock complex multi-device scenarios"""
    
    def __init__(self):
        self.devices = {}
        self.action_sequence = []
        
    def add_device(self, device_id, device_type, capabilities):
        self.devices[device_id] = {
            "type": device_type,
            "capabilities": capabilities,
            "state": {},
            "responsive": True
        }
        
    def simulate_device_failure(self, device_id):
        self.devices[device_id]["responsive"] = False
        
    def execute_action(self, device_id, action, params):
        self.action_sequence.append((device_id, action, params))
        if not self.devices[device_id]["responsive"]:
            raise DeviceUnresponsiveError(f"Device {device_id} not responding")
        return {"success": True, "new_state": params}
```

### 3. Conversation Context Mocking
```python
class ConversationContextMock:
    """Mock conversation history and context"""
    
    def __init__(self):
        self.conversation_history = []
        self.context = {}
        
    def add_exchange(self, user_input, system_response, timestamp=None):
        self.conversation_history.append({
            "user": user_input,
            "system": system_response,
            "timestamp": timestamp or datetime.now(),
            "context": self.context.copy()
        })
        
    def set_context(self, key, value):
        self.context[key] = value
        
    def get_recent_context(self, minutes=10):
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [ex for ex in self.conversation_history if ex["timestamp"] > cutoff]
```

## Specialized Testing for Consciousness Components

### 1. Emotional State Transition Testing
```python
class TestEmotionalStateTransitions:
    """Test emotional state changes are logical and consistent"""
    
    def test_happiness_to_worry_transition(self):
        """Test transition from happy to worried state"""
        state_manager = EmotionalStateManager()
        
        # Start happy
        state_manager.set_state("happy", level=0.8, context={"all_systems": "optimal"})
        
        # Introduce concerning observation
        observations = {"hvac_efficiency": 0.3, "error_rate": 0.15}
        new_state = state_manager.process_observations(observations)
        
        # Should transition through concern to worried
        assert new_state.primary in ["concerned", "worried"]
        assert new_state.level < 0.8  # Reduced happiness
        assert "hvac" in str(new_state.context).lower()
        
    def test_emotional_state_persistence(self):
        """Test that emotional states persist appropriately"""
        state_manager = EmotionalStateManager()
        
        # Worry should persist until resolved
        state_manager.set_state("worried", level=0.7, context={"storm_approaching": True})
        
        # Normal observations shouldn't immediately clear worry
        normal_observations = {"temperature": 72, "humidity": 45}
        state = state_manager.process_observations(normal_observations)
        assert state.primary == "worried"  # Still worried about storm
        
        # Storm resolution should clear worry
        resolution_observations = {"storm_passed": True, "no_damage": True}
        state = state_manager.process_observations(resolution_observations)
        assert state.primary in ["relieved", "happy"]
```

### 2. Query Understanding Testing
```python
class TestQueryProcessing:
    """Test natural language query processing"""
    
    @pytest.mark.parametrize("query,expected_intent", [
        ("How are you feeling?", "emotional_state_query"),
        ("What's wrong?", "problem_identification"),
        ("Why did you turn on the AC?", "action_explanation"),
        ("Is everything okay?", "system_status_query"),
        ("What's the temperature?", "sensor_data_query"),
    ])
    def test_intent_classification(self, query, expected_intent):
        processor = QueryProcessor()
        intent = processor.classify_intent(query)
        assert intent == expected_intent
        
    def test_context_aware_responses(self):
        """Test responses consider conversation context"""
        processor = QueryProcessor()
        context = ConversationContext()
        
        # First question establishes context
        context.add_exchange("What's the temperature?", "It's 72 degrees inside.")
        
        # Follow-up should understand "it" refers to temperature
        response = processor.process_query("Is it too warm?", context)
        assert "72" in response or "temperature" in response.lower()
```

### 3. SAFLA Loop Integration Testing
```python
class TestSaflaIntegration:
    """Test complete SAFLA loop integration"""
    
    def test_complete_consciousness_loop(self):
        """Test full observability -> consciousness -> control loop"""
        # Setup
        safla = SaflaLoop()
        mock_devices = MockDeviceOrchestrator()
        
        # Observability: High temperature detected
        observations = {
            "living_room_temp": 78,
            "target_temp": 72,
            "hvac_running": False,
            "outside_temp": 85
        }
        
        # Process through consciousness
        safla.process_observations(observations)
        
        # Verify consciousness state
        state = safla.get_consciousness_state()
        assert state["awareness"]["temperature_differential"] > 5
        assert state["emotional_state"]["primary"] in ["concerned", "active"]
        
        # Verify control action taken
        actions = mock_devices.get_executed_actions()
        assert any(action["device"] == "hvac" and action["command"] == "cool" 
                  for action in actions)
        
        # Verify feedback loop
        # Simulate temperature dropping after AC starts
        new_observations = {**observations, "hvac_running": True, "living_room_temp": 75}
        safla.process_observations(new_observations)
        
        new_state = safla.get_consciousness_state()
        assert new_state["emotional_state"]["primary"] in ["satisfied", "happy"]
```

## Test Strategy Summary

This TDD strategy provides comprehensive coverage for the consciousness framework by:

1. **Emphasizing testability** of SAFLA components through clear separation of concerns
2. **Providing realistic mock strategies** for complex IoT device interactions
3. **Ensuring database integrity** through comprehensive SQLite testing patterns
4. **Supporting continuous development** with fast, reliable test execution
5. **Maintaining high quality** through rigorous coverage requirements and CI/CD integration

The strategy balances thorough testing with practical development velocity, ensuring the consciousness framework can be developed with confidence while maintaining the flexibility to evolve as new requirements emerge.

---

*This TDD strategy document should be reviewed and updated as the consciousness framework architecture evolves and new testing patterns emerge from implementation experience.*