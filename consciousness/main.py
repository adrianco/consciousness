"""
Main FastAPI application for the House Consciousness System.
"""

import os
import random
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .demo_devices import device_simulator
from .simple_health import simple_health_checker


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
    return {
        "devices": device_simulator.get_all_devices(),
        "summary": device_simulator.get_device_summary(),
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
        if random.random() < 0.3:  # 30% chance of "finding" a new device
            import random

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


# Include additional routers when they're implemented
# app.include_router(api_router, prefix="/api/v1")
# app.include_router(consciousness_router, prefix="/consciousness")
# app.include_router(devices_router, prefix="/devices")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
