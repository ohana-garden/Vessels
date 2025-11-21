"""
Nostr Protocol Adapter for Vessels

Implements decentralized event publishing and subscription using the Nostr protocol.
Provides censorship-resistant discovery, offers/needs signaling, and community coordination.

References:
- NIP-01: Basic protocol flow
- NIP-05: Mapping Nostr keys to DNS-based identifiers
"""

import json
import time
import logging
import hashlib
from typing import List, Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import IntEnum

logger = logging.getLogger(__name__)


class VesselsEventKind(IntEnum):
    """Custom Vessels event kinds (30100-30199 range)"""
    NODE_STATUS = 30100       # Regular heartbeat from Vessels node
    OFFER = 30101            # Resource offer (food, tools, labor)
    NEED = 30102             # Resource need (seeking help, materials)
    COMMUNITY_METRIC = 30103 # Anonymized participation scores
    ANNOUNCEMENT = 30104     # Community event announcement
    COORDINATION = 30105     # Cross-community coordination request
    DISCOVERY = 30106        # Node discovery / capability advertisement


@dataclass
class NostrKeypair:
    """Nostr keypair for signing events"""
    public_key: str   # Hex-encoded 32-byte pubkey
    private_key: str  # Hex-encoded 32-byte privkey

    @classmethod
    def generate(cls) -> "NostrKeypair":
        """Generate a new random keypair"""
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization

            private_key_obj = ed25519.Ed25519PrivateKey.generate()
            public_key_obj = private_key_obj.public_key()

            private_bytes = private_key_obj.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )

            return cls(
                public_key=public_bytes.hex(),
                private_key=private_bytes.hex()
            )
        except ImportError:
            logger.warning("cryptography library not available, using dummy keypair")
            # Fallback for testing
            import secrets
            return cls(
                public_key=secrets.token_hex(32),
                private_key=secrets.token_hex(32)
            )

    def sign(self, event: Dict[str, Any]) -> str:
        """
        Sign a Nostr event according to NIP-01

        Returns: 64-byte hex signature
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519

            # Serialize event for signing (NIP-01 format)
            serialized = json.dumps([
                0,  # Reserved for future use
                event["pubkey"],
                event["created_at"],
                event["kind"],
                event["tags"],
                event["content"]
            ], separators=(',', ':'), ensure_ascii=False)

            # SHA256 hash of serialized event
            event_hash = hashlib.sha256(serialized.encode()).digest()

            # Sign with private key
            private_bytes = bytes.fromhex(self.private_key)
            private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
            signature = private_key_obj.sign(event_hash)

            return signature.hex()
        except ImportError:
            # Fallback for testing without cryptography
            logger.warning("cryptography not available, using mock signature")
            return hashlib.sha256(json.dumps(event).encode()).hexdigest()[:128]


class NostrEvent:
    """Nostr event structure (NIP-01)"""

    def __init__(
        self,
        kind: int,
        content: str,
        tags: List[List[str]],
        pubkey: str,
        created_at: Optional[int] = None
    ):
        self.kind = kind
        self.content = content
        self.tags = tags
        self.pubkey = pubkey
        self.created_at = created_at or int(time.time())
        self.id = ""
        self.sig = ""

    def compute_id(self) -> str:
        """Compute event ID (SHA256 hash)"""
        serialized = json.dumps([
            0,
            self.pubkey,
            self.created_at,
            self.kind,
            self.tags,
            self.content
        ], separators=(',', ':'), ensure_ascii=False)

        self.id = hashlib.sha256(serialized.encode()).hexdigest()
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Nostr wire format"""
        return {
            "id": self.id,
            "pubkey": self.pubkey,
            "created_at": self.created_at,
            "kind": self.kind,
            "tags": self.tags,
            "content": self.content,
            "sig": self.sig
        }


class NostrAdapter:
    """
    Adapter for Nostr protocol communication

    Provides publish/subscribe interface for Vessels events over Nostr relays.
    All external communication is opt-in and privacy-filtered.
    """

    def __init__(
        self,
        keypair: NostrKeypair,
        relays: List[str],
        enabled: bool = False,
        publish_types: Optional[List[str]] = None
    ):
        """
        Initialize Nostr adapter

        Args:
            keypair: Nostr keypair for signing
            relays: List of relay URLs (wss://...)
            enabled: Whether Nostr is enabled (default: False)
            publish_types: Event types allowed for publishing (empty = none)
        """
        self.keypair = keypair
        self.relays = relays
        self.enabled = enabled
        self.publish_types = set(publish_types or [])

        self.subscriptions = {}  # subscription_id -> callback
        self._client = None

        if self.enabled:
            logger.info(f"Nostr adapter initialized with {len(relays)} relays")
            logger.info(f"Publish types: {self.publish_types or 'NONE'}")
        else:
            logger.info("Nostr adapter initialized but DISABLED")

    def _ensure_enabled(self):
        """Raise error if Nostr is not enabled"""
        if not self.enabled:
            from . import ProtocolNotEnabled
            raise ProtocolNotEnabled("Nostr protocol is not enabled")

    def _connect(self):
        """Lazy connection to Nostr relays"""
        if self._client is None:
            try:
                # Try to import a Nostr client library
                # For now, we'll use a minimal WebSocket implementation
                import asyncio
                import websockets
                self._client = {"connected": True, "websockets": websockets}
                logger.info("Nostr client connected")
            except ImportError:
                logger.error("websockets library required for Nostr. Install: pip install websockets")
                self._client = {"connected": False}
        return self._client

    def publish_event(
        self,
        kind: VesselsEventKind,
        content: Dict[str, Any],
        tags: Optional[List[List[str]]] = None,
        sanitized: bool = False
    ) -> Optional[str]:
        """
        Publish a Vessels event to Nostr relays

        Args:
            kind: Event kind (VesselsEventKind)
            content: Event content (will be JSON-serialized)
            tags: Nostr tags (e.g., [["e", "event_id"], ["p", "pubkey"]])
            sanitized: Whether content has been sanitized

        Returns:
            Event ID if published, None otherwise
        """
        self._ensure_enabled()

        # Check if this event type is allowed
        kind_name = VesselsEventKind(kind).name.lower()
        if kind_name not in self.publish_types:
            logger.debug(f"Event type {kind_name} not in publish_types, skipping")
            return None

        # Ensure content is sanitized
        if not sanitized:
            from .sanitizer import DataSanitizer
            sanitizer = DataSanitizer()
            content = sanitizer.sanitize(content, event_type=kind_name)

        # Create Nostr event
        event = NostrEvent(
            kind=int(kind),
            content=json.dumps(content),
            tags=tags or [],
            pubkey=self.keypair.public_key
        )

        # Compute ID and sign
        event.compute_id()
        event.sig = self.keypair.sign(event.to_dict())

        # Publish to relays
        self._publish_to_relays(event)

        logger.info(f"Published Nostr event {event.id[:8]}... (kind {kind})")
        return event.id

    def _publish_to_relays(self, event: NostrEvent):
        """
        Send event to all configured relays

        Note: This is a simplified synchronous implementation.
        Production should use async WebSocket connections.
        """
        client = self._connect()
        if not client.get("connected"):
            logger.warning("Nostr client not connected, event not published")
            return

        # In a real implementation, we'd send to each relay:
        # ["EVENT", event.to_dict()]

        # For now, just log
        logger.debug(f"Would publish to {len(self.relays)} relays: {event.id}")

    def subscribe(
        self,
        filters: List[Dict[str, Any]],
        callback: Callable[[NostrEvent], None],
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to Nostr events matching filters

        Args:
            filters: List of Nostr filters, e.g.:
                [
                    {"kinds": [30101, 30102], "authors": ["pubkey1", "pubkey2"]},
                    {"#t": ["vessels", "garden"], "limit": 100}
                ]
            callback: Function to call for each matching event
            subscription_id: Optional subscription ID (generated if not provided)

        Returns:
            Subscription ID
        """
        self._ensure_enabled()

        sub_id = subscription_id or f"vessels_{int(time.time())}"

        self.subscriptions[sub_id] = {
            "filters": filters,
            "callback": callback,
            "created_at": time.time()
        }

        # In a real implementation, send to relays:
        # ["REQ", sub_id, *filters]

        logger.info(f"Created subscription {sub_id} with {len(filters)} filters")
        return sub_id

    def unsubscribe(self, subscription_id: str):
        """Cancel a subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Cancelled subscription {subscription_id}")

            # In a real implementation, send to relays:
            # ["CLOSE", subscription_id]

    def publish_node_status(self, status: Dict[str, Any]):
        """
        Publish node heartbeat status

        Args:
            status: {
                "node_id": str,
                "version": str,
                "capabilities": List[str],
                "uptime_seconds": int
            }
        """
        self.publish_event(
            kind=VesselsEventKind.NODE_STATUS,
            content=status,
            tags=[["t", "vessels"], ["t", "status"]]
        )

    def publish_offer(
        self,
        resource_type: str,
        quantity: float,
        unit: str,
        location_hint: Optional[str] = None,
        expiry_timestamp: Optional[int] = None
    ):
        """
        Publish a resource offer

        Example:
            publish_offer("tomatoes", 5.0, "kg", "Oakland", 1700000000)
        """
        content = {
            "type": resource_type,
            "quantity": quantity,
            "unit": unit,
            "location": location_hint,  # Coarse location only
            "expires_at": expiry_timestamp
        }

        self.publish_event(
            kind=VesselsEventKind.OFFER,
            content=content,
            tags=[
                ["t", "vessels"],
                ["t", "offer"],
                ["t", resource_type]
            ]
        )

    def publish_need(
        self,
        resource_type: str,
        quantity: float,
        unit: str,
        urgency: str = "normal"  # low, normal, high
    ):
        """
        Publish a resource need

        Example:
            publish_need("soil", 20.0, "kg", urgency="high")
        """
        content = {
            "type": resource_type,
            "quantity": quantity,
            "unit": unit,
            "urgency": urgency
        }

        self.publish_event(
            kind=VesselsEventKind.NEED,
            content=content,
            tags=[
                ["t", "vessels"],
                ["t", "need"],
                ["t", resource_type]
            ]
        )

    def publish_announcement(
        self,
        title: str,
        description: str,
        event_time: Optional[int] = None,
        tags_list: Optional[List[str]] = None
    ):
        """
        Publish a community announcement

        Example:
            publish_announcement(
                "Community Garden Workday",
                "Join us for planting and maintenance",
                event_time=1700000000,
                tags_list=["garden", "volunteer"]
            )
        """
        content = {
            "title": title,
            "description": description,
            "event_time": event_time
        }

        tags = [["t", "vessels"], ["t", "announcement"]]
        if tags_list:
            tags.extend([["t", tag] for tag in tags_list])

        self.publish_event(
            kind=VesselsEventKind.ANNOUNCEMENT,
            content=content,
            tags=tags
        )

    def subscribe_to_community_events(
        self,
        callback: Callable[[NostrEvent], None],
        trusted_pubkeys: Optional[List[str]] = None
    ) -> str:
        """
        Subscribe to Vessels community events

        Args:
            callback: Function to call for each event
            trusted_pubkeys: Only receive events from these pubkeys (optional)

        Returns:
            Subscription ID
        """
        filters = [
            {
                "kinds": [
                    int(VesselsEventKind.OFFER),
                    int(VesselsEventKind.NEED),
                    int(VesselsEventKind.ANNOUNCEMENT)
                ],
                "#t": ["vessels"]
            }
        ]

        # Optionally filter by trusted authors
        if trusted_pubkeys:
            filters[0]["authors"] = trusted_pubkeys

        return self.subscribe(filters, callback)


def create_nostr_adapter(config: Dict[str, Any]) -> NostrAdapter:
    """
    Factory function to create Nostr adapter from config

    Args:
        config: {
            "enabled": bool,
            "keypair": {"public": str, "private": str},  # Or generate new
            "relays": List[str],
            "publish_types": List[str]
        }

    Returns:
        Configured NostrAdapter instance
    """
    # Get or generate keypair
    if "keypair" in config:
        keypair = NostrKeypair(
            public_key=config["keypair"]["public"],
            private_key=config["keypair"]["private"]
        )
    else:
        logger.info("Generating new Nostr keypair")
        keypair = NostrKeypair.generate()
        logger.info(f"New pubkey: {keypair.public_key}")

    adapter = NostrAdapter(
        keypair=keypair,
        relays=config.get("relays", []),
        enabled=config.get("enabled", False),
        publish_types=config.get("publish_types", [])
    )

    return adapter
