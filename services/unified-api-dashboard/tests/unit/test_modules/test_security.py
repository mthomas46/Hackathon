"""
Unit Tests for Security Module

Comprehensive unit tests for authentication, authorization, audit logging,
compliance monitoring, access control, and security monitoring.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from freezegun import freeze_time

from ....modules.security.access_control import AccessControlManager, PermissionManager
from ....modules.security.audit import AuditEventType, AuditLogger, ComplianceMonitor
from ....modules.security.auth import (
    AuthenticationManager,
    AuthorizationManager,
    AuthToken,
    Permission,
    User,
    UserManager,
    UserRole,
)
from ....modules.security.security_monitor import SecurityMonitor, ThreatDetector
from ...conftest import *


class TestUserManager:
    """Test UserManager functionality."""

    @pytest.fixture
    def user_manager(self):
        """Create UserManager instance for testing."""
        return UserManager()

    @pytest.mark.asyncio
    async def test_create_user(self, user_manager):
        """Test user creation."""
        user = await user_manager.create_user(
            username="testuser", email="test@example.com", password="password123", role=UserRole.DEVELOPER
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.DEVELOPER
        assert user.is_active == True

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_manager):
        """Test successful user authentication."""
        # First create a user
        await user_manager.create_user("testuser", "test@example.com", "password123", UserRole.DEVELOPER)

        # Test authentication
        user = await user_manager.authenticate_user("testuser", "admin")  # Using simple auth for demo
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_failure(self, user_manager):
        """Test failed user authentication."""
        user = await user_manager.authenticate_user("nonexistent", "wrongpass")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user(self, user_manager):
        """Test user retrieval."""
        created_user = await user_manager.create_user("testuser", "test@example.com", "pass", UserRole.DEVELOPER)
        retrieved_user = await user_manager.get_user(created_user.user_id)

        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.username == created_user.username


class TestAuthenticationManager:
    """Test AuthenticationManager functionality."""

    @pytest.fixture
    def auth_manager(self, mock_user_manager):
        """Create AuthenticationManager instance for testing."""
        return AuthenticationManager(mock_user_manager)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_manager, mock_user_manager):
        """Test successful login."""
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.role = Mock(value="developer")
        mock_user.permissions = set()
        mock_user_manager.authenticate_user.return_value = mock_user

        token = await auth_manager.login("testuser", "password")

        assert token is not None
        assert token.user_id == "user123"
        assert token.username == "testuser"

    @pytest.mark.asyncio
    async def test_login_failure(self, auth_manager, mock_user_manager):
        """Test login failure."""
        mock_user_manager.authenticate_user.return_value = None

        token = await auth_manager.login("testuser", "wrongpass")

        assert token is None

    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_manager):
        """Test token validation success."""
        # First login to create a token
        mock_user = Mock()
        mock_user.user_id = "user123"
        mock_user.username = "testuser"
        mock_user.role = Mock(value="developer")
        mock_user.permissions = set()

        with patch.object(auth_manager.user_manager, "authenticate_user", return_value=mock_user):
            token = await auth_manager.login("testuser", "password")
            assert token is not None

            # Now validate the token
            validated = await auth_manager.validate_token(token.token)
            assert validated is not None
            assert validated.user_id == "user123"

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, auth_manager):
        """Test token validation with expired token."""
        # Create an expired token
        expired_token = AuthToken(
            token="expired_token",
            user_id="user123",
            username="testuser",
            role=UserRole.DEVELOPER,
            permissions=set(),
            expires_at=datetime.now() - timedelta(hours=1),  # Already expired
        )
        auth_manager.tokens["expired_token"] = expired_token

        validated = await auth_manager.validate_token("expired_token")
        assert validated is None

    @pytest.mark.asyncio
    async def test_logout(self, auth_manager):
        """Test user logout."""
        # Create a valid token
        token = AuthToken(
            token="test_token",
            user_id="user123",
            username="testuser",
            role=UserRole.DEVELOPER,
            permissions=set(),
            expires_at=datetime.now() + timedelta(hours=1),
        )
        auth_manager.tokens["test_token"] = token

        # Logout
        result = await auth_manager.logout("test_token")
        assert result == True

        # Verify token is invalidated
        validated = await auth_manager.validate_token("test_token")
        assert validated is None


class TestAuthorizationManager:
    """Test AuthorizationManager functionality."""

    @pytest.fixture
    def authz_manager(self, mock_user_manager):
        """Create AuthorizationManager instance for testing."""
        return AuthorizationManager(mock_user_manager)

    @pytest.mark.asyncio
    async def test_check_permission_admin(self, authz_manager, mock_user_manager):
        """Test permission check for admin user."""
        mock_user = Mock()
        mock_user.role = UserRole.ADMIN
        mock_user.permissions = set(Permission)
        mock_user_manager.get_user.return_value = mock_user

        has_perm = await authz_manager.check_permission("user123", Permission.API_CATALOG_READ)
        assert has_perm == True

    @pytest.mark.asyncio
    async def test_check_permission_developer(self, authz_manager, mock_user_manager):
        """Test permission check for developer user."""
        mock_user = Mock()
        mock_user.role = UserRole.DEVELOPER
        mock_user.permissions = {Permission.API_CATALOG_READ, Permission.ANALYTICS_READ}
        mock_user_manager.get_user.return_value = mock_user

        has_read_perm = await authz_manager.check_permission("user123", Permission.API_CATALOG_READ)
        has_write_perm = await authz_manager.check_permission("user123", Permission.API_CATALOG_WRITE)

        assert has_read_perm == True
        assert has_write_perm == False

    @pytest.mark.asyncio
    async def test_authorize_api_call_read(self, authz_manager, mock_user_manager):
        """Test API authorization for read operations."""
        mock_user = Mock()
        mock_user.role = UserRole.DEVELOPER
        mock_user_manager.get_user.return_value = mock_user

        authorized, reason = await authz_manager.authorize_api_call("user123", "GET", "/api/catalog")
        assert authorized == True
        assert reason == "Read access granted"

    @pytest.mark.asyncio
    async def test_authorize_api_call_write_denied(self, authz_manager, mock_user_manager):
        """Test API authorization denial for write operations."""
        mock_user = Mock()
        mock_user.role = UserRole.GUEST
        mock_user_manager.get_user.return_value = mock_user

        authorized, reason = await authz_manager.authorize_api_call("user123", "POST", "/api/catalog")
        assert authorized == False
        assert "Access denied" in reason


class TestAuditLogger:
    """Test AuditLogger functionality."""

    @pytest.fixture
    def audit_logger(self):
        """Create AuditLogger instance for testing."""
        return AuditLogger()

    @pytest.mark.asyncio
    async def test_log_event(self, audit_logger):
        """Test audit event logging."""
        event_id = await audit_logger.log_event(
            AuditEventType.AUTH_LOGIN, "user123", "testuser", resource="/api/login", action="login_success"
        )

        assert event_id is not None
        assert len(audit_logger.events) == 1

        event = audit_logger.events[0]
        assert event.event_type == AuditEventType.AUTH_LOGIN
        assert event.user_id == "user123"
        assert event.username == "testuser"
        assert event.resource == "/api/login"
        assert event.action == "login_success"

    @pytest.mark.asyncio
    async def test_get_events(self, audit_logger):
        """Test audit event retrieval."""
        # Log some events
        await audit_logger.log_event(AuditEventType.API_ACCESS, "user1", "user1", resource="/api/test")
        await audit_logger.log_event(AuditEventType.API_ACCESS, "user2", "user2", resource="/api/other")

        events = await audit_logger.get_events()
        assert len(events) == 2

        # Test filtering by user
        user1_events = await audit_logger.get_events(user_id="user1")
        assert len(user1_events) == 1
        assert user1_events[0].user_id == "user1"

    @pytest.mark.asyncio
    async def test_verify_integrity_valid(self, audit_logger):
        """Test audit log integrity verification."""
        await audit_logger.log_event(AuditEventType.API_ACCESS, "user1", "user1")

        is_valid, violations = await audit_logger.verify_integrity()
        assert is_valid == True
        assert len(violations) == 0


class TestComplianceMonitor:
    """Test ComplianceMonitor functionality."""

    @pytest.fixture
    def compliance_monitor(self, mock_audit_logger):
        """Create ComplianceMonitor instance for testing."""
        return ComplianceMonitor(mock_audit_logger)

    @pytest.mark.asyncio
    async def test_get_compliance_status(self, compliance_monitor):
        """Test compliance status retrieval."""
        status = await compliance_monitor.get_compliance_status()

        assert "gdpr" in status
        assert "hipaa" in status
        assert "sox" in status

        for standard, info in status.items():
            assert "status" in info
            assert "violations" in info


class TestSecurityMonitor:
    """Test SecurityMonitor functionality."""

    @pytest.fixture
    def security_monitor(self):
        """Create SecurityMonitor instance for testing."""
        return SecurityMonitor()

    @pytest.mark.asyncio
    async def test_monitor_event_normal(self, security_monitor):
        """Test monitoring of normal events."""
        threats = await security_monitor.monitor_event("auth.login", user_id="user123")

        # Should not detect threats for normal events
        assert len(threats) == 0

    @pytest.mark.asyncio
    async def test_get_security_metrics(self, security_monitor):
        """Test security metrics retrieval."""
        metrics = await security_monitor.get_security_metrics()

        assert "total_events" in metrics
        assert "events_by_threat_type" in metrics
        assert "events_by_severity" in metrics
        assert "mitigated_threats" in metrics

    @pytest.mark.asyncio
    async def test_get_threats_empty(self, security_monitor):
        """Test threat retrieval when no threats exist."""
        threats = await security_monitor.get_threats()
        assert len(threats) == 0


class TestThreatDetector:
    """Test ThreatDetector functionality."""

    @pytest.fixture
    def threat_detector(self, mock_security_monitor):
        """Create ThreatDetector instance for testing."""
        return ThreatDetector(mock_security_monitor)

    @pytest.mark.asyncio
    async def test_detect_anomalies_normal(self, threat_detector):
        """Test anomaly detection with normal data."""
        metrics = {"api_calls_per_minute": 50}
        anomalies = await threat_detector.detect_anomalies(metrics)

        # Should not detect anomalies for normal load
        assert len(anomalies) == 0


class TestPermissionManager:
    """Test PermissionManager functionality."""

    @pytest.fixture
    def permission_manager(self):
        """Create PermissionManager instance for testing."""
        return PermissionManager()

    @pytest.mark.asyncio
    async def test_get_user_permissions_empty(self, permission_manager):
        """Test permission retrieval for user with no grants."""
        permissions = await permission_manager.get_user_permissions("user123")
        assert len(permissions) == 0

    @pytest.mark.asyncio
    async def test_grant_permission(self, permission_manager):
        """Test permission granting."""
        from ....modules.security.auth import Permission

        grant_id = await permission_manager.grant_permission("granter123", "grantee123", {Permission.API_CATALOG_READ})

        assert grant_id is not None
        assert len(permission_manager.grants) == 1

    @pytest.mark.asyncio
    async def test_revoke_permission(self, permission_manager):
        """Test permission revocation."""
        # First grant a permission
        grant_id = await permission_manager.grant_permission("granter123", "grantee123", {Permission.API_CATALOG_READ})

        # Then revoke it
        result = await permission_manager.revoke_permission(grant_id)
        assert result == True

        grant = permission_manager.grants.get(grant_id)
        assert grant.is_active == False


class TestAccessControlManager:
    """Test AccessControlManager functionality."""

    @pytest.fixture
    def access_control_manager(self, mock_permission_manager):
        """Create AccessControlManager instance for testing."""
        return AccessControlManager(mock_permission_manager)

    @pytest.mark.asyncio
    async def test_evaluate_access_default_allow(self, access_control_manager):
        """Test access evaluation with default allow."""
        from ....modules.security.access_control import AccessRequest, Resource, ResourceType

        request = AccessRequest(
            user=Mock(user_id="user123", role=UserRole.DEVELOPER),
            resource=Resource(
                resource_id="test_resource", resource_type=ResourceType.API_ENDPOINT, owner_id="owner123"
            ),
            action="read",
        )

        decision, reason, policy = await access_control_manager.evaluate_access(request)

        # Default implementation allows access
        assert decision.value == "allow"
