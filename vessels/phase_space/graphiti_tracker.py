"""
Graphiti-backed Trajectory Tracker

Stores phase space states and trajectories in FalkorDB knowledge graph
alongside memory and coordination data.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..knowledge.graphiti_client import VesselsGraphitiClient
from ..knowledge.schema import NodeType, RelationType, PropertyName
from ..measurement.state import PhaseSpaceState
from ..gating.events import SecurityEvent, StateTransition

logger = logging.getLogger(__name__)


class GraphitiPhaseSpaceTracker:
    """
    Graphiti-backed storage for agent phase space trajectories.

    Stores 12D states in the knowledge graph to enable:
    - Temporal queries for state evolution
    - Pattern discovery across agents
    - Integration with memory and coordination
    - Cross-servant attractor detection
    """

    def __init__(
        self,
        graphiti_client: VesselsGraphitiClient,
        enable_attractor_storage: bool = True
    ):
        """
        Initialize Graphiti phase space tracker.

        Args:
            graphiti_client: VesselsGraphitiClient instance
            enable_attractor_storage: Store discovered attractors in graph
        """
        self.graphiti = graphiti_client
        self.enable_attractor_storage = enable_attractor_storage
        logger.info(
            f"Initialized GraphitiPhaseSpaceTracker for community: "
            f"{graphiti_client.community_id}"
        )

    def store_state(self, state: PhaseSpaceState):
        """
        Store a phase space state in the graph.

        Args:
            state: PhaseSpaceState to store
        """
        try:
            # Prepare node properties
            properties = {
                PropertyName.NAME: f"state_{state.agent_id}_{state.timestamp.isoformat()}",
                PropertyName.COMMUNITY_ID: self.graphiti.community_id,
                PropertyName.CREATED_AT: state.timestamp.isoformat(),
                "agent_id": state.agent_id,
                # Operational dimensions
                "activity": state.operational.activity,
                "coordination": state.operational.coordination,
                "effectiveness": state.operational.effectiveness,
                "resource_consumption": state.operational.resource_consumption,
                "system_health": state.operational.system_health,
                # Virtue dimensions
                "truthfulness": state.virtue.truthfulness,
                "justice": state.virtue.justice,
                "trustworthiness": state.virtue.trustworthiness,
                "unity": state.virtue.unity,
                "service": state.virtue.service,
                "detachment": state.virtue.detachment,
                "understanding": state.virtue.understanding,
            }

            # Add confidence if available
            if hasattr(state, 'confidence') and state.confidence:
                for dim, conf in state.confidence.items():
                    properties[f"confidence_{dim}"] = conf

            # Create node
            node_id = self.graphiti.create_node(
                node_type=NodeType.AGENT_STATE,
                properties=properties,
                node_id=f"state_{state.agent_id}_{int(state.timestamp.timestamp())}"
            )

            # Link to servant/agent node
            # First try to find or create the servant node
            servant_node_id = self._ensure_servant_node(state.agent_id)
            if servant_node_id:
                self.graphiti.create_relationship(
                    source_id=servant_node_id,
                    rel_type=RelationType.HAS_STATE,
                    target_id=node_id,
                    properties={"timestamp": state.timestamp.isoformat()}
                )

            logger.debug(f"Stored phase space state for agent {state.agent_id}")

        except Exception as e:
            logger.error(f"Error storing phase space state in Graphiti: {e}")
            raise

    def store_transition(self, transition: StateTransition):
        """
        Store a state transition.

        Args:
            transition: StateTransition to store
        """
        try:
            # Store as an event node
            properties = {
                PropertyName.NAME: f"transition_{transition.agent_id}_{transition.timestamp.isoformat()}",
                PropertyName.COMMUNITY_ID: self.graphiti.community_id,
                PropertyName.CREATED_AT: transition.timestamp.isoformat(),
                PropertyName.TYPE: "state_transition",
                "agent_id": transition.agent_id,
                "action_hash": transition.action_hash,
                "gating_result": transition.gating_result,
                "from_state": str(transition.from_state) if transition.from_state else None,
                "to_state": str(transition.to_state),
                "action_metadata": str(transition.action_metadata),
            }

            node_id = self.graphiti.create_node(
                node_type=NodeType.EVENT,
                properties=properties
            )

            logger.debug(f"Stored state transition for agent {transition.agent_id}")

        except Exception as e:
            logger.error(f"Error storing state transition: {e}")
            # Don't raise - transitions are supplementary

    def store_security_event(self, event: SecurityEvent):
        """
        Store a security event.

        Args:
            event: SecurityEvent to store
        """
        try:
            properties = {
                PropertyName.NAME: f"security_event_{event.agent_id}_{event.timestamp.isoformat()}",
                PropertyName.COMMUNITY_ID: self.graphiti.community_id,
                PropertyName.CREATED_AT: event.timestamp.isoformat(),
                PropertyName.TYPE: event.event_type,
                "agent_id": event.agent_id,
                "violations": str(event.violations),
                "blocked": event.blocked,
                "original_virtue_state": str(event.original_virtue_state),
                "corrected_virtue_state": str(event.corrected_virtue_state) if event.corrected_virtue_state else None,
                "residual_violations": str(event.residual_violations),
                "action_hash": event.action_hash,
            }

            node_id = self.graphiti.create_node(
                node_type=NodeType.EVENT,
                properties=properties
            )

            logger.debug(f"Stored security event for agent {event.agent_id}")

        except Exception as e:
            logger.error(f"Error storing security event: {e}")
            # Don't raise - events are supplementary

    def store_attractor(
        self,
        center: List[float],
        radius: float,
        classification: str,
        agent_count: int,
        outcomes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store a discovered attractor in the graph.

        Args:
            center: 12D center point
            radius: Attractor radius
            classification: Classification (desirable, undesirable, neutral)
            agent_count: Number of agents in this attractor
            outcomes: Optional outcome metrics
            metadata: Optional metadata

        Returns:
            Attractor node ID if successful
        """
        if not self.enable_attractor_storage:
            return None

        try:
            properties = {
                PropertyName.NAME: f"attractor_{classification}_{int(datetime.utcnow().timestamp())}",
                PropertyName.COMMUNITY_ID: self.graphiti.community_id,
                PropertyName.CREATED_AT: datetime.utcnow().isoformat(),
                PropertyName.TYPE: "attractor",
                PropertyName.DESCRIPTION: f"{classification} attractor with {agent_count} agents",
                "classification": classification,
                "radius": radius,
                "agent_count": agent_count,
                # Store center as individual dimensions
                "center_activity": center[0] if len(center) > 0 else 0.0,
                "center_coordination": center[1] if len(center) > 1 else 0.0,
                "center_effectiveness": center[2] if len(center) > 2 else 0.0,
                "center_resource_consumption": center[3] if len(center) > 3 else 0.0,
                "center_system_health": center[4] if len(center) > 4 else 0.0,
                "center_truthfulness": center[5] if len(center) > 5 else 0.0,
                "center_justice": center[6] if len(center) > 6 else 0.0,
                "center_trustworthiness": center[7] if len(center) > 7 else 0.0,
                "center_unity": center[8] if len(center) > 8 else 0.0,
                "center_service": center[9] if len(center) > 9 else 0.0,
                "center_detachment": center[10] if len(center) > 10 else 0.0,
                "center_understanding": center[11] if len(center) > 11 else 0.0,
                "outcomes": str(outcomes) if outcomes else None,
                "metadata": str(metadata) if metadata else None,
            }

            node_id = self.graphiti.create_node(
                node_type=NodeType.PATTERN,
                properties=properties
            )

            logger.info(f"Stored attractor: {classification} with {agent_count} agents")
            return node_id

        except Exception as e:
            logger.error(f"Error storing attractor: {e}")
            return None

    def get_trajectory(
        self,
        agent_id: str,
        limit: Optional[int] = None,
        lookback_days: int = 7
    ) -> List[PhaseSpaceState]:
        """
        Retrieve trajectory for an agent from the graph.

        Args:
            agent_id: Agent ID
            limit: Maximum number of states (most recent)
            lookback_days: Days to look back

        Returns:
            List of PhaseSpaceState objects
        """
        try:
            lookback_date = datetime.utcnow() - timedelta(days=lookback_days)

            cypher = """
            MATCH (s:Servant {id: $agent_id})-[:HAS_STATE]->(state:AgentState)
            WHERE state.created_at > $lookback_date
            RETURN state
            ORDER BY state.created_at DESC
            """

            if limit:
                cypher += f" LIMIT {limit}"

            results = self.graphiti.query(
                cypher,
                agent_id=agent_id,
                lookback_date=lookback_date.isoformat()
            )

            states = []
            for record in results:
                state_data = record.get("state", {})
                try:
                    state = self._result_to_phase_state(state_data)
                    states.append(state)
                except Exception as e:
                    logger.warning(f"Could not convert state: {e}")
                    continue

            # Return in chronological order
            return list(reversed(states))

        except Exception as e:
            logger.error(f"Error retrieving trajectory: {e}")
            return []

    def get_attractors(self, classification: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get discovered attractors from the graph.

        Args:
            classification: Filter by classification (desirable, undesirable, neutral)

        Returns:
            List of attractor dictionaries
        """
        try:
            where_clause = "WHERE p.type = 'attractor'"
            if classification:
                where_clause += f" AND p.classification = '{classification}'"

            cypher = f"""
            MATCH (p:Pattern)
            {where_clause}
            RETURN p
            ORDER BY p.created_at DESC
            """

            results = self.graphiti.query(cypher)

            attractors = []
            for record in results:
                pattern_data = record.get("p", {})
                if "properties" in pattern_data:
                    props = pattern_data["properties"]
                else:
                    props = pattern_data

                # Reconstruct center from individual dimensions
                center = [
                    props.get("center_activity", 0.0),
                    props.get("center_coordination", 0.0),
                    props.get("center_effectiveness", 0.0),
                    props.get("center_resource_consumption", 0.0),
                    props.get("center_system_health", 0.0),
                    props.get("center_truthfulness", 0.0),
                    props.get("center_justice", 0.0),
                    props.get("center_trustworthiness", 0.0),
                    props.get("center_unity", 0.0),
                    props.get("center_service", 0.0),
                    props.get("center_detachment", 0.0),
                    props.get("center_understanding", 0.0),
                ]

                attractors.append({
                    "id": props.get("id", ""),
                    "center": center,
                    "radius": props.get("radius", 0.0),
                    "classification": props.get("classification", "neutral"),
                    "agent_count": props.get("agent_count", 0),
                    "discovered_at": props.get("created_at", ""),
                    "outcomes": props.get("outcomes"),
                    "metadata": props.get("metadata"),
                })

            return attractors

        except Exception as e:
            logger.error(f"Error retrieving attractors: {e}")
            return []

    def _ensure_servant_node(self, agent_id: str) -> Optional[str]:
        """
        Ensure a servant node exists in the graph.

        Args:
            agent_id: Agent ID

        Returns:
            Servant node ID
        """
        try:
            # Try to find existing servant node
            cypher = """
            MATCH (s:Servant {id: $agent_id})
            RETURN s.id as id
            """

            results = self.graphiti.query(cypher, agent_id=agent_id)
            if results and len(results) > 0:
                return results[0].get("id", agent_id)

            # Create new servant node if not found
            properties = {
                PropertyName.NAME: agent_id,
                PropertyName.TYPE: "agent",
                PropertyName.STATUS: "active",
                PropertyName.COMMUNITY_ID: self.graphiti.community_id,
                PropertyName.CREATED_AT: datetime.utcnow().isoformat(),
            }

            return self.graphiti.create_node(
                node_type=NodeType.SERVANT,
                properties=properties,
                node_id=agent_id
            )

        except Exception as e:
            logger.warning(f"Could not ensure servant node: {e}")
            return None

    def _result_to_phase_state(self, state_data: Dict[str, Any]) -> PhaseSpaceState:
        """
        Convert graph query result to PhaseSpaceState.

        Args:
            state_data: Graph query result

        Returns:
            PhaseSpaceState object
        """
        from ..measurement.dimensions import OperationalDimensions, VirtueDimensions

        # Handle different result formats
        if "properties" in state_data:
            props = state_data["properties"]
        else:
            props = state_data

        # Extract timestamp
        timestamp_str = props.get(PropertyName.CREATED_AT, datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        # Create operational dimensions
        operational = OperationalDimensions(
            activity=float(props.get("activity", 0.0)),
            coordination=float(props.get("coordination", 0.0)),
            effectiveness=float(props.get("effectiveness", 0.0)),
            resource_consumption=float(props.get("resource_consumption", 0.0)),
            system_health=float(props.get("system_health", 0.0))
        )

        # Create virtue dimensions
        virtue = VirtueDimensions(
            truthfulness=float(props.get("truthfulness", 0.0)),
            justice=float(props.get("justice", 0.0)),
            trustworthiness=float(props.get("trustworthiness", 0.0)),
            unity=float(props.get("unity", 0.0)),
            service=float(props.get("service", 0.0)),
            detachment=float(props.get("detachment", 0.0)),
            understanding=float(props.get("understanding", 0.0))
        )

        # Create phase space state
        state = PhaseSpaceState(
            agent_id=props.get("agent_id", "unknown"),
            timestamp=timestamp,
            operational=operational,
            virtue=virtue
        )

        return state
