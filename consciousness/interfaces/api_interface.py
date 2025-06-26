"""
Comprehensive API Interface for the House Consciousness System.

This module implements the RESTful API endpoints, WebSocket real-time communication,
authentication, and OpenAPI documentation as specified in the API Interface Guide.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Security,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..core.consciousness_engine import ConsciousnessEngine
from ..core.memory_manager import MemoryManager
from ..core.query_engine import QueryEngine
from ..digital_twin.core import DigitalTwinManager
from ..io.device_controller import DeviceController
from ..simulators.manager import SimulatorManager
from ..utils.logging import get_logger
from ..utils.security import create_jwt_token, verify_jwt_token
from .openapi_config import OPENAPI_METADATA, OPENAPI_TAGS, customize_openapi_schema

logger = get_logger(__name__)


# Pydantic Models for API
class ConsciousnessQuery(BaseModel):
    """Natural language query to consciousness system."""

    query: str = Field(..., description="Natural language question or command")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context"
    )
    include_devices: bool = Field(
        default=True, description="Include device information in response"
    )


class DeviceControl(BaseModel):
    """Device control command."""

    action: str = Field(..., description="Action to perform")
    value: Optional[Union[str, int, float, bool]] = Field(
        None, description="Action value"
    )
    transition_time: Optional[int] = Field(
        None, description="Transition time in milliseconds"
    )


class BatchDeviceControl(BaseModel):
    """Batch device control commands."""

    devices: List[Dict[str, Any]] = Field(
        ..., description="List of device control commands"
    )


class MemoryEntry(BaseModel):
    """Memory entry for storage."""

    type: str = Field(..., description="Type of memory entry")
    content: str = Field(..., description="Memory content")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context"
    )


class InterviewStart(BaseModel):
    """Start device discovery interview."""

    house_id: str = Field(..., description="House identifier")


class InterviewMessage(BaseModel):
    """User message for interview."""

    message: str = Field(..., description="User message")


class InterviewConfirmation(BaseModel):
    """Confirm device candidates."""

    confirmed_candidates: List[Dict[str, Any]] = Field(
        ..., description="Confirmed device candidates"
    )


class DiscoveryScan(BaseModel):
    """Device discovery scan request."""

    protocols: List[str] = Field(
        default=["mdns", "upnp", "bluetooth"], description="Discovery protocols"
    )
    timeout_seconds: int = Field(default=30, description="Scan timeout")


class DeviceClassification(BaseModel):
    """Device classification request."""

    description: str = Field(..., description="Device description")
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Classification context"
    )


class ScenarioCreate(BaseModel):
    """Create scenario simulation."""

    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    duration: int = Field(..., description="Duration in seconds")
    events: List[Dict[str, Any]] = Field(..., description="Scenario events")
    twin_ids: List[str] = Field(..., description="Affected digital twin IDs")


class WhatIfAnalysis(BaseModel):
    """What-if analysis request."""

    scenario: str = Field(..., description="Scenario name")
    changes: Dict[str, Any] = Field(..., description="Changes to apply")
    duration: str = Field(..., description="Analysis duration")
    metrics: List[str] = Field(..., description="Metrics to analyze")


class TwinCreate(BaseModel):
    """Create digital twin."""

    device_id: str = Field(..., description="Device ID")
    fidelity_level: str = Field(default="advanced", description="Twin fidelity level")
    config: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Twin configuration"
    )


class AuthCredentials(BaseModel):
    """Authentication credentials."""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class SAFLATrigger(BaseModel):
    """SAFLA loop trigger request."""

    loop_id: str = Field(..., description="SAFLA loop ID")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Trigger parameters"
    )


# WebSocket Connection Manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_subscriptions: Dict[WebSocket, List[str]] = {}

    async def connect(self, websocket: WebSocket, subscriptions: List[str] = None):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_subscriptions[websocket] = subscriptions or []
        logger.info(
            f"WebSocket client connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        logger.info(
            f"WebSocket client disconnected. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ):
        """Send message to specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], subscription_filter: str = None):
        """Broadcast message to all connected clients or filtered by subscription."""
        disconnected = []

        for connection in self.active_connections:
            try:
                # Check subscription filter
                if subscription_filter:
                    subscriptions = self.client_subscriptions.get(connection, [])
                    if subscription_filter not in subscriptions:
                        continue

                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# API Exception Handlers
class APIError(Exception):
    """Custom API error with structured response."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Dict[str, Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


# Main API Application
class ConsciousnessAPI:
    """Main Consciousness System API."""

    def __init__(
        self,
        consciousness_engine: ConsciousnessEngine,
        device_controller: DeviceController = None,
        memory_manager: MemoryManager = None,
        digital_twin_manager: DigitalTwinManager = None,
        simulator_manager: SimulatorManager = None,
    ):
        self.consciousness = consciousness_engine
        self.device_controller = device_controller
        self.memory_manager = memory_manager
        self.digital_twin_manager = digital_twin_manager
        self.simulator_manager = simulator_manager

        # Initialize FastAPI app with OpenAPI configuration
        self.app = FastAPI(
            title=OPENAPI_METADATA["title"],
            description=OPENAPI_METADATA["description"],
            version=OPENAPI_METADATA["version"],
            contact=OPENAPI_METADATA.get("contact"),
            license_info=OPENAPI_METADATA.get("license"),
            openapi_tags=OPENAPI_TAGS,
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # WebSocket connection manager
        self.connection_manager = ConnectionManager()

        # Security
        self.security = HTTPBearer(auto_error=False)

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

        # Setup error handlers
        self._setup_error_handlers()

        # Customize OpenAPI schema
        customize_openapi_schema(self.app)

    def _setup_middleware(self):
        """Setup API middleware."""

        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure properly for production
        )

    def _setup_error_handlers(self):
        """Setup custom error handlers."""

        @self.app.exception_handler(APIError)
        async def api_error_handler(request, exc: APIError):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                        "timestamp": datetime.now().isoformat(),
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    }
                },
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": f"HTTP_{exc.status_code}",
                        "message": exc.detail,
                        "timestamp": datetime.now().isoformat(),
                        "request_id": getattr(request.state, "request_id", "unknown"),
                    }
                },
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Security(
            HTTPBearer(auto_error=False)
        ),
    ):
        """Validate JWT token and get current user."""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            payload = verify_jwt_token(credentials.credentials)
            return payload.get("sub")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def _setup_routes(self):
        """Setup all API routes."""

        # Health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "consciousness_engine": self.consciousness.is_active
                    if self.consciousness
                    else False,
                    "device_controller": bool(self.device_controller),
                    "memory_manager": bool(self.memory_manager),
                    "digital_twin_manager": bool(self.digital_twin_manager),
                },
            }

        # Demo endpoints (non-authenticated) for demo dashboard
        @self.app.get("/api/status")
        async def get_demo_status():
            """Get system status for demo dashboard."""
            consciousness_status = {}
            if self.consciousness:
                try:
                    status = await self.consciousness.get_status()
                    consciousness_status = {
                        "active": self.consciousness.is_active,
                        "emotional_state": status.get("emotional_state", "content"),
                        "mood": status.get("mood", "stable"),
                        "active_concerns": status.get("active_concerns", []),
                        "last_activity": datetime.now().isoformat()
                    }
                except:
                    consciousness_status = {"active": False}
            
            devices = {"total": 0, "active": 0, "types": {}}
            if self.device_controller:
                try:
                    all_devices = await self.device_controller.get_devices()
                    devices["total"] = len(all_devices)
                    devices["active"] = len([d for d in all_devices if d.get("status") == "active"])
                    for device in all_devices:
                        device_type = device.get("type", "unknown")
                        devices["types"][device_type] = devices["types"].get(device_type, 0) + 1
                except:
                    pass
            
            # Get available scenarios
            scenarios = [
                "smart_morning",
                "security_alert", 
                "energy_optimization",
                "party_mode",
                "vacation_mode"
            ]
            
            running_scenario = None
            if self.simulator_manager and hasattr(self.simulator_manager, 'current_scenario'):
                try:
                    running_scenario = self.simulator_manager.current_scenario
                except:
                    pass
            
            return {
                "timestamp": datetime.now().isoformat(),
                "consciousness_status": consciousness_status,
                "devices": devices,
                "scenarios": scenarios,
                "running_scenario": running_scenario
            }
        
        @self.app.get("/api/devices")
        async def get_demo_devices():
            """Get all devices for demo dashboard."""
            if not self.device_controller:
                return {"devices": []}
            
            try:
                devices = await self.device_controller.get_devices()
                return {"devices": devices}
            except:
                return {"devices": []}
        
        @self.app.post("/api/consciousness/query")
        async def query_demo_consciousness(query: Dict[str, str]):
            """Query consciousness for demo dashboard."""
            if not self.consciousness or not hasattr(self.consciousness, 'process_query'):
                return {"response": "Consciousness system is initializing..."}
            
            try:
                response = await self.consciousness.process_query(query.get("question", ""))
                return {"response": response}
            except:
                return {"response": "Unable to process query at this time."}
        
        @self.app.post("/api/devices/{device_id}/control")
        async def control_demo_device(device_id: int, command: Dict[str, Any]):
            """Control device for demo dashboard."""
            if not self.device_controller:
                return {"status": "error", "message": "Device controller not available"}
            
            try:
                result = await self.device_controller.control_device(
                    str(device_id),
                    command.get("action", "update"),
                    value=command.get("value"),
                )
                return {"status": "success", "device_id": device_id, "new_state": result}
            except:
                return {"status": "error", "message": f"Failed to control device {device_id}"}
        
        @self.app.post("/api/scenarios/{scenario_name}/run")
        async def run_demo_scenario(scenario_name: str):
            """Run a demo scenario."""
            if self.simulator_manager and hasattr(self.simulator_manager, 'run_scenario'):
                try:
                    await self.simulator_manager.run_scenario(scenario_name)
                    # Broadcast scenario start
                    await self.connection_manager.broadcast(
                        {
                            "type": "scenario_start",
                            "data": {
                                "scenario": scenario_name,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )
                    return {"status": "started", "scenario": scenario_name}
                except Exception as e:
                    return {"status": "error", "message": str(e)}
            else:
                # For demo purposes, just return success
                await self.connection_manager.broadcast(
                    {
                        "type": "scenario_start",
                        "data": {
                            "scenario": scenario_name,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                # Simulate scenario completion after delay
                async def simulate_scenario():
                    await asyncio.sleep(5)
                    await self.connection_manager.broadcast(
                        {
                            "type": "scenario_complete",
                            "data": {
                                "scenario": scenario_name,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                    )
                asyncio.create_task(simulate_scenario())
                return {"status": "started", "scenario": scenario_name}
        
        @self.app.post("/api/scenarios/stop")
        async def stop_demo_scenarios():
            """Stop all running scenarios."""
            if self.simulator_manager and hasattr(self.simulator_manager, 'stop_all_scenarios'):
                try:
                    await self.simulator_manager.stop_all_scenarios()
                except:
                    pass
            return {"status": "stopped"}

        # Authentication endpoints
        @self.app.post("/api/v1/auth/login")
        async def login(credentials: AuthCredentials):
            """Authenticate user and return JWT token."""
            # Implement actual authentication logic here
            # For demo purposes, using simple validation
            if (
                credentials.username == "admin"
                and credentials.password == "consciousness123"
            ):
                token = create_jwt_token({"sub": credentials.username})
                return {
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials",
                )

        # Consciousness endpoints
        @self.app.get("/api/v1/consciousness/status")
        async def get_consciousness_status(
            current_user: str = Depends(self.get_current_user),
        ):
            """Get current consciousness system status."""
            if not self.consciousness:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Consciousness engine not available", 503
                )

            try:
                status = await self.consciousness.get_status()
                return {
                    "status": "active" if self.consciousness.is_active else "inactive",
                    "awareness_level": status.get("awareness_level", 0.0),
                    "emotional_state": status.get("emotional_state", {}),
                    "active_devices": status.get("active_devices", 0),
                    "safla_loops": status.get("safla_loops", 0),
                    "last_update": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to get consciousness status: {e}")
                raise APIError(
                    "INTERNAL_ERROR", "Failed to retrieve consciousness status", 500
                )

        @self.app.get("/api/v1/consciousness/emotions")
        async def get_emotions(
            time_range: str = "1h",
            include_history: bool = True,
            current_user: str = Depends(self.get_current_user),
        ):
            """Get current emotional state and history."""
            if not self.consciousness or not self.consciousness.emotion_processor:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Emotion processor not available", 503
                )

            try:
                current_emotion = (
                    await self.consciousness.emotion_processor.get_current_emotion()
                )
                result = {
                    "current": {
                        "primary_emotion": current_emotion.get("primary", "neutral"),
                        "emotion_vector": current_emotion.get("vector", [0.0] * 5),
                        "arousal": current_emotion.get("arousal", 0.0),
                        "valence": current_emotion.get("valence", 0.0),
                    }
                }

                if include_history:
                    # Get emotion history for specified time range
                    history = (
                        await self.consciousness.emotion_processor.get_emotion_history(
                            time_range
                        )
                    )
                    result["history"] = history

                return result
            except Exception as e:
                logger.error(f"Failed to get emotions: {e}")
                raise APIError(
                    "INTERNAL_ERROR", "Failed to retrieve emotional state", 500
                )

        @self.app.post("/api/v1/consciousness/query")
        async def query_consciousness(
            query: ConsciousnessQuery,
            current_user: str = Depends(self.get_current_user),
        ):
            """Natural language query to consciousness system."""
            if not self.consciousness or not self.consciousness.query_engine:
                raise APIError("SERVICE_UNAVAILABLE", "Query engine not available", 503)

            try:
                response = await self.consciousness.query_engine.process_query(
                    query.query,
                    context=query.context,
                    include_devices=query.include_devices,
                )

                # Broadcast query event to WebSocket clients
                await self.connection_manager.broadcast(
                    {
                        "type": "consciousness_query",
                        "data": {
                            "query": query.query,
                            "response": response["response"],
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                    "consciousness",
                )

                return response
            except Exception as e:
                logger.error(f"Failed to process consciousness query: {e}")
                raise APIError(
                    "QUERY_FAILED", "Failed to process consciousness query", 500
                )

        # Device endpoints
        @self.app.get("/api/v1/devices")
        async def get_devices(
            status: Optional[str] = None,
            location: Optional[str] = None,
            device_type: Optional[str] = None,
            current_user: str = Depends(self.get_current_user),
        ):
            """List all connected devices with optional filtering."""
            if not self.device_controller:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Device controller not available", 503
                )

            try:
                devices = await self.device_controller.get_devices(
                    status=status, location=location, device_type=device_type
                )

                return {
                    "devices": devices,
                    "total": len(devices),
                    "filters_applied": {
                        "status": status,
                        "location": location,
                        "type": device_type,
                    },
                }
            except Exception as e:
                logger.error(f"Failed to get devices: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to retrieve devices", 500)

        @self.app.get("/api/v1/devices/{device_id}")
        async def get_device(
            device_id: str, current_user: str = Depends(self.get_current_user)
        ):
            """Get specific device details."""
            if not self.device_controller:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Device controller not available", 503
                )

            try:
                device = await self.device_controller.get_device(device_id)
                if not device:
                    raise APIError(
                        "DEVICE_NOT_FOUND", f"Device {device_id} not found", 404
                    )

                return device
            except APIError:
                raise
            except Exception as e:
                logger.error(f"Failed to get device {device_id}: {e}")
                raise APIError(
                    "INTERNAL_ERROR", f"Failed to retrieve device {device_id}", 500
                )

        @self.app.put("/api/v1/devices/{device_id}/control")
        async def control_device(
            device_id: str,
            command: DeviceControl,
            current_user: str = Depends(self.get_current_user),
        ):
            """Control a specific device."""
            if not self.device_controller:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Device controller not available", 503
                )

            try:
                result = await self.device_controller.control_device(
                    device_id,
                    command.action,
                    value=command.value,
                    transition_time=command.transition_time,
                )

                # Broadcast device update to WebSocket clients
                await self.connection_manager.broadcast(
                    {
                        "type": "device_update",
                        "data": {
                            "device_id": device_id,
                            "action": command.action,
                            "result": result,
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                    "devices",
                )

                return result
            except Exception as e:
                logger.error(f"Failed to control device {device_id}: {e}")
                raise APIError(
                    "CONTROL_FAILED", f"Failed to control device {device_id}", 500
                )

        @self.app.post("/api/v1/devices/batch-control")
        async def batch_control_devices(
            batch_command: BatchDeviceControl,
            current_user: str = Depends(self.get_current_user),
        ):
            """Control multiple devices simultaneously."""
            if not self.device_controller:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Device controller not available", 503
                )

            try:
                results = await self.device_controller.batch_control(
                    batch_command.devices
                )

                # Broadcast batch update to WebSocket clients
                await self.connection_manager.broadcast(
                    {
                        "type": "batch_device_update",
                        "data": {
                            "commands": batch_command.devices,
                            "results": results,
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                    "devices",
                )

                return {"results": results}
            except Exception as e:
                logger.error(f"Failed to perform batch device control: {e}")
                raise APIError(
                    "BATCH_CONTROL_FAILED",
                    "Failed to perform batch device control",
                    500,
                )

        # Memory endpoints
        @self.app.get("/api/v1/memory")
        async def get_memory(
            memory_type: Optional[str] = None,
            time_range: str = "7d",
            limit: int = 10,
            current_user: str = Depends(self.get_current_user),
        ):
            """Retrieve memory entries."""
            if not self.memory_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Memory manager not available", 503
                )

            try:
                memories = await self.memory_manager.get_memories(
                    memory_type=memory_type, time_range=time_range, limit=limit
                )

                return {"memories": memories}
            except Exception as e:
                logger.error(f"Failed to get memories: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to retrieve memories", 500)

        @self.app.post("/api/v1/memory")
        async def store_memory(
            memory: MemoryEntry, current_user: str = Depends(self.get_current_user)
        ):
            """Store new memory or experience."""
            if not self.memory_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Memory manager not available", 503
                )

            try:
                memory_id = await self.memory_manager.store_memory(
                    memory_type=memory.type,
                    content=memory.content,
                    context=memory.context,
                )

                return {
                    "memory_id": memory_id,
                    "status": "stored",
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to store memory: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to store memory", 500)

        # Interview endpoints
        @self.app.post("/api/v1/interview/start")
        async def start_interview(
            request: InterviewStart, current_user: str = Depends(self.get_current_user)
        ):
            """Start a new device discovery interview session."""
            try:
                # Create interview session (implement interview manager)
                interview_id = (
                    f"int_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(request)}"
                )

                return {
                    "interview_id": interview_id,
                    "status": "active",
                    "current_phase": "introduction",
                    "ai_message": "Hi! I'm here to learn about the smart devices in your home. Tell me about any connected devices you have - you can describe them however feels natural, by room, by brand, or just whatever comes to mind.",
                    "session_started_at": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to start interview: {e}")
                raise APIError(
                    "INTERVIEW_START_FAILED", "Failed to start interview session", 500
                )

        @self.app.post("/api/v1/interview/{interview_id}/message")
        async def send_interview_message(
            interview_id: str,
            message: InterviewMessage,
            current_user: str = Depends(self.get_current_user),
        ):
            """Send a user message to the interview system."""
            try:
                # Process message and generate AI response (implement NLP processing)
                response = {
                    "ai_response": f"I understand you mentioned: '{message.message}'. Let me help you identify and configure these devices.",
                    "current_phase": "classification",
                    "discovered_candidates": [],
                    "auto_discovery_results": {},
                }

                # Broadcast interview update
                await self.connection_manager.broadcast(
                    {
                        "type": "interview_update",
                        "data": {
                            "interview_id": interview_id,
                            "event": "user_message",
                            "message": message.message,
                            "timestamp": datetime.now().isoformat(),
                        },
                    },
                    "interview",
                )

                return response
            except Exception as e:
                logger.error(f"Failed to process interview message: {e}")
                raise APIError(
                    "MESSAGE_PROCESSING_FAILED", "Failed to process message", 500
                )

        @self.app.get("/api/v1/interview/{interview_id}/status")
        async def get_interview_status(
            interview_id: str, current_user: str = Depends(self.get_current_user)
        ):
            """Get the current status of an interview session."""
            try:
                return {
                    "interview_id": interview_id,
                    "status": "active",
                    "current_phase": "classification",
                    "progress": {
                        "total_devices_mentioned": 0,
                        "devices_confirmed": 0,
                        "devices_pending": 0,
                        "completion_percentage": 30,
                    },
                    "conversation_summary": {
                        "total_turns": 0,
                        "last_activity": datetime.now().isoformat(),
                    },
                }
            except Exception as e:
                logger.error(f"Failed to get interview status: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to get interview status", 500)

        # Discovery endpoints
        @self.app.post("/api/v1/discovery/scan")
        async def start_discovery_scan(
            scan_request: DiscoveryScan,
            current_user: str = Depends(self.get_current_user),
        ):
            """Trigger automatic device discovery across protocols."""
            try:
                scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(scan_request)}"

                # Start discovery scan (implement discovery manager)
                return {
                    "scan_id": scan_id,
                    "status": "running",
                    "started_at": datetime.now().isoformat(),
                    "estimated_completion": (
                        datetime.now() + timedelta(seconds=scan_request.timeout_seconds)
                    ).isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to start discovery scan: {e}")
                raise APIError(
                    "SCAN_START_FAILED", "Failed to start discovery scan", 500
                )

        @self.app.get("/api/v1/discovery/scan/{scan_id}")
        async def get_discovery_results(
            scan_id: str, current_user: str = Depends(self.get_current_user)
        ):
            """Get results from a discovery scan."""
            try:
                # Get scan results (implement discovery manager)
                return {
                    "scan_id": scan_id,
                    "status": "completed",
                    "results": {"mdns": [], "upnp": [], "bluetooth": []},
                    "total_devices_found": 0,
                    "completed_at": datetime.now().isoformat(),
                }
            except Exception as e:
                logger.error(f"Failed to get discovery results: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to get discovery results", 500)

        # Integration template endpoints
        @self.app.get("/api/v1/integrations/templates")
        async def get_integration_templates(
            brand: Optional[str] = None,
            device_class: Optional[str] = None,
            current_user: str = Depends(self.get_current_user),
        ):
            """Get available integration templates."""
            try:
                # Filter templates based on parameters
                templates = []  # Implement template manager

                return {"templates": templates}
            except Exception as e:
                logger.error(f"Failed to get integration templates: {e}")
                raise APIError(
                    "INTERNAL_ERROR", "Failed to get integration templates", 500
                )

        @self.app.post("/api/v1/integrations/classify")
        async def classify_device(
            classification_request: DeviceClassification,
            current_user: str = Depends(self.get_current_user),
        ):
            """Classify a device description using LLM."""
            try:
                # Use consciousness engine or dedicated NLP for classification
                classifications = []  # Implement device classifier

                return {"classifications": classifications}
            except Exception as e:
                logger.error(f"Failed to classify device: {e}")
                raise APIError(
                    "CLASSIFICATION_FAILED", "Failed to classify device", 500
                )

        # SAFLA Loop endpoints
        @self.app.get("/api/v1/safla/status")
        async def get_safla_status(current_user: str = Depends(self.get_current_user)):
            """Get SAFLA loop system status."""
            try:
                # Get SAFLA status from consciousness engine
                safla_status = {"active_loops": 0, "loops": []}

                if self.consciousness and hasattr(
                    self.consciousness, "safla_orchestrator"
                ):
                    # Get actual SAFLA status
                    pass

                return safla_status
            except Exception as e:
                logger.error(f"Failed to get SAFLA status: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to get SAFLA status", 500)

        @self.app.post("/api/v1/safla/trigger")
        async def trigger_safla_loop(
            trigger_request: SAFLATrigger,
            current_user: str = Depends(self.get_current_user),
        ):
            """Manually trigger a SAFLA loop iteration."""
            try:
                trigger_id = f"trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(trigger_request)}"

                # Trigger SAFLA loop
                return {
                    "loop_id": trigger_request.loop_id,
                    "trigger_id": trigger_id,
                    "status": "initiated",
                    "estimated_completion": 5000,
                }
            except Exception as e:
                logger.error(f"Failed to trigger SAFLA loop: {e}")
                raise APIError("TRIGGER_FAILED", "Failed to trigger SAFLA loop", 500)

        # Digital Twin endpoints
        @self.app.get("/api/v1/twins")
        async def get_digital_twins(
            device_id: Optional[str] = None,
            sync_status: Optional[str] = None,
            fidelity_level: Optional[str] = None,
            current_user: str = Depends(self.get_current_user),
        ):
            """List all digital twins in the system."""
            if not self.digital_twin_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Digital twin manager not available", 503
                )

            try:
                twins = await self.digital_twin_manager.get_twins(
                    device_id=device_id,
                    sync_status=sync_status,
                    fidelity_level=fidelity_level,
                )

                return {
                    "twins": twins,
                    "total": len(twins),
                    "synchronized": len(
                        [t for t in twins if t.get("sync_status") == "synchronized"]
                    ),
                    "out_of_sync": len(
                        [t for t in twins if t.get("sync_status") != "synchronized"]
                    ),
                }
            except Exception as e:
                logger.error(f"Failed to get digital twins: {e}")
                raise APIError("INTERNAL_ERROR", "Failed to get digital twins", 500)

        @self.app.post("/api/v1/twins")
        async def create_digital_twin(
            twin_request: TwinCreate, current_user: str = Depends(self.get_current_user)
        ):
            """Create a new digital twin for a device."""
            if not self.digital_twin_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Digital twin manager not available", 503
                )

            try:
                twin = await self.digital_twin_manager.create_twin(
                    device_id=twin_request.device_id,
                    fidelity_level=twin_request.fidelity_level,
                    config=twin_request.config,
                )

                return twin
            except Exception as e:
                logger.error(f"Failed to create digital twin: {e}")
                raise APIError(
                    "TWIN_CREATION_FAILED", "Failed to create digital twin", 500
                )

        # Scenario endpoints
        @self.app.post("/api/v1/scenarios")
        async def create_scenario(
            scenario: ScenarioCreate, current_user: str = Depends(self.get_current_user)
        ):
            """Create and run a scenario simulation."""
            if not self.simulator_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Simulator manager not available", 503
                )

            try:
                scenario_id = await self.simulator_manager.create_scenario(
                    name=scenario.name,
                    description=scenario.description,
                    duration=scenario.duration,
                    events=scenario.events,
                    twin_ids=scenario.twin_ids,
                )

                return {
                    "scenario_id": scenario_id,
                    "status": "running",
                    "estimated_completion": (
                        datetime.now() + timedelta(seconds=scenario.duration)
                    ).isoformat(),
                    "affected_twins": len(scenario.twin_ids),
                    "simulation_rate": 10.0,
                }
            except Exception as e:
                logger.error(f"Failed to create scenario: {e}")
                raise APIError(
                    "SCENARIO_CREATION_FAILED", "Failed to create scenario", 500
                )

        # Prediction endpoints
        @self.app.post("/api/v1/predictions/what-if")
        async def run_what_if_analysis(
            analysis: WhatIfAnalysis, current_user: str = Depends(self.get_current_user)
        ):
            """Run what-if analysis using digital twins."""
            if not self.digital_twin_manager:
                raise APIError(
                    "SERVICE_UNAVAILABLE", "Digital twin manager not available", 503
                )

            try:
                analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(analysis)}"

                # Run what-if analysis
                results = await self.digital_twin_manager.run_what_if_analysis(
                    scenario=analysis.scenario,
                    changes=analysis.changes,
                    duration=analysis.duration,
                    metrics=analysis.metrics,
                )

                return {
                    "analysis_id": analysis_id,
                    "status": "completed",
                    "results": results,
                    "recommendations": [],
                }
            except Exception as e:
                logger.error(f"Failed to run what-if analysis: {e}")
                raise APIError("ANALYSIS_FAILED", "Failed to run what-if analysis", 500)

        # WebSocket endpoint
        @self.app.websocket("/api/v1/realtime")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await self.connection_manager.connect(websocket)
        
        # Demo WebSocket endpoint (non-authenticated)
        @self.app.websocket("/ws")
        async def demo_websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for demo dashboard."""
            await self.connection_manager.connect(websocket)
            
            try:
                while True:
                    # Send periodic status updates
                    status = {
                        "type": "status_update",
                        "timestamp": datetime.now().isoformat(),
                        "consciousness": {},
                        "devices": {},
                        "running_scenario": None,
                        "device_states": {}
                    }
                    
                    # Get consciousness status
                    if self.consciousness:
                        try:
                            cs = await self.consciousness.get_status()
                            status["consciousness"] = {
                                "active": self.consciousness.is_active,
                                "emotional_state": cs.get("emotional_state", "content"),
                                "mood": cs.get("mood", "stable"),
                                "active_concerns": cs.get("active_concerns", [])
                            }
                        except:
                            status["consciousness"] = {"active": False}
                    
                    # Get device status
                    if self.device_controller:
                        try:
                            devices = await self.device_controller.get_devices()
                            status["devices"] = {
                                "total": len(devices),
                                "active": len([d for d in devices if d.get("status") == "active"])
                            }
                            # Include device states
                            for idx, device in enumerate(devices):
                                status["device_states"][str(idx)] = {
                                    "status": device.get("status", "offline"),
                                    "type": device.get("type", "unknown"),
                                    "name": device.get("name", f"Device {idx}")
                                }
                        except:
                            status["devices"] = {"total": 0, "active": 0}
                    
                    await websocket.send_json(status)
                    await asyncio.sleep(2)  # Update every 2 seconds
                    
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"Demo WebSocket error: {e}")
                self.connection_manager.disconnect(websocket)

            try:
                # Send initial status
                status = await self._get_realtime_status()
                await self.connection_manager.send_personal_message(status, websocket)

                while True:
                    # Wait for client messages
                    data = await websocket.receive_json()

                    if data.get("type") == "init":
                        # Handle client initialization
                        subscriptions = data.get("data", {}).get("subscriptions", [])
                        self.connection_manager.client_subscriptions[
                            websocket
                        ] = subscriptions

                        await self.connection_manager.send_personal_message(
                            {
                                "type": "init_complete",
                                "data": {
                                    "subscriptions": subscriptions,
                                    "client_id": id(websocket),
                                },
                            },
                            websocket,
                        )

                    elif data.get("type") == "ping":
                        # Handle ping
                        await self.connection_manager.send_personal_message(
                            {"type": "pong", "timestamp": datetime.now().isoformat()},
                            websocket,
                        )

            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.connection_manager.disconnect(websocket)

    async def _get_realtime_status(self) -> Dict[str, Any]:
        """Get current status for real-time updates."""
        try:
            consciousness_status = {}
            if self.consciousness:
                consciousness_status = await self.consciousness.get_status()

            device_status = {}
            if self.device_controller:
                devices = await self.device_controller.get_devices()
                device_status = {
                    "total": len(devices),
                    "active": len([d for d in devices if d.get("status") == "active"]),
                }

            return {
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "consciousness": consciousness_status,
                    "devices": device_status,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get realtime status: {e}")
            return {
                "type": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the API server."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            log_level="info" if not debug else "debug",
        )


def create_api(consciousness_engine: ConsciousnessEngine, **kwargs) -> ConsciousnessAPI:
    """Create and configure the Consciousness API."""
    return ConsciousnessAPI(consciousness_engine, **kwargs)


# For development/testing
if __name__ == "__main__":
    # Create a basic consciousness engine for testing
    from ..core.consciousness_engine import ConsciousnessEngine

    consciousness = ConsciousnessEngine()
    api = create_api(consciousness)
    api.run(debug=True)
