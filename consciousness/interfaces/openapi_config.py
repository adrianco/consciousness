"""
OpenAPI configuration and documentation for the Consciousness System API.
"""

from typing import Any, Dict

# OpenAPI metadata
OPENAPI_METADATA = {
    "title": "Consciousness System API",
    "description": """
# AI-Powered House Consciousness System API

This API provides comprehensive access to an AI-powered house consciousness system that enables:

- **Natural Language Interaction**: Query and control your home using natural language
- **Device Orchestration**: Manage and control smart home devices across multiple protocols
- **Digital Twin Management**: Create and manage digital twins of your devices for simulation and prediction
- **Real-time Communication**: WebSocket connections for live updates and monitoring
- **SAFLA Loop Integration**: Access to the Sense-Analyze-Feel-Learn-Act cognitive loops
- **Scenario Testing**: Run simulations and what-if analyses on your home environment

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include your token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Real-time Updates

Connect to the WebSocket endpoint at `/api/v1/realtime` for real-time system updates including:
- Consciousness state changes
- Device status updates
- SAFLA loop events
- Interview session progress
- Discovery results

## Rate Limiting

API endpoints are rate-limited to ensure system stability:
- General endpoints: 100 requests per 15 minutes
- Write operations: 20 requests per 5 minutes
- Consciousness queries: 10 requests per minute

## Error Handling

All errors follow a consistent format with structured error codes and helpful messages.
See the error handling section for details on specific error codes and recovery strategies.

## Workflow Examples

### Device Discovery Workflow
1. Start interview session: `POST /api/v1/interview/start`
2. Send user messages: `POST /api/v1/interview/{id}/message`
3. Confirm devices: `POST /api/v1/interview/{id}/confirm`
4. Monitor via WebSocket for real-time updates

### Digital Twin Simulation
1. Create digital twin: `POST /api/v1/twins`
2. Run scenario: `POST /api/v1/scenarios`
3. Analyze results: `POST /api/v1/predictions/what-if`

### Natural Language Control
1. Send consciousness query: `POST /api/v1/consciousness/query`
2. Monitor emotional responses: `GET /api/v1/consciousness/emotions`
3. Track system status: `GET /api/v1/consciousness/status`
    """,
    "version": "1.0.0",
    "contact": {
        "name": "Consciousness System Support",
        "email": "support@consciousness.local",
        "url": "https://consciousness.local/support",
    },
    "license": {
        "name": "Apache License 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
    "servers": [
        {
            "url": "https://api.consciousness.local/v1",
            "description": "Production API Server",
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development API Server",
        },
    ],
}

# OpenAPI tags for endpoint organization
OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": "User authentication and authorization endpoints",
    },
    {
        "name": "Consciousness",
        "description": "Core consciousness system status and natural language interaction",
    },
    {"name": "Devices", "description": "Smart device management and control"},
    {"name": "Interview", "description": "Device discovery interview system"},
    {"name": "Discovery", "description": "Automatic device discovery across protocols"},
    {
        "name": "Integrations",
        "description": "Device integration templates and classification",
    },
    {"name": "Memory", "description": "System memory and experience management"},
    {"name": "SAFLA", "description": "SAFLA loop monitoring and control"},
    {"name": "Digital Twins", "description": "Digital twin creation and management"},
    {"name": "Scenarios", "description": "Scenario simulation and testing"},
    {"name": "Predictions", "description": "Predictive analysis and what-if scenarios"},
    {"name": "Real-time", "description": "WebSocket real-time communication"},
    {"name": "System", "description": "System health and diagnostics"},
]

# Security schemes
SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token obtained from /auth/login endpoint",
    },
    "apiKey": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key for service-to-service authentication",
    },
}

# Example responses for documentation
EXAMPLE_RESPONSES = {
    "consciousness_status": {
        "description": "Consciousness system status",
        "content": {
            "application/json": {
                "example": {
                    "status": "active",
                    "awareness_level": 0.85,
                    "emotional_state": {
                        "primary": "calm",
                        "secondary": ["curious", "attentive"],
                        "intensity": 0.6,
                    },
                    "active_devices": 24,
                    "safla_loops": 3,
                    "last_update": "2024-01-20T10:30:00Z",
                }
            }
        },
    },
    "device_list": {
        "description": "List of connected devices",
        "content": {
            "application/json": {
                "example": {
                    "devices": [
                        {
                            "id": "light_001",
                            "name": "Living Room Ceiling Light",
                            "type": "light",
                            "status": "on",
                            "capabilities": ["dimming", "color_temperature"],
                            "current_state": {"brightness": 80, "color_temp": 3000},
                        }
                    ],
                    "total": 24,
                    "filters_applied": {
                        "status": "active",
                        "location": "living_room",
                        "type": "light",
                    },
                }
            }
        },
    },
    "error_response": {
        "description": "Error response",
        "content": {
            "application/json": {
                "example": {
                    "error": {
                        "code": "DEVICE_NOT_FOUND",
                        "message": "The requested device could not be found",
                        "details": {
                            "device_id": "invalid_device_123",
                            "suggestion": "Check device ID or use GET /devices to list available devices",
                        },
                        "timestamp": "2024-01-20T10:30:00Z",
                        "request_id": "req_12345",
                    }
                }
            }
        },
    },
    "websocket_message": {
        "description": "WebSocket message format",
        "content": {
            "application/json": {
                "examples": {
                    "consciousness_update": {
                        "summary": "Consciousness state update",
                        "value": {
                            "type": "consciousness_update",
                            "data": {
                                "awareness_level": 0.87,
                                "emotional_state": {
                                    "primary": "attentive",
                                    "intensity": 0.7,
                                },
                                "timestamp": "2024-01-20T10:31:00Z",
                            },
                        },
                    },
                    "device_update": {
                        "summary": "Device state change",
                        "value": {
                            "type": "device_update",
                            "data": {
                                "device_id": "light_001",
                                "changes": {"brightness": 75, "status": "on"},
                                "source": "user_interaction",
                                "timestamp": "2024-01-20T10:31:00Z",
                            },
                        },
                    },
                }
            }
        },
    },
}


# API documentation configuration
def get_openapi_config() -> Dict[str, Any]:
    """Get complete OpenAPI configuration."""
    return {
        "openapi": "3.0.0",
        "info": OPENAPI_METADATA,
        "tags": OPENAPI_TAGS,
        "components": {"securitySchemes": SECURITY_SCHEMES},
        "security": [{"bearerAuth": []}, {"apiKey": []}],
        "paths": {
            # Paths will be auto-generated by FastAPI
        },
    }


# Custom OpenAPI schema modifications
def customize_openapi_schema(app):
    """Customize the OpenAPI schema with additional examples and documentation."""

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = app.openapi()

        # Add custom metadata
        openapi_schema.update(OPENAPI_METADATA)
        openapi_schema["tags"] = OPENAPI_TAGS

        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

        # Add global security
        openapi_schema["security"] = [{"bearerAuth": []}]

        # Customize specific endpoints
        paths = openapi_schema.get("paths", {})

        # Add examples to consciousness status endpoint
        if "/api/v1/consciousness/status" in paths:
            get_op = paths["/api/v1/consciousness/status"].get("get", {})
            if "responses" in get_op and "200" in get_op["responses"]:
                get_op["responses"]["200"].update(
                    EXAMPLE_RESPONSES["consciousness_status"]
                )

        # Add examples to device list endpoint
        if "/api/v1/devices" in paths:
            get_op = paths["/api/v1/devices"].get("get", {})
            if "responses" in get_op and "200" in get_op["responses"]:
                get_op["responses"]["200"].update(EXAMPLE_RESPONSES["device_list"])

        # Add WebSocket documentation
        if "/api/v1/realtime" in paths:
            ws_op = paths["/api/v1/realtime"]
            ws_op["summary"] = "WebSocket Real-time Communication"
            ws_op[
                "description"
            ] = """
            WebSocket endpoint for real-time bidirectional communication.

            **Connection:**
            - URL: ws://host/api/v1/realtime
            - Authentication: Include JWT token in connection headers

            **Message Types:**
            - init: Initialize connection with subscriptions
            - ping/pong: Keep-alive mechanism
            - status_update: Real-time system status
            - consciousness_update: Consciousness state changes
            - device_update: Device state changes
            - safla_event: SAFLA loop events
            - interview_update: Interview session progress
            """

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app
