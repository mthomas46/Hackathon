"""Notifications API handlers.

Handles HTTP requests and responses for webhook management and notification monitoring.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException

from services.prompt_store.domain.notifications.service import NotificationsService
from services.prompt_store.core.models import WebhookCreate
from services.shared.responses import create_success_response, create_error_response


class NotificationsHandlers:
    """Handlers for notification and webhook management endpoints."""

    def __init__(self):
        self.notifications_service = NotificationsService()

    async def handle_register_webhook(self, webhook_data: WebhookCreate,
                                    user_id: str = "api_user") -> Dict[str, Any]:
        """Handle webhook registration request."""

        try:
            # Convert to dict and add user
            webhook_dict = webhook_data.dict()
            webhook_dict["created_by"] = user_id

            result = await self.notifications_service.register_webhook(webhook_dict)

            response = create_success_response(
                data=result,
                message=f"Webhook '{webhook_data.name}' registered successfully"
            )
            return response.model_dump()

        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
            return error_response.model_dump()
        except Exception as e:
            error_response = create_error_response(f"Failed to register webhook: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    def handle_list_webhooks(self, active_only: bool = False) -> Dict[str, Any]:
        """Handle request to list webhooks."""

        try:
            result = self.notifications_service.list_webhooks(active_only)

            response = create_success_response(
                data=result,
                message=f"Retrieved {result['count']} webhooks"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to list webhooks: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    def handle_get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Handle request to get webhook details."""

        try:
            result = self.notifications_service.get_webhook(webhook_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} not found")

            response = create_success_response(
                data=result,
                message=f"Retrieved webhook {webhook_id}"
            )
            return response.model_dump()

        except HTTPException:
            raise
        except Exception as e:
            error_response = create_error_response(f"Failed to get webhook: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_update_webhook(self, webhook_id: str, updates: Dict[str, Any],
                                  user_id: str = "api_user") -> Dict[str, Any]:
        """Handle webhook update request."""

        try:
            result = await self.notifications_service.update_webhook(webhook_id, updates)

            response = create_success_response(
                data=result,
                message=f"Webhook {webhook_id} updated successfully"
            )
            return response.model_dump()

        except ValueError as e:
            error_response = create_error_response(str(e), "VALIDATION_ERROR")
            return error_response.model_dump()
        except Exception as e:
            error_response = create_error_response(f"Failed to update webhook: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_delete_webhook(self, webhook_id: str, user_id: str = "api_user") -> Dict[str, Any]:
        """Handle webhook deletion request."""

        try:
            result = await self.notifications_service.delete_webhook(webhook_id)

            response = create_success_response(
                data=result,
                message=f"Webhook {webhook_id} deleted successfully"
            )
            return response.model_dump()

        except ValueError as e:
            error_response = create_error_response(str(e), "NOT_FOUND")
            return error_response.model_dump()
        except Exception as e:
            error_response = create_error_response(f"Failed to delete webhook: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_notify_event(self, event_type: str, event_data: Dict[str, Any],
                                user_id: str = "api_user") -> Dict[str, Any]:
        """Handle manual event notification trigger."""

        try:
            result = await self.notifications_service.notify_event(event_type, event_data)

            response = create_success_response(
                data=result,
                message=f"Event '{event_type}' notifications sent"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to send notifications: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    async def handle_process_notifications(self) -> Dict[str, Any]:
        """Handle request to process pending notifications."""

        try:
            result = await self.notifications_service.process_pending_notifications()

            response = create_success_response(
                data=result,
                message=f"Processed {result['processed']} notifications"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to process notifications: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    def handle_get_notification_stats(self) -> Dict[str, Any]:
        """Handle request to get notification statistics."""

        try:
            result = self.notifications_service.get_notification_stats()

            response = create_success_response(
                data=result,
                message="Retrieved notification statistics"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to get statistics: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    def handle_cleanup_notifications(self, days_old: int = 30) -> Dict[str, Any]:
        """Handle request to clean up old notifications."""

        try:
            result = self.notifications_service.cleanup_old_notifications(days_old)

            response = create_success_response(
                data=result,
                message=f"Cleaned up {result['records_deleted']} old notification records"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to cleanup notifications: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()

    def handle_get_valid_events(self) -> Dict[str, Any]:
        """Handle request to get list of valid event types."""

        try:
            result = {
                "valid_event_types": list(self.notifications_service.repo.VALID_EVENT_TYPES),
                "event_categories": {
                    "prompt_events": [e for e in self.notifications_service.repo.VALID_EVENT_TYPES if e.startswith("prompt.")],
                    "ab_test_events": [e for e in self.notifications_service.repo.VALID_EVENT_TYPES if e.startswith("ab_test.")],
                    "bulk_operation_events": [e for e in self.notifications_service.repo.VALID_EVENT_TYPES if e.startswith("bulk_operation.")],
                    "relationship_events": [e for e in self.notifications_service.repo.VALID_EVENT_TYPES if e.startswith("relationship.")],
                    "refinement_events": [e for e in self.notifications_service.repo.VALID_EVENT_TYPES if e.startswith("refinement.")]
                }
            }

            response = create_success_response(
                data=result,
                message=f"Retrieved {len(result['valid_event_types'])} valid event types"
            )
            return response.model_dump()

        except Exception as e:
            error_response = create_error_response(f"Failed to get event types: {str(e)}", "INTERNAL_ERROR")
            return error_response.model_dump()
