"""
Security configuration and middleware for the House Consciousness System.
"""

import hashlib
import hmac
import time
from collections import defaultdict
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    # Authentication
    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # API Security
    API_RATE_LIMIT: str = "100/hour"
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE"]

    # SSL/TLS
    SSL_CERT_PATH: Optional[str] = None
    SSL_KEY_PATH: Optional[str] = None
    FORCE_HTTPS: bool = True

    # Database Security
    DATABASE_ENCRYPTION_KEY: Optional[str] = None

    # Device Security
    DEVICE_AUTH_TIMEOUT: int = 300  # 5 minutes
    MAX_FAILED_AUTH_ATTEMPTS: int = 5

    # Logging Security
    LOG_SENSITIVE_DATA: bool = False
    AUDIT_LOG_RETENTION_DAYS: int = 90

    class Config:
        env_file = ".env"
        case_sensitive = True


security = HTTPBearer()


class SecurityMiddleware:
    """Enhanced security middleware for the consciousness system."""

    def __init__(self, app: FastAPI, settings: SecuritySettings):
        self.app = app
        self.settings = settings
        self.failed_attempts = defaultdict(list)
        self.rate_limits = defaultdict(list)

    async def __call__(self, request: Request, call_next):
        """Process request through security middleware."""

        # Rate limiting check
        client_ip = self._get_client_ip(request)
        if self._is_rate_limited(client_ip):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Process request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client IP is rate limited."""
        now = time.time()
        window = 3600  # 1 hour
        limit = 100  # requests per hour

        # Clean old entries
        self.rate_limits[client_ip] = [
            timestamp
            for timestamp in self.rate_limits[client_ip]
            if now - timestamp < window
        ]

        # Check current count
        if len(self.rate_limits[client_ip]) >= limit:
            return True

        # Add current request
        self.rate_limits[client_ip].append(now)
        return False

    def _add_security_headers(self, response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        if self.settings.FORCE_HTTPS:
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

    def verify_request_signature(
        self, request: Request, signature: str, secret: str
    ) -> bool:
        """Verify request signature for device authentication."""
        try:
            body = request.body()
            expected_signature = hmac.new(
                secret.encode(), body, hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    def record_failed_attempt(self, identifier: str):
        """Record a failed authentication attempt."""
        now = time.time()
        window = 900  # 15 minutes

        # Clean old entries
        self.failed_attempts[identifier] = [
            timestamp
            for timestamp in self.failed_attempts[identifier]
            if now - timestamp < window
        ]

        # Add current failure
        self.failed_attempts[identifier].append(now)

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked due to failed attempts."""
        now = time.time()
        window = 900  # 15 minutes

        # Clean old entries
        self.failed_attempts[identifier] = [
            timestamp
            for timestamp in self.failed_attempts[identifier]
            if now - timestamp < window
        ]

        return (
            len(self.failed_attempts[identifier])
            >= self.settings.MAX_FAILED_AUTH_ATTEMPTS
        )


class CSRFProtection:
    """CSRF protection for form submissions."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key, message.encode(), hashlib.sha256
        ).hexdigest()

        return f"{timestamp}:{signature}"

    def verify_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Verify CSRF token."""
        try:
            timestamp_str, signature = token.split(":", 1)
            timestamp = int(timestamp_str)

            # Check token age
            if time.time() - timestamp > max_age:
                return False

            # Verify signature
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hmac.new(
                self.secret_key, message.encode(), hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, TypeError):
            return False


class InputValidator:
    """Input validation and sanitization."""

    @staticmethod
    def validate_device_id(device_id: str) -> bool:
        """Validate device ID format."""
        if not device_id or len(device_id) > 50:
            return False

        # Allow alphanumeric, hyphens, and underscores
        return device_id.replace("-", "").replace("_", "").isalnum()

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id or len(session_id) != 36:
            return False

        # Check UUID format
        parts = session_id.split("-")
        return (
            len(parts) == 5
            and len(parts[0]) == 8
            and len(parts[1]) == 4
            and len(parts[2]) == 4
            and len(parts[3]) == 4
            and len(parts[4]) == 12
        )

    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Sanitize log message to prevent log injection."""
        if not message:
            return ""

        # Remove line breaks and control characters
        sanitized = message.replace("\n", " ").replace("\r", " ")
        sanitized = "".join(
            char for char in sanitized if ord(char) >= 32 or char == " "
        )

        # Truncate if too long
        return sanitized[:1000] if len(sanitized) > 1000 else sanitized
