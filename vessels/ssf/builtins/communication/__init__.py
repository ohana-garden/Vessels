"""
Communication SSFs - SMS, Email, Notifications.

These SSFs handle outbound communication with appropriate
constraint binding for message content validation.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging

from ...schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER IMPLEMENTATIONS
# ============================================================================

async def handle_send_sms(
    phone_number: str,
    message: str,
    sender_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Send an SMS message.

    Args:
        phone_number: Recipient phone number (E.164 format)
        message: Message content (max 1600 chars)
        sender_id: Optional sender identification

    Returns:
        Dictionary with send status and message ID
    """
    # This would integrate with Twilio or similar
    logger.info(f"SMS to {phone_number}: {message[:50]}...")

    # Placeholder - actual implementation would call SMS provider
    return {
        "status": "sent",
        "message_id": str(uuid4()),
        "recipient": phone_number,
        "character_count": len(message),
    }


async def handle_send_email(
    to: str,
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    cc: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        from_address: Optional sender address
        cc: Optional CC recipients
        html_body: Optional HTML body

    Returns:
        Dictionary with send status and message ID
    """
    logger.info(f"Email to {to}: {subject}")

    # Placeholder - actual implementation would call email provider
    return {
        "status": "sent",
        "message_id": str(uuid4()),
        "recipient": to,
        "subject": subject,
    }


async def handle_send_notification(
    user_id: str,
    title: str,
    body: str,
    channel: str = "push",
    priority: str = "normal",
    **kwargs
) -> Dict[str, Any]:
    """
    Send a notification to a user.

    Args:
        user_id: Target user ID
        title: Notification title
        body: Notification body
        channel: Notification channel (push, email, sms)
        priority: Priority level (low, normal, high, urgent)

    Returns:
        Dictionary with delivery status
    """
    logger.info(f"Notification to {user_id}: {title}")

    return {
        "status": "delivered",
        "notification_id": str(uuid4()),
        "user_id": user_id,
        "channel": channel,
    }


async def handle_post_to_channel(
    channel_id: str,
    message: str,
    mentions: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Post a message to a communication channel.

    Args:
        channel_id: Target channel ID
        message: Message content
        mentions: Optional user IDs to mention
        attachments: Optional attachments

    Returns:
        Dictionary with post status and message ID
    """
    logger.info(f"Post to channel {channel_id}: {message[:50]}...")

    return {
        "status": "posted",
        "message_id": str(uuid4()),
        "channel_id": channel_id,
        "timestamp": "2024-01-01T00:00:00Z",
    }


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_send_sms_ssf() -> SSFDefinition:
    """Create the send_sms SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="send_sms",
        version="1.0.0",
        category=SSFCategory.COMMUNICATION,
        tags=["sms", "messaging", "mobile", "text"],
        description="Send an SMS text message to a phone number. Supports E.164 format numbers and messages up to 1600 characters.",
        description_for_llm="Use this SSF when you need to send a text message to someone's phone. Requires a phone number in E.164 format (+1234567890) and the message content. Good for urgent notifications, reminders, or when email isn't suitable.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.communication",
            function_name="handle_send_sms",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "pattern": r"^\+[1-9]\d{1,14}$",
                    "description": "Phone number in E.164 format",
                },
                "message": {
                    "type": "string",
                    "maxLength": 1600,
                    "description": "SMS message content",
                },
                "sender_id": {
                    "type": "string",
                    "description": "Optional sender identification",
                },
            },
            "required": ["phone_number", "message"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["sent", "queued", "failed"]},
                "message_id": {"type": "string"},
                "recipient": {"type": "string"},
                "character_count": {"type": "integer"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        required_tools=[],
        required_permissions=["communication:sms"],
        risk_level=RiskLevel.HIGH,
        side_effects=[
            "Sends SMS message via external service (Twilio)",
            "May incur cost per message",
            "Message delivery is not guaranteed",
            "Cannot be recalled once sent",
        ],
        reversible=False,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.BLOCK,
            forbidden_input_patterns=[
                r"(?i)password",
                r"(?i)\bssn\b",
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
                r"(?i)credit.?card",
            ],
        ),
    )


def _create_send_email_ssf() -> SSFDefinition:
    """Create the send_email SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="send_email",
        version="1.0.0",
        category=SSFCategory.COMMUNICATION,
        tags=["email", "messaging", "communication"],
        description="Send an email message with optional HTML body and attachments. Supports plain text and HTML content.",
        description_for_llm="Use this SSF when you need to send an email to someone. Supports plain text or HTML content, subject lines, and CC recipients. Better for longer messages, formal communication, or when you need a record of the communication.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.communication",
            function_name="handle_send_email",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "format": "email",
                    "description": "Recipient email address",
                },
                "subject": {
                    "type": "string",
                    "maxLength": 200,
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Plain text email body",
                },
                "from_address": {
                    "type": "string",
                    "format": "email",
                    "description": "Sender email address",
                },
                "cc": {
                    "type": "array",
                    "items": {"type": "string", "format": "email"},
                    "description": "CC recipients",
                },
                "html_body": {
                    "type": "string",
                    "description": "Optional HTML body",
                },
            },
            "required": ["to", "subject", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message_id": {"type": "string"},
                "recipient": {"type": "string"},
                "subject": {"type": "string"},
            },
        },
        timeout_seconds=60,
        memory_mb=128,
        risk_level=RiskLevel.HIGH,
        side_effects=[
            "Sends email via external service",
            "Cannot be recalled once sent",
            "May be filtered as spam",
        ],
        reversible=False,
        constraint_binding=ConstraintBindingConfig.strict(),
    )


def _create_send_notification_ssf() -> SSFDefinition:
    """Create the send_notification SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="send_notification",
        version="1.0.0",
        category=SSFCategory.COMMUNICATION,
        tags=["notification", "push", "alert"],
        description="Send a notification to a user via their preferred channel (push, email, or SMS).",
        description_for_llm="Use this SSF to send notifications to users. Automatically routes to their preferred channel. Good for alerts, updates, reminders, and status changes. Supports priority levels for urgent notifications.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.communication",
            function_name="handle_send_notification",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Target user ID",
                },
                "title": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "Notification title",
                },
                "body": {
                    "type": "string",
                    "maxLength": 500,
                    "description": "Notification body",
                },
                "channel": {
                    "type": "string",
                    "enum": ["push", "email", "sms", "auto"],
                    "default": "auto",
                    "description": "Notification channel",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"],
                    "default": "normal",
                    "description": "Notification priority",
                },
            },
            "required": ["user_id", "title", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "notification_id": {"type": "string"},
                "user_id": {"type": "string"},
                "channel": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=["Sends notification to user device"],
        reversible=False,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FILTERED,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.WARN,
        ),
    )


def _create_post_to_channel_ssf() -> SSFDefinition:
    """Create the post_to_channel SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="post_to_channel",
        version="1.0.0",
        category=SSFCategory.COMMUNICATION,
        tags=["channel", "broadcast", "messaging", "team"],
        description="Post a message to a communication channel (Slack, Teams, Discord, etc.).",
        description_for_llm="Use this SSF to post messages to team communication channels. Good for announcements, updates, or collaborative discussions. Supports @mentions and attachments.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.communication",
            function_name="handle_post_to_channel",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "string",
                    "description": "Target channel ID",
                },
                "message": {
                    "type": "string",
                    "maxLength": 4000,
                    "description": "Message content",
                },
                "mentions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "User IDs to mention",
                },
                "attachments": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Message attachments",
                },
            },
            "required": ["channel_id", "message"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "message_id": {"type": "string"},
                "channel_id": {"type": "string"},
                "timestamp": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=["Posts message visible to channel members"],
        reversible=True,  # Messages can typically be deleted
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in communication SSFs."""
    return [
        _create_send_sms_ssf(),
        _create_send_email_ssf(),
        _create_send_notification_ssf(),
        _create_post_to_channel_ssf(),
    ]
