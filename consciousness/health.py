"""
Comprehensive health checking system for the House Consciousness System.
"""

import asyncio
import shutil
from datetime import datetime, timedelta
from typing import Any, Dict

import psutil
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session
from .models.consciousness import ConsciousnessSession
from .models.entities import Device


class HealthChecker:
    """Comprehensive health checking for the consciousness system."""

    def __init__(self):
        self.checks = {
            "database": self._check_database,
            "consciousness_engine": self._check_consciousness_engine,
            "devices": self._check_devices,
            "memory": self._check_memory_usage,
            "disk_space": self._check_disk_space,
            "redis": self._check_redis,
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "overall": True,
        }

        for check_name, check_func in self.checks.items():
            try:
                result = await check_func()
                health_status["checks"][check_name] = result
                if not result["healthy"]:
                    health_status["overall"] = False
                    if result.get("critical", False):
                        health_status["status"] = "critical"
                    elif health_status["status"] != "critical":
                        health_status["status"] = "degraded"
            except Exception as e:
                health_status["checks"][check_name] = {
                    "healthy": False,
                    "error": str(e),
                    "critical": True,
                }
                health_status["overall"] = False
                health_status["status"] = "critical"

        return health_status

    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            async with get_async_session() as session:
                # Test basic connectivity
                start_time = datetime.utcnow()
                await session.execute(text("SELECT 1"))
                response_time = (datetime.utcnow() - start_time).total_seconds()

                # Check recent activity
                recent_sessions = await session.execute(
                    select(func.count(ConsciousnessSession.id)).where(
                        ConsciousnessSession.created_at
                        >= datetime.utcnow() - timedelta(hours=1)
                    )
                )
                session_count = recent_sessions.scalar()

                return {
                    "healthy": response_time < 1.0,
                    "response_time_ms": response_time * 1000,
                    "recent_sessions": session_count,
                    "critical": response_time > 5.0,
                }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": True}

    async def _check_consciousness_engine(self) -> Dict[str, Any]:
        """Check consciousness engine status."""
        try:
            async with get_async_session() as session:
                # Check for active sessions
                active_sessions = await session.execute(
                    select(ConsciousnessSession)
                    .where(ConsciousnessSession.status == "active")
                    .order_by(ConsciousnessSession.created_at.desc())
                    .limit(1)
                )
                latest_session = active_sessions.scalar_one_or_none()

                if not latest_session:
                    return {
                        "healthy": False,
                        "error": "No active consciousness sessions found",
                        "critical": True,
                    }

                # Check session age
                session_age = datetime.utcnow() - latest_session.created_at
                session_age_minutes = session_age.total_seconds() / 60

                return {
                    "healthy": session_age_minutes < 10,  # Session should be recent
                    "active_session": latest_session.session_id,
                    "session_age_minutes": session_age_minutes,
                    "events_processed": latest_session.events_processed,
                    "critical": session_age_minutes > 30,
                }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": True}

    async def _check_devices(self) -> Dict[str, Any]:
        """Check device connectivity status."""
        try:
            async with get_async_session() as session:
                device_stats = await session.execute(
                    select(
                        func.count(Device.id).label("total"),
                        func.sum(
                            func.case([(Device.status == "online", 1)], else_=0)
                        ).label("online"),
                        func.sum(
                            func.case([(Device.status == "error", 1)], else_=0)
                        ).label("error"),
                    )
                )
                stats = device_stats.first()

                if not stats or stats.total == 0:
                    return {
                        "healthy": True,  # No devices is not critical
                        "total_devices": 0,
                        "online_devices": 0,
                        "error_devices": 0,
                        "online_percentage": 0,
                    }

                online_pct = (stats.online / stats.total) * 100
                error_pct = (stats.error / stats.total) * 100

                return {
                    "healthy": online_pct >= 80 and error_pct < 20,
                    "total_devices": stats.total,
                    "online_devices": stats.online,
                    "error_devices": stats.error,
                    "online_percentage": online_pct,
                    "critical": online_pct < 50 or error_pct > 50,
                }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": False}

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_pct = memory.percent

            return {
                "healthy": memory_pct < 80,
                "memory_usage_percent": memory_pct,
                "available_gb": memory.available / (1024**3),
                "total_gb": memory.total / (1024**3),
                "critical": memory_pct > 95,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": False}

    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            # Check data directory space
            total, used, free = shutil.disk_usage("/app/data")

            total_gb = total / (1024**3)
            used_gb = used / (1024**3)
            free_gb = free / (1024**3)
            used_pct = (used / total) * 100

            return {
                "healthy": used_pct < 80 and free_gb > 1,
                "disk_usage_percent": used_pct,
                "free_gb": free_gb,
                "total_gb": total_gb,
                "critical": used_pct > 95 or free_gb < 0.5,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": False}

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            import redis.asyncio as redis

            from .config import settings

            redis_client = redis.from_url(
                settings.REDIS_URL
                if hasattr(settings, "REDIS_URL")
                else "redis://localhost:6379/0"
            )

            # Test connectivity
            start_time = datetime.utcnow()
            await redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()

            # Get Redis info
            info = await redis_client.info()
            memory_usage = info.get("used_memory", 0)
            memory_usage_mb = memory_usage / (1024**2)

            await redis_client.close()

            return {
                "healthy": response_time < 0.1,
                "response_time_ms": response_time * 1000,
                "memory_usage_mb": memory_usage_mb,
                "connected_clients": info.get("connected_clients", 0),
                "critical": response_time > 1.0,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e), "critical": True}


# Global health checker instance
health_checker = HealthChecker()
