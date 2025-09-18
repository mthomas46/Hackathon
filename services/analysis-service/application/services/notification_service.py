"""Application Notification Service - Event-driven notifications and alerts."""

import asyncio
import smtplib
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .application_service import ApplicationService, ServiceContext


@dataclass
class NotificationMessage:
    """Notification message structure."""
    recipient: str
    subject: str
    body: str
    message_type: str = "info"
    metadata: Optional[Dict[str, Any]] = None
    priority: str = "normal"

    def __post_init__(self):
        """Validate notification message."""
        if not self.recipient:
            raise ValueError("Recipient is required")

        if not self.subject:
            raise ValueError("Subject is required")

        if not self.body:
            raise ValueError("Body is required")

        if self.message_type not in ['info', 'warning', 'error', 'critical']:
            raise ValueError(f"Invalid message type: {self.message_type}")

        if self.priority not in ['low', 'normal', 'high', 'urgent']:
            raise ValueError(f"Invalid priority: {self.priority}")


class NotificationChannel(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, message: NotificationMessage) -> bool:
        """Send notification message."""
        pass

    @abstractmethod
    def get_channel_type(self) -> str:
        """Get channel type identifier."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if channel is available."""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
        from_address: str = "noreply@analysis-service.com"
    ):
        """Initialize email notification channel."""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.from_address = from_address

    def get_channel_type(self) -> str:
        """Get channel type."""
        return "email"

    def is_available(self) -> bool:
        """Check if email channel is available."""
        return bool(self.smtp_server)

    async def send(self, message: NotificationMessage) -> bool:
        """Send email notification."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = message.recipient
            msg['Subject'] = message.subject

            # Add body
            body_part = MIMEText(message.body, 'plain')
            msg.attach(body_part)

            # Add metadata as JSON attachment if present
            if message.metadata:
                metadata_part = MIMEText(
                    json.dumps(message.metadata, indent=2),
                    'json'
                )
                metadata_part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename='metadata.json'
                )
                msg.attach(metadata_part)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)

            if self.use_tls:
                server.starttls()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel."""

    def __init__(self, webhook_url: str, timeout_seconds: int = 10):
        """Initialize webhook notification channel."""
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def get_channel_type(self) -> str:
        """Get channel type."""
        return "webhook"

    def is_available(self) -> bool:
        """Check if webhook channel is available."""
        return bool(self.webhook_url)

    async def send(self, message: NotificationMessage) -> bool:
        """Send webhook notification."""
        try:
            import aiohttp

            payload = {
                'recipient': message.recipient,
                'subject': message.subject,
                'body': message.body,
                'type': message.message_type,
                'priority': message.priority,
                'metadata': message.metadata or {},
                'timestamp': asyncio.get_event_loop().time()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel."""

    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        """Initialize Slack notification channel."""
        self.webhook_url = webhook_url
        self.channel = channel

    def get_channel_type(self) -> str:
        """Get channel type."""
        return "slack"

    def is_available(self) -> bool:
        """Check if Slack channel is available."""
        return bool(self.webhook_url)

    async def send(self, message: NotificationMessage) -> bool:
        """Send Slack notification."""
        try:
            import aiohttp

            # Format message for Slack
            slack_message = {
                'channel': self.channel,
                'text': f"*{message.subject}*\n\n{message.body}",
                'attachments': []
            }

            # Add metadata as attachment if present
            if message.metadata:
                attachment = {
                    'title': 'Additional Details',
                    'text': json.dumps(message.metadata, indent=2),
                    'color': self._get_color_for_priority(message.priority)
                }
                slack_message['attachments'].append(attachment)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    def _get_color_for_priority(self, priority: str) -> str:
        """Get color for priority level."""
        color_map = {
            'low': 'good',
            'normal': '#439FE0',
            'high': 'warning',
            'urgent': 'danger'
        }
        return color_map.get(priority, '#439FE0')


class ConsoleNotificationChannel(NotificationChannel):
    """Console notification channel for development and testing."""

    def __init__(self):
        """Initialize console notification channel."""
        pass

    def get_channel_type(self) -> str:
        """Get channel type."""
        return "console"

    def is_available(self) -> bool:
        """Console is always available."""
        return True

    async def send(self, message: NotificationMessage) -> bool:
        """Send console notification."""
        print(f"\n=== NOTIFICATION ({message.message_type.upper()}) ===")
        print(f"To: {message.recipient}")
        print(f"Subject: {message.subject}")
        print(f"Priority: {message.priority}")
        print(f"Body: {message.body}")

        if message.metadata:
            print(f"Metadata: {json.dumps(message.metadata, indent=2)}")

        print("=" * 50)

        return True


class ApplicationNotifier:
    """Application notification manager."""

    def __init__(self):
        """Initialize application notifier."""
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_rules: Dict[str, Dict[str, Any]] = {}

    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """Add notification channel."""
        self.channels[name] = channel

    def remove_channel(self, name: str) -> None:
        """Remove notification channel."""
        self.channels.pop(name, None)

    def add_notification_rule(
        self,
        rule_name: str,
        event_type: str,
        channels: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None
    ) -> None:
        """Add notification rule."""
        self.notification_rules[rule_name] = {
            'event_type': event_type,
            'channels': channels,
            'conditions': conditions or {},
            'template': template
        }

    def get_available_channels(self) -> List[str]:
        """Get list of available channels."""
        return [name for name, channel in self.channels.items() if channel.is_available()]

    async def send_notification(
        self,
        channels: List[str],
        message: NotificationMessage
    ) -> Dict[str, bool]:
        """Send notification through specified channels."""
        results = {}

        for channel_name in channels:
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                success = await channel.send(message)
                results[channel_name] = success
            else:
                results[channel_name] = False

        return results

    async def send_notification_by_rule(
        self,
        rule_name: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Send notification based on rule."""
        if rule_name not in self.notification_rules:
            return {}

        rule = self.notification_rules[rule_name]

        # Check conditions
        if not self._check_conditions(rule['conditions'], event_data):
            return {}

        # Create message
        message = self._create_message_from_rule(rule, event_data)

        # Send notification
        return await self.send_notification(rule['channels'], message)

    def _check_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Check if conditions are met."""
        for key, expected_value in conditions.items():
            actual_value = event_data.get(key)

            if isinstance(expected_value, dict):
                # Complex condition
                if '$gte' in expected_value and actual_value < expected_value['$gte']:
                    return False
                if '$lte' in expected_value and actual_value > expected_value['$lte']:
                    return False
                if '$eq' in expected_value and actual_value != expected_value['$eq']:
                    return False
            else:
                # Simple equality
                if actual_value != expected_value:
                    return False

        return True

    def _create_message_from_rule(self, rule: Dict[str, Any], event_data: Dict[str, Any]) -> NotificationMessage:
        """Create notification message from rule."""
        event_type = rule['event_type']

        # Default template if none provided
        if rule.get('template'):
            template = rule['template']
        else:
            template = f"Event: {event_type}\n\nDetails: {{event_data}}"

        # Format message
        subject = f"Analysis Service - {event_type.replace('_', ' ').title()}"
        body = template.format(event_data=json.dumps(event_data, indent=2))

        # Determine recipient based on event data
        recipient = event_data.get('recipient', 'admin@company.com')

        # Determine message type based on event
        message_type = 'info'
        if 'error' in event_data or 'failed' in event_type.lower():
            message_type = 'error'
        elif 'warning' in event_data:
            message_type = 'warning'

        return NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            message_type=message_type,
            metadata=event_data
        )


class NotificationService(ApplicationService):
    """Application notification service."""

    def __init__(self):
        """Initialize notification service."""
        super().__init__("notification_service")
        self.notifier = ApplicationNotifier()

        # Setup default channels and rules
        self._setup_default_channels()
        self._setup_default_rules()

    def _setup_default_channels(self) -> None:
        """Setup default notification channels."""
        # Console channel for development
        self.notifier.add_channel('console', ConsoleNotificationChannel())

        # Add other channels based on configuration
        # This would be expanded based on actual configuration

    def _setup_default_rules(self) -> None:
        """Setup default notification rules."""
        # Analysis failure notifications
        self.notifier.add_notification_rule(
            'analysis_failed',
            'analysis_failed',
            ['console'],  # Would be ['email', 'slack'] in production
            {'severity': 'high'}
        )

        # System health alerts
        self.notifier.add_notification_rule(
            'system_critical',
            'system_health_check',
            ['console'],
            {'status': 'critical'}
        )

        # High-priority findings
        self.notifier.add_notification_rule(
            'high_priority_finding',
            'finding_created',
            ['console'],
            {'severity': 'critical'}
        )

    async def send_notification(
        self,
        channels: List[str],
        recipient: str,
        subject: str,
        body: str,
        message_type: str = "info",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """Send notification."""
        async with self.operation_context("send_notification"):
            message = NotificationMessage(
                recipient=recipient,
                subject=subject,
                body=body,
                message_type=message_type,
                priority=priority,
                metadata=metadata
            )

            results = await self.notifier.send_notification(channels, message)

            # Log notification results
            successful_channels = [ch for ch, success in results.items() if success]
            failed_channels = [ch for ch, success in results.items() if not success]

            if successful_channels:
                self.logger.info(f"Notification sent successfully to: {successful_channels}")

            if failed_channels:
                self.logger.error(f"Notification failed for channels: {failed_channels}")

            return results

    async def add_notification_channel(
        self,
        name: str,
        channel_type: str,
        config: Dict[str, Any]
    ) -> None:
        """Add notification channel."""
        async with self.operation_context("add_notification_channel"):
            channel = None

            if channel_type == 'email':
                channel = EmailNotificationChannel(**config)
            elif channel_type == 'webhook':
                channel = WebhookNotificationChannel(**config)
            elif channel_type == 'slack':
                channel = SlackNotificationChannel(**config)
            elif channel_type == 'console':
                channel = ConsoleNotificationChannel()
            else:
                raise ValueError(f"Unsupported channel type: {channel_type}")

            self.notifier.add_channel(name, channel)
            self.logger.info(f"Added notification channel: {name} ({channel_type})")

    async def add_notification_rule(
        self,
        rule_name: str,
        event_type: str,
        channels: List[str],
        conditions: Optional[Dict[str, Any]] = None,
        template: Optional[str] = None
    ) -> None:
        """Add notification rule."""
        async with self.operation_context("add_notification_rule"):
            self.notifier.add_notification_rule(
                rule_name, event_type, channels, conditions, template
            )
            self.logger.info(f"Added notification rule: {rule_name}")

    async def process_event_notification(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Process event for notifications."""
        # Find matching rules
        matching_rules = [
            rule_name for rule_name, rule in self.notifier.notification_rules.items()
            if rule['event_type'] == event_type
        ]

        if not matching_rules:
            return

        # Send notifications for matching rules
        for rule_name in matching_rules:
            try:
                results = await self.notifier.send_notification_by_rule(rule_name, event_data)

                successful_channels = [ch for ch, success in results.items() if success]
                if successful_channels:
                    self.logger.info(f"Event notification sent for {rule_name}: {successful_channels}")

            except Exception as e:
                self.logger.error(f"Error sending notification for rule {rule_name}: {e}")

    async def get_notification_status(self) -> Dict[str, Any]:
        """Get notification service status."""
        return {
            'channels': self.notifier.get_available_channels(),
            'rules_count': len(self.notifier.notification_rules),
            'rules': list(self.notifier.notification_rules.keys())
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add notification-specific health info
        try:
            status = await self.get_notification_status()
            health['notification_service'] = {
                'available_channels': status['channels'],
                'notification_rules': status['rules_count'],
                'rules': status['rules']
            }

        except Exception as e:
            health['notification_service'] = {'error': str(e)}

        return health


# Global notification service instance
notification_service = NotificationService()

# Create application notifier instance
app_notifier = notification_service.notifier
