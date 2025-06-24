"""Security utilities for the consciousness system."""

import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_jwt_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access",
) -> str:
    """Create a JWT token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
            if token_type == "access"
            else REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": token_type})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def create_access_token(user_id: str, additional_claims: Dict[str, Any] = None) -> str:
    """Create an access token for a user."""
    claims = {"sub": user_id}
    if additional_claims:
        claims.update(additional_claims)

    return create_jwt_token(claims, token_type="access")


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token for a user."""
    return create_jwt_token(
        {"sub": user_id},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"consciousness_api_{secrets.token_urlsafe(32)}"


def verify_api_key(api_key: str) -> bool:
    """Verify an API key (implement based on your storage mechanism)."""
    # For demo purposes, accept any key starting with consciousness_api_
    # In production, verify against database
    return api_key.startswith("consciousness_api_")


def create_csrf_token() -> str:
    """Create a CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, stored_token: str) -> bool:
    """Verify a CSRF token."""
    return secrets.compare_digest(token, stored_token)


def rate_limit_key(user_id: str, endpoint: str) -> str:
    """Generate a rate limiting key."""
    return f"rate_limit:{user_id}:{endpoint}"


def sanitize_input(input_string: str) -> str:
    """Basic input sanitization."""
    if not isinstance(input_string, str):
        return str(input_string)

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", '"', "'", "&", ";", "(", ")", "{", "}", "[", "]"]
    for char in dangerous_chars:
        input_string = input_string.replace(char, "")

    return input_string.strip()


def validate_request_size(content_length: int, max_size_mb: int = 10) -> bool:
    """Validate request content size."""
    max_size_bytes = max_size_mb * 1024 * 1024
    return content_length <= max_size_bytes


class SecurityHeaders:
    """Security headers for API responses."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = {}

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is within rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key] if req_time > window_start
            ]
        else:
            self.requests[key] = []

        # Check limit
        if len(self.requests[key]) >= limit:
            return False

        # Add current request
        self.requests[key].append(now)
        return True

    def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests for a key."""
        if key not in self.requests:
            return limit
        return max(0, limit - len(self.requests[key]))


# Global rate limiter instance
rate_limiter = RateLimiter()
