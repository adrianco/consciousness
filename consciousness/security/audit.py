"""
Audit logging system for the House Consciousness System.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_async_session
from ..models.base import BaseModel


class AuditLog(BaseModel):
    """Audit log model for security events."""

    __tablename__ = "audit_logs"

    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), index=True)
    session_id = Column(String(255), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    resource = Column(String(255), index=True)
    action = Column(String(100), nullable=False, index=True)
    outcome = Column(String(50), nullable=False, index=True)  # success, failure, error
    details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Create composite indexes for common queries
    __table_args__ = (
        Index("idx_audit_event_outcome", "event_type", "outcome"),
        Index("idx_audit_timestamp_type", "timestamp", "event_type"),
        Index("idx_audit_user_action", "user_id", "action"),
    )


class AuditLogger:
    """Centralized audit logging system."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.session:
            return self.session
        return get_async_session()

    async def log_authentication(
        self,
        user_id: str,
        outcome: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log authentication events."""
        await self._log_event(
            event_type="authentication",
            user_id=user_id,
            session_id=session_id,
            action="login",
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_device_access(
        self,
        device_id: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """Log device access events."""
        await self._log_event(
            event_type="device_access",
            user_id=user_id,
            session_id=session_id,
            resource=f"device:{device_id}",
            action=action,
            outcome=outcome,
            details=details or {},
            ip_address=ip_address,
        )

    async def log_data_access(
        self,
        resource: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """Log data access events."""
        await self._log_event(
            event_type="data_access",
            user_id=user_id,
            session_id=session_id,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {},
            ip_address=ip_address,
        )

    async def log_security_event(
        self,
        event_type: str,
        outcome: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log security-related events."""
        await self._log_event(
            event_type=f"security:{event_type}",
            user_id=user_id,
            session_id=session_id,
            action=event_type,
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_consciousness_event(
        self,
        action: str,
        outcome: str,
        consciousness_session_id: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """Log consciousness system events."""
        await self._log_event(
            event_type="consciousness",
            user_id=user_id,
            session_id=consciousness_session_id,
            resource=f"consciousness_session:{consciousness_session_id}",
            action=action,
            outcome=outcome,
            details=details or {},
        )

    async def log_api_request(
        self,
        endpoint: str,
        method: str,
        outcome: str,
        response_time_ms: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        """Log API request events."""
        details = {"method": method, "response_time_ms": response_time_ms}
        if status_code:
            details["status_code"] = status_code

        await self._log_event(
            event_type="api_request",
            user_id=user_id,
            session_id=session_id,
            resource=f"endpoint:{endpoint}",
            action=method.lower(),
            outcome=outcome,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def _log_event(
        self,
        event_type: str,
        action: str,
        outcome: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Internal method to log audit events."""
        try:
            # Sanitize sensitive data
            clean_details = self._sanitize_details(details or {})

            audit_entry = AuditLog(
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent[:1000]
                if user_agent
                else None,  # Truncate user agent
                resource=resource,
                action=action,
                outcome=outcome,
                details=clean_details,
            )

            if self.session:
                self.session.add(audit_entry)
                await self.session.commit()
            else:
                async with get_async_session() as session:
                    session.add(audit_entry)
                    await session.commit()

        except Exception as e:
            # Log to standard logging if database logging fails
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to write audit log: {e}")

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from audit details."""
        sensitive_keys = {
            "password",
            "secret",
            "token",
            "key",
            "credential",
            "auth",
            "authorization",
            "signature",
            "hash",
        }

        sanitized = {}
        for key, value in details.items():
            key_lower = key.lower()

            # Check if key contains sensitive words
            if any(sensitive_word in key_lower for sensitive_word in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # Truncate long strings
                if isinstance(value, str) and len(value) > 1000:
                    sanitized[key] = value[:1000] + "..."
                else:
                    sanitized[key] = value

        return sanitized


class SecurityEventLogger:
    """Specialized logger for security events."""

    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger

    async def log_failed_login(
        self,
        user_id: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log failed login attempt."""
        await self.audit_logger.log_authentication(
            user_id=user_id,
            outcome="failure",
            details={"reason": reason, "event": "login_failed"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_successful_login(
        self,
        user_id: str,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Log successful login."""
        await self.audit_logger.log_authentication(
            user_id=user_id,
            outcome="success",
            details={"event": "login_successful"},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
        )

    async def log_logout(
        self, user_id: str, session_id: str, reason: str = "user_initiated"
    ):
        """Log user logout."""
        await self.audit_logger.log_authentication(
            user_id=user_id,
            outcome="success",
            details={"event": "logout", "reason": reason},
            session_id=session_id,
        )

    async def log_rate_limit_exceeded(
        self, ip_address: str, endpoint: str, user_agent: Optional[str] = None
    ):
        """Log rate limit exceeded events."""
        await self.audit_logger.log_security_event(
            event_type="rate_limit_exceeded",
            outcome="blocked",
            details={"endpoint": endpoint, "limit_type": "request_rate"},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_unauthorized_access(
        self,
        resource: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log unauthorized access attempts."""
        await self.audit_logger.log_security_event(
            event_type="unauthorized_access",
            outcome="blocked",
            details=details or {"resource": resource},
            user_id=user_id,
            ip_address=ip_address,
        )

    async def log_device_auth_failure(
        self, device_id: str, reason: str, ip_address: Optional[str] = None
    ):
        """Log device authentication failures."""
        await self.audit_logger.log_device_access(
            device_id=device_id,
            action="authenticate",
            outcome="failure",
            details={"reason": reason},
            ip_address=ip_address,
        )
