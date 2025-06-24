"""
Main FastAPI application for the House Consciousness System.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .health import health_checker


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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "House Consciousness System",
        "version": "1.0.0",
        "status": "active",
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "consciousness-system",
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with all components."""
    health_status = await health_checker.get_health_status()

    # Return appropriate HTTP status code based on health
    if health_status["status"] == "critical":
        raise HTTPException(status_code=503, detail=health_status)
    elif health_status["status"] == "degraded":
        raise HTTPException(status_code=200, detail=health_status)

    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # This would be implemented with prometheus_client
    # For now, return basic metrics
    return {
        "consciousness_active_sessions": 1,
        "consciousness_total_requests": 100,
        "consciousness_device_count": 5,
    }


# Include additional routers when they're implemented
# app.include_router(api_router, prefix="/api/v1")
# app.include_router(consciousness_router, prefix="/consciousness")
# app.include_router(devices_router, prefix="/devices")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
