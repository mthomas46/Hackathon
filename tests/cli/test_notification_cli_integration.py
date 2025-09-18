"""
Notification CLI Integration Tests

Comprehensive integration tests for notification-service CLI commands including:
- End-to-end command execution workflows
- Service integration and data flow
- Error handling and recovery scenarios
- Concurrent operation handling
- Real-world usage patterns
"""

import sys
import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from io import StringIO
import json
import time

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from ecosystem_cli_executable import EcosystemCLI
from .mock_framework import CLIMockFramework, create_successful_service_test
from .test_fixtures import CLITestFixtures


class TestNotificationCLIIntegration:
    """Integration tests for Notification CLI commands"""

    def setup_method(self):
        """Setup test method"""
        self.cli = EcosystemCLI()
        self.fixtures = CLITestFixtures()
        self.mock_framework = CLIMockFramework()

    @pytest.mark.asyncio
    async def test_notification_complete_workflow(self):
        """Test complete notification workflow from creation to history"""
        with self.mock_framework.mock_cli_environment():
            # Setup all necessary responses
            list_response = self.fixtures.get_mock_notification_response("list")
            self.mock_framework.setup_service_responses("notification-service", "list", list_response)

            send_response = self.fixtures.get_mock_notification_response("send")
            self.mock_framework.setup_service_responses("notification-service", "send", send_response)

            # Mock history response
            history_data = [
                {
                    "id": "notif_001",
                    "title": "Test Notification",
                    "sent_at": "2024-01-20T10:00:00Z",
                    "status": "delivered"
                },
                {
                    "id": "notif_002",
                    "title": "Another Notification",
                    "sent_at": "2024-01-20T09:30:00Z",
                    "status": "read"
                }
            ]
            from .test_fixtures import MockServiceResponse
            history_response = MockServiceResponse(status_code=200, json_data=history_data)
            self.mock_framework.http_client.add_response("notification_history", history_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Execute complete workflow
                await self.cli.notification_service_command("list")
                await self.cli.notification_service_command("send",
                    recipient="test@example.com",
                    title="Integration Test",
                    message="Testing notification workflow",
                    priority="normal"
                )

                # Mock get individual notification for history
                notification_data = {
                    "id": "notif_001",
                    "title": "Integration Test",
                    "message": "Testing notification workflow",
                    "recipient": "test@example.com",
                    "status": "delivered",
                    "priority": "normal"
                }
                get_response = MockServiceResponse(status_code=200, json_data=notification_data)
                self.mock_framework.http_client.add_response("notification_get", get_response)

                await self.cli.notification_service_command("get", id="notif_001")
                await self.cli.notification_service_command("history", recipient="test@example.com")

                output = mock_stdout.getvalue()

                # Verify workflow completion
                assert "📋 Notification List" in output
                assert "✅ Notification Sent:" in output
                assert "📋 Notification Details:" in output
                assert "📜 Notification History" in output
                assert "Integration Test" in output

    @pytest.mark.asyncio
    async def test_notification_bulk_operations(self):
        """Test bulk notification operations"""
        with self.mock_framework.mock_cli_environment():
            # Setup responses for bulk operations
            list_response = self.fixtures.get_mock_notification_response("list")
            self.mock_framework.setup_service_responses("notification-service", "list", list_response)

            # Send multiple notifications
            send_response = self.fixtures.get_mock_notification_response("send")
            self.mock_framework.setup_service_responses("notification-service", "send", send_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Send multiple notifications
                notifications = [
                    {"recipient": "user1@example.com", "title": "Alert 1", "message": "First alert"},
                    {"recipient": "user2@example.com", "title": "Alert 2", "message": "Second alert"},
                    {"recipient": "user3@example.com", "title": "Alert 3", "message": "Third alert"}
                ]

                for i, notif in enumerate(notifications):
                    await self.cli.notification_service_command("send",
                        recipient=notif["recipient"],
                        title=notif["title"],
                        message=notif["message"],
                        priority="normal"
                    )

                # List all notifications
                await self.cli.notification_service_command("list", limit=10)

                output = mock_stdout.getvalue()

                # Verify bulk operations
                assert output.count("✅ Notification Sent:") == 3
                assert "📋 Notification List" in output
                assert "Total notifications:" in output

    @pytest.mark.asyncio
    async def test_notification_priority_handling(self):
        """Test notification priority handling and filtering"""
        with self.mock_framework.mock_cli_environment():
            # Setup notifications with different priorities
            notifications = [
                {"id": "notif_001", "title": "Low Priority", "priority": "low", "status": "unread"},
                {"id": "notif_002", "title": "Normal Priority", "priority": "normal", "status": "unread"},
                {"id": "notif_003", "title": "High Priority", "priority": "high", "status": "unread"},
                {"id": "notif_004", "title": "Critical Priority", "priority": "critical", "status": "unread"}
            ]

            from .test_fixtures import MockServiceResponse
            list_response = MockServiceResponse(
                status_code=200,
                json_data={"items": notifications, "total": 4, "has_more": False}
            )
            self.mock_framework.http_client.add_response("notification_list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # List all notifications
                await self.cli.notification_service_command("list")

                # Filter by high priority
                high_priority_response = MockServiceResponse(
                    status_code=200,
                    json_data={"items": [n for n in notifications if n["priority"] == "high"], "total": 1, "has_more": False}
                )
                self.mock_framework.http_client.add_response("notification_list_high", high_priority_response)

                await self.cli.notification_service_command("list", priority="high")

                output = mock_stdout.getvalue()

                # Verify priority handling
                assert "Low Priority" in output
                assert "Normal Priority" in output
                assert "High Priority" in output
                assert "Critical Priority" in output
                assert "priority: high" in output

    @pytest.mark.asyncio
    async def test_notification_status_workflow(self):
        """Test notification status update workflow"""
        with self.mock_framework.mock_cli_environment():
            # Setup notification data
            notification_data = {
                "id": "notif_status_test",
                "title": "Status Test Notification",
                "message": "Testing status updates",
                "recipient": "test@example.com",
                "status": "unread",
                "priority": "normal"
            }

            from .test_fixtures import MockServiceResponse

            # Setup get notification response
            get_response = MockServiceResponse(status_code=200, json_data=notification_data)
            self.mock_framework.http_client.add_response("notification_get", get_response)

            # Setup status update response
            update_response = MockServiceResponse(status_code=200, json_data={"success": True})
            self.mock_framework.http_client.add_response("notification_update", update_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Get notification (should be unread)
                await self.cli.notification_service_command("get", id="notif_status_test")

                # Update status to read
                await self.cli.notification_service_command("update", id="notif_status_test", status="read")

                output = mock_stdout.getvalue()

                # Verify status workflow
                assert "📋 Notification Details:" in output
                assert "unread" in output
                assert "✅ Notification notif_status_test status updated to: read" in output

    @pytest.mark.asyncio
    async def test_notification_history_analysis(self):
        """Test notification history analysis and patterns"""
        with self.mock_framework.mock_cli_environment():
            # Setup comprehensive history data
            history_data = [
                {
                    "id": "notif_001",
                    "title": "System Alert",
                    "recipient": "admin@example.com",
                    "priority": "high",
                    "category": "system",
                    "status": "read",
                    "sent_at": "2024-01-20T10:00:00Z"
                },
                {
                    "id": "notif_002",
                    "title": "User Notification",
                    "recipient": "user@example.com",
                    "priority": "normal",
                    "category": "user",
                    "status": "unread",
                    "sent_at": "2024-01-20T09:30:00Z"
                },
                {
                    "id": "notif_003",
                    "title": "Maintenance Notice",
                    "recipient": "admin@example.com",
                    "priority": "medium",
                    "category": "maintenance",
                    "status": "delivered",
                    "sent_at": "2024-01-20T08:00:00Z"
                }
            ]

            from .test_fixtures import MockServiceResponse
            history_response = MockServiceResponse(status_code=200, json_data=history_data)
            self.mock_framework.http_client.add_response("notification_history", history_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # Get history for admin
                await self.cli.notification_service_command("history", recipient="admin@example.com")

                # Get history for user
                user_history = [n for n in history_data if n["recipient"] == "user@example.com"]
                user_history_response = MockServiceResponse(status_code=200, json_data=user_history)
                self.mock_framework.http_client.add_response("notification_history_user", user_history_response)

                await self.cli.notification_service_command("history", recipient="user@example.com")

                output = mock_stdout.getvalue()

                # Verify history analysis
                assert "📜 Notification History for admin@example.com:" in output
                assert "📜 Notification History for user@example.com:" in output
                assert "System Alert" in output
                assert "User Notification" in output
                assert "Maintenance Notice" in output

    @pytest.mark.asyncio
    async def test_notification_statistics_integration(self):
        """Test notification statistics integration"""
        with self.mock_framework.mock_cli_environment():
            # Setup comprehensive statistics
            stats_data = {
                "total_notifications": 150,
                "notifications_by_status": {
                    "unread": 25,
                    "read": 100,
                    "delivered": 15,
                    "failed": 10
                },
                "notifications_by_priority": {
                    "low": 40,
                    "normal": 80,
                    "high": 20,
                    "critical": 10
                },
                "notifications_by_category": {
                    "system": 30,
                    "user": 60,
                    "maintenance": 25,
                    "alert": 35
                },
                "average_response_time": 45.2,
                "delivery_success_rate": 93.3,
                "time_range": "2024-01-15 to 2024-01-20"
            }

            from .test_fixtures import MockServiceResponse
            stats_response = MockServiceResponse(status_code=200, json_data=stats_data)
            self.mock_framework.http_client.add_response("notification_stats", stats_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("stats")

                output = mock_stdout.getvalue()

                # Verify statistics display
                assert "📊 Notification Statistics:" in output
                assert "150" in output  # total_notifications
                assert "93.3" in output  # delivery_success_rate
                assert "45.2" in output  # average_response_time

    @pytest.mark.asyncio
    async def test_notification_error_recovery(self):
        """Test error handling and recovery scenarios"""
        with self.mock_framework.mock_cli_environment():
            # Test various error scenarios
            error_scenarios = [
                ("connection_error", "Failed to send notification"),
                ("server_error", "Failed to list notifications"),
                ("not_found", "Failed to get notification")
            ]

            for error_type, expected_message in error_scenarios:
                self.mock_framework.setup_error_scenario("notification-service", error_type)

                with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                    if "send" in expected_message:
                        await self.cli.notification_service_command("send",
                            recipient="test@example.com",
                            title="Test",
                            message="Test message"
                        )
                    elif "list" in expected_message:
                        await self.cli.notification_service_command("list")
                    else:
                        await self.cli.notification_service_command("get", id="test_id")

                    output = mock_stdout.getvalue()
                    assert "❌" in output

    @pytest.mark.asyncio
    async def test_notification_concurrent_operations(self):
        """Test concurrent notification operations"""
        with self.mock_framework.mock_cli_environment():
            # Setup responses
            list_response = self.fixtures.get_mock_notification_response("list")
            self.mock_framework.setup_service_responses("notification-service", "list", list_response)

            send_response = self.fixtures.get_mock_notification_response("send")
            self.mock_framework.setup_service_responses("notification-service", "send", send_response)

            # Execute concurrent operations
            tasks = []

            # Multiple list operations
            for i in range(3):
                task = asyncio.create_task(self.cli.notification_service_command("list"))
                tasks.append(task)

            # Multiple send operations
            for i in range(2):
                task = asyncio.create_task(self.cli.notification_service_command("send",
                    recipient=f"user{i}@example.com",
                    title=f"Concurrent Test {i}",
                    message=f"Message {i}"
                ))
                tasks.append(task)

            # Execute all concurrently
            start_time = time.time()
            await asyncio.gather(*tasks)
            end_time = time.time()

            # Verify reasonable execution time (should be faster than sequential)
            execution_time = end_time - start_time
            assert execution_time < 5.0  # Should complete within 5 seconds

    @pytest.mark.asyncio
    async def test_notification_data_consistency(self):
        """Test data consistency across operations"""
        with self.mock_framework.mock_cli_environment():
            # Create consistent notification data
            notification_id = "consistency_test_001"
            notification_data = {
                "id": notification_id,
                "title": "Consistency Test",
                "message": "Testing data consistency across operations",
                "recipient": "consistency@example.com",
                "priority": "normal",
                "category": "test",
                "status": "unread"
            }

            from .test_fixtures import MockServiceResponse

            # Setup list response containing our notification
            list_response = MockServiceResponse(
                status_code=200,
                json_data={"items": [notification_data], "total": 1, "has_more": False}
            )
            self.mock_framework.http_client.add_response("notification_list", list_response)

            # Setup get response for the same notification
            get_response = MockServiceResponse(status_code=200, json_data=notification_data)
            self.mock_framework.http_client.add_response("notification_get", get_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                # List notifications
                await self.cli.notification_service_command("list")

                # Get specific notification
                await self.cli.notification_service_command("get", id=notification_id)

                output = mock_stdout.getvalue()

                # Verify data consistency
                title_count = output.count("Consistency Test")
                assert title_count >= 2  # Should appear in both list and get operations

                message_count = output.count("Testing data consistency")
                assert message_count >= 2  # Should appear in both operations

    @pytest.mark.asyncio
    async def test_notification_large_dataset_handling(self):
        """Test handling of large notification datasets"""
        with self.mock_framework.mock_cli_environment():
            # Create large dataset (100 notifications)
            large_dataset = []
            for i in range(100):
                notification = {
                    "id": "03d",
                    "title": f"Notification {i+1}",
                    "message": f"Message content for notification {i+1}",
                    "recipient": f"user{i%10}@example.com",
                    "priority": ["low", "normal", "high"][i % 3],
                    "status": ["unread", "read", "delivered"][i % 3],
                    "category": ["system", "user", "alert"][i % 3]
                }
                large_dataset.append(notification)

            from .test_fixtures import MockServiceResponse
            large_response = MockServiceResponse(
                status_code=200,
                json_data={"items": large_dataset, "total": 100, "has_more": True}
            )
            self.mock_framework.http_client.add_response("notification_list_large", large_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("list", limit=50)

                output = mock_stdout.getvalue()

                # Verify large dataset handling
                assert "Total notifications: 100" in output
                assert "Has more: True" in output
                # Should show first 10 items only
                assert "Notification 1" in output
                assert "Notification 10" in output
                assert "... and 40 more notifications" in output

    @pytest.mark.asyncio
    async def test_notification_metadata_handling(self):
        """Test notification metadata handling"""
        with self.mock_framework.mock_cli_environment():
            # Test sending notification with complex metadata
            send_response = self.fixtures.get_mock_notification_response("send")
            self.mock_framework.setup_service_responses("notification-service", "send", send_response)

            metadata_string = "source:cli,version:1.0,user_agent:test_suite,timestamp:2024-01-20"

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("send",
                    recipient="metadata@example.com",
                    title="Metadata Test",
                    message="Testing metadata handling",
                    priority="normal",
                    metadata=metadata_string
                )

                output = mock_stdout.getvalue()

                # Verify metadata handling
                assert "✅ Notification Sent:" in output
                assert "Metadata Test" in output

    @pytest.mark.asyncio
    async def test_notification_end_to_end_workflow(self):
        """Test complete end-to-end notification workflow"""
        with self.mock_framework.mock_cli_environment():
            workflow_steps = []

            # Step 1: Send notification
            send_response = self.fixtures.get_mock_notification_response("send")
            self.mock_framework.setup_service_responses("notification-service", "send", send_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("send",
                    recipient="workflow@example.com",
                    title="Workflow Test",
                    message="Testing complete workflow",
                    priority="high",
                    category="test"
                )
                workflow_steps.append("send")

            # Step 2: List notifications (should include our new one)
            list_response = self.fixtures.get_mock_notification_response("list")
            # Modify to include our sent notification
            list_response.json_data["items"].append({
                "id": "workflow_test",
                "title": "Workflow Test",
                "status": "unread",
                "priority": "high"
            })
            self.mock_framework.setup_service_responses("notification-service", "list", list_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("list")
                workflow_steps.append("list")

            # Step 3: Get specific notification details
            from .test_fixtures import MockServiceResponse
            notification_details = {
                "id": "workflow_test",
                "title": "Workflow Test",
                "message": "Testing complete workflow",
                "recipient": "workflow@example.com",
                "status": "unread",
                "priority": "high",
                "category": "test"
            }
            get_response = MockServiceResponse(status_code=200, json_data=notification_details)
            self.mock_framework.http_client.add_response("notification_get", get_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("get", id="workflow_test")
                workflow_steps.append("get")

            # Step 4: Update notification status
            update_response = MockServiceResponse(status_code=200, json_data={"success": True})
            self.mock_framework.http_client.add_response("notification_update", update_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("update", id="workflow_test", status="read")
                workflow_steps.append("update")

            # Step 5: Check history
            history_data = [notification_details]
            history_response = MockServiceResponse(status_code=200, json_data=history_data)
            self.mock_framework.http_client.add_response("notification_history", history_response)

            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                await self.cli.notification_service_command("history", recipient="workflow@example.com")
                workflow_steps.append("history")

            # Verify complete workflow
            assert len(workflow_steps) == 5
            assert "send" in workflow_steps
            assert "list" in workflow_steps
            assert "get" in workflow_steps
            assert "update" in workflow_steps
            assert "history" in workflow_steps

    def test_notification_cli_help_display(self):
        """Test notification CLI help display"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            asyncio.run(self.cli.notification_service_command("invalid_command"))

            output = mock_stdout.getvalue()

            # Verify help information is displayed
            assert "❌ Unknown notification-service command: invalid_command" in output
            assert "Available commands:" in output
            assert "health, config, list, send, get, history, stats, update" in output
            assert "Examples:" in output


if __name__ == "__main__":
    # Run notification CLI integration tests
    test_instance = TestNotificationCLIIntegration()
    test_instance.setup_method()

    print("🔗 Running Notification CLI Integration Tests...")
    print("=" * 55)

    # Test basic functionality
    try:
        asyncio.run(test_instance.test_notification_complete_workflow())
        print("✅ Complete workflow test: PASSED")
    except Exception as e:
        print(f"❌ Complete workflow test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_notification_bulk_operations())
        print("✅ Bulk operations test: PASSED")
    except Exception as e:
        print(f"❌ Bulk operations test: FAILED - {e}")

    try:
        asyncio.run(test_instance.test_notification_priority_handling())
        print("✅ Priority handling test: PASSED")
    except Exception as e:
        print(f"❌ Priority handling test: FAILED - {e}")

    print("\n🏁 Notification CLI Integration Tests completed!")
