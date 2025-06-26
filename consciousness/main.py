"""
Main FastAPI application for the House Consciousness System.
"""

import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .demo_devices import device_simulator
from .simple_health import simple_health_checker


# Authentication models and functions
class AuthCredentials(BaseModel):
    """Authentication credentials."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# Simple JWT-like token generation (for demo purposes)
def create_simple_token(username: str) -> str:
    """Create a simple token for demo purposes."""
    import base64
    import json

    token_data = {
        "sub": username,
        "exp": (datetime.now() + timedelta(hours=1)).isoformat(),
        "iat": datetime.now().isoformat(),
    }
    token_json = json.dumps(token_data)
    return base64.b64encode(token_json.encode()).decode()


def verify_simple_token(token: str) -> dict:
    """Verify simple token for demo purposes."""
    import base64
    import json

    try:
        token_json = base64.b64decode(token.encode()).decode()
        token_data = json.loads(token_json)
        # Check if token is expired
        exp_time = datetime.fromisoformat(token_data["exp"])
        if datetime.now() > exp_time:
            raise HTTPException(status_code=401, detail="Token expired")
        return token_data
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# Security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    """Get current user from token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    token_data = verify_simple_token(credentials.credentials)
    return token_data.get("sub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting House Consciousness System...")
    yield
    # Shutdown
    print("Shutting down House Consciousness System...")


# Create FastAPI application
app = FastAPI(
    title="House Consciousness System",
    description="Intelligent home automation system with consciousness-driven decision making",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def root():
    """Serve the web interface."""
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(static_path):
        with open(static_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return {
            "message": "House Consciousness System",
            "version": "1.0.0",
            "status": "active",
            "web_interface": "Install complete system to access web interface",
        }


@app.get("/api")
async def api_root():
    """API root endpoint."""
    return {
        "message": "House Consciousness System API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs",
        "web_interface": "/",
    }


# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(credentials: AuthCredentials):
    """Authenticate user and return token."""
    # Simple demo authentication - in production, use proper password hashing
    if credentials.username == "admin" and credentials.password == "consciousness123":
        token = create_simple_token(credentials.username)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Consciousness endpoints
@app.get("/api/v1/consciousness/status")
async def get_consciousness_status(current_user: str = Depends(get_current_user)):
    """Get consciousness system status."""
    return {
        "status": "active",
        "awareness_level": 0.85,
        "emotional_state": {"primary": "calm", "arousal": 0.3, "valence": 0.7},
        "active_devices": device_simulator.get_device_count(),
        "safla_loops": 3,
        "last_update": datetime.now().isoformat(),
    }


@app.get("/api/v1/consciousness/emotions")
async def get_emotions(current_user: str = Depends(get_current_user)):
    """Get emotional state."""
    return {"current": {"primary_emotion": "calm", "arousal": 0.3, "valence": 0.7}}


@app.post("/api/v1/consciousness/query")
async def query_consciousness(
    query_data: dict, current_user: str = Depends(get_current_user)
):
    """Process consciousness query."""
    query = query_data.get("query", "")
    return {
        "response": f"I understand your query: '{query}'. I'm here to help manage your smart home.",
        "timestamp": datetime.now().isoformat(),
    }


# Device endpoints (v1 API versions)
@app.get("/api/v1/devices")
async def get_devices_v1(current_user: str = Depends(get_current_user)):
    """Get all devices (v1 API)."""
    devices = device_simulator.get_all_devices()
    return {"devices": devices, "total": len(devices)}


@app.put("/api/v1/devices/{device_id}/control")
async def control_device_v1(
    device_id: str, command: dict, current_user: str = Depends(get_current_user)
):
    """Control a device (v1 API)."""
    device = device_simulator.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    action = command.get("action")
    value = command.get("value")

    # Simulate device control
    update_data = {"last_action": action, "last_update": datetime.now().isoformat()}
    if action == "turn_on":
        update_data["status"] = "active"
    elif action == "turn_off":
        update_data["status"] = "inactive"

    updated_device = device_simulator.update_device(device_id, update_data)
    return {"status": "success", "device": updated_device}


@app.post("/api/v1/devices/batch-control")
async def batch_control_devices_v1(
    batch_data: dict, current_user: str = Depends(get_current_user)
):
    """Batch control devices (v1 API)."""
    devices = batch_data.get("devices", [])
    results = []

    for device_cmd in devices:
        device_id = device_cmd.get("device_id")
        action = device_cmd.get("action")

        if device_id and device_simulator.get_device(device_id):
            update_data = {
                "last_action": action,
                "last_update": datetime.now().isoformat(),
            }
            if action == "turn_on":
                update_data["status"] = "active"
            elif action == "turn_off":
                update_data["status"] = "inactive"

            device_simulator.update_device(device_id, update_data)
            results.append({"device_id": device_id, "status": "success"})
        else:
            results.append(
                {
                    "device_id": device_id,
                    "status": "error",
                    "message": "Device not found",
                }
            )

    return {"results": results}


# Memory endpoints
@app.get("/api/v1/memory")
async def get_memory(current_user: str = Depends(get_current_user)):
    """Get memory entries."""
    return {
        "memories": [
            {
                "type": "experience",
                "content": "User turned on living room lights at 7:30 PM",
                "timestamp": datetime.now().isoformat(),
            }
        ]
    }


@app.post("/api/v1/memory")
async def store_memory(
    memory_data: dict, current_user: str = Depends(get_current_user)
):
    """Store memory entry."""
    return {
        "memory_id": f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "stored",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "consciousness-system",
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components."""
    health_status = await simple_health_checker.get_health_status()

    # Return appropriate HTTP status code based on health
    if health_status["status"] == "critical":
        raise HTTPException(status_code=503, detail=health_status)
    elif health_status["status"] == "degraded":
        # Return 200 for degraded status (some warnings but still functional)
        return health_status

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Get basic system metrics
    try:
        import psutil

        memory = psutil.virtual_memory()
        device_count = device_simulator.get_device_count()

        return {
            "consciousness_active_sessions": 1,
            "consciousness_total_requests": 100,
            "consciousness_device_count": device_count,
            "consciousness_memory_usage_percent": round(memory.percent, 1),
            "consciousness_uptime_seconds": 300,  # Placeholder
            "consciousness_api_status": "healthy",
            "consciousness_demo_mode": device_simulator.demo_mode,
        }
    except Exception:
        return {
            "consciousness_active_sessions": 1,
            "consciousness_total_requests": 100,
            "consciousness_device_count": 0,
            "consciousness_api_status": "healthy",
        }


# Device and Discovery API endpoints
@app.get("/api/devices")
async def get_devices():
    """Get all discovered devices."""
    devices = device_simulator.get_all_devices()
    # Format devices for demo dashboard compatibility
    formatted_devices = []
    for device in devices:
        formatted_devices.append({
            "id": device.get("id"),
            "name": device.get("name", f"Device {device.get('id')}"),
            "type": device.get("type", "unknown"),
            "location": device.get("location", "unknown"),
            "state": device.get("properties", {}),
            "running": device.get("status") == "active"
        })
    return {
        "devices": formatted_devices
    }


@app.get("/api/devices/{device_id}")
async def get_device(device_id: str):
    """Get a specific device by ID."""
    device = device_simulator.get_device(device_id)
    if device:
        return device
    raise HTTPException(status_code=404, detail="Device not found")


@app.post("/api/devices")
async def add_device(device_data: dict):
    """Add a new device to the simulator."""
    device = device_simulator.add_device(device_data)
    return {"message": "Device added successfully", "device": device}


@app.put("/api/devices/{device_id}")
async def update_device(device_id: str, updates: dict):
    """Update an existing device."""
    device = device_simulator.update_device(device_id, updates)
    if device:
        return {"message": "Device updated successfully", "device": device}
    raise HTTPException(status_code=404, detail="Device not found")


@app.delete("/api/devices/{device_id}")
async def remove_device(device_id: str):
    """Remove a device from the simulator."""
    success = device_simulator.remove_device(device_id)
    if success:
        return {"message": "Device removed successfully"}
    raise HTTPException(status_code=404, detail="Device not found")


@app.post("/api/demo/enable")
async def enable_demo_mode():
    """Enable demo mode with simulated devices."""
    device_simulator.enable_demo_mode()
    return {
        "message": "Demo mode enabled",
        "device_count": device_simulator.get_device_count(),
        "demo_mode": True,
    }


@app.post("/api/demo/disable")
async def disable_demo_mode():
    """Disable demo mode and clear simulated devices."""
    device_simulator.disable_demo_mode()
    return {"message": "Demo mode disabled", "device_count": 0, "demo_mode": False}


@app.post("/api/discovery/scan")
async def scan_for_devices():
    """Trigger device discovery scan."""
    if device_simulator.demo_mode:
        # In demo mode, simulate finding new devices occasionally
        import random

        if random.random() < 0.3:  # 30% chance of "finding" a new device
            new_device = {
                "name": f"New Device {random.randint(100, 999)}",
                "type": random.choice(["smart_plug", "sensor", "light", "speaker"]),
                "location": random.choice(
                    ["bedroom", "kitchen", "living_room", "office"]
                ),
                "properties": {"signal_strength": random.randint(50, 100)},
                "discovery_method": random.choice(["mdns", "upnp", "bluetooth"]),
            }
            device = device_simulator.add_device(new_device)
            return {
                "message": "Discovery scan completed",
                "new_devices_found": 1,
                "new_device": device,
            }
        else:
            return {"message": "Discovery scan completed", "new_devices_found": 0}
    else:
        # Real device discovery would go here
        return {
            "message": "Discovery scan completed - real device discovery not implemented yet",
            "new_devices_found": 0,
            "note": "Enable demo mode to see simulated devices",
        }


@app.get("/api/discovery/status")
async def get_discovery_status():
    """Get device discovery status."""
    return {
        "demo_mode": device_simulator.demo_mode,
        "total_devices": device_simulator.get_device_count(),
        "discovery_methods": ["bluetooth", "mdns", "upnp", "zigbee"],
        "last_scan": datetime.now().isoformat(),
    }


# Demo Dashboard endpoints
@app.get("/api/status")
async def get_demo_status():
    """Get system status for demo dashboard."""
    devices = device_simulator.get_all_devices()
    device_types = {}
    for device in devices:
        device_type = device.get("type", "unknown")
        device_types[device_type] = device_types.get(device_type, 0) + 1
    
    return {
        "timestamp": datetime.now().isoformat(),
        "consciousness_status": {
            "active": True,
            "emotional_state": "content",
            "mood": "stable",
            "active_concerns": [],
            "last_activity": datetime.now().isoformat()
        },
        "devices": {
            "total": len(devices),
            "active": len([d for d in devices if d.get("status") == "active"]),
            "types": device_types
        },
        "scenarios": [
            "smart_morning",
            "security_alert",
            "energy_optimization",
            "party_mode",
            "vacation_mode"
        ],
        "running_scenario": None
    }


@app.post("/api/consciousness/query")
async def query_demo_consciousness(query_data: dict):
    """Query consciousness for demo dashboard."""
    question = query_data.get("question", "")
    return {
        "response": f"I understand your query: '{question}'. I'm monitoring your smart home and everything is running smoothly."
    }


@app.get("/api/devices/{device_id}")
async def get_demo_device(device_id: str):
    """Get specific device details for demo dashboard."""
    device = device_simulator.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@app.post("/api/devices/{device_id}/control")
async def control_demo_device(device_id: str, command: dict):
    """Control device for demo dashboard."""
    device = device_simulator.get_device(device_id)
    if not device:
        return {"status": "error", "message": f"Device {device_id} not found"}
    
    # Update device state
    update_data = command.copy()
    update_data["last_update"] = datetime.now().isoformat()
    
    updated_device = device_simulator.update_device(device_id, update_data)
    return {
        "status": "success",
        "device_id": device_id,
        "new_state": updated_device.get("properties", {})
    }


@app.post("/api/scenarios/{scenario_name}/run")
async def run_demo_scenario(scenario_name: str):
    """Run a demo scenario."""
    # Simulate scenario execution
    return {"status": "started", "scenario": scenario_name}


@app.post("/api/scenarios/stop")
async def stop_demo_scenarios():
    """Stop all running scenarios."""
    return {"status": "stopped"}


# Additional demo endpoints for API test UI
@app.get("/api/consciousness/status")
async def get_consciousness_status():
    """Get consciousness status (demo)."""
    return {
        "status": "active",
        "emotional_state": {
            "primary": "content",
            "secondary": "curious",
            "intensity": 0.7
        },
        "awareness_level": 0.85,
        "active_concerns": [],
        "last_activity": datetime.now().isoformat()
    }


@app.get("/api/consciousness/emotions")
async def get_consciousness_emotions(time_range: str = "1h", include_history: bool = True):
    """Get consciousness emotions (demo)."""
    return {
        "current_emotion": {
            "primary": "content",
            "secondary": "curious",
            "intensity": 0.7,
            "timestamp": datetime.now().isoformat()
        },
        "history": [
            {
                "emotion": "happy",
                "intensity": 0.8,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "trigger": "user_interaction"
            }
        ] if include_history else [],
        "time_range": time_range
    }


@app.post("/api/devices/batch-control")
async def batch_control_devices(batch_data: dict):
    """Batch control multiple devices (demo)."""
    results = []
    for command in batch_data.get("devices", []):
        device_id = command.get("device_id")
        action = command.get("action")
        results.append({
            "device_id": device_id,
            "action": action,
            "status": "success",
            "timestamp": datetime.now().isoformat()
        })
    return {"results": results, "total": len(results)}


@app.get("/api/memory")
async def get_memory(memory_type: str = None, time_range: str = "7d", limit: int = 10):
    """Get memory entries (demo)."""
    return {
        "memories": [
            {
                "id": "mem_001",
                "type": memory_type or "interaction",
                "content": "User adjusted thermostat to 72°F",
                "timestamp": datetime.now().isoformat(),
                "context": {"device": "thermostat", "room": "living_room"}
            }
        ],
        "total": 1,
        "time_range": time_range,
        "limit": limit
    }


@app.post("/api/memory")
async def store_memory(memory_data: dict):
    """Store memory entry (demo)."""
    return {
        "id": f"mem_{datetime.now().timestamp()}",
        "type": memory_data.get("type", "general"),
        "content": memory_data.get("content", ""),
        "timestamp": datetime.now().isoformat(),
        "stored": True
    }


@app.post("/api/interview/start")
async def start_interview(interview_data: dict):
    """Start interview session (demo)."""
    return {
        "interview_id": f"interview_{datetime.now().timestamp()}",
        "house_id": interview_data.get("house_id"),
        "status": "active",
        "current_question": "Tell me about your smart home devices."
    }


@app.post("/api/interview/{interview_id}/message")
async def send_interview_message(interview_id: str, message_data: dict):
    """Send message in interview (demo)."""
    return {
        "interview_id": interview_id,
        "response": "I understand. Let me learn more about your preferences.",
        "next_question": "What times do you typically wake up and go to bed?",
        "progress": 0.3
    }


@app.get("/api/interview/{interview_id}/status")
async def get_interview_status(interview_id: str):
    """Get interview status (demo)."""
    return {
        "interview_id": interview_id,
        "status": "active",
        "progress": 0.3,
        "questions_asked": 3,
        "estimated_completion": "5 minutes"
    }


@app.get("/api/discovery/scan/{scan_id}")
async def get_scan_results(scan_id: str):
    """Get discovery scan results (demo)."""
    return {
        "scan_id": scan_id,
        "status": "completed",
        "devices_found": [
            {
                "name": "Smart Bulb",
                "type": "light",
                "manufacturer": "Philips",
                "model": "Hue Color"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/integrations/templates")
async def get_integration_templates(brand: str = None, device_class: str = None):
    """Get integration templates (demo)."""
    templates = [
        {
            "id": "tpl_001",
            "brand": "philips",
            "device_class": "light",
            "name": "Philips Hue Light",
            "configuration": {"bridge_required": True}
        },
        {
            "id": "tpl_002",
            "brand": "nest",
            "device_class": "thermostat",
            "name": "Nest Thermostat",
            "configuration": {"oauth_required": True}
        }
    ]
    
    if brand:
        templates = [t for t in templates if t["brand"] == brand.lower()]
    if device_class:
        templates = [t for t in templates if t["device_class"] == device_class.lower()]
    
    return {"templates": templates, "total": len(templates)}


@app.post("/api/integrations/classify")
async def classify_device(classification_data: dict):
    """Classify device based on description (demo)."""
    description = classification_data.get("description", "").lower()
    
    # Simple classification logic
    device_type = "unknown"
    if "light" in description or "bulb" in description:
        device_type = "light"
    elif "thermostat" in description or "temperature" in description:
        device_type = "thermostat"
    elif "camera" in description:
        device_type = "camera"
    elif "sensor" in description:
        device_type = "sensor"
    
    return {
        "classification": {
            "device_type": device_type,
            "confidence": 0.85,
            "suggested_template": "tpl_001" if device_type == "light" else "tpl_generic"
        },
        "description": classification_data.get("description")
    }


@app.get("/api/safla/status")
async def get_safla_status():
    """Get SAFLA loop status (demo)."""
    return {
        "active_loops": [
            {
                "id": "main_loop",
                "status": "running",
                "iterations": 42,
                "last_run": datetime.now().isoformat()
            }
        ],
        "total_iterations": 42,
        "system_status": "optimal"
    }


@app.post("/api/safla/trigger")
async def trigger_safla(safla_data: dict):
    """Trigger SAFLA loop (demo)."""
    return {
        "loop_id": safla_data.get("loop_id", "main_loop"),
        "status": "triggered",
        "execution_id": f"exec_{datetime.now().timestamp()}",
        "estimated_duration": "30 seconds"
    }


@app.get("/api/twins")
async def get_digital_twins(device_id: str = None, sync_status: str = None, fidelity_level: str = None):
    """Get digital twins (demo)."""
    twins = [
        {
            "twin_id": "twin_001",
            "device_id": "device_001",
            "fidelity_level": "advanced",
            "sync_status": "synchronized",
            "last_sync": datetime.now().isoformat()
        }
    ]
    
    if device_id:
        twins = [t for t in twins if t["device_id"] == device_id]
    if sync_status:
        twins = [t for t in twins if t["sync_status"] == sync_status]
    if fidelity_level:
        twins = [t for t in twins if t["fidelity_level"] == fidelity_level]
    
    return {"twins": twins, "total": len(twins)}


@app.post("/api/twins")
async def create_digital_twin(twin_data: dict):
    """Create digital twin (demo)."""
    return {
        "twin_id": f"twin_{datetime.now().timestamp()}",
        "device_id": twin_data.get("device_id"),
        "fidelity_level": twin_data.get("fidelity_level", "standard"),
        "status": "created",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/scenarios")
async def create_scenario(scenario_data: dict):
    """Create scenario (demo)."""
    return {
        "scenario_id": f"scenario_{datetime.now().timestamp()}",
        "name": scenario_data.get("name"),
        "description": scenario_data.get("description"),
        "duration": scenario_data.get("duration", 300),
        "status": "created",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/predictions/what-if")
async def what_if_analysis(prediction_data: dict):
    """What-if analysis (demo)."""
    return {
        "analysis_id": f"analysis_{datetime.now().timestamp()}",
        "scenario": prediction_data.get("scenario"),
        "predictions": {
            "energy_consumption": {"change": "-15%", "confidence": 0.82},
            "comfort_level": {"change": "+5%", "confidence": 0.75},
            "cost": {"change": "-12%", "confidence": 0.88}
        },
        "recommendations": [
            "Consider implementing this scenario during peak hours",
            "Monitor comfort levels for the first week"
        ],
        "timestamp": datetime.now().isoformat()
    }


# WebSocket endpoint for demo dashboard
from fastapi import WebSocket, WebSocketDisconnect
import asyncio


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for demo dashboard."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic status updates
            devices = device_simulator.get_all_devices()
            device_states = {}
            for idx, device in enumerate(devices):
                device_states[str(idx)] = {
                    "status": device.get("status", "offline"),
                    "type": device.get("type", "unknown"),
                    "name": device.get("name", f"Device {idx}")
                }
            
            status = {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "consciousness": {
                    "active": True,
                    "emotional_state": "content",
                    "mood": "stable",
                    "active_concerns": []
                },
                "devices": {
                    "total": len(devices),
                    "active": len([d for d in devices if d.get("status") == "active"])
                },
                "running_scenario": None,
                "device_states": device_states
            }
            
            await websocket.send_json(status)
            await asyncio.sleep(2)  # Update every 2 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Include additional routers when they're implemented
# app.include_router(api_router, prefix="/api/v1")
# app.include_router(consciousness_router, prefix="/consciousness")
# app.include_router(devices_router, prefix="/devices")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
