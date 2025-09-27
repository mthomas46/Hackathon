"""Data Transfer Objects for User operations.

This module contains DTOs used for user-related operations in the
application layer, providing clean interfaces for API interactions.
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserRequest(BaseModel):
    """Request DTO for creating a new user."""

    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    display_name: Optional[str] = Field(None, description="Display name for the user")
    role: str = Field("viewer", description="User role (admin, analyst, developer, manager, viewer)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = ["admin", "analyst", "developer", "manager", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v


class UpdateUserRequest(BaseModel):
    """Request DTO for updating user information."""

    display_name: Optional[str] = Field(None, description="Display name")
    bio: Optional[str] = Field(None, description="User biography")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    role: Optional[str] = Field(None, description="User role")
    status: Optional[str] = Field(None, description="User status")
    topic_interests: Optional[List[str]] = Field(None, description="Topics of interest")
    service_subscriptions: Optional[List[str]] = Field(None, description="Subscribed services")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        valid_roles = ["admin", "analyst", "developer", "manager", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        valid_statuses = ["active", "inactive", "suspended", "pending"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v


class UserPreferencesRequest(BaseModel):
    """Request DTO for updating user preferences."""

    email_notifications: Optional[bool] = Field(None, description="Enable email notifications")
    webhook_notifications: Optional[bool] = Field(None, description="Enable webhook notifications")
    notification_channels: Optional[List[str]] = Field(None, description="Notification channels")
    theme: Optional[str] = Field(None, description="UI theme preference")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="Preferred language")


class UserResponse(BaseModel):
    """Response DTO for user information."""

    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="Unique username")
    display_name: str = Field(..., description="Display name")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User account status")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, description="User biography")
    document_relationships: List[str] = Field(default_factory=list, description="Related document IDs")
    service_subscriptions: List[str] = Field(default_factory=list, description="Subscribed services")
    topic_interests: List[str] = Field(default_factory=list, description="Topics of interest")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserPreferencesResponse(BaseModel):
    """Response DTO for user preferences."""

    user_id: str = Field(..., description="User identifier")
    email_notifications: bool = Field(..., description="Email notifications enabled")
    webhook_notifications: bool = Field(..., description="Webhook notifications enabled")
    notification_channels: List[str] = Field(..., description="Active notification channels")
    theme: str = Field(..., description="UI theme preference")
    timezone: str = Field(..., description="User timezone")
    language: str = Field(..., description="Preferred language")


class UserSearchResponse(BaseModel):
    """Response DTO for user search results."""

    users: List[UserResponse] = Field(..., description="List of matching users")
    total_count: int = Field(..., description="Total number of matching users")
    query: str = Field(..., description="Search query used")


class UserStatsResponse(BaseModel):
    """Response DTO for user statistics."""

    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    inactive_users: int = Field(..., description="Number of inactive users")
    admin_users: int = Field(..., description="Number of admin users")
    analyst_users: int = Field(..., description="Number of analyst users")
    developer_users: int = Field(..., description="Number of developer users")
    manager_users: int = Field(..., description="Number of manager users")
    viewer_users: int = Field(..., description="Number of viewer users")
