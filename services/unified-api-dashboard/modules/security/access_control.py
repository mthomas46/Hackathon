"""
Access Control and Permission Management

Advanced access control system supporting:
- Attribute-based access control (ABAC)
- Permission inheritance and delegation
- Resource-level permissions
- Time-based access restrictions
- Geographic access controls
"""

import ipaddress
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .auth import Permission, User, UserRole


class AccessDecision(Enum):
    """Access control decisions."""

    ALLOW = "allow"
    DENY = "deny"
    ABSTAIN = "abstain"


class ResourceType(Enum):
    """Types of resources that can be protected."""

    API_ENDPOINT = "api_endpoint"
    DATA_RESOURCE = "data_resource"
    USER_ACCOUNT = "user_account"
    SYSTEM_CONFIG = "system_config"
    AUDIT_LOG = "audit_log"


@dataclass
class Resource:
    """Resource definition for access control."""

    resource_id: str
    resource_type: ResourceType
    owner_id: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class AccessPolicy:
    """Access control policy with conditions."""

    policy_id: str
    name: str
    description: str
    effect: AccessDecision
    principals: List[str]  # User IDs, roles, or wildcards
    resources: List[str]  # Resource IDs or patterns
    actions: List[str]  # Allowed actions
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AccessRequest:
    """Access control request context."""

    user: User
    resource: Resource
    action: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PermissionGrant:
    """Permission delegation record."""

    grant_id: str
    granter_id: str
    grantee_id: str
    permissions: Set[Permission]
    resource_pattern: str
    conditions: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


class PermissionManager:
    """
    Fine-grained permission management with delegation support.

    Manages permissions, grants, and delegations.
    """

    def __init__(self):
        self.grants: Dict[str, PermissionGrant] = {}
        self.role_permissions: Dict[UserRole, Set[Permission]] = (
            self._get_default_role_permissions()
        )

    def _get_default_role_permissions(self) -> Dict[UserRole, Set[Permission]]:
        """Get default permissions for each role."""
        from .auth import Permission

        return {
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
                Permission.ADMIN_USERS,
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

    async def grant_permission(
        self,
        granter_id: str,
        grantee_id: str,
        permissions: Set[Permission],
        resource_pattern: str = "*",
        conditions: Dict[str, Any] = None,
        expires_at: Optional[datetime] = None,
    ) -> str:
        """Grant permissions to a user with optional conditions."""
        grant_id = f"grant_{len(self.grants) + 1}"

        grant = PermissionGrant(
            grant_id=grant_id,
            granter_id=granter_id,
            grantee_id=grantee_id,
            permissions=permissions,
            resource_pattern=resource_pattern,
            conditions=conditions or {},
            expires_at=expires_at,
        )

        self.grants[grant_id] = grant
        return grant_id

    async def revoke_permission(self, grant_id: str) -> bool:
        """Revoke a permission grant."""
        if grant_id in self.grants:
            self.grants[grant_id].is_active = False
            return True
        return False

    async def get_user_permissions(
        self, user_id: str, resource: str = None
    ) -> Set[Permission]:
        """Get effective permissions for a user, optionally for a specific resource."""
        permissions = set()

        # Add role-based permissions
        user_role = None  # Would be fetched from user manager
        if user_role:
            permissions.update(self.role_permissions.get(user_role, set()))

        # Add delegated permissions
        for grant in self.grants.values():
            if grant.is_active and grant.grantee_id == user_id:
                # Check expiration
                if grant.expires_at and datetime.now() > grant.expires_at:
                    continue

                # Check resource pattern
                if resource and not self._matches_pattern(
                    resource, grant.resource_pattern
                ):
                    continue

                permissions.update(grant.permissions)

        return permissions

    async def check_delegation_allowed(
        self, granter_id: str, permissions: Set[Permission]
    ) -> bool:
        """Check if a user can delegate specific permissions."""
        granter_permissions = await self.get_user_permissions(granter_id)
        return permissions.issubset(granter_permissions)

    def _matches_pattern(self, resource: str, pattern: str) -> bool:
        """Check if resource matches a permission pattern."""
        if pattern == "*":
            return True

        # Convert glob pattern to regex
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", resource))


class AccessControlManager:
    """
    Advanced access control with ABAC (Attribute-Based Access Control).

    Supports policies with complex conditions and context-aware decisions.
    """

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.policies: Dict[str, AccessPolicy] = {}
        self.resources: Dict[str, Resource] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Load default access control policies."""
        self.policies = {
            "admin_full_access": AccessPolicy(
                policy_id="admin_full_access",
                name="Administrator Full Access",
                description="Full system access for administrators",
                effect=AccessDecision.ALLOW,
                principals=["role:admin"],
                resources=["*"],
                actions=["*"],
                priority=100,
            ),
            "manager_service_access": AccessPolicy(
                policy_id="manager_service_access",
                name="Manager Service Access",
                description="Service management access for managers",
                effect=AccessDecision.ALLOW,
                principals=["role:manager"],
                resources=["api/*", "analytics/*", "topology/*"],
                actions=["read", "write", "execute"],
                priority=80,
            ),
            "developer_development_access": AccessPolicy(
                policy_id="developer_development_access",
                name="Developer Development Access",
                description="Development tools and API access for developers",
                effect=AccessDecision.ALLOW,
                principals=["role:developer"],
                resources=["api/*", "tools/*", "analytics/read/*"],
                actions=["read", "execute"],
                priority=60,
            ),
            "analyst_read_only": AccessPolicy(
                policy_id="analyst_read_only",
                name="Analyst Read-Only Access",
                description="Read-only access for analysts",
                effect=AccessDecision.ALLOW,
                principals=["role:analyst"],
                resources=["analytics/*", "topology/read/*", "api/catalog/*"],
                actions=["read"],
                priority=40,
            ),
            "business_hours_only": AccessPolicy(
                policy_id="business_hours_only",
                name="Business Hours Only",
                description="Access restricted to business hours",
                effect=AccessDecision.DENY,
                principals=["*"],
                resources=["*"],
                actions=["*"],
                conditions={
                    "time_restriction": {
                        "type": "business_hours",
                        "timezone": "UTC",
                        "business_hours": {"start": "09:00", "end": "17:00"},
                        "business_days": [
                            "monday",
                            "tuesday",
                            "wednesday",
                            "thursday",
                            "friday",
                        ],
                    }
                },
                priority=10,
            ),
            "geographic_restriction": AccessPolicy(
                policy_id="geographic_restriction",
                name="Geographic Access Restriction",
                description="Restrict access from certain geographic regions",
                effect=AccessDecision.DENY,
                principals=["*"],
                resources=["*"],
                actions=["*"],
                conditions={
                    "ip_restriction": {
                        "type": "country_block",
                        "blocked_countries": [
                            "KP",
                            "IR",
                            "CU",
                        ],  # North Korea, Iran, Cuba
                    }
                },
                priority=5,
            ),
        }

    async def register_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        owner_id: str,
        attributes: Dict[str, Any] = None,
    ) -> Resource:
        """Register a resource for access control."""
        resource = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_id=owner_id,
            attributes=attributes or {},
        )

        self.resources[resource_id] = resource
        return resource

    async def create_policy(
        self,
        name: str,
        description: str,
        effect: AccessDecision,
        principals: List[str],
        resources: List[str],
        actions: List[str],
        conditions: Dict[str, Any] = None,
        priority: int = 0,
    ) -> str:
        """Create a new access control policy."""
        policy_id = f"policy_{len(self.policies) + 1}"

        policy = AccessPolicy(
            policy_id=policy_id,
            name=name,
            description=description,
            effect=effect,
            principals=principals,
            resources=resources,
            actions=actions,
            conditions=conditions or {},
            priority=priority,
        )

        self.policies[policy_id] = policy
        return policy_id

    async def evaluate_access(
        self, access_request: AccessRequest
    ) -> Tuple[AccessDecision, str, Optional[AccessPolicy]]:
        """
        Evaluate access request against policies.

        Returns (decision, reason, matched_policy)
        """
        # Sort policies by priority (highest first)
        sorted_policies = sorted(
            self.policies.values(), key=lambda p: p.priority, reverse=True
        )

        for policy in sorted_policies:
            if not policy.enabled:
                continue

            match_result = await self._matches_policy(policy, access_request)
            if match_result[0]:  # Policy matches
                # Check conditions
                if await self._evaluate_conditions(policy.conditions, access_request):
                    return policy.effect, match_result[1], policy

        # Default deny
        return AccessDecision.DENY, "No matching policy found", None

    async def _matches_policy(
        self, policy: AccessPolicy, request: AccessRequest
    ) -> Tuple[bool, str]:
        """Check if request matches a policy."""
        # Check principal
        if not self._matches_principal(policy.principals, request.user):
            return False, "Principal mismatch"

        # Check resource
        if not self._matches_resource(policy.resources, request.resource):
            return False, "Resource mismatch"

        # Check action
        if not self._matches_action(policy.actions, request.action):
            return False, "Action mismatch"

        return True, "Policy matched"


    def _check_wildcard_principal(self, principal: str) -> bool:
        """Check if principal is a wildcard match."""
        return principal == "*"

    def _check_role_principal(self, principal: str, user: User) -> bool:
        """Check if principal matches user role."""
        if principal.startswith("role:"):
            role_name = principal[5:]
            return user.role.value == role_name
        return False

    def _check_user_principal(self, principal: str, user: User) -> bool:
        """Check if principal matches user ID or username."""
        if principal.startswith("user:"):
            user_id = principal[5:]
            return user.user_id == user_id
        return False

    def _check_direct_principal(self, principal: str, user: User) -> bool:
        """Check for direct user ID or username match."""
        return user.user_id == principal or user.username == principal

    def _matches_principal(self, principals: List[str], user: User) -> bool:
        """Check if user matches any principal pattern."""
        for principal in principals:
            if self._check_wildcard_principal(principal):
                return True
            elif self._check_role_principal(principal, user):
                return True
            elif self._check_user_principal(principal, user):
                return True
            elif self._check_direct_principal(principal, user):
                return True

        return False

    def _matches_resource(self, resources: List[str], resource: Resource) -> bool:
        """Check if resource matches any resource pattern."""
        resource_identifier = f"{resource.resource_type.value}:{resource.resource_id}"

        for resource_pattern in resources:
            if resource_pattern == "*":
                return True
            elif self._matches_pattern(resource_identifier, resource_pattern):
                return True

        return False

    def _matches_action(self, actions: List[str], action: str) -> bool:
        """Check if action matches any action pattern."""
        for action_pattern in actions:
            if action_pattern == "*":
                return True
            elif action_pattern == action:
                return True
            elif self._matches_pattern(action, action_pattern):
                return True

        return False

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Check if value matches a pattern with wildcards."""
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        return bool(re.match(f"^{regex_pattern}$", value))

    async def _evaluate_conditions(
        self, conditions: Dict[str, Any], request: AccessRequest
    ) -> bool:
        """Evaluate policy conditions."""
        for condition_name, condition_config in conditions.items():
            condition_type = condition_config.get("type")

            if condition_type == "business_hours":
                if not self._check_business_hours(condition_config, request.timestamp):
                    return False

            elif condition_type == "ip_restriction":
                client_ip = request.context.get("ip_address")
                if client_ip and not self._check_ip_restriction(
                    condition_config, client_ip
                ):
                    return False

            elif condition_type == "time_window":
                if not self._check_time_window(condition_config, request.timestamp):
                    return False

        return True

    def _check_business_hours(
        self, config: Dict[str, Any], timestamp: datetime
    ) -> bool:
        """Check if timestamp falls within business hours."""
        business_hours = config.get("business_hours", {})
        business_days = config.get("business_days", [])

        # Check day of week
        day_name = timestamp.strftime("%A").lower()
        if day_name not in [d.lower() for d in business_days]:
            return False

        # Check time
        start_time = datetime.strptime(business_hours["start"], "%H:%M").time()
        end_time = datetime.strptime(business_hours["end"], "%H:%M").time()
        current_time = timestamp.time()

        return start_time <= current_time <= end_time

    def _check_ip_restriction(self, config: Dict[str, Any], ip_address: str) -> bool:
        """Check IP address against restrictions."""
        try:
            ipaddress.ip_address(ip_address)
        except ValueError:
            return False

        # Check blocked countries (simplified - would need geo IP database)
        blocked_countries = config.get("blocked_countries", [])
        if blocked_countries:
            # In production, would use geo IP service
            # For now, assume IP is allowed
            pass

        return True

    def _check_time_window(self, config: Dict[str, Any], timestamp: datetime) -> bool:
        """Check if timestamp falls within allowed time window."""
        start_time = config.get("start_time")
        end_time = config.get("end_time")

        if start_time and end_time:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            return start <= timestamp <= end

        return True

    async def get_policies_for_user(
        self, user: User, resource: Optional[Resource] = None
    ) -> List[AccessPolicy]:
        """Get all policies that apply to a user and optional resource."""
        applicable_policies = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            if self._matches_principal(policy.principals, user):
                if resource is None or self._matches_resource(
                    policy.resources, resource
                ):
                    applicable_policies.append(policy)

        return sorted(applicable_policies, key=lambda p: p.priority, reverse=True)
