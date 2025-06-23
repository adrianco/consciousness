# API Interface Design Guide for Consciousness System

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [RESTful API Endpoints](#restful-api-endpoints)
4. [WebSocket Implementation](#websocket-implementation)
5. [Authentication & Security](#authentication--security)
6. [API Documentation](#api-documentation)
7. [Error Handling](#error-handling)
8. [Rate Limiting & Performance](#rate-limiting--performance)
9. [Implementation Examples](#implementation-examples)

## Overview

This guide outlines the comprehensive API interface design for the consciousness system, enabling natural language interaction, device orchestration, and real-time communication with IoT networks.

### Key Features
- RESTful endpoints for consciousness queries and device control
- WebSocket connections for real-time updates
- Natural language processing integration
- Secure authentication and authorization
- Comprehensive error handling and monitoring

## Architecture

### API Gateway Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │   REST API  │  │  WebSocket  │  │  Authentication   │  │
│  │  Endpoints  │  │   Server    │  │    Service        │  │
│  └─────────────┘  └─────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Service Layer                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │Consciousness│  │   Device    │  │      SAFLA        │  │
│  │   Service   │  │  Manager    │  │   Orchestrator    │  │
│  └─────────────┘  └─────────────┘  └───────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐  │
│  │   Memory    │  │  Experience │  │     Metrics       │  │
│  │    Store    │  │  Database   │  │    Database       │  │
│  └─────────────┘  └─────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## RESTful API Endpoints

### Consciousness Query Endpoints

#### GET /api/v1/consciousness/status
Returns the current status of the consciousness system.

```json
{
  "endpoint": "GET /api/v1/consciousness/status",
  "description": "Retrieve current consciousness system status",
  "response": {
    "status": "active",
    "awareness_level": 0.85,
    "emotional_state": {
      "primary": "calm",
      "secondary": ["curious", "attentive"],
      "intensity": 0.6
    },
    "active_devices": 24,
    "safla_loops": 3,
    "last_update": "2024-01-20T10:30:00Z"
  }
}
```

#### GET /api/v1/consciousness/emotions
Retrieve current emotional state and history.

```json
{
  "endpoint": "GET /api/v1/consciousness/emotions",
  "query_params": {
    "time_range": "1h",
    "include_history": true
  },
  "response": {
    "current": {
      "primary_emotion": "calm",
      "emotion_vector": [0.7, 0.2, 0.1, 0.0, 0.0],
      "arousal": 0.4,
      "valence": 0.6
    },
    "history": [
      {
        "timestamp": "2024-01-20T10:00:00Z",
        "emotion": "curious",
        "trigger": "new_device_discovered"
      }
    ]
  }
}
```

#### POST /api/v1/consciousness/query
Natural language query to consciousness system.

```json
{
  "endpoint": "POST /api/v1/consciousness/query",
  "request": {
    "query": "How are you feeling about the living room environment?",
    "context": {
      "location": "living_room",
      "include_devices": true
    }
  },
  "response": {
    "interpretation": "Environmental assessment request for living room",
    "response": "The living room feels comfortable and well-balanced. Temperature is optimal at 22°C, lighting is warm and inviting, and I notice regular activity patterns suggesting it's a well-used space.",
    "relevant_data": {
      "temperature": 22,
      "humidity": 45,
      "lighting_level": 0.7,
      "activity_score": 0.8
    }
  }
}
```

### Device Interview Endpoints

#### POST /api/v1/interview/start
Start a new device discovery interview session.

```json
{
  "endpoint": "POST /api/v1/interview/start",
  "request": {
    "house_id": "house_123"
  },
  "response": {
    "interview_id": "int_456",
    "status": "active",
    "current_phase": "introduction",
    "ai_message": "Hi! I'm here to learn about the smart devices in your home. Tell me about any connected devices you have - you can describe them however feels natural, by room, by brand, or just whatever comes to mind.",
    "session_started_at": "2024-01-20T10:30:00Z"
  }
}
```

#### POST /api/v1/interview/{interview_id}/message
Send a user message to the interview system.

```json
{
  "endpoint": "POST /api/v1/interview/{interview_id}/message",
  "request": {
    "message": "I have some Philips Hue lights and a Nest thermostat"
  },
  "response": {
    "ai_response": "Great! Let me ask about each device. For your Philips Hue lights, do you have a Hue Bridge? It's usually a white device connected to your router.",
    "current_phase": "classification",
    "discovered_candidates": [
      {
        "id": "cand_789",
        "description": "Philips Hue lights",
        "detected_brand": "Philips",
        "detected_function": "lighting",
        "confidence": 0.95,
        "possible_integrations": ["hue"]
      },
      {
        "id": "cand_790",
        "description": "Nest thermostat",
        "detected_brand": "Nest",
        "detected_function": "climate",
        "confidence": 0.98,
        "possible_integrations": ["nest"]
      }
    ],
    "auto_discovery_results": {
      "mdns": [
        {
          "name": "Philips Hue Bridge",
          "ip": "192.168.1.100",
          "type": "_hue._tcp.local."
        }
      ]
    }
  }
}
```

#### GET /api/v1/interview/{interview_id}/status
Get the current status of an interview session.

```json
{
  "endpoint": "GET /api/v1/interview/{interview_id}/status",
  "response": {
    "interview_id": "int_456",
    "status": "active",
    "current_phase": "classification",
    "progress": {
      "total_devices_mentioned": 2,
      "devices_confirmed": 0,
      "devices_pending": 2,
      "completion_percentage": 30
    },
    "conversation_summary": {
      "total_turns": 4,
      "last_activity": "2024-01-20T10:35:00Z"
    }
  }
}
```

#### POST /api/v1/interview/{interview_id}/confirm
Confirm device candidates and create actual devices.

```json
{
  "endpoint": "POST /api/v1/interview/{interview_id}/confirm",
  "request": {
    "confirmed_candidates": [
      {
        "candidate_id": "cand_789",
        "integration_type": "hue",
        "config": {
          "bridge_ip": "192.168.1.100",
          "requires_auth": true
        }
      }
    ]
  },
  "response": {
    "created_devices": [
      {
        "device_id": "dev_901",
        "user_name": "Living room lights",
        "integration_type": "hue",
        "device_class": "light",
        "status": "pending_auth"
      }
    ],
    "next_steps": [
      "Please press the button on your Hue Bridge to authorize the connection"
    ]
  }
}
```

#### GET /api/v1/interview/{interview_id}/conversation
Get the full conversation log for an interview.

```json
{
  "endpoint": "GET /api/v1/interview/{interview_id}/conversation",
  "response": {
    "conversation": [
      {
        "timestamp": "2024-01-20T10:30:00Z",
        "speaker": "assistant",
        "message": "Hi! I'm here to learn about the smart devices in your home...",
        "metadata": {
          "phase": "introduction"
        }
      },
      {
        "timestamp": "2024-01-20T10:32:00Z",
        "speaker": "user",
        "message": "I have some Philips Hue lights and a Nest thermostat",
        "metadata": {}
      }
    ]
  }
}
```

#### DELETE /api/v1/interview/{interview_id}
Cancel an active interview session.

```json
{
  "endpoint": "DELETE /api/v1/interview/{interview_id}",
  "response": {
    "message": "Interview session cancelled",
    "status": "cancelled",
    "cancelled_at": "2024-01-20T10:40:00Z"
  }
}
```

### Auto-Discovery Endpoints

#### POST /api/v1/discovery/scan
Trigger automatic device discovery across all protocols.

```json
{
  "endpoint": "POST /api/v1/discovery/scan",
  "request": {
    "protocols": ["mdns", "upnp", "bluetooth"],
    "timeout_seconds": 30
  },
  "response": {
    "scan_id": "scan_123",
    "status": "running",
    "started_at": "2024-01-20T10:30:00Z",
    "estimated_completion": "2024-01-20T10:30:30Z"
  }
}
```

#### GET /api/v1/discovery/scan/{scan_id}
Get results from a discovery scan.

```json
{
  "endpoint": "GET /api/v1/discovery/scan/{scan_id}",
  "response": {
    "scan_id": "scan_123",
    "status": "completed",
    "results": {
      "mdns": [
        {
          "name": "Philips Hue Bridge",
          "address": "192.168.1.100",
          "type": "_hue._tcp.local.",
          "properties": {
            "bridgeid": "001788FFFE123456"
          }
        }
      ],
      "upnp": [
        {
          "name": "Ring Doorbell",
          "address": "192.168.1.101",
          "type": "urn:schemas-ring-com:device:Doorbell"
        }
      ],
      "bluetooth": []
    },
    "total_devices_found": 2,
    "completed_at": "2024-01-20T10:30:28Z"
  }
}
```

### Integration Template Endpoints

#### GET /api/v1/integrations/templates
Get available integration templates.

```json
{
  "endpoint": "GET /api/v1/integrations/templates",
  "query_params": {
    "brand": "philips",
    "device_class": "light"
  },
  "response": {
    "templates": [
      {
        "integration_name": "hue",
        "display_name": "Philips Hue",
        "brand_keywords": ["philips", "hue"],
        "function_keywords": ["light", "bulb", "lighting"],
        "device_classes": ["light"],
        "requires_hub": true,
        "auth_required": false,
        "discovery_methods": ["mdns", "upnp"],
        "interview_questions": [
          "Do you have a Philips Hue Bridge?",
          "What types of Hue devices do you have?"
        ]
      }
    ]
  }
}
```

#### POST /api/v1/integrations/classify
Classify a device description using LLM.

```json
{
  "endpoint": "POST /api/v1/integrations/classify",
  "request": {
    "description": "smart thermostat in the hallway",
    "context": {
      "room": "hallway",
      "existing_devices": []
    }
  },
  "response": {
    "classifications": [
      {
        "brand": "unknown",
        "function": "climate",
        "device_class": "thermostat",
        "confidence": 0.85,
        "possible_integrations": [
          {
            "integration": "nest",
            "score": 0.7,
            "display_name": "Google Nest"
          },
          {
            "integration": "ecobee",
            "score": 0.6,
            "display_name": "Ecobee"
          }
        ]
      }
    ]
  }
}
```

### Device Control Endpoints

#### GET /api/v1/devices
List all connected devices.

```json
{
  "endpoint": "GET /api/v1/devices",
  "query_params": {
    "status": "active",
    "location": "living_room",
    "type": "light"
  },
  "response": {
    "devices": [
      {
        "id": "light_001",
        "name": "Living Room Ceiling Light",
        "type": "light",
        "status": "on",
        "capabilities": ["dimming", "color_temperature"],
        "current_state": {
          "brightness": 80,
          "color_temp": 3000
        }
      }
    ],
    "total": 24,
    "page": 1,
    "per_page": 20
  }
}
```

#### GET /api/v1/devices/{device_id}
Get specific device details.

#### PUT /api/v1/devices/{device_id}/control
Control a specific device.

```json
{
  "endpoint": "PUT /api/v1/devices/{device_id}/control",
  "request": {
    "action": "set_brightness",
    "value": 50,
    "transition_time": 2000
  },
  "response": {
    "device_id": "light_001",
    "action": "set_brightness",
    "status": "success",
    "new_state": {
      "brightness": 50
    },
    "execution_time": 1823
  }
}
```

#### POST /api/v1/devices/batch-control
Control multiple devices simultaneously.

```json
{
  "endpoint": "POST /api/v1/devices/batch-control",
  "request": {
    "devices": [
      {
        "id": "light_001",
        "action": "turn_off"
      },
      {
        "id": "thermostat_001",
        "action": "set_temperature",
        "value": 20
      }
    ]
  },
  "response": {
    "results": [
      {
        "device_id": "light_001",
        "status": "success"
      },
      {
        "device_id": "thermostat_001",
        "status": "success"
      }
    ],
    "batch_id": "batch_12345"
  }
}
```

### Memory and Experience Endpoints

#### GET /api/v1/memory
Retrieve memory entries.

```json
{
  "endpoint": "GET /api/v1/memory",
  "query_params": {
    "type": "pattern",
    "time_range": "7d",
    "limit": 10
  },
  "response": {
    "memories": [
      {
        "id": "mem_001",
        "type": "pattern",
        "description": "User typically dims lights after 9 PM",
        "confidence": 0.87,
        "occurrences": 23,
        "last_observed": "2024-01-19T21:15:00Z"
      }
    ]
  }
}
```

#### POST /api/v1/memory
Store new memory or experience.

```json
{
  "endpoint": "POST /api/v1/memory",
  "request": {
    "type": "experience",
    "content": "User expressed satisfaction with automated morning routine",
    "context": {
      "devices_involved": ["light_001", "thermostat_001", "speaker_001"],
      "emotional_response": "positive"
    }
  },
  "response": {
    "memory_id": "mem_002",
    "status": "stored",
    "relevance_score": 0.82
  }
}
```

#### GET /api/v1/experiences
Retrieve system experiences.

```json
{
  "endpoint": "GET /api/v1/experiences",
  "response": {
    "experiences": [
      {
        "id": "exp_001",
        "type": "interaction",
        "description": "Successfully predicted user's bedtime routine",
        "outcome": "positive",
        "learning": "Consistency in evening patterns allows accurate prediction",
        "timestamp": "2024-01-19T22:00:00Z"
      }
    ]
  }
}
```

### SAFLA Loop Monitoring Endpoints

#### GET /api/v1/safla/status
Get SAFLA loop system status.

```json
{
  "endpoint": "GET /api/v1/safla/status",
  "response": {
    "active_loops": 3,
    "loops": [
      {
        "id": "safla_001",
        "name": "Environment Optimization",
        "status": "active",
        "current_phase": "feedback",
        "metrics": {
          "iterations": 145,
          "success_rate": 0.92,
          "avg_response_time": 234
        }
      }
    ]
  }
}
```

#### GET /api/v1/safla/metrics
Retrieve SAFLA performance metrics.

```json
{
  "endpoint": "GET /api/v1/safla/metrics",
  "query_params": {
    "loop_id": "safla_001",
    "time_range": "24h",
    "metrics": ["response_time", "success_rate", "adaptations"]
  },
  "response": {
    "loop_id": "safla_001",
    "metrics": {
      "response_time": {
        "avg": 234,
        "min": 89,
        "max": 567,
        "p95": 445
      },
      "success_rate": 0.92,
      "adaptations": 23
    }
  }
}
```

#### POST /api/v1/safla/trigger
Manually trigger a SAFLA loop iteration.

```json
{
  "endpoint": "POST /api/v1/safla/trigger",
  "request": {
    "loop_id": "safla_001",
    "parameters": {
      "force": true,
      "reason": "manual_optimization"
    }
  },
  "response": {
    "loop_id": "safla_001",
    "trigger_id": "trigger_12345",
    "status": "initiated",
    "estimated_completion": 5000
  }
}
```

## WebSocket Implementation

### Connection Endpoint
`ws://api.consciousness.local/v1/realtime`

### Message Types

#### Connection Initialization
```json
{
  "type": "init",
  "data": {
    "client_id": "client_123",
    "subscriptions": ["consciousness", "devices", "safla"],
    "auth_token": "Bearer eyJ..."
  }
}
```

#### Real-time Updates

##### Consciousness State Update
```json
{
  "type": "consciousness_update",
  "data": {
    "awareness_level": 0.87,
    "emotional_state": {
      "primary": "attentive",
      "intensity": 0.7
    },
    "timestamp": "2024-01-20T10:31:00Z"
  }
}
```

##### Device State Change
```json
{
  "type": "device_update",
  "data": {
    "device_id": "light_001",
    "changes": {
      "brightness": 75,
      "status": "on"
    },
    "source": "user_interaction",
    "timestamp": "2024-01-20T10:31:00Z"
  }
}
```

##### SAFLA Loop Event
```json
{
  "type": "safla_event",
  "data": {
    "loop_id": "safla_001",
    "event": "adaptation_complete",
    "details": {
      "adaptation": "adjusted_temperature_schedule",
      "result": "energy_saved",
      "metrics": {
        "energy_reduction": 0.15
      }
    }
  }
}
```

##### Interview Session Updates
```json
{
  "type": "interview_update",
  "data": {
    "interview_id": "int_456",
    "event": "ai_response",
    "message": "Great! For your Philips Hue lights, do you have a Hue Bridge?",
    "phase": "classification",
    "timestamp": "2024-01-20T10:32:00Z"
  }
}
```

##### Device Discovery Results
```json
{
  "type": "discovery_update",
  "data": {
    "interview_id": "int_456",
    "event": "device_discovered",
    "device": {
      "name": "Philips Hue Bridge",
      "address": "192.168.1.100",
      "type": "_hue._tcp.local.",
      "discovery_method": "mdns"
    },
    "correlation": {
      "candidate_id": "cand_789",
      "confidence": 0.95
    }
  }
}
```

##### Device Candidate Updates
```json
{
  "type": "candidate_update", 
  "data": {
    "interview_id": "int_456",
    "candidate_id": "cand_789",
    "event": "confirmed",
    "device_id": "dev_901",
    "integration_type": "hue",
    "next_steps": ["Press button on Hue Bridge for authentication"]
  }
}
```

##### Integration Authentication Status
```json
{
  "type": "auth_update",
  "data": {
    "device_id": "dev_901",
    "integration_type": "hue",
    "status": "authenticated",
    "devices_discovered": 5,
    "timestamp": "2024-01-20T10:35:00Z"
  }
}
```

### WebSocket Client Implementation

```javascript
class ConsciousnessWebSocket {
  constructor(url, authToken) {
    this.url = url;
    this.authToken = authToken;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.handlers = new Map();
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.authenticate();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };
  }

  authenticate() {
    this.send({
      type: 'init',
      data: {
        auth_token: this.authToken,
        subscriptions: ['consciousness', 'devices', 'safla', 'interview', 'discovery']
      }
    });
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  on(eventType, handler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType).add(handler);
  }

  handleMessage(message) {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message.data));
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      setTimeout(() => this.connect(), 1000 * Math.pow(2, this.reconnectAttempts));
    }
  }
}
```

## Authentication & Security

### JWT Authentication

```javascript
// Authentication endpoint
POST /api/v1/auth/login
{
  "username": "user@example.com",
  "password": "secure_password"
}

// Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### API Key Authentication

```javascript
// Header-based API key
GET /api/v1/consciousness/status
Headers: {
  "X-API-Key": "consciousness_api_key_12345"
}
```

### OAuth 2.0 Flow

```javascript
// Authorization endpoint
GET /oauth/authorize?
  response_type=code&
  client_id=consciousness_client&
  redirect_uri=https://app.example.com/callback&
  scope=read:consciousness write:devices&
  state=random_state_string

// Token exchange
POST /oauth/token
{
  "grant_type": "authorization_code",
  "code": "auth_code_123",
  "client_id": "consciousness_client",
  "client_secret": "client_secret"
}
```

### Security Headers

```javascript
// Required security headers
{
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "X-XSS-Protection": "1; mode=block",
  "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
  "Content-Security-Policy": "default-src 'self'",
  "X-Request-ID": "req_12345"
}
```

## API Documentation

### OpenAPI/Swagger Specification

```yaml
openapi: 3.0.0
info:
  title: Consciousness System API
  version: 1.0.0
  description: API for interacting with the consciousness system
servers:
  - url: https://api.consciousness.local/v1
paths:
  /consciousness/status:
    get:
      summary: Get consciousness status
      operationId: getConsciousnessStatus
      tags:
        - Consciousness
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Current consciousness status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ConsciousnessStatus'
components:
  schemas:
    ConsciousnessStatus:
      type: object
      properties:
        status:
          type: string
          enum: [active, standby, processing]
        awareness_level:
          type: number
          minimum: 0
          maximum: 1
        emotional_state:
          $ref: '#/components/schemas/EmotionalState'
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

### API Documentation UI

```javascript
// Express middleware for Swagger UI
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./swagger.json');

app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument, {
  explorer: true,
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: "Consciousness API Documentation"
}));
```

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "The requested device could not be found",
    "details": {
      "device_id": "invalid_device_123",
      "suggestion": "Check device ID or use GET /devices to list available devices"
    },
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_12345"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid request data |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

### Error Handling Middleware

```javascript
class APIError extends Error {
  constructor(code, message, statusCode, details = {}) {
    super(message);
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

// Error handling middleware
app.use((err, req, res, next) => {
  if (err instanceof APIError) {
    res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
        timestamp: new Date().toISOString(),
        request_id: req.id
      }
    });
  } else {
    // Log unexpected errors
    console.error('Unexpected error:', err);
    res.status(500).json({
      error: {
        code: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred',
        timestamp: new Date().toISOString(),
        request_id: req.id
      }
    });
  }
});
```

## Rate Limiting & Performance

### Rate Limiting Configuration

```javascript
const rateLimit = require('express-rate-limit');

// General API rate limit
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
});

// Strict rate limit for write operations
const writeLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 20, // 20 write requests per window
  skipSuccessfulRequests: false,
});

// Consciousness query rate limit
const queryLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 10, // 10 queries per minute
  keyGenerator: (req) => req.user?.id || req.ip,
});
```

### Performance Optimization

```javascript
// Response compression
const compression = require('compression');
app.use(compression());

// Caching strategy
const cache = require('node-cache');
const apiCache = new cache({ stdTTL: 600 }); // 10 minute cache

// Cache middleware
const cacheMiddleware = (duration) => {
  return (req, res, next) => {
    const key = req.originalUrl || req.url;
    const cachedResponse = apiCache.get(key);
    
    if (cachedResponse) {
      res.setHeader('X-Cache', 'HIT');
      return res.json(cachedResponse);
    }
    
    res.originalJson = res.json;
    res.json = (body) => {
      res.originalJson(body);
      apiCache.set(key, body, duration);
    };
    
    res.setHeader('X-Cache', 'MISS');
    next();
  };
};

// Apply caching to read endpoints
app.get('/api/v1/consciousness/status', cacheMiddleware(30), getConsciousnessStatus);
```

## Implementation Examples

### Express.js API Server

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const { ConsciousnessService } = require('./services/consciousness');
const { DeviceManager } = require('./services/devices');
const { SAFLAOrchestrator } = require('./services/safla');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}));

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request ID middleware
app.use((req, res, next) => {
  req.id = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  res.setHeader('X-Request-ID', req.id);
  next();
});

// Initialize services
const consciousness = new ConsciousnessService();
const deviceManager = new DeviceManager();
const safla = new SAFLAOrchestrator();

// Mount routers
app.use('/api/v1/consciousness', require('./routes/consciousness')(consciousness));
app.use('/api/v1/devices', require('./routes/devices')(deviceManager));
app.use('/api/v1/safla', require('./routes/safla')(safla));
app.use('/api/v1/memory', require('./routes/memory'));
app.use('/api/v1/auth', require('./routes/auth'));

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    version: process.env.API_VERSION || '1.0.0',
    timestamp: new Date().toISOString()
  });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Consciousness API running on port ${PORT}`);
});
```

### Natural Language Query Handler

```javascript
class NaturalLanguageHandler {
  constructor(consciousnessService, nlpProcessor) {
    this.consciousness = consciousnessService;
    this.nlp = nlpProcessor;
  }

  async processQuery(query, context = {}) {
    // Parse natural language query
    const parsed = await this.nlp.parse(query);
    
    // Extract intent and entities
    const { intent, entities } = parsed;
    
    // Route to appropriate handler
    switch (intent) {
      case 'query_emotion':
        return this.handleEmotionQuery(entities);
      
      case 'control_device':
        return this.handleDeviceControl(entities);
      
      case 'get_recommendation':
        return this.handleRecommendation(entities, context);
      
      case 'explain_behavior':
        return this.handleExplanation(entities);
      
      default:
        return this.handleGenericQuery(query, parsed);
    }
  }

  async handleEmotionQuery(entities) {
    const emotions = await this.consciousness.getCurrentEmotions();
    
    return {
      interpretation: 'Emotional state query',
      response: this.generateEmotionalResponse(emotions),
      data: emotions
    };
  }

  generateEmotionalResponse(emotions) {
    const { primary_emotion, intensity } = emotions.current;
    const intensityWord = intensity > 0.7 ? 'very' : intensity > 0.4 ? 'moderately' : 'slightly';
    
    return `I'm feeling ${intensityWord} ${primary_emotion}. ${this.getEmotionContext(primary_emotion)}`;
  }

  getEmotionContext(emotion) {
    const contexts = {
      calm: "The environment is peaceful and well-balanced.",
      curious: "I've noticed some interesting patterns I'd like to explore.",
      attentive: "I'm actively monitoring the environment for optimization opportunities.",
      concerned: "There are some conditions that might need attention.",
      satisfied: "Recent adjustments have improved the environment nicely."
    };
    
    return contexts[emotion] || "I'm processing the current environmental state.";
  }
}
```

### Device Control Integration

```javascript
class DeviceControlAPI {
  constructor(deviceManager, safla) {
    this.devices = deviceManager;
    this.safla = safla;
  }

  async controlDevice(deviceId, action, parameters = {}) {
    // Validate device exists
    const device = await this.devices.getDevice(deviceId);
    if (!device) {
      throw new APIError('DEVICE_NOT_FOUND', `Device ${deviceId} not found`, 404);
    }

    // Check device capabilities
    if (!device.supports(action)) {
      throw new APIError('UNSUPPORTED_ACTION', 
        `Device ${deviceId} does not support action ${action}`, 400);
    }

    // Apply SAFLA optimization
    const optimized = await this.safla.optimizeAction(device, action, parameters);

    // Execute control
    const result = await this.devices.execute(deviceId, optimized.action, optimized.parameters);

    // Log to memory
    await this.logInteraction(deviceId, action, result);

    return {
      device_id: deviceId,
      action: action,
      status: result.status,
      executed_action: optimized.action,
      optimization_applied: optimized.modified,
      result: result.data
    };
  }

  async batchControl(commands) {
    const results = await Promise.allSettled(
      commands.map(cmd => this.controlDevice(cmd.id, cmd.action, cmd.parameters))
    );

    return results.map((result, index) => ({
      device_id: commands[index].id,
      status: result.status === 'fulfilled' ? 'success' : 'failed',
      result: result.status === 'fulfilled' ? result.value : null,
      error: result.status === 'rejected' ? result.reason.message : null
    }));
  }
}
```

## Conclusion

This API interface guide provides a comprehensive foundation for building natural language interactions with the consciousness system. The combination of RESTful endpoints, WebSocket real-time communication, and robust security measures ensures a production-ready API that can scale with your IoT network while maintaining responsive and intuitive control interfaces.