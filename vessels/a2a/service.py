"""
A2A Service - Agent-to-Agent Communication Service

Manages A2A channels, task delegation, and inter-agent coordination.
Uses Nostr as the decentralized transport layer.

REQUIRES AgentZeroCore - all A2A operations are coordinated through A0.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

from .types import (
    AgentCard,
    AgentSkill,
    Task,
    TaskState,
    Message,
    MessageRole,
    TextPart,
    DataPart,
)

if TYPE_CHECKING:
    from vessels.communication.nostr_adapter import NostrAdapter
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


# =============================================================================
# A2A Event Kinds (Nostr custom kinds 30200-30299)
# =============================================================================

class A2AEventKind:
    """Custom Nostr event kinds for A2A protocol."""
    AGENT_CARD = 30200        # Agent card publication
    TASK_REQUEST = 30201      # Task request from one agent to another
    TASK_UPDATE = 30202       # Task state update
    TASK_RESPONSE = 30203     # Task response/completion
    DISCOVERY_QUERY = 30204   # Query for agents with specific capabilities
    DISCOVERY_RESPONSE = 30205  # Response to discovery query
    CHANNEL_OPEN = 30206      # Open a direct communication channel
    CHANNEL_MESSAGE = 30207   # Message within an established channel
    CHANNEL_CLOSE = 30208     # Close a communication channel


# =============================================================================
# A2A Channel - Direct Agent-to-Agent Communication
# =============================================================================

@dataclass
class A2AChannel:
    """
    Direct communication channel between two agents.

    Channels enable ongoing conversations between agents without
    needing to create new tasks for each message.
    """
    channel_id: str
    local_agent_id: str
    remote_agent_id: str
    remote_agent_card: Optional[AgentCard] = None

    # Channel state
    is_open: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None

    # Message history
    messages: List[Message] = field(default_factory=list)

    # Associated tasks
    task_ids: List[str] = field(default_factory=list)

    def add_message(self, message: Message) -> None:
        """Add a message to the channel."""
        self.messages.append(message)
        self.last_message_at = datetime.utcnow()

    def close(self) -> None:
        """Close the channel."""
        self.is_open = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channelId": self.channel_id,
            "localAgentId": self.local_agent_id,
            "remoteAgentId": self.remote_agent_id,
            "isOpen": self.is_open,
            "createdAt": self.created_at.isoformat(),
            "lastMessageAt": self.last_message_at.isoformat() if self.last_message_at else None,
            "messageCount": len(self.messages),
            "taskIds": self.task_ids,
        }


# =============================================================================
# A2A Service - Main Coordination Service
# =============================================================================

class A2AService:
    """
    Agent-to-Agent Communication Service.

    Manages:
    - Agent card publication and discovery
    - Task delegation between agents
    - Direct communication channels
    - Message routing via Nostr

    REQUIRES AgentZeroCore - all A2A communication is coordinated through A0.

    Usage:
        service = A2AService(agent_zero, my_agent_card, nostr_adapter)
        service.publish_card()  # Make discoverable

        # Send a task to another agent
        task = service.delegate_task(
            target_agent_id="agent-123",
            request="Please help me research grants for community gardens"
        )

        # Open direct channel
        channel = service.open_channel(remote_agent_id="agent-456")
        service.send_message(channel.channel_id, "Hello, can we collaborate?")
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        agent_card: AgentCard,
        nostr_adapter: Optional["NostrAdapter"] = None,
        graphiti_client: Optional[Any] = None,
    ):
        """
        Initialize A2A service.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            agent_card: This agent's identity and capabilities
            nostr_adapter: Nostr adapter for decentralized messaging
            graphiti_client: Optional Graphiti client for graph storage
        """
        if agent_zero is None:
            raise ValueError("A2AService requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.agent_card = agent_card
        self.nostr = nostr_adapter
        self.graphiti = graphiti_client or agent_zero.memory_system

        # Track active tasks and channels
        self.tasks: Dict[str, Task] = {}
        self.channels: Dict[str, A2AChannel] = {}

        # Known remote agents (agent_id -> AgentCard)
        self.known_agents: Dict[str, AgentCard] = {}

        # Callbacks for incoming events
        self._task_handlers: Dict[str, Callable[[Task], None]] = {}
        self._message_handlers: Dict[str, Callable[[Message], None]] = {}

        # Register with A0
        self.agent_zero.a2a_service = self

        logger.info(f"A2A Service initialized for agent: {agent_card.name} ({agent_card.agent_id})")

    # =========================================================================
    # Graph Persistence Helpers
    # =========================================================================

    def _get_graphiti_client(self) -> Optional[Any]:
        """Get the underlying Graphiti client for persistence."""
        if not self.graphiti:
            return None
        # Direct VesselsGraphitiClient
        if hasattr(self.graphiti, 'create_node'):
            return self.graphiti
        # Wrapped in GraphitiMemoryBackend
        if hasattr(self.graphiti, 'graphiti') and hasattr(self.graphiti.graphiti, 'create_node'):
            return self.graphiti.graphiti
        return None

    def _persist_task(self, task: Task) -> None:
        """Persist a task to the knowledge graph."""
        client = self._get_graphiti_client()
        if not client:
            return

        try:
            from vessels.knowledge.schema import NodeType, PropertyName

            client.create_node(
                node_type=NodeType.A2A_TASK,
                properties={
                    "task_id": task.task_id,
                    "context_id": task.context_id,
                    "state": task.state.value,
                    "requester_agent_id": task.requester_agent_id,
                    "executor_agent_id": task.executor_agent_id,
                    "request_text": task.request_message.get_text() if task.request_message else "",
                    "error_message": task.error_message,
                    PropertyName.CREATED_AT: task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                },
                node_id=task.task_id,
            )
        except Exception as e:
            logger.error(f"Failed to persist task to graph: {e}")

    def _persist_channel(self, channel: A2AChannel) -> None:
        """Persist a channel to the knowledge graph."""
        client = self._get_graphiti_client()
        if not client:
            return

        try:
            from vessels.knowledge.schema import NodeType, PropertyName

            client.create_node(
                node_type=NodeType.A2A_CHANNEL,
                properties={
                    "channel_id": channel.channel_id,
                    "local_agent_id": channel.local_agent_id,
                    "remote_agent_id": channel.remote_agent_id,
                    "is_open": channel.is_open,
                    "message_count": len(channel.messages),
                    PropertyName.CREATED_AT: channel.created_at.isoformat(),
                    "last_message_at": channel.last_message_at.isoformat() if channel.last_message_at else None,
                },
                node_id=channel.channel_id,
            )
        except Exception as e:
            logger.error(f"Failed to persist channel to graph: {e}")

    def _persist_message(self, message: Message, channel_id: str) -> None:
        """Persist a message to the knowledge graph."""
        client = self._get_graphiti_client()
        if not client:
            return

        try:
            from vessels.knowledge.schema import NodeType, PropertyName

            client.create_node(
                node_type=NodeType.A2A_MESSAGE,
                properties={
                    "message_id": message.message_id,
                    "channel_id": channel_id,
                    "task_id": message.task_id,
                    "role": message.role.value,
                    "content": message.get_text(),
                    PropertyName.CREATED_AT: message.created_at.isoformat(),
                },
                node_id=message.message_id,
            )
        except Exception as e:
            logger.error(f"Failed to persist message to graph: {e}")

    # =========================================================================
    # Agent Card Management
    # =========================================================================

    def publish_card(self) -> Optional[str]:
        """
        Publish agent card to Nostr for discovery.

        Returns:
            Event ID if published, None otherwise
        """
        if not self.nostr or not self.nostr.enabled:
            logger.warning("Cannot publish agent card - Nostr not enabled")
            return None

        from vessels.communication.nostr_adapter import NostrEvent

        # Create Nostr event with agent card
        event = NostrEvent(
            kind=A2AEventKind.AGENT_CARD,
            content=self.agent_card.to_json(),
            tags=[
                ["t", "vessels"],
                ["t", "a2a"],
                ["t", "agent-card"],
                ["d", self.agent_card.agent_id],  # NIP-33 replaceable event
            ],
            pubkey=self.nostr.keypair.public_key,
        )

        event.compute_id()
        event.sig = self.nostr.keypair.sign(event.to_dict())

        # Publish
        self.nostr._publish_to_relays(event)
        logger.info(f"Published agent card for {self.agent_card.name}")

        return event.id

    def update_card(self, **updates) -> None:
        """Update agent card fields."""
        for key, value in updates.items():
            if hasattr(self.agent_card, key):
                setattr(self.agent_card, key, value)
        self.agent_card.updated_at = datetime.utcnow()
        self.publish_card()

    # =========================================================================
    # Task Delegation
    # =========================================================================

    def delegate_task(
        self,
        target_agent_id: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
    ) -> Task:
        """
        Delegate a task to another agent.

        Args:
            target_agent_id: ID of the agent to handle the task
            request: Natural language task request
            context: Optional context data
            timeout_seconds: Task timeout

        Returns:
            Created Task object
        """
        task = Task.create(
            request_text=request,
            requester_id=self.agent_card.agent_id,
            executor_id=target_agent_id,
        )

        # Add context if provided
        if context:
            task.request_message.parts.append(DataPart(data=context))

        self.tasks[task.task_id] = task

        # Persist to graph
        self._persist_task(task)

        # Send via Nostr
        self._send_task_event(task, A2AEventKind.TASK_REQUEST)

        logger.info(f"Delegated task {task.task_id[:8]}... to agent {target_agent_id[:8]}...")
        return task

    def accept_task(self, task_id: str) -> Optional[Task]:
        """Accept an incoming task and start working on it."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None

        task.transition_to(TaskState.WORKING)
        self._persist_task(task)  # Update state in graph
        self._send_task_event(task, A2AEventKind.TASK_UPDATE)

        return task

    def complete_task(
        self,
        task_id: str,
        response: str,
        artifacts: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Task]:
        """
        Complete a task with a response.

        Args:
            task_id: ID of the task to complete
            response: Response message
            artifacts: Optional list of artifacts produced

        Returns:
            Updated Task or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None

        # Add response
        response_msg = Message.from_text(
            MessageRole.AGENT,
            response,
            task_id=task_id,
            context_id=task.context_id,
        )
        task.add_response(response_msg)

        # Add artifacts
        if artifacts:
            from .types import TaskArtifact
            for a in artifacts:
                task.artifacts.append(TaskArtifact(
                    artifact_id=str(uuid.uuid4()),
                    name=a.get("name", "artifact"),
                    description=a.get("description"),
                    parts=[DataPart(data=a.get("data", {}))] if "data" in a else [],
                ))

        task.transition_to(TaskState.COMPLETED)
        self._persist_task(task)  # Update state in graph
        self._send_task_event(task, A2AEventKind.TASK_RESPONSE)

        logger.info(f"Completed task {task_id[:8]}...")
        return task

    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """Mark a task as failed."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.transition_to(TaskState.FAILED, error=error)
        self._persist_task(task)  # Update state in graph
        self._send_task_event(task, A2AEventKind.TASK_RESPONSE)

        logger.warning(f"Task {task_id[:8]}... failed: {error}")
        return task

    def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.transition_to(TaskState.CANCELLED)
        self._persist_task(task)  # Update state in graph
        self._send_task_event(task, A2AEventKind.TASK_UPDATE)

        logger.info(f"Cancelled task {task_id[:8]}...")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        state: Optional[TaskState] = None,
        agent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filtering."""
        tasks = list(self.tasks.values())

        if state:
            tasks = [t for t in tasks if t.state == state]
        if agent_id:
            tasks = [t for t in tasks
                    if t.requester_agent_id == agent_id
                    or t.executor_agent_id == agent_id]

        return tasks

    def _send_task_event(self, task: Task, kind: int) -> None:
        """Send task event via Nostr."""
        if not self.nostr or not self.nostr.enabled:
            return

        from vessels.communication.nostr_adapter import NostrEvent

        event = NostrEvent(
            kind=kind,
            content=json.dumps(task.to_dict()),
            tags=[
                ["t", "vessels"],
                ["t", "a2a"],
                ["t", "task"],
                ["task", task.task_id],
                ["p", task.executor_agent_id or ""],  # Target agent
            ],
            pubkey=self.nostr.keypair.public_key,
        )

        event.compute_id()
        event.sig = self.nostr.keypair.sign(event.to_dict())
        self.nostr._publish_to_relays(event)

    # =========================================================================
    # Direct Channels
    # =========================================================================

    def open_channel(
        self,
        remote_agent_id: str,
        remote_agent_card: Optional[AgentCard] = None,
    ) -> A2AChannel:
        """
        Open a direct communication channel with another agent.

        Args:
            remote_agent_id: ID of the remote agent
            remote_agent_card: Optional agent card (will be looked up if not provided)

        Returns:
            Opened A2AChannel
        """
        channel_id = str(uuid.uuid4())

        channel = A2AChannel(
            channel_id=channel_id,
            local_agent_id=self.agent_card.agent_id,
            remote_agent_id=remote_agent_id,
            remote_agent_card=remote_agent_card or self.known_agents.get(remote_agent_id),
        )

        self.channels[channel_id] = channel

        # Persist to graph
        self._persist_channel(channel)

        # Announce channel opening
        self._send_channel_event(channel, A2AEventKind.CHANNEL_OPEN)

        logger.info(f"Opened channel {channel_id[:8]}... with agent {remote_agent_id[:8]}...")
        return channel

    def send_message(
        self,
        channel_id: str,
        text: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Message]:
        """
        Send a message on a channel.

        Args:
            channel_id: ID of the channel
            text: Message text
            data: Optional structured data

        Returns:
            Sent Message or None if channel not found
        """
        channel = self.channels.get(channel_id)
        if not channel or not channel.is_open:
            logger.warning(f"Channel {channel_id} not found or closed")
            return None

        parts = [TextPart(text=text)]
        if data:
            parts.append(DataPart(data=data))

        message = Message(
            role=MessageRole.AGENT,
            parts=parts,
            context_id=channel_id,
        )

        channel.add_message(message)

        # Persist to graph
        self._persist_message(message, channel_id)

        # Send via Nostr
        self._send_message_event(channel, message)

        return message

    def close_channel(self, channel_id: str) -> bool:
        """Close a communication channel."""
        channel = self.channels.get(channel_id)
        if not channel:
            return False

        channel.close()
        self._send_channel_event(channel, A2AEventKind.CHANNEL_CLOSE)

        logger.info(f"Closed channel {channel_id[:8]}...")
        return True

    def get_channel(self, channel_id: str) -> Optional[A2AChannel]:
        """Get channel by ID."""
        return self.channels.get(channel_id)

    def list_channels(self, include_closed: bool = False) -> List[A2AChannel]:
        """List channels."""
        channels = list(self.channels.values())
        if not include_closed:
            channels = [c for c in channels if c.is_open]
        return channels

    def _send_channel_event(self, channel: A2AChannel, kind: int) -> None:
        """Send channel event via Nostr."""
        if not self.nostr or not self.nostr.enabled:
            return

        from vessels.communication.nostr_adapter import NostrEvent

        event = NostrEvent(
            kind=kind,
            content=json.dumps(channel.to_dict()),
            tags=[
                ["t", "vessels"],
                ["t", "a2a"],
                ["t", "channel"],
                ["channel", channel.channel_id],
                ["p", channel.remote_agent_id],
            ],
            pubkey=self.nostr.keypair.public_key,
        )

        event.compute_id()
        event.sig = self.nostr.keypair.sign(event.to_dict())
        self.nostr._publish_to_relays(event)

    def _send_message_event(self, channel: A2AChannel, message: Message) -> None:
        """Send message event via Nostr."""
        if not self.nostr or not self.nostr.enabled:
            return

        from vessels.communication.nostr_adapter import NostrEvent

        event = NostrEvent(
            kind=A2AEventKind.CHANNEL_MESSAGE,
            content=json.dumps(message.to_dict()),
            tags=[
                ["t", "vessels"],
                ["t", "a2a"],
                ["channel", channel.channel_id],
                ["p", channel.remote_agent_id],
            ],
            pubkey=self.nostr.keypair.public_key,
        )

        event.compute_id()
        event.sig = self.nostr.keypair.sign(event.to_dict())
        self.nostr._publish_to_relays(event)

    # =========================================================================
    # Event Handling
    # =========================================================================

    def on_task(self, task_id: str, handler: Callable[[Task], None]) -> None:
        """Register handler for task updates."""
        self._task_handlers[task_id] = handler

    def on_message(self, channel_id: str, handler: Callable[[Message], None]) -> None:
        """Register handler for incoming messages."""
        self._message_handlers[channel_id] = handler

    def subscribe_to_a2a_events(self) -> Optional[str]:
        """
        Subscribe to incoming A2A events via Nostr.

        Returns:
            Subscription ID if successful
        """
        if not self.nostr or not self.nostr.enabled:
            logger.warning("Cannot subscribe - Nostr not enabled")
            return None

        filters = [{
            "kinds": [
                A2AEventKind.TASK_REQUEST,
                A2AEventKind.TASK_UPDATE,
                A2AEventKind.TASK_RESPONSE,
                A2AEventKind.CHANNEL_OPEN,
                A2AEventKind.CHANNEL_MESSAGE,
            ],
            "#p": [self.agent_card.nostr_pubkey or self.nostr.keypair.public_key],
            "#t": ["a2a"],
        }]

        return self.nostr.subscribe(filters, self._handle_a2a_event)

    def _handle_a2a_event(self, event: Any) -> None:
        """Handle incoming A2A Nostr event."""
        try:
            content = json.loads(event.content)

            if event.kind == A2AEventKind.TASK_REQUEST:
                self._handle_incoming_task(content)
            elif event.kind in (A2AEventKind.TASK_UPDATE, A2AEventKind.TASK_RESPONSE):
                self._handle_task_update(content)
            elif event.kind == A2AEventKind.CHANNEL_MESSAGE:
                self._handle_channel_message(content, event)

        except Exception as e:
            logger.error(f"Error handling A2A event: {e}")

    def _handle_incoming_task(self, content: Dict[str, Any]) -> None:
        """Handle incoming task request."""
        task_id = content.get("taskId")
        if not task_id:
            return

        # Create local task representation
        task = Task(
            task_id=task_id,
            context_id=content.get("contextId", str(uuid.uuid4())),
            state=TaskState.PENDING,
            requester_agent_id=content.get("requesterAgentId"),
            executor_agent_id=self.agent_card.agent_id,
        )

        # Parse request message
        if "requestMessage" in content:
            rm = content["requestMessage"]
            task.request_message = Message(
                role=MessageRole(rm.get("role", "user")),
                parts=[TextPart(text=p.get("text", "")) for p in rm.get("parts", [])
                       if p.get("type") == "text"],
                message_id=rm.get("messageId", str(uuid.uuid4())),
            )

        self.tasks[task_id] = task

        # Notify handler
        if task_id in self._task_handlers:
            self._task_handlers[task_id](task)

        logger.info(f"Received task request: {task_id[:8]}...")

    def _handle_task_update(self, content: Dict[str, Any]) -> None:
        """Handle task update."""
        task_id = content.get("taskId")
        if not task_id or task_id not in self.tasks:
            return

        task = self.tasks[task_id]
        new_state = TaskState(content.get("state", "pending"))
        task.transition_to(new_state, error=content.get("errorMessage"))

        # Parse response messages
        for rm in content.get("responseMessages", []):
            task.response_messages.append(Message(
                role=MessageRole(rm.get("role", "agent")),
                parts=[TextPart(text=p.get("text", "")) for p in rm.get("parts", [])
                       if p.get("type") == "text"],
                message_id=rm.get("messageId", str(uuid.uuid4())),
            ))

        # Notify handler
        if task_id in self._task_handlers:
            self._task_handlers[task_id](task)

    def _handle_channel_message(self, content: Dict[str, Any], event: Any) -> None:
        """Handle incoming channel message."""
        channel_id = content.get("contextId")

        # Try to find channel from event tags
        for tag in event.tags:
            if tag[0] == "channel" and len(tag) > 1:
                channel_id = tag[1]
                break

        if not channel_id:
            return

        # Get or create channel
        if channel_id not in self.channels:
            # Create channel from incoming message
            sender_pubkey = event.pubkey
            self.channels[channel_id] = A2AChannel(
                channel_id=channel_id,
                local_agent_id=self.agent_card.agent_id,
                remote_agent_id=sender_pubkey,  # Use pubkey as fallback ID
            )

        channel = self.channels[channel_id]

        # Parse message
        message = Message(
            role=MessageRole(content.get("role", "agent")),
            parts=[TextPart(text=p.get("text", "")) for p in content.get("parts", [])
                   if p.get("type") == "text"],
            message_id=content.get("messageId", str(uuid.uuid4())),
            context_id=channel_id,
        )

        channel.add_message(message)

        # Persist incoming message to graph
        self._persist_message(message, channel_id)

        # Notify handler
        if channel_id in self._message_handlers:
            self._message_handlers[channel_id](message)

    # =========================================================================
    # Agent Discovery
    # =========================================================================

    def register_known_agent(self, agent_card: AgentCard) -> None:
        """Register a known agent for future communication."""
        self.known_agents[agent_card.agent_id] = agent_card
        logger.debug(f"Registered known agent: {agent_card.name}")

    def get_known_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get a known agent by ID."""
        return self.known_agents.get(agent_id)

    def find_agents_for_need(
        self,
        need: str,
        tags: Optional[List[str]] = None,
    ) -> List[AgentCard]:
        """
        Find known agents that can help with a need.

        Args:
            need: Description of what's needed
            tags: Optional tags to filter by

        Returns:
            List of matching AgentCards sorted by relevance
        """
        scored_agents = []

        for agent_card in self.known_agents.values():
            score = agent_card.matches_need(need, tags)
            if score > 0:
                scored_agents.append((score, agent_card))

        # Sort by score descending
        scored_agents.sort(key=lambda x: x[0], reverse=True)

        return [card for _, card in scored_agents]

    def to_dict(self) -> Dict[str, Any]:
        """Get service status as dictionary."""
        return {
            "agentId": self.agent_card.agent_id,
            "agentName": self.agent_card.name,
            "nostrEnabled": self.nostr.enabled if self.nostr else False,
            "activeTasks": len([t for t in self.tasks.values() if not t.state.is_terminal()]),
            "totalTasks": len(self.tasks),
            "openChannels": len([c for c in self.channels.values() if c.is_open]),
            "knownAgents": len(self.known_agents),
        }
