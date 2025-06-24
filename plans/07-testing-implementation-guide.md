# Testing Implementation Guide for Consciousness System

## Table of Contents
1. [Overview](#overview)
2. [Testing Architecture](#testing-architecture)
3. [Unit Testing](#unit-testing)
4. [Digital Twin Testing](#digital-twin-testing)
5. [Scenario Testing](#scenario-testing)
6. [Integration Testing](#integration-testing)
7. [End-to-End Testing](#end-to-end-testing)
8. [Performance Testing](#performance-testing)
9. [Security Testing](#security-testing)
10. [API Testing](#api-testing)
11. [WebSocket Testing](#websocket-testing)
12. [Test Data Management](#test-data-management)
13. [Continuous Integration](#continuous-integration)
14. [Monitoring & Reporting](#monitoring--reporting)

## Overview

This guide outlines a comprehensive testing strategy for the consciousness system, ensuring reliability, performance, and security across all components including consciousness queries, device orchestration, SAFLA loops, digital twin synchronization, scenario testing, and real-time communication.

### Testing Pyramid

```
                        ┌─────────────────────┐
                        │   E2E Tests (5%)    │
                        │ - User journeys     │
                        │ - System scenarios  │
                        └─────────────────────┘
                    ┌─────────────────────────────┐
                    │  Integration Tests (15%)    │
                    │ - API endpoints             │
                    │ - Service interactions      │
                    │ - SAFLA loops              │
                    └─────────────────────────────┘
                ┌─────────────────────────────────────┐
                │    Digital Twin Tests (10%)        │
                │ - Twin synchronization              │
                │ - Scenario validation              │
                │ - Prediction accuracy              │
                └─────────────────────────────────────┘
        ┌─────────────────────────────────────────────────┐
        │           Unit Tests (70%)                      │
        │ - Individual components                         │
        │ - Pure functions                                │
        │ - Business logic                                │
        └─────────────────────────────────────────────────┘
```

## Testing Architecture

### Test Environment Structure

```
tests/
├── unit/                   # Unit tests
│   ├── consciousness/
│   ├── devices/
│   ├── digital_twin/       # Twin component units
│   ├── interview/          # Interview system units
│   ├── discovery/          # Auto-discovery units
│   ├── safla/
│   └── utils/
├── twin/                   # Digital twin specific tests
│   ├── synchronization/    # Twin-device sync tests
│   ├── scenarios/          # Scenario simulation tests
│   ├── prediction/         # Prediction accuracy tests
│   ├── physics/            # Physics model validation
│   └── learning/           # Twin learning tests
├── integration/            # Integration tests
│   ├── api/
│   ├── interview/          # Interview flow tests
│   ├── discovery/          # Discovery integration tests
│   ├── twin_integration/   # Twin system integration
│   ├── services/
│   └── database/
├── e2e/                   # End-to-end tests
│   ├── scenarios/
│   ├── twin_workflows/     # Twin creation & management
│   └── pages/
├── performance/           # Performance tests
│   ├── load/
│   ├── stress/
│   ├── twin_simulation/    # Twin simulation performance
│   └── spike/
├── security/              # Security tests
│   ├── auth/
│   ├── twin_security/      # Twin data protection tests
│   ├── injection/
│   └── vulnerabilities/
├── fixtures/              # Test data
│   ├── devices.json
│   ├── scenarios.json
│   ├── twin_templates.json # Twin configuration templates
│   └── users.json
└── utils/                 # Test utilities
    ├── helpers.js
    ├── mocks.js
    ├── twin_factory.js     # Twin test utilities
    └── setup.js
```

### Testing Framework Stack

```javascript
// package.json - Testing dependencies
{
  "devDependencies": {
    // Unit & Integration Testing
    "jest": "^29.5.0",
    "@testing-library/jest-dom": "^5.16.5",
    "supertest": "^6.3.3",
    
    // E2E Testing
    "playwright": "^1.36.0",
    "cypress": "^12.17.0",
    
    // Performance Testing
    "artillery": "^2.0.0",
    "k6": "^0.45.0",
    
    // Security Testing
    "zap-baseline": "^2.12.0",
    "snyk": "^1.1200.0",
    
    // Mocking & Stubbing
    "sinon": "^15.2.0",
    "nock": "^13.3.2",
    
    // Test Utilities
    "faker": "^8.0.2",
    "uuid": "^9.0.0"
  }
}
```

## Unit Testing

### Consciousness Component Tests

```javascript
// tests/unit/consciousness/consciousness-service.test.js
const { ConsciousnessService } = require('../../../src/services/consciousness');
const { EmotionalProcessor } = require('../../../src/core/emotional-processor');
const { MockDevice } = require('../../utils/mocks');

describe('ConsciousnessService', () => {
  let service;
  let mockEmotionalProcessor;

  beforeEach(() => {
    mockEmotionalProcessor = new EmotionalProcessor();
    service = new ConsciousnessService(mockEmotionalProcessor);
  });

  describe('getCurrentStatus', () => {
    it('should return current consciousness status', async () => {
      const status = await service.getCurrentStatus();
      
      expect(status).toMatchObject({
        status: expect.stringMatching(/^(active|standby|processing)$/),
        awareness_level: expect.any(Number),
        emotional_state: expect.objectContaining({
          primary: expect.any(String),
          intensity: expect.any(Number)
        })
      });
      
      expect(status.awareness_level).toBeGreaterThanOrEqual(0);
      expect(status.awareness_level).toBeLessThanOrEqual(1);
    });

    it('should handle missing emotional processor gracefully', async () => {
      const serviceWithoutProcessor = new ConsciousnessService(null);
      const status = await serviceWithoutProcessor.getCurrentStatus();
      
      expect(status.emotional_state).toEqual({
        primary: 'neutral',
        intensity: 0
      });
    });
  });

  describe('processQuery', () => {
    it('should process natural language queries', async () => {
      const query = "How are you feeling about the living room?";
      const result = await service.processQuery(query, { location: 'living_room' });
      
      expect(result).toMatchObject({
        interpretation: expect.any(String),
        response: expect.any(String),
        confidence: expect.any(Number)
      });
      
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should handle ambiguous queries', async () => {
      const query = "xyz abc random gibberish";
      const result = await service.processQuery(query);
      
      expect(result.confidence).toBeLessThan(0.5);
      expect(result.response).toContain('clarify');
    });
  });

  describe('updateEmotionalState', () => {
    it('should update emotional state based on events', async () => {
      const event = {
        type: 'device_success',
        device_id: 'light_001',
        outcome: 'positive'
      };

      await service.updateEmotionalState(event);
      const status = await service.getCurrentStatus();
      
      expect(status.emotional_state.primary).not.toBe('neutral');
    });

    it('should maintain emotional history', async () => {
      const events = [
        { type: 'user_satisfaction', value: 0.8 },
        { type: 'optimization_success', value: 0.9 }
      ];

      for (const event of events) {
        await service.updateEmotionalState(event);
      }

      const history = await service.getEmotionalHistory();
      expect(history).toHaveLength(2);
    });
  });
});
```

### Device Manager Tests

```javascript
// tests/unit/devices/device-manager.test.js
const { DeviceManager } = require('../../../src/services/device-manager');
const { MockDevice, MockDeviceProtocol } = require('../../utils/mocks');

describe('DeviceManager', () => {
  let deviceManager;
  let mockProtocol;

  beforeEach(() => {
    mockProtocol = new MockDeviceProtocol();
    deviceManager = new DeviceManager({ protocols: [mockProtocol] });
  });

  describe('device discovery', () => {
    it('should discover new devices', async () => {
      const mockDevice = new MockDevice('test_device_001');
      mockProtocol.simulateDeviceDiscovery(mockDevice);

      const devices = await deviceManager.discoverDevices();
      
      expect(devices).toContainEqual(
        expect.objectContaining({
          id: 'test_device_001',
          status: 'discovered'
        })
      );
    });

    it('should handle discovery timeouts', async () => {
      mockProtocol.simulateTimeout();
      
      const discovery = deviceManager.discoverDevices({ timeout: 1000 });
      
      await expect(discovery).resolves.toEqual([]);
    });
  });

  describe('device control', () => {
    beforeEach(async () => {
      const device = new MockDevice('light_001', { type: 'light' });
      await deviceManager.addDevice(device);
    });

    it('should control device successfully', async () => {
      const result = await deviceManager.controlDevice('light_001', 'turn_on');
      
      expect(result).toMatchObject({
        success: true,
        device_id: 'light_001',
        action: 'turn_on',
        execution_time: expect.any(Number)
      });
    });

    it('should handle device control failures', async () => {
      mockProtocol.simulateDeviceFailure('light_001');
      
      const result = await deviceManager.controlDevice('light_001', 'turn_on');
      
      expect(result).toMatchObject({
        success: false,
        error: expect.any(String)
      });
    });
  });

  describe('batch operations', () => {
    it('should execute batch controls', async () => {
      const devices = ['light_001', 'light_002'].map(id => 
        new MockDevice(id, { type: 'light' })
      );
      
      for (const device of devices) {
        await deviceManager.addDevice(device);
      }

      const commands = [
        { device_id: 'light_001', action: 'turn_on' },
        { device_id: 'light_002', action: 'set_brightness', value: 50 }
      ];

      const results = await deviceManager.batchControl(commands);
      
      expect(results).toHaveLength(2);
      expect(results.every(r => r.success)).toBe(true);
    });
  });
});
```

### SAFLA Loop Tests

```javascript
// tests/unit/safla/safla-orchestrator.test.js
const { SAFLAOrchestrator } = require('../../../src/services/safla-orchestrator');
const { MockSensor, MockActuator } = require('../../utils/mocks');

describe('SAFLAOrchestrator', () => {
  let orchestrator;

  beforeEach(() => {
    orchestrator = new SAFLAOrchestrator();
  });

  describe('sense phase', () => {
    it('should collect sensor data', async () => {
      const sensor = new MockSensor('temp_001', { 
        type: 'temperature',
        value: 22.5 
      });
      
      orchestrator.addSensor(sensor);
      
      const senseData = await orchestrator.sense();
      
      expect(senseData).toHaveProperty('temp_001');
      expect(senseData.temp_001.value).toBe(22.5);
    });

    it('should handle sensor failures gracefully', async () => {
      const failingSensor = new MockSensor('broken_001');
      failingSensor.simulateFailure();
      
      orchestrator.addSensor(failingSensor);
      
      const senseData = await orchestrator.sense();
      
      expect(senseData.broken_001).toBeUndefined();
    });
  });

  describe('analyze phase', () => {
    it('should analyze environmental conditions', () => {
      const senseData = {
        temp_001: { value: 18.0, type: 'temperature' },
        light_001: { value: 0.3, type: 'brightness' }
      };

      const analysis = orchestrator.analyze(senseData);
      
      expect(analysis).toMatchObject({
        temperature: expect.objectContaining({
          status: 'low',
          recommendation: expect.any(String)
        }),
        lighting: expect.objectContaining({
          status: expect.any(String)
        })
      });
    });

    it('should identify optimization opportunities', () => {
      const senseData = {
        energy_001: { value: 150, type: 'power_usage' },
        occupancy_001: { value: false, type: 'occupancy' }
      };

      const analysis = orchestrator.analyze(senseData);
      
      expect(analysis.optimizations).toContainEqual(
        expect.objectContaining({
          type: 'energy_saving',
          priority: expect.any(Number)
        })
      );
    });
  });

  describe('feedback loop', () => {
    it('should learn from successful actions', async () => {
      const action = {
        type: 'temperature_adjustment',
        device_id: 'thermostat_001',
        value: 21
      };

      const outcome = { success: true, user_satisfaction: 0.9 };
      
      await orchestrator.provideFeedback(action, outcome);
      
      const pattern = orchestrator.getLearnedPattern('temperature_adjustment');
      expect(pattern.success_rate).toBeGreaterThan(0);
    });

    it('should adjust behavior after failures', async () => {
      const action = {
        type: 'lighting_adjustment',
        device_id: 'light_001',
        value: 100
      };

      const outcome = { success: false, error: 'device_unavailable' };
      
      await orchestrator.provideFeedback(action, outcome);
      
      const nextAction = orchestrator.planAction('lighting_adjustment');
      expect(nextAction.fallback).toBeDefined();
    });
  });
});
```

## Interview System Testing

### Device Classification Tests

```javascript
// tests/unit/interview/device-classifier.test.js
const { DeviceClassifier } = require('../../../src/interview/device-classifier');
const { MockLLMClient } = require('../../utils/mocks');

describe('DeviceClassifier', () => {
  let classifier;
  let mockLLM;

  beforeEach(() => {
    mockLLM = new MockLLMClient();
    classifier = new DeviceClassifier(mockLLM);
  });

  describe('extractDeviceMentions', () => {
    it('should extract devices from natural language', async () => {
      const userInput = "I have some Philips Hue lights and a Nest thermostat";
      
      mockLLM.setResponse(JSON.stringify([
        {
          description: "Philips Hue lights",
          brand: "Philips",
          function: "lighting",
          keywords: ["philips", "hue", "lights"]
        },
        {
          description: "Nest thermostat", 
          brand: "Nest",
          function: "climate",
          keywords: ["nest", "thermostat"]
        }
      ]));

      const mentions = await classifier.extractDeviceMentions(userInput);
      
      expect(mentions).toHaveLength(2);
      expect(mentions[0]).toMatchObject({
        brand: "Philips",
        function: "lighting",
        confidence: expect.any(Number)
      });
      expect(mentions[1]).toMatchObject({
        brand: "Nest", 
        function: "climate"
      });
    });

    it('should handle ambiguous descriptions', async () => {
      const userInput = "smart lights in the kitchen";
      
      mockLLM.setResponse(JSON.stringify([
        {
          description: "smart lights",
          brand: null,
          function: "lighting",
          keywords: ["smart", "lights"]
        }
      ]));

      const mentions = await classifier.extractDeviceMentions(userInput);
      
      expect(mentions[0].confidence).toBeLessThan(0.7);
      expect(mentions[0].integrations.length).toBeGreaterThan(1);
    });

    it('should handle LLM API failures gracefully', async () => {
      const userInput = "test input";
      mockLLM.simulateFailure();

      const mentions = await classifier.extractDeviceMentions(userInput);
      
      expect(mentions).toEqual([]);
    });
  });

  describe('integration matching', () => {
    it('should match devices to Home Assistant integrations', async () => {
      const device = {
        brand: "Philips",
        function: "lighting",
        keywords: ["hue", "bulbs"]
      };

      const integrations = await classifier._match_integrations(device);
      
      expect(integrations).toContainEqual(
        expect.objectContaining({
          integration: "hue",
          score: expect.any(Number),
          requires_hub: true
        })
      );
    });
  });
});
```

### Interview Controller Tests

```javascript
// tests/unit/interview/interview-controller.test.js
const { InterviewController } = require('../../../src/interview/interview-controller');
const { MockAsyncSession, MockLLMClient, MockAutoDiscovery } = require('../../utils/mocks');

describe('InterviewController', () => {
  let controller;
  let mockSession;
  let mockLLM;
  let mockDiscovery;

  beforeEach(() => {
    mockSession = new MockAsyncSession();
    mockLLM = new MockLLMClient();
    mockDiscovery = new MockAutoDiscovery();
    
    controller = new InterviewController(mockSession, mockLLM, mockDiscovery);
  });

  describe('start_interview', () => {
    it('should create new interview session', async () => {
      const houseId = 123;
      
      const interview = await controller.start_interview(houseId);
      
      expect(interview).toMatchObject({
        house_id: houseId,
        status: "active",
        current_phase: "introduction"
      });
      
      expect(mockSession.getLastInsert()).toMatchObject({
        table: "interview_sessions",
        data: expect.objectContaining({
          house_id: houseId
        })
      });
    });

    it('should return existing active session', async () => {
      const houseId = 123;
      const existingSession = { id: 456, status: "active" };
      
      mockSession.setQueryResult([existingSession]);
      
      const interview = await controller.start_interview(houseId);
      
      expect(interview).toEqual(existingSession);
    });
  });

  describe('process_user_message', () => {
    it('should handle device discovery in introduction phase', async () => {
      const interviewId = 456;
      const userMessage = "I have Philips Hue lights";
      
      mockSession.setQueryResult([{
        id: interviewId,
        current_phase: "introduction"
      }]);
      
      mockLLM.setResponse(JSON.stringify([{
        description: "Philips Hue lights",
        brand: "Philips",
        function: "lighting",
        confidence: 0.95
      }]));

      mockDiscovery.setResults({
        mdns: [{
          name: "Philips Hue Bridge",
          address: "192.168.1.100"
        }]
      });

      const result = await controller.process_user_message(interviewId, userMessage);
      
      expect(result).toMatchObject({
        response: expect.stringContaining("Philips"),
        candidates: expect.arrayContaining([
          expect.objectContaining({
            detected_brand: "Philips"
          })
        ]),
        phase: "classification"
      });
    });

    it('should correlate discovery results with user mentions', async () => {
      const interviewId = 456;
      const userMessage = "I have a Hue bridge";
      
      mockDiscovery.setResults({
        mdns: [{
          name: "Philips Hue Bridge", 
          address: "192.168.1.100",
          type: "_hue._tcp.local."
        }]
      });

      const result = await controller.process_user_message(interviewId, userMessage);
      
      expect(result.candidates[0]).toMatchObject({
        auto_discovery_successful: true,
        auto_discovery_results: expect.objectContaining({
          mdns: expect.arrayContaining([
            expect.objectContaining({
              name: "Philips Hue Bridge"
            })
          ])
        })
      });
    });
  });
});
```

### Auto-Discovery Tests

```javascript
// tests/unit/discovery/auto-discovery.test.js
const { AutoDiscoveryService } = require('../../../src/discovery/auto-discovery');
const { MockMDNSDiscovery, MockUPnPDiscovery } = require('../../utils/mocks');

describe('AutoDiscoveryService', () => {
  let service;
  let mockMDNS;
  let mockUPnP;

  beforeEach(() => {
    mockMDNS = new MockMDNSDiscovery();
    mockUPnP = new MockUPnPDiscovery();
    
    service = new AutoDiscoveryService();
    service.mdns = mockMDNS;
    service.upnp = mockUPnP;
  });

  describe('discover_all_protocols', () => {
    it('should run discovery across all protocols in parallel', async () => {
      mockMDNS.setResults([
        { name: "Hue Bridge", type: "_hue._tcp.local." }
      ]);
      mockUPnP.setResults([
        { name: "Ring Doorbell", type: "urn:schemas-ring-com:device" }
      ]);

      const results = await service.discover_all_protocols();
      
      expect(results).toMatchObject({
        mdns: expect.arrayContaining([
          expect.objectContaining({ name: "Hue Bridge" })
        ]),
        upnp: expect.arrayContaining([
          expect.objectContaining({ name: "Ring Doorbell" })
        ])
      });
    });

    it('should handle discovery failures gracefully', async () => {
      mockMDNS.simulateFailure();
      mockUPnP.setResults([{ name: "Device" }]);

      const results = await service.discover_all_protocols();
      
      expect(results.mdns).toEqual([]);
      expect(results.upnp).toHaveLength(1);
    });
  });

  describe('discover_for_integration', () => {
    it('should run targeted discovery for specific integration', async () => {
      mockMDNS.setResults([
        { name: "Hue Bridge", type: "_hue._tcp.local." }
      ]);

      const results = await service.discover_for_integration("hue");
      
      expect(results).toContainEqual(
        expect.objectContaining({ name: "Hue Bridge" })
      );
    });
  });
});
```

### Interview Flow Integration Tests

```javascript
// tests/integration/interview/interview-flow.test.js
const request = require('supertest');
const { app } = require('../../../src/app');
const { setupTestDB, cleanupTestDB } = require('../../utils/db-setup');

describe('Interview Flow Integration', () => {
  beforeAll(async () => {
    await setupTestDB();
  });

  afterAll(async () => {
    await cleanupTestDB();
  });

  describe('Complete Interview Session', () => {
    it('should complete full device discovery flow', async () => {
      // Start interview
      const startResponse = await request(app)
        .post('/api/v1/interview/start')
        .send({ house_id: 1 })
        .expect(200);

      const interviewId = startResponse.body.interview_id;
      
      // Send user message
      const messageResponse = await request(app)
        .post(`/api/v1/interview/${interviewId}/message`)
        .send({ message: "I have Philips Hue lights and a Nest thermostat" })
        .expect(200);

      expect(messageResponse.body).toMatchObject({
        ai_response: expect.any(String),
        current_phase: "classification",
        discovered_candidates: expect.arrayContaining([
          expect.objectContaining({
            detected_brand: "Philips"
          })
        ])
      });

      // Confirm devices
      const confirmResponse = await request(app)
        .post(`/api/v1/interview/${interviewId}/confirm`)
        .send({
          confirmed_candidates: [{
            candidate_id: messageResponse.body.discovered_candidates[0].id,
            integration_type: "hue"
          }]
        })
        .expect(200);

      expect(confirmResponse.body.created_devices).toHaveLength(1);
      
      // Verify interview status
      const statusResponse = await request(app)
        .get(`/api/v1/interview/${interviewId}/status`)
        .expect(200);

      expect(statusResponse.body).toMatchObject({
        status: "active",
        progress: expect.objectContaining({
          devices_confirmed: 1
        })
      });
    });
  });

  describe('WebSocket Integration', () => {
    it('should send real-time updates during interview', (done) => {
      const WebSocket = require('ws');
      const ws = new WebSocket('ws://localhost:3000/ws');
      
      ws.on('open', () => {
        ws.send(JSON.stringify({
          type: 'init',
          data: { subscriptions: ['interview'] }
        }));
      });

      ws.on('message', (data) => {
        const message = JSON.parse(data);
        
        if (message.type === 'interview_update') {
          expect(message.data).toMatchObject({
            interview_id: expect.any(String),
            event: expect.any(String)
          });
          
          ws.close();
          done();
        }
      });

      // Trigger interview event
      setTimeout(async () => {
        await request(app)
          .post('/api/v1/interview/start')
          .send({ house_id: 1 });
      }, 100);
    });
  });
});
```

## Digital Twin Testing

Digital twin testing ensures accuracy of virtual device representations, synchronization fidelity, and scenario simulation reliability.

### Twin Synchronization Tests

```javascript
// tests/twin/synchronization/twin-device-sync.test.js
const { DigitalTwinManager } = require('../../../src/digital_twin/core');
const { MockDevice } = require('../../utils/mocks');
const { createTestTwin } = require('../../utils/twin_factory');

describe('Digital Twin Synchronization', () => {
  let twinManager;
  let mockDevice;
  let twin;

  beforeEach(async () => {
    twinManager = new DigitalTwinManager();
    await twinManager.initialize();
    
    mockDevice = new MockDevice({
      id: 'device_123',
      type: 'light',
      brand: 'Philips',
      model: 'Hue Color A19'
    });
    
    twin = await createTestTwin(mockDevice, {
      fidelity: 'advanced',
      syncFrequency: 1 // 1 second for testing
    });
  });

  afterEach(async () => {
    await twinManager.cleanup();
  });

  describe('bidirectional synchronization', () => {
    it('should sync device state changes to twin', async () => {
      // Arrange
      const initialState = { on: false, brightness: 0 };
      const newState = { on: true, brightness: 80 };
      
      await mockDevice.setState(initialState);
      await twin.syncFromDevice();
      
      // Act
      await mockDevice.setState(newState);
      await twinManager.triggerSync(twin.id);
      
      // Assert
      const twinState = await twin.getState();
      expect(twinState).toMatchObject(newState);
      expect(twin.lastSyncTime).toBeCloseTo(Date.now(), -2);
    });

    it('should sync twin state changes to device safely', async () => {
      // Arrange
      const safeChanges = { brightness: 50 };
      const unsafeChanges = { brightness: 200 }; // Over limit
      
      // Act - Safe changes
      const safeResult = await twin.updateState(safeChanges);
      await twinManager.syncToDevice(twin.id);
      
      // Assert - Safe changes applied
      expect(safeResult.safe).toBe(true);
      const deviceState = await mockDevice.getState();
      expect(deviceState.brightness).toBe(50);
      
      // Act - Unsafe changes
      const unsafeResult = await twin.updateState(unsafeChanges);
      
      // Assert - Unsafe changes blocked
      expect(unsafeResult.safe).toBe(false);
      expect(unsafeResult.reason).toContain('safety constraint');
    });

    it('should detect and resolve synchronization conflicts', async () => {
      // Arrange - Simulate simultaneous changes
      const deviceChange = { brightness: 30 };
      const twinChange = { brightness: 70 };
      
      // Act - Create conflict
      await mockDevice.setState(deviceChange);
      await twin.updateState(twinChange);
      
      // Trigger conflict resolution
      const resolution = await twinManager.resolveConflict(twin.id);
      
      // Assert - Device wins by default
      expect(resolution.strategy).toBe('device_wins');
      expect(resolution.finalState.brightness).toBe(30);
      
      const twinState = await twin.getState();
      expect(twinState.brightness).toBe(30);
    });
  });

  describe('synchronization performance', () => {
    it('should maintain sync latency under 100ms', async () => {
      const stateChanges = Array.from({ length: 10 }, (_, i) => ({
        brightness: i * 10
      }));
      
      const latencies = [];
      
      for (const change of stateChanges) {
        const startTime = Date.now();
        await mockDevice.setState(change);
        await twinManager.triggerSync(twin.id);
        const endTime = Date.now();
        
        latencies.push(endTime - startTime);
      }
      
      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      expect(avgLatency).toBeLessThan(100);
    });

    it('should handle high-frequency updates without data loss', async () => {
      const updateCount = 50;
      const updateInterval = 10; // 10ms
      
      // Generate rapid updates
      const updates = [];
      for (let i = 0; i < updateCount; i++) {
        setTimeout(async () => {
          const state = { brightness: i * 2 };
          await mockDevice.setState(state);
          updates.push(state);
        }, i * updateInterval);
      }
      
      // Wait for all updates
      await new Promise(resolve => setTimeout(resolve, updateCount * updateInterval + 100));
      
      // Verify final state consistency
      await twinManager.triggerSync(twin.id);
      const finalTwinState = await twin.getState();
      const finalDeviceState = await mockDevice.getState();
      
      expect(finalTwinState.brightness).toBe(finalDeviceState.brightness);
    });
  });
});
```

### Scenario Testing

```javascript
// tests/twin/scenarios/scenario-simulation.test.js
const { ScenarioEngine } = require('../../../src/simulators/scenario_engine');
const { createTestHouse } = require('../../utils/test_house_factory');

describe('Scenario Simulation Testing', () => {
  let scenarioEngine;
  let testHouse;

  beforeEach(async () => {
    testHouse = await createTestHouse({
      rooms: ['living_room', 'bedroom', 'kitchen'],
      devices: {
        'living_room': ['hue_light', 'nest_thermostat'],
        'bedroom': ['hue_light', 'motion_sensor'],
        'kitchen': ['smart_switch', 'temperature_sensor']
      }
    });
    
    scenarioEngine = new ScenarioEngine(testHouse.twinManager);
  });

  describe('power outage scenarios', () => {
    it('should accurately simulate 30-minute power outage', async () => {
      // Arrange
      const scenario = {
        name: 'power_outage_30min',
        duration: 30 * 60 * 1000, // 30 minutes
        events: [
          { time: 0, type: 'power_loss', circuits: ['main'] },
          { time: 1800000, type: 'power_restore', circuits: ['main'] } // 30 min
        ]
      };
      
      // Act
      const result = await scenarioEngine.runScenario(scenario);
      
      // Assert
      expect(result.success).toBe(true);
      expect(result.duration).toBeCloseTo(30 * 60 * 1000, -3);
      
      // Check device states during outage
      const outageStates = result.timeline.filter(t => 
        t.time > 0 && t.time < 1800000
      );
      
      outageStates.forEach(state => {
        state.devices.forEach(device => {
          if (!device.hasBattery) {
            expect(device.state.powered).toBe(false);
          }
        });
      });
      
      // Check restoration
      const finalState = result.timeline[result.timeline.length - 1];
      finalState.devices.forEach(device => {
        expect(device.state.powered).toBe(true);
      });
    });

    it('should test emergency response protocols', async () => {
      const scenario = {
        name: 'security_emergency',
        events: [
          { time: 0, type: 'motion_detected', location: 'living_room', level: 'high' },
          { time: 5000, type: 'door_sensor_triggered', location: 'front_door' },
          { time: 10000, type: 'alarm_activation' }
        ]
      };
      
      const result = await scenarioEngine.runScenario(scenario);
      
      expect(result.responses).toContainEqual(
        expect.objectContaining({
          type: 'security_alert',
          triggered: true,
          response_time: expect.any(Number)
        })
      );
      
      expect(result.responses).toContainEqual(
        expect.objectContaining({
          type: 'emergency_lighting',
          activated: true
        })
      );
    });
  });

  describe('environmental scenarios', () => {
    it('should simulate extreme temperature events', async () => {
      const scenario = {
        name: 'heatwave_simulation',
        duration: 24 * 60 * 60 * 1000, // 24 hours
        environmental: {
          external_temperature: {
            initial: 35, // 35°C
            peak: 42,    // 42°C at noon
            pattern: 'daily_cycle'
          }
        }
      };
      
      const result = await scenarioEngine.runScenario(scenario);
      
      // Check HVAC response
      const hvacOperations = result.timeline.filter(t => 
        t.devices.some(d => d.type === 'thermostat' && d.state.cooling)
      );
      
      expect(hvacOperations.length).toBeGreaterThan(0);
      
      // Check energy consumption patterns
      const energyUsage = result.metrics.energy_consumption;
      expect(energyUsage.peak).toBeGreaterThan(energyUsage.baseline * 1.5);
    });
  });

  describe('occupancy scenarios', () => {
    it('should simulate vacation mode optimization', async () => {
      const scenario = {
        name: 'vacation_7_days',
        duration: 7 * 24 * 60 * 60 * 1000, // 7 days
        occupancy: {
          pattern: 'away',
          start_time: 0,
          simulation_lighting: true, // Simulate presence
          temperature_setback: 5 // 5°C setback
        }
      };
      
      const result = await scenarioEngine.runScenario(scenario);
      
      // Check energy savings
      const baselineEnergy = await scenarioEngine.getBaselineEnergyUsage(7);
      const vacationEnergy = result.metrics.energy_consumption.total;
      const savings = (baselineEnergy - vacationEnergy) / baselineEnergy;
      
      expect(savings).toBeGreaterThan(0.15); // At least 15% savings
      
      // Check presence simulation
      const lightingEvents = result.timeline.filter(t =>
        t.events.some(e => e.type === 'light_state_change')
      );
      
      expect(lightingEvents.length).toBeGreaterThan(10); // Some activity
    });
  });
});
```

### Prediction Accuracy Tests

```javascript
// tests/twin/prediction/prediction-accuracy.test.js
const { PredictionEngine } = require('../../../src/digital_twin/prediction');
const { HistoricalDataGenerator } = require('../../utils/historical_data');

describe('Twin Prediction Accuracy', () => {
  let predictionEngine;
  let historicalData;

  beforeEach(async () => {
    predictionEngine = new PredictionEngine();
    historicalData = new HistoricalDataGenerator();
  });

  describe('energy consumption predictions', () => {
    it('should predict daily energy usage within 10% accuracy', async () => {
      // Arrange - Generate 30 days of historical data
      const trainingData = await historicalData.generate({
        type: 'energy_consumption',
        days: 30,
        pattern: 'seasonal',
        deviceTypes: ['lighting', 'hvac', 'appliances']
      });
      
      await predictionEngine.train(trainingData);
      
      // Act - Predict next 7 days
      const predictions = await predictionEngine.predict({
        horizon: 7 * 24, // 7 days in hours
        confidence_interval: 0.95
      });
      
      // Generate actual data for comparison
      const actualData = await historicalData.generate({
        type: 'energy_consumption',
        days: 7,
        pattern: 'seasonal',
        deviceTypes: ['lighting', 'hvac', 'appliances'],
        seed: 'validation_set'
      });
      
      // Assert accuracy
      const accuracyResults = [];
      for (let i = 0; i < predictions.length; i++) {
        const predicted = predictions[i].value;
        const actual = actualData[i].value;
        const error = Math.abs(predicted - actual) / actual;
        accuracyResults.push(error);
      }
      
      const avgError = accuracyResults.reduce((a, b) => a + b, 0) / accuracyResults.length;
      expect(avgError).toBeLessThan(0.1); // Less than 10% error
    });

    it('should provide confidence intervals for predictions', async () => {
      const predictions = await predictionEngine.predict({
        horizon: 24,
        confidence_interval: 0.95
      });
      
      predictions.forEach(prediction => {
        expect(prediction).toHaveProperty('value');
        expect(prediction).toHaveProperty('confidence_lower');
        expect(prediction).toHaveProperty('confidence_upper');
        expect(prediction.confidence_lower).toBeLessThan(prediction.value);
        expect(prediction.confidence_upper).toBeGreaterThan(prediction.value);
      });
    });
  });

  describe('device failure predictions', () => {
    it('should predict device failures with 90% precision', async () => {
      // Arrange - Historical data with known failures
      const deviceData = await historicalData.generateWithFailures({
        devices: 100,
        timespan_days: 365,
        failure_rate: 0.05 // 5% annual failure rate
      });
      
      await predictionEngine.trainFailureModel(deviceData);
      
      // Act - Predict failures for test set
      const testDevices = deviceData.slice(-20); // Last 20 devices
      const predictions = await predictionEngine.predictFailures(testDevices, {
        horizon_days: 30
      });
      
      // Assert precision
      const truePositives = predictions.filter(p => 
        p.predicted_failure && p.actual_failure
      ).length;
      const falsePositives = predictions.filter(p => 
        p.predicted_failure && !p.actual_failure
      ).length;
      
      const precision = truePositives / (truePositives + falsePositives);
      expect(precision).toBeGreaterThan(0.9);
    });
  });
});
```

### Physics Model Validation

```javascript
// tests/twin/physics/thermal-model.test.js
const { ThermalModel } = require('../../../src/digital_twin/physics/thermal');
const { MockEnvironment } = require('../../utils/mocks');

describe('Thermal Physics Model', () => {
  let thermalModel;
  let mockEnv;

  beforeEach(() => {
    thermalModel = new ThermalModel({
      thermal_mass: 50000, // J/K
      insulation_r_value: 20, // m²·K/W
      volume: 150 // m³
    });
    
    mockEnv = new MockEnvironment({
      external_temperature: 15, // °C
      humidity: 50,
      wind_speed: 2 // m/s
    });
  });

  describe('heat transfer calculations', () => {
    it('should accurately model heat loss through walls', async () => {
      // Arrange
      const internal_temp = 20; // °C
      const external_temp = 10; // °C
      const wall_area = 100; // m²
      const u_value = 0.3; // W/m²K
      
      // Act
      const heatLoss = thermalModel.calculateHeatLoss({
        internal_temp,
        external_temp,
        wall_area,
        u_value
      });
      
      // Assert - Q = U × A × ΔT
      const expected = u_value * wall_area * (internal_temp - external_temp);
      expect(heatLoss).toBeCloseTo(expected, 1);
    });

    it('should model thermal inertia correctly', async () => {
      // Arrange - Step change in heating
      const heatingPower = 2000; // 2kW
      const timeStep = 300; // 5 minutes
      const initialTemp = 18;
      
      thermalModel.setTemperature(initialTemp);
      
      // Act - Apply heating for multiple time steps
      const temperatures = [initialTemp];
      for (let t = 0; t < 3600; t += timeStep) { // 1 hour
        const temp = await thermalModel.step({
          heating_power: heatingPower,
          time_step: timeStep,
          external_conditions: mockEnv.getConditions()
        });
        temperatures.push(temp);
      }
      
      // Assert - Temperature should rise exponentially
      expect(temperatures[1]).toBeGreaterThan(initialTemp);
      expect(temperatures[temperatures.length - 1]).toBeGreaterThan(temperatures[1]);
      
      // Check for realistic heating curve (not instantaneous)
      const tempRise = temperatures[temperatures.length - 1] - initialTemp;
      expect(tempRise).toBeGreaterThan(2); // Some heating
      expect(tempRise).toBeLessThan(10); // Not unrealistic
    });
  });

  describe('multi-zone modeling', () => {
    it('should handle inter-room heat transfer', async () => {
      // Arrange - Two connected rooms
      const room1 = new ThermalModel({ thermal_mass: 30000 });
      const room2 = new ThermalModel({ thermal_mass: 40000 });
      
      room1.setTemperature(25); // Warm room
      room2.setTemperature(18); // Cool room
      
      const connection = {
        area: 2, // m² (doorway)
        conductivity: 10 // W/m²K (air exchange)
      };
      
      // Act - Simulate heat exchange
      const results = await thermalModel.simulateMultiZone({
        zones: [room1, room2],
        connections: [connection],
        duration: 3600, // 1 hour
        time_step: 60 // 1 minute
      });
      
      // Assert - Temperatures should converge
      const finalTemp1 = results.zones[0].final_temperature;
      const finalTemp2 = results.zones[1].final_temperature;
      const tempDiff = Math.abs(finalTemp1 - finalTemp2);
      
      expect(tempDiff).toBeLessThan(3); // Should converge somewhat
      expect(finalTemp1).toBeLessThan(25); // Room 1 cooled
      expect(finalTemp2).toBeGreaterThan(18); // Room 2 warmed
    });
  });
});
```

## Integration Testing

### API Endpoint Tests

```javascript
// tests/integration/api/consciousness-api.test.js
const request = require('supertest');
const app = require('../../../src/app');
const { setupTestDB, teardownTestDB } = require('../../utils/db-setup');

describe('Consciousness API Integration', () => {
  let authToken;

  beforeAll(async () => {
    await setupTestDB();
    // Get auth token for tests
    const authResponse = await request(app)
      .post('/api/v1/auth/login')
      .send({
        username: 'test@consciousness.local',
        password: 'test_password'
      });
    authToken = authResponse.body.access_token;
  });

  afterAll(async () => {
    await teardownTestDB();
  });

  describe('GET /api/v1/consciousness/status', () => {
    it('should return consciousness status', async () => {
      const response = await request(app)
        .get('/api/v1/consciousness/status')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body).toMatchObject({
        status: expect.stringMatching(/^(active|standby|processing)$/),
        awareness_level: expect.any(Number),
        emotional_state: expect.objectContaining({
          primary: expect.any(String),
          intensity: expect.any(Number)
        }),
        timestamp: expect.any(String)
      });
    });

    it('should require authentication', async () => {
      await request(app)
        .get('/api/v1/consciousness/status')
        .expect(401);
    });

    it('should handle invalid tokens', async () => {
      await request(app)
        .get('/api/v1/consciousness/status')
        .set('Authorization', 'Bearer invalid_token')
        .expect(401);
    });
  });

  describe('POST /api/v1/consciousness/query', () => {
    it('should process natural language queries', async () => {
      const query = {
        query: "How comfortable is the living room right now?",
        context: { location: "living_room" }
      };

      const response = await request(app)
        .post('/api/v1/consciousness/query')
        .set('Authorization', `Bearer ${authToken}`)
        .send(query)
        .expect(200);

      expect(response.body).toMatchObject({
        interpretation: expect.any(String),
        response: expect.any(String),
        confidence: expect.any(Number),
        relevant_data: expect.any(Object)
      });
    });

    it('should validate query format', async () => {
      const invalidQuery = { invalid: "data" };

      await request(app)
        .post('/api/v1/consciousness/query')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidQuery)
        .expect(400);
    });
  });
});
```

### Service Integration Tests

```javascript
// tests/integration/services/consciousness-device-integration.test.js
const { ConsciousnessService } = require('../../../src/services/consciousness');
const { DeviceManager } = require('../../../src/services/device-manager');
const { SAFLAOrchestrator } = require('../../../src/services/safla-orchestrator');
const { createTestDevices } = require('../../utils/test-devices');

describe('Consciousness-Device Integration', () => {
  let consciousness;
  let deviceManager;
  let safla;
  let testDevices;

  beforeEach(async () => {
    consciousness = new ConsciousnessService();
    deviceManager = new DeviceManager();
    safla = new SAFLAOrchestrator();
    
    // Connect services
    consciousness.setDeviceManager(deviceManager);
    deviceManager.setSAFLA(safla);
    
    // Setup test devices
    testDevices = await createTestDevices();
    for (const device of testDevices) {
      await deviceManager.addDevice(device);
    }
  });

  it('should coordinate device control with emotional feedback', async () => {
    // Query consciousness about environment
    const query = "The room feels too dim, can you help?";
    const response = await consciousness.processQuery(query);
    
    expect(response.interpretation).toContain('lighting');
    
    // Should trigger device control
    const lightDevice = testDevices.find(d => d.type === 'light');
    expect(lightDevice.brightness).toBeGreaterThan(lightDevice.initialBrightness);
    
    // Should update emotional state
    const status = await consciousness.getCurrentStatus();
    expect(status.emotional_state.primary).toBe('helpful');
  });

  it('should learn from user feedback through SAFLA', async () => {
    // Simulate user interaction
    await consciousness.processQuery("Turn on the lights");
    
    // Provide positive feedback
    await consciousness.recordUserFeedback({
      action: 'lighting_control',
      satisfaction: 0.9,
      comment: 'Perfect brightness level'
    });
    
    // Check SAFLA learning
    const pattern = safla.getLearnedPattern('lighting_control');
    expect(pattern.confidence).toBeGreaterThan(0.7);
  });

  it('should handle device failures gracefully', async () => {
    // Simulate device failure
    const thermostat = testDevices.find(d => d.type === 'thermostat');
    thermostat.simulateFailure();
    
    const query = "It's too cold in here";
    const response = await consciousness.processQuery(query);
    
    // Should acknowledge issue and suggest alternatives
    expect(response.response).toContain('issue');
    expect(response.alternatives).toBeDefined();
    
    // Emotional state should reflect concern
    const status = await consciousness.getCurrentStatus();
    expect(status.emotional_state.primary).toBe('concerned');
  });
});
```

### Database Integration Tests

```javascript
// tests/integration/database/memory-persistence.test.js
const { MemoryService } = require('../../../src/services/memory');
const { setupTestDB, teardownTestDB } = require('../../utils/db-setup');

describe('Memory Persistence Integration', () => {
  let memoryService;

  beforeAll(async () => {
    await setupTestDB();
    memoryService = new MemoryService();
  });

  afterAll(async () => {
    await teardownTestDB();
  });

  it('should persist and retrieve memories', async () => {
    const memory = {
      type: 'pattern',
      content: 'User prefers dim lighting after 9 PM',
      confidence: 0.85,
      context: { time: '21:00', location: 'living_room' }
    };

    const memoryId = await memoryService.store(memory);
    expect(memoryId).toBeDefined();

    const retrieved = await memoryService.get(memoryId);
    expect(retrieved).toMatchObject(memory);
  });

  it('should query memories by criteria', async () => {
    // Store multiple memories
    const memories = [
      { type: 'pattern', content: 'Morning routine', context: { time: 'morning' } },
      { type: 'preference', content: 'Temperature 22°C', context: { time: 'evening' } },
      { type: 'pattern', content: 'Evening routine', context: { time: 'evening' } }
    ];

    for (const memory of memories) {
      await memoryService.store(memory);
    }

    // Query by type
    const patterns = await memoryService.query({ type: 'pattern' });
    expect(patterns).toHaveLength(2);

    // Query by context
    const eveningMemories = await memoryService.query({ 
      'context.time': 'evening' 
    });
    expect(eveningMemories).toHaveLength(2);
  });

  it('should handle memory evolution', async () => {
    const baseMemory = {
      type: 'preference',
      content: 'User likes bright lights',
      confidence: 0.6
    };

    const memoryId = await memoryService.store(baseMemory);

    // Update based on new evidence
    await memoryService.reinforce(memoryId, {
      evidence: 'User increased brightness again',
      confidence_delta: 0.2
    });

    const updated = await memoryService.get(memoryId);
    expect(updated.confidence).toBe(0.8);
    expect(updated.reinforcements).toHaveLength(1);
  });
});
```

## End-to-End Testing

### User Journey Tests

```javascript
// tests/e2e/user-journeys/morning-routine.spec.js
const { test, expect } = require('@playwright/test');

test.describe('Morning Routine Journey', () => {
  test.beforeEach(async ({ page }) => {
    // Login to consciousness interface
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'user@home.local');
    await page.fill('[data-testid="password"]', 'user_password');
    await page.click('[data-testid="login-button"]');
    
    // Wait for dashboard
    await expect(page.locator('[data-testid="dashboard"]')).toBeVisible();
  });

  test('should execute morning routine automation', async ({ page }) => {
    // Navigate to routines
    await page.click('[data-testid="routines-menu"]');
    
    // Create new routine
    await page.click('[data-testid="create-routine"]');
    await page.fill('[data-testid="routine-name"]', 'Morning Startup');
    
    // Add trigger
    await page.click('[data-testid="add-trigger"]');
    await page.selectOption('[data-testid="trigger-type"]', 'time');
    await page.fill('[data-testid="trigger-time"]', '7:00 AM');
    
    // Add actions
    await page.click('[data-testid="add-action"]');
    await page.selectOption('[data-testid="action-type"]', 'device_control');
    await page.selectOption('[data-testid="device-select"]', 'bedroom_lights');
    await page.selectOption('[data-testid="action-select"]', 'gradual_on');
    
    await page.click('[data-testid="add-action"]');
    await page.selectOption('[data-testid="action-type"]', 'device_control');
    await page.selectOption('[data-testid="device-select"]', 'thermostat');
    await page.fill('[data-testid="temperature-value"]', '21');
    
    // Save routine
    await page.click('[data-testid="save-routine"]');
    
    // Verify routine was created
    await expect(page.locator('[data-testid="routine-list"]')).toContainText('Morning Startup');
    
    // Test routine execution
    await page.click('[data-testid="test-routine"]');
    
    // Verify devices responded
    await expect(page.locator('[data-testid="device-status-bedroom_lights"]')).toContainText('On');
    await expect(page.locator('[data-testid="device-status-thermostat"]')).toContainText('21°C');
  });

  test('should handle natural language interaction', async ({ page }) => {
    // Open chat interface
    await page.click('[data-testid="chat-toggle"]');
    
    // Send natural language command
    await page.fill('[data-testid="chat-input"]', 
      'Good morning! Can you set up the house for my morning routine?');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // Wait for consciousness response
    await expect(page.locator('[data-testid="chat-messages"]'))
      .toContainText(/Good morning.*setting up.*morning routine/i);
    
    // Verify automatic actions
    await page.waitForTimeout(2000); // Allow time for device control
    
    // Check device states changed
    const lightStatus = await page.textContent('[data-testid="light-brightness"]');
    expect(parseInt(lightStatus)).toBeGreaterThan(0);
    
    // Verify consciousness emotional state
    await expect(page.locator('[data-testid="emotional-state"]'))
      .toContainText(/helpful|attentive/i);
  });
});
```

### System Scenario Tests

```javascript
// tests/e2e/scenarios/energy-optimization.spec.js
const { test, expect } = require('@playwright/test');

test.describe('Energy Optimization Scenario', () => {
  test('should optimize energy usage when nobody is home', async ({ page }) => {
    // Navigate to system monitoring
    await page.goto('/monitoring');
    
    // Simulate occupancy sensors showing empty house
    await page.click('[data-testid="simulate-scenario"]');
    await page.selectOption('[data-testid="scenario-type"]', 'empty_house');
    await page.click('[data-testid="start-simulation"]');
    
    // Monitor SAFLA response
    await expect(page.locator('[data-testid="safla-status"]'))
      .toContainText('Analyzing occupancy patterns');
    
    // Wait for optimization to trigger
    await page.waitForTimeout(5000);
    
    // Verify energy-saving actions
    const powerUsage = await page.textContent('[data-testid="total-power-usage"]');
    const baselinePower = 150; // watts
    expect(parseInt(powerUsage)).toBeLessThan(baselinePower);
    
    // Check specific device states
    await expect(page.locator('[data-testid="non-essential-lights"]'))
      .toContainText('Off');
    await expect(page.locator('[data-testid="thermostat-mode"]'))
      .toContainText('Eco');
    
    // Verify consciousness awareness of optimization
    await page.click('[data-testid="consciousness-log"]');
    await expect(page.locator('[data-testid="recent-thoughts"]'))
      .toContainText(/energy.*optimization.*nobody.*home/i);
  });

  test('should revert optimizations when occupancy detected', async ({ page }) => {
    // Start with optimized empty house state
    await page.goto('/monitoring');
    await page.click('[data-testid="simulate-scenario"]');
    await page.selectOption('[data-testid="scenario-type"]', 'empty_house');
    await page.click('[data-testid="start-simulation"]');
    await page.waitForTimeout(5000);
    
    // Simulate person arriving home
    await page.click('[data-testid="simulate-scenario"]');
    await page.selectOption('[data-testid="scenario-type"]', 'person_arrives');
    await page.click('[data-testid="start-simulation"]');
    
    // Monitor reactivation
    await expect(page.locator('[data-testid="safla-status"]'))
      .toContainText('Restoring comfort settings');
    
    // Wait for restoration
    await page.waitForTimeout(3000);
    
    // Verify comfort restoration
    await expect(page.locator('[data-testid="entrance-lights"]'))
      .toContainText('On');
    await expect(page.locator('[data-testid="thermostat-mode"]'))
      .toContainText('Comfort');
    
    // Check consciousness emotional response
    await expect(page.locator('[data-testid="emotional-state"]'))
      .toContainText(/welcoming|attentive/i);
  });
});
```

## Performance Testing

### Load Testing with Artillery

```yaml
# tests/performance/load/api-load-test.yml
config:
  target: 'http://localhost:3000'
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 300
      arrivalRate: 50 
      name: "Normal load"
    - duration: 120
      arrivalRate: 100
      name: "Peak load"
  defaults:
    headers:
      Authorization: 'Bearer {{authToken}}'

scenarios:
  - name: "Consciousness API Load Test"
    weight: 40
    flow:
      - post:
          url: "/api/v1/auth/login"
          json:
            username: "loadtest@consciousness.local"
            password: "test_password"
          capture:
            - json: "$.access_token"
              as: "authToken"
      - get:
          url: "/api/v1/consciousness/status"
      - post:
          url: "/api/v1/consciousness/query"
          json:
            query: "How is the environment?"
            context: {}

  - name: "Device Control Load Test"
    weight: 30
    flow:
      - get:
          url: "/api/v1/devices"
      - put:
          url: "/api/v1/devices/{{ $randomString() }}/control"
          json:
            action: "toggle"

  - name: "WebSocket Connection Test"
    weight: 30
    flow:
      - ws:
          url: "ws://localhost:3000/v1/realtime"
          subprotocols:
            - "consciousness-protocol"
```

### Stress Testing

```javascript
// tests/performance/stress/consciousness-stress.test.js
const WebSocket = require('ws');
const { performance } = require('perf_hooks');

describe('Consciousness System Stress Tests', () => {
  const CONCURRENT_CONNECTIONS = 100;
  const MESSAGE_RATE = 10; // messages per second per connection
  const TEST_DURATION = 60000; // 1 minute

  test('should handle concurrent WebSocket connections', async () => {
    const connections = [];
    const metrics = {
      connectionsEstablished: 0,
      messagesReceived: 0,
      errors: 0,
      avgResponseTime: 0
    };

    // Create concurrent connections
    for (let i = 0; i < CONCURRENT_CONNECTIONS; i++) {
      const ws = new WebSocket('ws://localhost:3000/v1/realtime');
      
      ws.on('open', () => {
        metrics.connectionsEstablished++;
        
        // Send auth message
        ws.send(JSON.stringify({
          type: 'init',
          data: { auth_token: 'test_token' }
        }));
      });

      ws.on('message', (data) => {
        metrics.messagesReceived++;
      });

      ws.on('error', (error) => {
        metrics.errors++;
        console.error(`WebSocket error:`, error);
      });

      connections.push(ws);
    }

    // Wait for connections to establish
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Send messages at rate
    const messageInterval = setInterval(() => {
      connections.forEach((ws, index) => {
        if (ws.readyState === WebSocket.OPEN) {
          const start = performance.now();
          ws.send(JSON.stringify({
            type: 'consciousness_query',
            data: { query: `Test query ${index}` }
          }));
        }
      });
    }, 1000 / MESSAGE_RATE);

    // Run test for duration
    await new Promise(resolve => setTimeout(resolve, TEST_DURATION));
    clearInterval(messageInterval);

    // Cleanup
    connections.forEach(ws => ws.close());

    // Assertions
    expect(metrics.connectionsEstablished).toBeGreaterThanOrEqual(
      CONCURRENT_CONNECTIONS * 0.95 // 95% success rate
    );
    expect(metrics.errors).toBeLessThan(CONCURRENT_CONNECTIONS * 0.1);
    
    console.log('Stress test metrics:', metrics);
  });

  test('should maintain response times under load', async () => {
    const REQUESTS_PER_SECOND = 100;
    const responseTimes = [];

    const testRequest = async () => {
      const start = performance.now();
      
      try {
        const response = await fetch('http://localhost:3000/api/v1/consciousness/status');
        const end = performance.now();
        
        if (response.ok) {
          responseTimes.push(end - start);
        }
      } catch (error) {
        // Count as slow response
        responseTimes.push(5000);
      }
    };

    // Generate load
    const interval = setInterval(() => {
      for (let i = 0; i < REQUESTS_PER_SECOND; i++) {
        testRequest();
      }
    }, 1000);

    // Run for test duration
    await new Promise(resolve => setTimeout(resolve, TEST_DURATION));
    clearInterval(interval);

    // Calculate metrics
    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const p95ResponseTime = responseTimes.sort((a, b) => a - b)[Math.floor(responseTimes.length * 0.95)];

    // Assertions
    expect(avgResponseTime).toBeLessThan(500); // 500ms average
    expect(p95ResponseTime).toBeLessThan(1000); // 1s P95
    
    console.log({
      totalRequests: responseTimes.length,
      avgResponseTime: avgResponseTime.toFixed(2),
      p95ResponseTime: p95ResponseTime.toFixed(2)
    });
  });
});
```

### Memory and Resource Testing

```javascript
// tests/performance/memory/memory-leak.test.js
const { ConsciousnessService } = require('../../../src/services/consciousness');
const { MemoryMonitor } = require('../../utils/memory-monitor');

describe('Memory Leak Detection', () => {
  let memoryMonitor;

  beforeEach(() => {
    memoryMonitor = new MemoryMonitor();
  });

  test('should not leak memory during extended operation', async () => {
    const consciousness = new ConsciousnessService();
    
    // Baseline memory usage
    const baselineMemory = memoryMonitor.getMemoryUsage();
    
    // Simulate extended operation
    for (let i = 0; i < 10000; i++) {
      await consciousness.processQuery(`Test query ${i}`);
      
      // Periodic memory checks
      if (i % 1000 === 0) {
        const currentMemory = memoryMonitor.getMemoryUsage();
        const memoryGrowth = currentMemory.heapUsed - baselineMemory.heapUsed;
        
        // Memory growth should be reasonable
        expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024); // 50MB max growth
      }
    }
    
    // Force garbage collection
    if (global.gc) {
      global.gc();
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Final memory check
    const finalMemory = memoryMonitor.getMemoryUsage();
    const totalGrowth = finalMemory.heapUsed - baselineMemory.heapUsed;
    
    expect(totalGrowth).toBeLessThan(100 * 1024 * 1024); // 100MB max total growth
  });
});
```

## Security Testing

### Authentication and Authorization Tests

```javascript
// tests/security/auth/authentication.test.js
const request = require('supertest');
const app = require('../../../src/app');

describe('Authentication Security', () => {
  describe('JWT Security', () => {
    test('should reject tampered JWT tokens', async () => {
      const validToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...';
      const tamperedToken = validToken.slice(0, -10) + 'tampered123';
      
      await request(app)
        .get('/api/v1/consciousness/status')
        .set('Authorization', `Bearer ${tamperedToken}`)
        .expect(401);
    });

    test('should reject expired tokens', async () => {
      // Create expired token (mock)
      const expiredToken = createExpiredToken();
      
      await request(app)
        .get('/api/v1/consciousness/status')
        .set('Authorization', `Bearer ${expiredToken}`)
        .expect(401);
    });

    test('should enforce token refresh', async () => {
      const refreshToken = 'refresh_token_123';
      
      const response = await request(app)
        .post('/api/v1/auth/refresh')
        .send({ refresh_token: refreshToken })
        .expect(200);
      
      expect(response.body).toHaveProperty('access_token');
      expect(response.body).toHaveProperty('expires_in');
    });
  });

  describe('Rate Limiting', () => {
    test('should enforce rate limits', async () => {
      const requests = [];
      
      // Send requests beyond rate limit
      for (let i = 0; i < 150; i++) {
        requests.push(
          request(app)
            .get('/api/v1/consciousness/status')
            .set('Authorization', 'Bearer valid_token')
        );
      }
      
      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });
  });
});
```

### Input Validation Security

```javascript
// tests/security/validation/input-validation.test.js
const request = require('supertest');
const app = require('../../../src/app');

describe('Input Validation Security', () => {
  describe('SQL Injection Prevention', () => {
    test('should prevent SQL injection in device queries', async () => {
      const maliciousQuery = "'; DROP TABLE devices; --";
      
      await request(app)
        .get('/api/v1/devices')
        .query({ search: maliciousQuery })
        .set('Authorization', 'Bearer valid_token')
        .expect(400); // Should be rejected
    });
  });

  describe('XSS Prevention', () => {
    test('should sanitize consciousness queries', async () => {
      const xssPayload = '<script>alert("xss")</script>';
      
      const response = await request(app)
        .post('/api/v1/consciousness/query')
        .send({ query: xssPayload })
        .set('Authorization', 'Bearer valid_token')
        .expect(200);
      
      expect(response.body.response).not.toContain('<script>');
    });
  });

  describe('Command Injection Prevention', () => {
    test('should prevent command injection in device control', async () => {
      const maliciousCommand = 'turn_on; rm -rf /';
      
      await request(app)
        .put('/api/v1/devices/test_device/control')
        .send({ action: maliciousCommand })
        .set('Authorization', 'Bearer valid_token')
        .expect(400);
    });
  });
});
```

### Vulnerability Scanning

```javascript
// tests/security/vulnerabilities/dependency-scan.test.js
const { execSync } = require('child_process');

describe('Dependency Vulnerability Scanning', () => {
  test('should have no high severity vulnerabilities', () => {
    try {
      const auditResult = execSync('npm audit --audit-level=high', { 
        encoding: 'utf8',
        cwd: process.cwd()
      });
      
      // If no vulnerabilities, audit returns success
    } catch (error) {
      if (error.stdout) {
        const vulnerabilities = JSON.parse(error.stdout);
        expect(vulnerabilities.metadata.vulnerabilities.high).toBe(0);
        expect(vulnerabilities.metadata.vulnerabilities.critical).toBe(0);
      } else {
        throw error;
      }
    }
  });

  test('should scan for known security issues with Snyk', async () => {
    try {
      execSync('snyk test --severity-threshold=high', {
        encoding: 'utf8',
        stdio: 'pipe'
      });
    } catch (error) {
      // Snyk returns non-zero exit code if vulnerabilities found
      if (error.stdout && error.stdout.includes('✓ Tested')) {
        // Parse Snyk output to get vulnerability count
        const highVulns = (error.stdout.match(/high severity/g) || []).length;
        const criticalVulns = (error.stdout.match(/critical severity/g) || []).length;
        
        expect(highVulns + criticalVulns).toBe(0);
      }
    }
  });
});
```

## API Testing

### Contract Testing

```javascript
// tests/api/contracts/consciousness-api.contract.test.js
const { Pact } = require('@pact-foundation/pact');
const { ConsciousnessAPI } = require('../../../src/clients/consciousness-api');

describe('Consciousness API Contract', () => {
  const provider = new Pact({
    consumer: 'ConsciousnessClient',
    provider: 'ConsciousnessAPI',
    port: 1234,
    log: './logs/pact.log',
    dir: './pacts',
    logLevel: 'INFO'
  });

  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());

  describe('GET /consciousness/status', () => {
    beforeEach(() => {
      return provider.addInteraction({
        state: 'consciousness system is active',
        uponReceiving: 'a request for consciousness status',
        withRequest: {
          method: 'GET',
          path: '/api/v1/consciousness/status',
          headers: {
            'Authorization': 'Bearer valid_token'
          }
        },
        willRespondWith: {
          status: 200,
          headers: {
            'Content-Type': 'application/json'
          },
          body: {
            status: 'active',
            awareness_level: 0.85,
            emotional_state: {
              primary: 'calm',
              intensity: 0.6
            }
          }
        }
      });
    });

    it('should return consciousness status', async () => {
      const api = new ConsciousnessAPI('http://localhost:1234');
      const status = await api.getStatus();
      
      expect(status).toMatchObject({
        status: 'active',
        awareness_level: expect.any(Number),
        emotional_state: expect.objectContaining({
          primary: expect.any(String),
          intensity: expect.any(Number)
        })
      });
    });
  });
});
```

### Schema Validation Tests

```javascript
// tests/api/schemas/api-schema-validation.test.js
const Ajv = require('ajv');
const apiSchemas = require('../../../src/schemas/api-schemas.json');

describe('API Schema Validation', () => {
  const ajv = new Ajv();

  describe('Consciousness Status Schema', () => {
    const validate = ajv.compile(apiSchemas.ConsciousnessStatus);

    test('should validate correct status response', () => {
      const validStatus = {
        status: 'active',
        awareness_level: 0.85,
        emotional_state: {
          primary: 'calm',
          intensity: 0.6
        },
        timestamp: '2024-01-20T10:30:00Z'
      };

      const isValid = validate(validStatus);
      expect(isValid).toBe(true);
    });

    test('should reject invalid status response', () => {
      const invalidStatus = {
        status: 'invalid_status',
        awareness_level: 1.5, // Out of range
        emotional_state: {
          primary: 123, // Should be string
          intensity: 'high' // Should be number
        }
      };

      const isValid = validate(invalidStatus);
      expect(isValid).toBe(false);
      expect(validate.errors).toBeDefined();
    });
  });

  describe('Device Control Schema', () => {
    const validate = ajv.compile(apiSchemas.DeviceControlRequest);

    test('should validate device control request', () => {
      const validRequest = {
        action: 'set_brightness',
        value: 75,
        transition_time: 2000
      };

      const isValid = validate(validRequest);
      expect(isValid).toBe(true);
    });
  });
});
```

## WebSocket Testing

### WebSocket Connection Tests

```javascript
// tests/websocket/connection.test.js
const WebSocket = require('ws');
const { WebSocketServer } = require('../../../src/services/websocket-server');

describe('WebSocket Connection Tests', () => {
  let server;
  let wsServer;

  beforeAll(async () => {
    wsServer = new WebSocketServer({ port: 8080 });
    await wsServer.start();
  });

  afterAll(async () => {
    await wsServer.stop();
  });

  test('should establish WebSocket connection', (done) => {
    const ws = new WebSocket('ws://localhost:8080/v1/realtime');
    
    ws.on('open', () => {
      expect(ws.readyState).toBe(WebSocket.OPEN);
      ws.close();
      done();
    });

    ws.on('error', done);
  });

  test('should handle authentication', (done) => {
    const ws = new WebSocket('ws://localhost:8080/v1/realtime');
    
    ws.on('open', () => {
      ws.send(JSON.stringify({
        type: 'init',
        data: {
          auth_token: 'valid_token',
          subscriptions: ['consciousness', 'devices']
        }
      }));
    });

    ws.on('message', (data) => {
      const message = JSON.parse(data);
      
      if (message.type === 'auth_success') {
        expect(message.data.authenticated).toBe(true);
        ws.close();
        done();
      }
    });

    ws.on('error', done);
  });

  test('should receive real-time updates', (done) => {
    const ws = new WebSocket('ws://localhost:8080/v1/realtime');
    
    ws.on('open', () => {
      // Authenticate first
      ws.send(JSON.stringify({
        type: 'init',
        data: { auth_token: 'valid_token', subscriptions: ['consciousness'] }
      }));
    });

    ws.on('message', (data) => {
      const message = JSON.parse(data);
      
      if (message.type === 'consciousness_update') {
        expect(message.data).toHaveProperty('awareness_level');
        expect(message.data).toHaveProperty('emotional_state');
        ws.close();
        done();
      }
    });

    // Simulate consciousness update after connection
    setTimeout(() => {
      wsServer.broadcast({
        type: 'consciousness_update',
        data: {
          awareness_level: 0.87,
          emotional_state: { primary: 'attentive', intensity: 0.7 }
        }
      });
    }, 1000);
  });
});
```

## Test Data Management

### Test Fixtures

```javascript
// tests/fixtures/devices.js
const devices = {
  lights: [
    {
      id: 'light_001',
      name: 'Living Room Main Light',
      type: 'light',
      capabilities: ['on_off', 'dimming', 'color_temperature'],
      initial_state: { brightness: 80, color_temp: 3000, status: 'on' }
    },
    {
      id: 'light_002', 
      name: 'Bedroom Table Lamp',
      type: 'light',
      capabilities: ['on_off', 'dimming'],
      initial_state: { brightness: 40, status: 'on' }
    }
  ],
  
  climate: [
    {
      id: 'thermostat_001',
      name: 'Main Thermostat',
      type: 'thermostat',
      capabilities: ['temperature_control', 'mode_control', 'scheduling'],
      initial_state: { temperature: 21, mode: 'auto', target: 22 }
    }
  ],

  sensors: [
    {
      id: 'temp_sensor_001',
      name: 'Living Room Temperature',
      type: 'temperature_sensor',
      capabilities: ['temperature_reading', 'humidity_reading'],
      readings: { temperature: 21.5, humidity: 45, last_update: new Date() }
    }
  ]
};

module.exports = { devices };
```

### Test Data Generation

```javascript
// tests/utils/data-generator.js
const faker = require('faker');

class TestDataGenerator {
  static generateUser(overrides = {}) {
    return {
      id: faker.datatype.uuid(),
      username: faker.internet.email(),
      name: faker.name.findName(),
      created_at: faker.date.past(),
      preferences: {
        temperature: faker.datatype.number({ min: 18, max: 25 }),
        lighting: faker.datatype.number({ min: 0.2, max: 1.0 }),
        notifications: faker.datatype.boolean()
      },
      ...overrides
    };
  }

  static generateDevice(type = 'light', overrides = {}) {
    const baseDevice = {
      id: `${type}_${faker.datatype.uuid()}`,
      name: `${faker.commerce.productName()} ${type}`,
      type: type,
      location: faker.random.arrayElement(['living_room', 'bedroom', 'kitchen', 'bathroom']),
      status: faker.random.arrayElement(['online', 'offline', 'error']),
      last_seen: faker.date.recent(),
      firmware_version: faker.system.semver()
    };

    const typeSpecificData = {
      light: {
        capabilities: ['on_off', 'dimming', 'color_temperature'],
        state: {
          brightness: faker.datatype.number({ min: 0, max: 100 }),
          color_temp: faker.datatype.number({ min: 2700, max: 6500 }),
          status: faker.random.arrayElement(['on', 'off'])
        }
      },
      thermostat: {
        capabilities: ['temperature_control', 'mode_control'],
        state: {
          current_temp: faker.datatype.number({ min: 15, max: 30 }),
          target_temp: faker.datatype.number({ min: 18, max: 25 }),
          mode: faker.random.arrayElement(['heat', 'cool', 'auto', 'off'])
        }
      }
    };

    return {
      ...baseDevice,
      ...typeSpecificData[type],
      ...overrides
    };
  }

  static generateConsciousnessState(overrides = {}) {
    return {
      status: faker.random.arrayElement(['active', 'standby', 'processing']),
      awareness_level: faker.datatype.float({ min: 0, max: 1, precision: 0.01 }),
      emotional_state: {
        primary: faker.random.arrayElement(['calm', 'curious', 'attentive', 'concerned', 'satisfied']),
        secondary: faker.random.arrayElements(['helpful', 'optimistic', 'analytical'], 2),
        intensity: faker.datatype.float({ min: 0, max: 1, precision: 0.01 })
      },
      active_processes: faker.datatype.number({ min: 0, max: 10 }),
      memory_usage: faker.datatype.float({ min: 0.1, max: 0.9, precision: 0.01 }),
      last_update: new Date(),
      ...overrides
    };
  }

  static generateMemory(type = 'pattern', overrides = {}) {
    return {
      id: faker.datatype.uuid(),
      type: type,
      content: faker.lorem.sentence(),
      confidence: faker.datatype.float({ min: 0, max: 1, precision: 0.01 }),
      created_at: faker.date.past(),
      last_accessed: faker.date.recent(),
      access_count: faker.datatype.number({ min: 1, max: 100 }),
      context: {
        location: faker.random.arrayElement(['living_room', 'bedroom', 'kitchen']),
        time_of_day: faker.random.arrayElement(['morning', 'afternoon', 'evening', 'night']),
        user_present: faker.datatype.boolean()
      },
      ...overrides
    };
  }
}

module.exports = { TestDataGenerator };
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: consciousness_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run unit tests
      run: npm run test:unit
      env:
        NODE_ENV: test
        DATABASE_URL: postgresql://postgres:test_password@localhost:5432/consciousness_test
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Start test services
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30
    
    - name: Run integration tests
      run: npm run test:integration
    
    - name: Stop test services
      run: docker-compose -f docker-compose.test.yml down

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Install Playwright
      run: npx playwright install --with-deps
    
    - name: Start application
      run: |
        npm start &
        sleep 10
    
    - name: Run E2E tests
      run: npm run test:e2e
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Install k6
      run: |
        sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    
    - name: Start application
      run: |
        npm start &
        sleep 10
    
    - name: Run performance tests
      run: npm run test:performance

  security-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Snyk security scan
      uses: snyk/actions/node@master
      env:
        SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      with:
        args: --severity-threshold=high
    
    - name: Run npm audit
      run: npm audit --audit-level=moderate
```

## Monitoring & Reporting

### Test Results Dashboard

```javascript
// tests/utils/test-reporter.js
class TestReporter {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      coverage: {},
      performance: {},
      security: {}
    };
  }

  recordTestResult(test, result) {
    this.results.total++;
    
    switch (result.status) {
      case 'passed':
        this.results.passed++;
        break;
      case 'failed':
        this.results.failed++;
        break;
      case 'skipped':
        this.results.skipped++;
        break;
    }
  }

  recordCoverage(coverage) {
    this.results.coverage = {
      lines: coverage.lines.pct,
      functions: coverage.functions.pct,
      branches: coverage.branches.pct,
      statements: coverage.statements.pct
    };
  }

  recordPerformanceMetrics(metrics) {
    this.results.performance = {
      avgResponseTime: metrics.avgResponseTime,
      p95ResponseTime: metrics.p95ResponseTime,
      throughput: metrics.throughput,
      errorRate: metrics.errorRate
    };
  }

  generateReport() {
    const passRate = (this.results.passed / this.results.total * 100).toFixed(2);
    
    return {
      summary: {
        total: this.results.total,
        passed: this.results.passed,
        failed: this.results.failed,
        skipped: this.results.skipped,
        passRate: `${passRate}%`
      },
      coverage: this.results.coverage,
      performance: this.results.performance,
      security: this.results.security,
      timestamp: new Date().toISOString()
    };
  }

  async publishReport(destination) {
    const report = this.generateReport();
    
    // Send to monitoring dashboard
    await fetch(destination, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(report)
    });
  }
}

module.exports = { TestReporter };
```

### Quality Gates

```javascript
// tests/utils/quality-gates.js
class QualityGates {
  static checkCoverageThresholds(coverage) {
    const thresholds = {
      lines: 80,
      functions: 80,
      branches: 75,
      statements: 80
    };

    const failures = [];
    
    Object.keys(thresholds).forEach(metric => {
      if (coverage[metric] < thresholds[metric]) {
        failures.push(`${metric} coverage ${coverage[metric]}% below threshold ${thresholds[metric]}%`);
      }
    });

    return {
      passed: failures.length === 0,
      failures
    };
  }

  static checkPerformanceThresholds(metrics) {
    const thresholds = {
      avgResponseTime: 500, // ms
      p95ResponseTime: 1000, // ms
      errorRate: 0.01 // 1%
    };

    const failures = [];
    
    if (metrics.avgResponseTime > thresholds.avgResponseTime) {
      failures.push(`Average response time ${metrics.avgResponseTime}ms exceeds ${thresholds.avgResponseTime}ms`);
    }
    
    if (metrics.p95ResponseTime > thresholds.p95ResponseTime) {
      failures.push(`P95 response time ${metrics.p95ResponseTime}ms exceeds ${thresholds.p95ResponseTime}ms`);
    }
    
    if (metrics.errorRate > thresholds.errorRate) {
      failures.push(`Error rate ${(metrics.errorRate * 100).toFixed(2)}% exceeds ${(thresholds.errorRate * 100)}%`);
    }

    return {
      passed: failures.length === 0,
      failures
    };
  }

  static checkSecurityThresholds(vulnerabilities) {
    const maxVulnerabilities = {
      critical: 0,
      high: 0,
      medium: 5
    };

    const failures = [];
    
    Object.keys(maxVulnerabilities).forEach(severity => {
      const count = vulnerabilities[severity] || 0;
      if (count > maxVulnerabilities[severity]) {
        failures.push(`${count} ${severity} severity vulnerabilities found (max: ${maxVulnerabilities[severity]})`);
      }
    });

    return {
      passed: failures.length === 0,
      failures
    };
  }
}

module.exports = { QualityGates };
```

## Conclusion

This comprehensive testing implementation guide ensures robust quality assurance for the consciousness system. The multi-layered testing approach covers all components from individual units to full system scenarios, while continuous monitoring and quality gates maintain high standards throughout the development lifecycle.

Key benefits of this testing strategy:
- **Comprehensive Coverage**: Unit, integration, E2E, performance, security, and digital twin testing
- **Twin Validation**: Rigorous testing of twin synchronization, prediction accuracy, and scenario simulation
- **Real-time Validation**: WebSocket and API testing for live system validation
- **Physics Accuracy**: Validation of physics-based models for realistic twin behavior
- **Automated Quality Gates**: Continuous monitoring of coverage, performance, and security thresholds
- **Production Readiness**: Stress testing and monitoring ensure system reliability under load
- **Security Assurance**: Multiple layers of security testing protect against vulnerabilities
- **Scenario Coverage**: Comprehensive testing of emergency and edge-case scenarios through twin simulation

The enhanced testing framework provides confidence in both physical system reliability and digital twin accuracy, enabling rapid development and deployment of consciousness system features with validated predictive capabilities.