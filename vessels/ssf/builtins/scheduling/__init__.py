"""
Scheduling SSFs - Appointments, Reminders, Calendar Operations.

These SSFs handle time-based operations including appointment
management, reminders, and calendar interactions.
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

async def handle_create_appointment(
    title: str,
    start_time: str,
    end_time: str,
    attendees: List[str],
    location: Optional[str] = None,
    description: Optional[str] = None,
    calendar_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a calendar appointment.

    Args:
        title: Appointment title
        start_time: Start time (ISO 8601)
        end_time: End time (ISO 8601)
        attendees: List of attendee IDs/emails
        location: Optional location
        description: Optional description
        calendar_id: Target calendar ID

    Returns:
        Created appointment details
    """
    logger.info(f"Creating appointment: {title}")

    return {
        "appointment_id": str(uuid4()),
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "status": "confirmed",
    }


async def handle_check_availability(
    user_ids: List[str],
    start_time: str,
    end_time: str,
    duration_minutes: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Check availability for multiple users.

    Args:
        user_ids: Users to check
        start_time: Range start (ISO 8601)
        end_time: Range end (ISO 8601)
        duration_minutes: Optional meeting duration to find slots

    Returns:
        Availability information
    """
    logger.info(f"Checking availability for {len(user_ids)} users")

    return {
        "available_slots": [],
        "busy_periods": [],
        "users_checked": user_ids,
    }


async def handle_send_reminder(
    user_id: str,
    message: str,
    remind_at: str,
    appointment_id: Optional[str] = None,
    reminder_type: str = "push",
    **kwargs
) -> Dict[str, Any]:
    """
    Schedule a reminder for a user.

    Args:
        user_id: User to remind
        message: Reminder message
        remind_at: When to send (ISO 8601)
        appointment_id: Optional linked appointment
        reminder_type: Reminder delivery method

    Returns:
        Scheduled reminder details
    """
    logger.info(f"Scheduling reminder for {user_id} at {remind_at}")

    return {
        "reminder_id": str(uuid4()),
        "user_id": user_id,
        "remind_at": remind_at,
        "status": "scheduled",
    }


async def handle_cancel_appointment(
    appointment_id: str,
    reason: Optional[str] = None,
    notify_attendees: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Cancel an existing appointment.

    Args:
        appointment_id: Appointment to cancel
        reason: Cancellation reason
        notify_attendees: Whether to notify attendees

    Returns:
        Cancellation confirmation
    """
    logger.info(f"Cancelling appointment: {appointment_id}")

    return {
        "appointment_id": appointment_id,
        "status": "cancelled",
        "attendees_notified": notify_attendees,
    }


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_create_appointment_ssf() -> SSFDefinition:
    """Create the create_appointment SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="create_appointment",
        version="1.0.0",
        category=SSFCategory.SCHEDULING,
        tags=["calendar", "appointment", "meeting", "schedule"],
        description="Create a new calendar appointment with attendees, time, and location.",
        description_for_llm="Use this SSF to schedule appointments or meetings. Requires title, start/end times, and attendees. Good for coordinating meetings, scheduling appointments with service providers, or booking time slots.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.scheduling",
            function_name="handle_create_appointment",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Appointment title",
                },
                "start_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Start time (ISO 8601)",
                },
                "end_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "End time (ISO 8601)",
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Attendee IDs or emails",
                },
                "location": {
                    "type": "string",
                    "description": "Meeting location",
                },
                "description": {
                    "type": "string",
                    "description": "Appointment description",
                },
                "calendar_id": {
                    "type": "string",
                    "description": "Target calendar ID",
                },
            },
            "required": ["title", "start_time", "end_time", "attendees"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "title": {"type": "string"},
                "start_time": {"type": "string"},
                "end_time": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Creates calendar event",
            "Sends invitations to attendees",
            "Blocks time on calendars",
        ],
        reversible=True,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        ),
    )


def _create_check_availability_ssf() -> SSFDefinition:
    """Create the check_availability SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="check_availability",
        version="1.0.0",
        category=SSFCategory.SCHEDULING,
        tags=["calendar", "availability", "schedule", "free-busy"],
        description="Check calendar availability for one or more users within a time range.",
        description_for_llm="Use this SSF to find when people are available for meetings. Checks calendars and returns free/busy information. Good for finding meeting times, checking if someone is available, or scheduling across multiple people.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.scheduling",
            function_name="handle_check_availability",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Users to check",
                },
                "start_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Range start",
                },
                "end_time": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Range end",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Meeting duration to find slots for",
                },
            },
            "required": ["user_ids", "start_time", "end_time"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "available_slots": {"type": "array"},
                "busy_periods": {"type": "array"},
                "users_checked": {"type": "array"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_send_reminder_ssf() -> SSFDefinition:
    """Create the send_reminder SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="send_reminder",
        version="1.0.0",
        category=SSFCategory.SCHEDULING,
        tags=["reminder", "notification", "schedule", "alert"],
        description="Schedule a reminder notification to be sent at a specific time.",
        description_for_llm="Use this SSF to schedule future reminders for users. Can be linked to appointments or standalone. Good for medication reminders, appointment reminders, follow-up tasks, or time-based alerts.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.scheduling",
            function_name="handle_send_reminder",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User to remind",
                },
                "message": {
                    "type": "string",
                    "description": "Reminder message",
                },
                "remind_at": {
                    "type": "string",
                    "format": "date-time",
                    "description": "When to send reminder",
                },
                "appointment_id": {
                    "type": "string",
                    "description": "Optional linked appointment",
                },
                "reminder_type": {
                    "type": "string",
                    "enum": ["push", "sms", "email"],
                    "default": "push",
                    "description": "Delivery method",
                },
            },
            "required": ["user_id", "message", "remind_at"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "reminder_id": {"type": "string"},
                "user_id": {"type": "string"},
                "remind_at": {"type": "string"},
                "status": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=["Schedules future notification"],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_cancel_appointment_ssf() -> SSFDefinition:
    """Create the cancel_appointment SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="cancel_appointment",
        version="1.0.0",
        category=SSFCategory.SCHEDULING,
        tags=["calendar", "appointment", "cancel", "schedule"],
        description="Cancel an existing appointment and optionally notify attendees.",
        description_for_llm="Use this SSF to cancel appointments. Can notify attendees automatically. Good for rescheduling, handling conflicts, or removing events.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.scheduling",
            function_name="handle_cancel_appointment",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "appointment_id": {
                    "type": "string",
                    "description": "Appointment to cancel",
                },
                "reason": {
                    "type": "string",
                    "description": "Cancellation reason",
                },
                "notify_attendees": {
                    "type": "boolean",
                    "default": True,
                    "description": "Notify attendees",
                },
            },
            "required": ["appointment_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "status": {"type": "string"},
                "attendees_notified": {"type": "boolean"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Removes calendar event",
            "Sends cancellation notices",
        ],
        reversible=False,  # Cancellation cannot be undone automatically
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        ),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in scheduling SSFs."""
    return [
        _create_create_appointment_ssf(),
        _create_check_availability_ssf(),
        _create_send_reminder_ssf(),
        _create_cancel_appointment_ssf(),
    ]
