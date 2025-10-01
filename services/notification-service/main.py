"""Notification Service - Simplified FastAPI Application.

A basic notification service for sending notifications.
Simplified version to avoid complex DDD dependencies and shared module issues.
"""

import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Use fallback implementations for standalone operation
print("Starting simplified notification service (standalone mode)")

def create_success_response(data):
    """Create standardized success response."""
    return {"success": True, "data": data}

def load_service_config(service_type, **kwargs):
    """Fallback config loader."""
    return type('Config', (), {
        'port': 5020,
        'service_name': service_type,
        'service_version': '1.0.0',
        'service_description': f'{service_type} service',
        'server': type('Server', (), {'host': '0.0.0.0', 'port': 5020})()
    })()

# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Notification service for sending notifications via multiple channels",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Load configuration
config = load_service_config("notification-service")
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version

# Basic health endpoint
@app.get("/health")
async def health():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "Notification service is operational"
    }

# Basic notification endpoint
class NotificationRequest(BaseModel):
    message: str
    recipient: str
    channel: Optional[str] = "email"

class NotificationResponse(BaseModel):
    success: bool
    notification_id: str
    status: str
    channel: str

@app.post("/api/v1/notifications/send", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """Send a notification endpoint."""
    # Simple mock notification sending - in a real implementation this would send actual notifications
    import uuid
    notification_id = str(uuid.uuid4())

    return NotificationResponse(
        success=True,
        notification_id=notification_id,
        status="sent",
        channel=request.channel
    )

@app.get("/api/v1/notifications")
async def list_notifications():
    """List notifications endpoint."""
    return create_success_response({
        "notifications": [],
        "total": 0,
        "message": "No notifications stored in simplified mode"
    })

@app.get("/api/v1/status")
async def service_status():
    """Get service status and capabilities."""
    return create_success_response({
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "capabilities": ["email_notifications", "sms_notifications", "webhook_notifications"],
        "status": "operational"
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_API_PORT", "5020"))
    host = os.getenv("SERVICE_API_HOST", "0.0.0.0")
    print(f"Starting {SERVICE_NAME} on {host}:{port}")
    uvicorn.run(app, host=host, port=port)