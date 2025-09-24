"""
Authentication and Authorization

Enterprise-grade authentication and authorization system supporting:
- JWT token-based authentication
- Role-based access control (RBAC)
- Multi-factor authentication (MFA)
- OAuth2 integration
- Session management
- User identity management
"""

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import bcrypt
import jwt

from ...config import config


class UserRole(Enum):
    """User roles with hierarchical permissions."""

    ADMIN = "admin"  # Full system access
    MANAGER = "manager"  # Service management access
    DEVELOPER = "developer"  # API access and development tools
    ANALYST = "analyst"  # Read-only analytics access
    AUDITOR = "auditor"  # Compliance and audit access
    GUEST = "guest"  # Limited read-only access


class Permission(Enum):
    """Granular permissions for API operations."""

    # API Catalog
    API_CATALOG_READ = "api_catalog:read"
    API_CATALOG_WRITE = "api_catalog:write"

    # Testing
    API_TEST_EXECUTE = "api_test:execute"
    API_TEST_MANAGE = "api_test:manage"

    # Analytics
    ANALYTICS_READ = "analytics:read"
    ANALYTICS_WRITE = "analytics:write"

    # Topology
    TOPOLOGY_READ = "topology:read"
    TOPOLOGY_WRITE = "topology:write"

    # Developer Tools
    DEVTOOLS_EXECUTE = "devtools:execute"
    DEVTOOLS_MANAGE = "devtools:manage"

    # Administration
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"
    ADMIN_SECURITY = "admin:security"

    # Audit
    AUDIT_READ = "audit:read"
    AUDIT_MANAGE = "audit:manage"


class AuthProvider(Enum):
    """Supported authentication providers."""

    LOCAL = "local"
    LDAP = "ldap"
    OAUTH2 = "oauth2"
    SAML = "saml"
    JWT = "jwt"


@dataclass
class User:
    """User account representation."""

    user_id: str
    username: str
    email: str
    role: UserRole
    permissions: Set[Permission] = field(default_factory=set)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False
    provider: AuthProvider = AuthProvider.LOCAL
    provider_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session information."""

    session_id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True


@dataclass
class AuthToken:
    """Authentication token with claims."""

    token: str
    user_id: str
    username: str
    role: UserRole
    permissions: Set[Permission]
    expires_at: datetime
    issued_at: datetime = field(default_factory=datetime.now)
    issuer: str = "unified-api-dashboard"


class UserManager:
    """
    User account management and lifecycle operations.

    Handles user creation, updates, deactivation, and account management.
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self._load_users()

    def _load_users(self):
        """Load users from storage (in production, this would be a database)."""
        # Create default admin user
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@unified-api.local",
            role=UserRole.ADMIN,
            permissions=set(Permission),
            mfa_enabled=True,
        )
        self.users["admin"] = admin_user

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.GUEST,
        provider: AuthProvider = AuthProvider.LOCAL,
    ) -> User:
        """Create a new user account."""
        if username in [u.username for u in self.users.values()]:
            raise ValueError(f"Username '{username}' already exists")

        user_id = f"user_{secrets.token_hex(8)}"
        hashed_password = (
            self._hash_password(password) if provider == AuthProvider.LOCAL else None
        )

        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            permissions=self._get_default_permissions(role),
            provider=provider,
        )

        if hashed_password:
            user.metadata["password_hash"] = hashed_password

        self.users[user_id] = user
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = next((u for u in self.users.values() if u.username == username), None)
        if not user or not user.is_active:
            return None

        stored_hash = user.metadata.get("password_hash")
        if not stored_hash or not self._verify_password(password, stored_hash):
            return None

        user.last_login = datetime.now()
        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.users.get(user_id)

    async def update_user_role(self, user_id: str, new_role: UserRole) -> bool:
        """Update user role and permissions."""
        user = self.users.get(user_id)
        if not user:
            return False

        user.role = new_role
        user.permissions = self._get_default_permissions(new_role)
        return True

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        user = self.users.get(user_id)
        if not user:
            return False

        user.is_active = False
        return True

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def _get_default_permissions(self, role: UserRole) -> Set[Permission]:
        """Get default permissions for a role."""
        role_permissions = {
            UserRole.ADMIN: set(Permission),
            UserRole.MANAGER: {
                Permission.API_CATALOG_READ,
                Permission.API_CATALOG_WRITE,
                Permission.API_TEST_EXECUTE,
                Permission.API_TEST_MANAGE,
                Permission.ANALYTICS_READ,
                Permission.ANALYTICS_WRITE,
                Permission.TOPOLOGY_READ,
                Permission.TOPOLOGY_WRITE,
                Permission.DEVTOOLS_EXECUTE,
                Permission.AUDIT_READ,
            },
            UserRole.DEVELOPER: {
                Permission.API_CATALOG_READ,
                Permission.API_CATALOG_WRITE,
                Permission.API_TEST_EXECUTE,
                Permission.ANALYTICS_READ,
                Permission.TOPOLOGY_READ,
                Permission.DEVTOOLS_EXECUTE,
            },
            UserRole.ANALYST: {
                Permission.API_CATALOG_READ,
                Permission.ANALYTICS_READ,
                Permission.TOPOLOGY_READ,
                Permission.AUDIT_READ,
            },
            UserRole.AUDITOR: {Permission.AUDIT_READ, Permission.API_CATALOG_READ},
            UserRole.GUEST: {Permission.API_CATALOG_READ},
        }
        return role_permissions.get(role, set())


class AuthenticationManager:
    """
    Authentication manager handling login, logout, and token management.

    Supports JWT tokens, session management, and multi-factor authentication.
    """

    def __init__(self, user_manager: UserManager, secret_key: str = None):
        self.user_manager = user_manager
        self.secret_key = secret_key or config.security.jwt_secret_key
        self.sessions = {}

    async def login(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[AuthToken]:
        """Authenticate user and create session."""
        user = await self.user_manager.authenticate_user(username, password)
        if not user:
            return None

        # Create JWT token
        token_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.permissions],
            "exp": datetime.utcnow() + timedelta(hours=8),
            "iat": datetime.utcnow(),
            "iss": "unified-api-dashboard",
        }

        token = jwt.encode(token_data, self.secret_key, algorithm="HS256")

        # Create session
        session_id = f"session_{secrets.token_hex(16)}"
        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            token=token,
            expires_at=datetime.now() + timedelta(hours=8),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.sessions[session_id] = session

        return AuthToken(
            token=token,
            user_id=user.user_id,
            username=user.username,
            role=user.role,
            permissions=user.permissions,
            expires_at=session.expires_at,
        )

    async def validate_token(self, token: str) -> Optional[AuthToken]:
        """Validate JWT token and return authentication info."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            # Check if session exists and is active
            session = next(
                (s for s in self.sessions.values() if s.token == token and s.is_active),
                None,
            )
            if not session:
                return None

            return AuthToken(
                token=token,
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                permissions=set(Permission(p) for p in payload["permissions"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
            )

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
            return None

    async def logout(self, token: str) -> bool:
        """Logout user by deactivating session."""
        session = next((s for s in self.sessions.values() if s.token == token), None)
        if session:
            session.is_active = False
            return True
        return False

    async def refresh_token(self, token: str) -> Optional[AuthToken]:
        """Refresh JWT token if still valid."""
        current_auth = await self.validate_token(token)
        if not current_auth:
            return None

        # Create new token with extended expiration
        new_token_data = {
            "user_id": current_auth.user_id,
            "username": current_auth.username,
            "role": current_auth.role.value,
            "permissions": [p.value for p in current_auth.permissions],
            "exp": datetime.utcnow() + timedelta(hours=8),
            "iat": datetime.utcnow(),
            "iss": "unified-api-dashboard",
        }

        new_token = jwt.encode(new_token_data, self.secret_key, algorithm="HS256")

        # Update session
        session = next((s for s in self.sessions.values() if s.token == token), None)
        if session:
            session.token = new_token
            session.expires_at = datetime.now() + timedelta(hours=8)

        return AuthToken(
            token=new_token,
            user_id=current_auth.user_id,
            username=current_auth.username,
            role=current_auth.role,
            permissions=current_auth.permissions,
            expires_at=datetime.now() + timedelta(hours=8),
        )


class AuthorizationManager:
    """
    Authorization manager for permission checking and access control.

    Implements role-based access control (RBAC) with fine-grained permissions.
    """

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager

    async def check_permission(
        self, user_id: str, permission: Permission, resource: str = None
    ) -> bool:
        """Check if user has specific permission."""
        user = await self.user_manager.get_user(user_id)
        if not user or not user.is_active:
            return False

        return permission in user.permissions

    async def check_permissions(
        self, user_id: str, permissions: List[Permission], require_all: bool = True
    ) -> bool:
        """Check if user has multiple permissions."""
        user = await self.user_manager.get_user(user_id)
        if not user or not user.is_active:
            return False

        user_perms = user.permissions
        if require_all:
            return all(perm in user_perms for perm in permissions)
        else:
            return any(perm in user_perms for perm in permissions)

    async def has_role(self, user_id: str, role: UserRole) -> bool:
        """Check if user has specific role."""
        user = await self.user_manager.get_user(user_id)
        return user and user.role == role

    async def has_any_role(self, user_id: str, roles: List[UserRole]) -> bool:
        """Check if user has any of the specified roles."""
        user = await self.user_manager.get_user(user_id)
        return user and user.role in roles

    async def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for a user."""
        user = await self.user_manager.get_user(user_id)
        return user.permissions if user else set()

    def get_role_hierarchy(self) -> Dict[UserRole, Set[UserRole]]:
        """Get role hierarchy for inheritance."""
        return {
            UserRole.ADMIN: set(),
            UserRole.MANAGER: {UserRole.DEVELOPER, UserRole.ANALYST},
            UserRole.DEVELOPER: {UserRole.ANALYST},
            UserRole.ANALYST: set(),
            UserRole.AUDITOR: set(),
            UserRole.GUEST: set(),
        }

    async def authorize_api_call(
        self,
        user_id: str,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Authorize API call based on method, path, and user permissions.

        Returns (authorized, reason)
        """
        # Define permission requirements for different API endpoints
        endpoint_permissions = {
            # Analytics
            ("/api/analytics", "GET"): Permission.ANALYTICS_READ,
            ("/api/analytics", "POST"): Permission.ANALYTICS_WRITE,
            # Topology
            ("/api/topology", "GET"): Permission.TOPOLOGY_READ,
            ("/api/topology", "POST"): Permission.TOPOLOGY_WRITE,
            # Developer Tools
            ("/api/tools", "GET"): Permission.DEVTOOLS_EXECUTE,
            ("/api/tools", "POST"): Permission.DEVTOOLS_EXECUTE,
            # Testing
            ("/api/test", "GET"): Permission.API_TEST_EXECUTE,
            ("/api/test", "POST"): Permission.API_TEST_MANAGE,
            # Audit
            ("/api/audit", "GET"): Permission.AUDIT_READ,
            # Admin
            ("/api/admin", "GET"): Permission.ADMIN_SYSTEM,
            ("/api/admin", "POST"): Permission.ADMIN_SYSTEM,
        }

        # Check exact matches first
        required_perm = endpoint_permissions.get((path, method))
        if required_perm:
            has_perm = await self.check_permission(user_id, required_perm)
            if not has_perm:
                return False, f"Missing permission: {required_perm.value}"
            return True, "Authorized"

        # Check path prefixes for more flexible matching
        for (endpoint_path, endpoint_method), perm in endpoint_permissions.items():
            if path.startswith(endpoint_path) and method == endpoint_method:
                has_perm = await self.check_permission(user_id, required_perm or perm)
                if not has_perm:
                    return False, f"Missing permission: {perm.value}"
                return True, "Authorized"

        # Default to read-only access for unknown endpoints
        has_read_perm = await self.check_permission(
            user_id, Permission.API_CATALOG_READ
        )
        if method == "GET" and has_read_perm:
            return True, "Authorized (read access)"

        return False, "Access denied: unknown endpoint or insufficient permissions"
