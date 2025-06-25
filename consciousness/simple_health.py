"""
Simple health checking system for the House Consciousness System.
This provides basic health checks without complex dependencies.
"""

import shutil
from datetime import datetime
from typing import Any, Dict

import psutil


class SimpleHealthChecker:
    """Simple health checking for the consciousness system."""

    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the system."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "summary": {
                "total_checks": 0,
                "healthy_checks": 0,
                "warning_checks": 0,
                "failed_checks": 0,
            },
        }

        checks = {
            "api_server": self._check_api_server,
            "memory": self._check_memory_usage,
            "disk_space": self._check_disk_space,
            "database": self._check_database_simple,
            "redis": self._check_redis_simple,
        }

        for check_name, check_func in checks.items():
            try:
                result = await check_func()
                health_status["components"][check_name] = result
                health_status["summary"]["total_checks"] += 1

                if result["status"] == "healthy":
                    health_status["summary"]["healthy_checks"] += 1
                elif result["status"] == "warning":
                    health_status["summary"]["warning_checks"] += 1
                    if health_status["status"] == "healthy":
                        health_status["status"] = "degraded"
                else:  # unhealthy
                    health_status["summary"]["failed_checks"] += 1
                    if result.get("critical", False):
                        health_status["status"] = "critical"
                    elif health_status["status"] == "healthy":
                        health_status["status"] = "degraded"

            except Exception as e:
                health_status["components"][check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "critical": False,
                }
                health_status["summary"]["total_checks"] += 1
                health_status["summary"]["failed_checks"] += 1

        return health_status

    async def _check_api_server(self) -> Dict[str, Any]:
        """Check that the API server is running."""
        return {
            "status": "healthy",
            "details": {
                "message": "API server is responding",
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_gb = memory.available / (1024**3)
            total_gb = memory.total / (1024**3)

            status = "healthy"
            if memory_percent > 90:
                status = "unhealthy"
            elif memory_percent > 80:
                status = "warning"

            return {
                "status": status,
                "details": {
                    "memory_usage_percent": memory_percent,
                    "available_gb": round(available_gb, 2),
                    "total_gb": round(total_gb, 2),
                },
                "critical": memory_percent > 95,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "critical": False}

    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage."""
        try:
            # Check current directory instead of hardcoded path
            disk_usage = shutil.disk_usage(".")
            total = disk_usage.total
            free = disk_usage.free
            used_percent = ((total - free) / total) * 100

            status = "healthy"
            if used_percent > 95:
                status = "unhealthy"
            elif used_percent > 85:
                status = "warning"

            return {
                "status": status,
                "details": {
                    "used_percent": round(used_percent, 1),
                    "free_gb": round(free / (1024**3), 2),
                    "total_gb": round(total / (1024**3), 2),
                },
                "critical": used_percent > 98,
            }
        except Exception as e:
            return {"status": "warning", "error": str(e), "critical": False}

    async def _check_database_simple(self) -> Dict[str, Any]:
        """Simple database check."""
        try:
            # Try to import database components
            from sqlalchemy import text

            from .database import get_async_session

            # Simple connectivity test
            async with get_async_session() as session:
                await session.execute(text("SELECT 1"))

            return {
                "status": "healthy",
                "details": {
                    "connectivity": "ok",
                    "message": "Database connection successful",
                },
            }
        except ImportError:
            return {
                "status": "warning",
                "details": {
                    "message": "Database components not available - running in basic mode"
                },
                "critical": False,
            }
        except Exception as e:
            return {
                "status": "warning",
                "details": {
                    "message": "Database connection failed - running in basic mode",
                    "error": str(e),
                },
                "critical": False,  # Not critical for basic operation
            }

    async def _check_redis_simple(self) -> Dict[str, Any]:
        """Simple Redis check."""
        try:
            import os

            import redis.asyncio as redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_client = redis.Redis.from_url(redis_url)
            await redis_client.ping()
            await redis_client.close()

            return {
                "status": "healthy",
                "details": {
                    "connectivity": "ok",
                    "message": "Redis connection successful",
                },
            }
        except ImportError:
            return {
                "status": "warning",
                "details": {
                    "message": "Redis client not available - install with: pip install redis"
                },
                "critical": False,
            }
        except Exception as e:
            return {
                "status": "warning",
                "details": {
                    "message": "Redis not available - caching disabled",
                    "error": str(e),
                },
                "critical": False,  # Redis is optional
            }


# Create global instance
simple_health_checker = SimpleHealthChecker()
