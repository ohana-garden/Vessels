"""
SSF Logging - Execution Logging to Graphiti.

All SSF executions are logged to the shared memory system for:
- Audit trails
- Performance analysis
- Pattern detection
- Debugging
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .schema import SSFResult, SSFStatus, SSFCategory, RiskLevel

logger = logging.getLogger(__name__)


class ExecutionEventType(str, Enum):
    """Types of execution events."""
    INVOKED = "invoked"           # SSF was invoked
    SUCCEEDED = "succeeded"       # SSF completed successfully
    BLOCKED = "blocked"           # SSF was blocked by constraints
    FAILED = "failed"             # SSF failed with error
    TIMEOUT = "timeout"           # SSF timed out
    ESCALATED = "escalated"       # SSF escalated to supervisor
    SPAWNED = "spawned"           # New SSF was spawned
    COMPOSED = "composed"         # SSF composition executed


@dataclass
class SSFExecutionLog:
    """
    Log entry for an SSF execution.

    Contains all relevant context for audit and analysis.
    """
    # Identity
    log_id: UUID = field(default_factory=uuid4)
    event_type: ExecutionEventType = ExecutionEventType.INVOKED

    # SSF info
    ssf_id: UUID = field(default_factory=uuid4)
    ssf_name: str = ""
    ssf_version: str = "1.0.0"
    category: SSFCategory = SSFCategory.COMPUTATION
    risk_level: RiskLevel = RiskLevel.LOW

    # Execution context
    persona_id: Optional[UUID] = None
    agent_id: Optional[str] = None
    community_id: Optional[str] = None
    vessel_id: Optional[str] = None
    request_id: Optional[UUID] = None

    # Execution details
    inputs_hash: Optional[str] = None  # Hash of inputs for privacy
    inputs_summary: Optional[str] = None  # Summarized inputs
    output_hash: Optional[str] = None  # Hash of output
    output_summary: Optional[str] = None  # Summarized output

    # Result
    status: SSFStatus = SSFStatus.SUCCESS
    error_message: Optional[str] = None
    constraint_violations: List[str] = field(default_factory=list)

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    overhead_ms: float = 0.0  # SSF system overhead

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "log_id": str(self.log_id),
            "event_type": self.event_type.value,
            "ssf_id": str(self.ssf_id),
            "ssf_name": self.ssf_name,
            "ssf_version": self.ssf_version,
            "category": self.category.value,
            "risk_level": self.risk_level.value,
            "persona_id": str(self.persona_id) if self.persona_id else None,
            "agent_id": self.agent_id,
            "community_id": self.community_id,
            "vessel_id": self.vessel_id,
            "request_id": str(self.request_id) if self.request_id else None,
            "inputs_hash": self.inputs_hash,
            "inputs_summary": self.inputs_summary,
            "output_hash": self.output_hash,
            "output_summary": self.output_summary,
            "status": self.status.value,
            "error_message": self.error_message,
            "constraint_violations": self.constraint_violations,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "overhead_ms": self.overhead_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSFExecutionLog":
        """Create from dictionary."""
        return cls(
            log_id=UUID(d["log_id"]) if d.get("log_id") else uuid4(),
            event_type=ExecutionEventType(d.get("event_type", "invoked")),
            ssf_id=UUID(d["ssf_id"]) if d.get("ssf_id") else uuid4(),
            ssf_name=d.get("ssf_name", ""),
            ssf_version=d.get("ssf_version", "1.0.0"),
            category=SSFCategory(d.get("category", "computation")),
            risk_level=RiskLevel(d.get("risk_level", "low")),
            persona_id=UUID(d["persona_id"]) if d.get("persona_id") else None,
            agent_id=d.get("agent_id"),
            community_id=d.get("community_id"),
            vessel_id=d.get("vessel_id"),
            request_id=UUID(d["request_id"]) if d.get("request_id") else None,
            inputs_hash=d.get("inputs_hash"),
            inputs_summary=d.get("inputs_summary"),
            output_hash=d.get("output_hash"),
            output_summary=d.get("output_summary"),
            status=SSFStatus(d.get("status", "success")),
            error_message=d.get("error_message"),
            constraint_violations=d.get("constraint_violations", []),
            started_at=datetime.fromisoformat(d["started_at"]) if d.get("started_at") else datetime.utcnow(),
            completed_at=datetime.fromisoformat(d["completed_at"]) if d.get("completed_at") else None,
            duration_seconds=d.get("duration_seconds", 0.0),
            overhead_ms=d.get("overhead_ms", 0.0),
            metadata=d.get("metadata", {}),
        )


class SSFLogger:
    """
    Logger for SSF executions.

    Logs to both:
    - Standard Python logging (for immediate visibility)
    - Graphiti memory (for persistent audit trail)
    """

    def __init__(
        self,
        memory_client: Optional[Any] = None,
        community_id: Optional[str] = None,
        enable_detailed_logging: bool = True,
        max_summary_length: int = 200,
    ):
        """
        Initialize the SSF logger.

        Args:
            memory_client: Graphiti client for persistence
            community_id: Default community ID for logs
            enable_detailed_logging: Whether to log detailed info
            max_summary_length: Max length for input/output summaries
        """
        self.memory_client = memory_client
        self.community_id = community_id
        self.enable_detailed_logging = enable_detailed_logging
        self.max_summary_length = max_summary_length

        # In-memory buffer for batching
        self._buffer: List[SSFExecutionLog] = []
        self._buffer_max_size = 100

        # Statistics
        self._total_logged = 0
        self._logs_by_status: Dict[str, int] = {}

    async def log_execution(
        self,
        ssf_id: UUID,
        ssf_name: str,
        category: SSFCategory,
        risk_level: RiskLevel,
        result: SSFResult,
        inputs: Dict[str, Any],
        persona_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        community_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        request_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SSFExecutionLog:
        """
        Log an SSF execution.

        Args:
            ssf_id: ID of the SSF
            ssf_name: Name of the SSF
            category: SSF category
            risk_level: Risk level
            result: Execution result
            inputs: Input parameters
            persona_id: Invoking persona ID
            agent_id: Invoking agent ID
            community_id: Community context
            vessel_id: Vessel context
            request_id: Request tracking ID
            metadata: Additional metadata

        Returns:
            Created log entry
        """
        # Determine event type from result
        event_type = self._status_to_event_type(result.status)

        # Create log entry
        log_entry = SSFExecutionLog(
            event_type=event_type,
            ssf_id=ssf_id,
            ssf_name=ssf_name,
            category=category,
            risk_level=risk_level,
            persona_id=persona_id,
            agent_id=agent_id,
            community_id=community_id or self.community_id,
            vessel_id=vessel_id,
            request_id=request_id,
            inputs_hash=self._hash_data(inputs),
            inputs_summary=self._summarize_data(inputs),
            output_hash=self._hash_data(result.output) if result.output else None,
            output_summary=self._summarize_data(result.output) if result.output else None,
            status=result.status,
            error_message=result.error,
            constraint_violations=(
                result.constraint_violation.violations
                if result.constraint_violation else []
            ),
            started_at=result.invoked_at,
            completed_at=datetime.utcnow(),
            duration_seconds=result.execution_time_seconds,
            metadata=metadata or {},
        )

        # Log to Python logger
        self._log_to_python_logger(log_entry)

        # Add to buffer
        self._buffer.append(log_entry)

        # Update statistics
        self._total_logged += 1
        status_key = result.status.value
        self._logs_by_status[status_key] = self._logs_by_status.get(status_key, 0) + 1

        # Flush buffer if full
        if len(self._buffer) >= self._buffer_max_size:
            await self.flush()

        return log_entry

    async def log_spawn(
        self,
        ssf_id: UUID,
        ssf_name: str,
        spawned_by_persona: UUID,
        spawned_by_agent: str,
        community_id: Optional[str] = None,
    ) -> SSFExecutionLog:
        """
        Log an SSF spawn event.

        Args:
            ssf_id: ID of the spawned SSF
            ssf_name: Name of the spawned SSF
            spawned_by_persona: Persona that spawned it
            spawned_by_agent: Agent that spawned it
            community_id: Community context

        Returns:
            Created log entry
        """
        log_entry = SSFExecutionLog(
            event_type=ExecutionEventType.SPAWNED,
            ssf_id=ssf_id,
            ssf_name=ssf_name,
            persona_id=spawned_by_persona,
            agent_id=spawned_by_agent,
            community_id=community_id or self.community_id,
            status=SSFStatus.SUCCESS,
            metadata={"event": "ssf_spawned"},
        )

        self._log_to_python_logger(log_entry)
        self._buffer.append(log_entry)

        return log_entry

    async def log_composition(
        self,
        composition_id: UUID,
        step_count: int,
        completed_steps: int,
        status: str,
        duration_seconds: float,
        persona_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        community_id: Optional[str] = None,
    ) -> SSFExecutionLog:
        """
        Log an SSF composition event.

        Args:
            composition_id: ID of the composition
            step_count: Total number of steps
            completed_steps: Steps completed
            status: Composition status
            duration_seconds: Total duration
            persona_id: Invoking persona
            agent_id: Invoking agent
            community_id: Community context

        Returns:
            Created log entry
        """
        log_entry = SSFExecutionLog(
            event_type=ExecutionEventType.COMPOSED,
            ssf_id=composition_id,
            ssf_name=f"composition_{composition_id}",
            persona_id=persona_id,
            agent_id=agent_id,
            community_id=community_id or self.community_id,
            status=SSFStatus.SUCCESS if status == "complete" else SSFStatus.ERROR,
            duration_seconds=duration_seconds,
            metadata={
                "event": "ssf_composition",
                "step_count": step_count,
                "completed_steps": completed_steps,
                "composition_status": status,
            },
        )

        self._log_to_python_logger(log_entry)
        self._buffer.append(log_entry)

        return log_entry

    async def flush(self) -> int:
        """
        Flush buffered logs to persistent storage.

        Returns:
            Number of logs flushed
        """
        if not self._buffer:
            return 0

        logs_to_flush = self._buffer.copy()
        self._buffer.clear()

        if self.memory_client:
            try:
                await self._persist_to_graphiti(logs_to_flush)
            except Exception as e:
                logger.error(f"Failed to persist SSF logs: {e}")
                # Re-add to buffer on failure
                self._buffer.extend(logs_to_flush)
                return 0

        return len(logs_to_flush)

    async def query_logs(
        self,
        ssf_id: Optional[UUID] = None,
        persona_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        status: Optional[SSFStatus] = None,
        event_type: Optional[ExecutionEventType] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SSFExecutionLog]:
        """
        Query execution logs.

        Args:
            ssf_id: Filter by SSF ID
            persona_id: Filter by persona ID
            agent_id: Filter by agent ID
            status: Filter by status
            event_type: Filter by event type
            since: Start time filter
            until: End time filter
            limit: Maximum results

        Returns:
            Matching log entries
        """
        # Query from buffer first
        results = []

        for log in self._buffer:
            if ssf_id and log.ssf_id != ssf_id:
                continue
            if persona_id and log.persona_id != persona_id:
                continue
            if agent_id and log.agent_id != agent_id:
                continue
            if status and log.status != status:
                continue
            if event_type and log.event_type != event_type:
                continue
            if since and log.started_at < since:
                continue
            if until and log.started_at > until:
                continue

            results.append(log)

        # Query from Graphiti if available
        if self.memory_client:
            try:
                persisted = await self._query_from_graphiti(
                    ssf_id=ssf_id,
                    persona_id=persona_id,
                    agent_id=agent_id,
                    status=status,
                    event_type=event_type,
                    since=since,
                    until=until,
                    limit=limit - len(results),
                )
                results.extend(persisted)
            except Exception as e:
                logger.warning(f"Failed to query Graphiti logs: {e}")

        # Sort by time and limit
        results.sort(key=lambda x: x.started_at, reverse=True)
        return results[:limit]

    def _status_to_event_type(self, status: SSFStatus) -> ExecutionEventType:
        """Convert SSF status to event type."""
        mapping = {
            SSFStatus.SUCCESS: ExecutionEventType.SUCCEEDED,
            SSFStatus.BLOCKED: ExecutionEventType.BLOCKED,
            SSFStatus.ESCALATED: ExecutionEventType.ESCALATED,
            SSFStatus.TIMEOUT: ExecutionEventType.TIMEOUT,
            SSFStatus.ERROR: ExecutionEventType.FAILED,
            SSFStatus.OUTPUT_BLOCKED: ExecutionEventType.BLOCKED,
            SSFStatus.PARTIAL: ExecutionEventType.FAILED,
        }
        return mapping.get(status, ExecutionEventType.INVOKED)

    def _hash_data(self, data: Any) -> str:
        """Create a hash of data for tracking without storing content."""
        import hashlib

        try:
            content = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except Exception:
            return "hash_error"

    def _summarize_data(self, data: Any) -> str:
        """Create a safe summary of data."""
        if data is None:
            return "null"

        try:
            text = json.dumps(data, default=str)
            if len(text) > self.max_summary_length:
                return text[:self.max_summary_length] + "..."
            return text
        except Exception:
            return str(data)[:self.max_summary_length]

    def _log_to_python_logger(self, log_entry: SSFExecutionLog) -> None:
        """Log to Python logger."""
        if not self.enable_detailed_logging:
            return

        level = logging.INFO
        if log_entry.status in [SSFStatus.BLOCKED, SSFStatus.OUTPUT_BLOCKED]:
            level = logging.WARNING
        elif log_entry.status in [SSFStatus.ERROR, SSFStatus.TIMEOUT]:
            level = logging.ERROR

        message = (
            f"SSF {log_entry.event_type.value}: {log_entry.ssf_name} "
            f"[{log_entry.status.value}] "
            f"({log_entry.duration_seconds:.3f}s)"
        )

        if log_entry.error_message:
            message += f" - {log_entry.error_message}"

        logger.log(level, message)

    async def _persist_to_graphiti(self, logs: List[SSFExecutionLog]) -> None:
        """Persist logs to Graphiti."""
        # Placeholder - implementation depends on Graphiti interface
        pass

    async def _query_from_graphiti(
        self,
        **filters: Any
    ) -> List[SSFExecutionLog]:
        """Query logs from Graphiti."""
        # Placeholder - implementation depends on Graphiti interface
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        return {
            "total_logged": self._total_logged,
            "buffer_size": len(self._buffer),
            "logs_by_status": self._logs_by_status,
        }


# Global logger instance
ssf_logger = SSFLogger()
