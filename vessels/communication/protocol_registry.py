"""
Protocol Registry for Vessels Communication

Manages multiple communication protocols (Nostr, local RPC, future additions).
Provides unified interface for publishing and subscribing to events.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class Protocol(Enum):
    """Supported communication protocols"""
    LOCAL_RPC = "local_rpc"
    NOSTR = "nostr"
    # Future: IPFS, Matrix, ActivityPub, etc.


class ProtocolRegistry:
    """
    Central registry for all communication protocols

    Allows agents to publish/subscribe without knowing which protocols
    are active. Handles routing and protocol-specific adaptations.
    """

    def __init__(self):
        self.protocols: Dict[Protocol, Any] = {}
        self.enabled_protocols: Set[Protocol] = set()
        self.event_log = []  # For debugging

    def register(self, protocol: Protocol, adapter: Any):
        """
        Register a protocol adapter

        Args:
            protocol: Protocol type
            adapter: Adapter instance (NostrAdapter, etc.)
        """
        self.protocols[protocol] = adapter
        if getattr(adapter, "enabled", False):
            self.enabled_protocols.add(protocol)
            logger.info(f"Registered and enabled protocol: {protocol.value}")
        else:
            logger.info(f"Registered protocol {protocol.value} (DISABLED)")

    def unregister(self, protocol: Protocol):
        """Remove a protocol from the registry"""
        if protocol in self.protocols:
            del self.protocols[protocol]
            self.enabled_protocols.discard(protocol)
            logger.info(f"Unregistered protocol: {protocol.value}")

    def publish(
        self,
        event_type: str,
        content: Dict[str, Any],
        protocols: Optional[List[Protocol]] = None,
        **kwargs
    ):
        """
        Publish event to one or more protocols

        Args:
            event_type: Type of event (e.g., "offer", "need", "status")
            content: Event content
            protocols: List of protocols to use (None = all enabled)
            **kwargs: Protocol-specific arguments
        """
        target_protocols = protocols or list(self.enabled_protocols)

        results = {}
        for protocol in target_protocols:
            if protocol not in self.enabled_protocols:
                logger.debug(f"Protocol {protocol.value} not enabled, skipping")
                continue

            adapter = self.protocols.get(protocol)
            if not adapter:
                logger.warning(f"Protocol {protocol.value} not registered")
                continue

            try:
                if protocol == Protocol.NOSTR:
                    result = self._publish_nostr(adapter, event_type, content, kwargs)
                elif protocol == Protocol.LOCAL_RPC:
                    result = self._publish_local_rpc(adapter, event_type, content, kwargs)
                else:
                    logger.warning(f"Unknown protocol: {protocol}")
                    continue

                results[protocol] = result
                self.event_log.append({
                    "protocol": protocol.value,
                    "event_type": event_type,
                    "success": True
                })

            except Exception as e:
                logger.error(f"Failed to publish to {protocol.value}: {e}")
                results[protocol] = {"error": str(e)}
                self.event_log.append({
                    "protocol": protocol.value,
                    "event_type": event_type,
                    "success": False,
                    "error": str(e)
                })

        return results

    def _publish_nostr(self, adapter, event_type: str, content: Dict[str, Any], kwargs: Dict):
        """Publish to Nostr protocol"""
        from .nostr_adapter import VesselsEventKind

        # Map event type to Nostr kind
        kind_map = {
            "status": VesselsEventKind.NODE_STATUS,
            "offer": VesselsEventKind.OFFER,
            "need": VesselsEventKind.NEED,
            "metric": VesselsEventKind.COMMUNITY_METRIC,
            "announcement": VesselsEventKind.ANNOUNCEMENT,
            "coordination": VesselsEventKind.COORDINATION,
            "discovery": VesselsEventKind.DISCOVERY
        }

        kind = kind_map.get(event_type)
        if not kind:
            logger.warning(f"Unknown event type for Nostr: {event_type}")
            return None

        return adapter.publish_event(
            kind=kind,
            content=content,
            tags=kwargs.get("tags"),
            sanitized=kwargs.get("sanitized", False)
        )

    def _publish_local_rpc(self, adapter, event_type: str, content: Dict[str, Any], kwargs: Dict):
        """Publish to local RPC (Tier 0 → Tier 1)"""
        # Local RPC doesn't need sanitization (trusted network)
        return adapter.send_event(event_type, content)

    def subscribe(
        self,
        event_types: List[str],
        callback: Callable[[Dict[str, Any]], None],
        protocols: Optional[List[Protocol]] = None,
        **kwargs
    ) -> Dict[Protocol, str]:
        """
        Subscribe to events across protocols

        Args:
            event_types: Types of events to subscribe to
            callback: Function to call for each event
            protocols: List of protocols to subscribe on (None = all enabled)
            **kwargs: Protocol-specific arguments

        Returns:
            Dict mapping Protocol → subscription_id
        """
        target_protocols = protocols or list(self.enabled_protocols)

        subscriptions = {}
        for protocol in target_protocols:
            if protocol not in self.enabled_protocols:
                continue

            adapter = self.protocols.get(protocol)
            if not adapter:
                continue

            try:
                if protocol == Protocol.NOSTR:
                    sub_id = self._subscribe_nostr(adapter, event_types, callback, kwargs)
                elif protocol == Protocol.LOCAL_RPC:
                    sub_id = self._subscribe_local_rpc(adapter, event_types, callback, kwargs)
                else:
                    continue

                subscriptions[protocol] = sub_id
                logger.info(f"Subscribed to {protocol.value}: {sub_id}")

            except Exception as e:
                logger.error(f"Failed to subscribe on {protocol.value}: {e}")

        return subscriptions

    def _subscribe_nostr(self, adapter, event_types: List[str], callback: Callable, kwargs: Dict) -> str:
        """Subscribe to Nostr events"""
        from .nostr_adapter import VesselsEventKind

        # Map event types to Nostr kinds
        kind_map = {
            "status": VesselsEventKind.NODE_STATUS,
            "offer": VesselsEventKind.OFFER,
            "need": VesselsEventKind.NEED,
            "metric": VesselsEventKind.COMMUNITY_METRIC,
            "announcement": VesselsEventKind.ANNOUNCEMENT,
            "coordination": VesselsEventKind.COORDINATION,
            "discovery": VesselsEventKind.DISCOVERY
        }

        kinds = [int(kind_map[et]) for et in event_types if et in kind_map]

        filters = [{"kinds": kinds, "#t": ["vessels"]}]

        # Add trusted authors if specified
        if "trusted_pubkeys" in kwargs:
            filters[0]["authors"] = kwargs["trusted_pubkeys"]

        return adapter.subscribe(filters, callback)

    def _subscribe_local_rpc(self, adapter, event_types: List[str], callback: Callable, kwargs: Dict) -> str:
        """Subscribe to local RPC events"""
        return adapter.subscribe_events(event_types, callback)

    def unsubscribe(self, protocol: Protocol, subscription_id: str):
        """Cancel a subscription"""
        adapter = self.protocols.get(protocol)
        if adapter:
            if protocol == Protocol.NOSTR:
                adapter.unsubscribe(subscription_id)
            elif protocol == Protocol.LOCAL_RPC:
                adapter.unsubscribe(subscription_id)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all protocols"""
        status = {
            "enabled_protocols": [p.value for p in self.enabled_protocols],
            "registered_protocols": [p.value for p in self.protocols.keys()],
            "event_count": len(self.event_log),
            "protocols": {}
        }

        for protocol, adapter in self.protocols.items():
            status["protocols"][protocol.value] = {
                "enabled": protocol in self.enabled_protocols,
                "type": type(adapter).__name__
            }

        return status


def create_protocol_registry(config: Dict[str, Any]) -> ProtocolRegistry:
    """
    Factory function to create and configure protocol registry

    Args:
        config: {
            "local_rpc": {
                "enabled": bool,
                "host": str,
                "port": int
            },
            "nostr": {
                "enabled": bool,
                "relays": List[str],
                "publish_types": List[str]
            }
        }

    Returns:
        Configured ProtocolRegistry
    """
    registry = ProtocolRegistry()

    # Register Local RPC
    if config.get("local_rpc", {}).get("enabled", True):
        # TODO: Implement LocalRPCAdapter
        logger.info("Local RPC enabled (adapter not yet implemented)")

    # Register Nostr
    if config.get("nostr", {}).get("enabled", False):
        from .nostr_adapter import create_nostr_adapter
        nostr_adapter = create_nostr_adapter(config["nostr"])
        registry.register(Protocol.NOSTR, nostr_adapter)

    logger.info(f"Protocol registry initialized: {registry.get_status()}")
    return registry


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = {
        "local_rpc": {
            "enabled": True,
            "host": "localhost",
            "port": 8080
        },
        "nostr": {
            "enabled": True,
            "relays": ["wss://relay.damus.io"],
            "publish_types": ["offer", "need"]
        }
    }

    registry = create_protocol_registry(config)

    # Publish an offer
    registry.publish(
        event_type="offer",
        content={
            "type": "tomatoes",
            "quantity": 5.0,
            "unit": "kg"
        }
    )

    # Check status
    print(registry.get_status())
