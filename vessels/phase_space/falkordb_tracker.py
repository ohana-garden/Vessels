"""
FalkorDB Phase Space Trajectory Tracker

Graph-native implementation of agent state tracking with:
- 12D phase space state nodes
- State transition relationships
- Constraint violation tracking
- Attractor discovery and persistence
- Behavioral pattern analysis
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import asdict

from vessels.measurement.state import PhaseSpaceState
from vessels.gating.events import SecurityEvent, StateTransition

logger = logging.getLogger(__name__)


class FalkorDBPhaseSpaceTracker:
    """
    Graph-native phase space trajectory tracker.

    Graph structure:
        (agent:Servant) -[HAS_STATE {timestamp}]-> (state:AgentState {12D vector})
        (state1:AgentState) -[TRANSITIONS_TO {action_hash, gating_result}]-> (state2:AgentState)
        (state:AgentState) -[VIOLATED {timestamp}]-> (constraint:Constraint)
        (event:SecurityEvent) -[LOGGED_FOR]-> (state:AgentState)
        (state:AgentState) -[IN_ATTRACTOR {distance}]-> (attractor:Attractor)
    """

    def __init__(self, falkor_client, graph_name: str = "vessels_phase_space"):
        """
        Initialize FalkorDB phase space tracker.

        Args:
            falkor_client: FalkorDBClient instance
            graph_name: Graph namespace for phase space data
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        logger.info(f"Using FalkorDB Phase Space Tracker with graph '{graph_name}'")

    def record_state(
        self,
        agent_id: str,
        state: PhaseSpaceState,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a new phase space state for an agent.

        Args:
            agent_id: Agent identifier
            state: 12D phase space state
            metadata: Optional additional metadata

        Returns:
            True if successful
        """
        try:
            # Extract operational and virtue components
            op_state = state.operational
            virtue_state = state.virtue

            state_props = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": agent_id,
                # Operational (5D)
                "activity_level": op_state.activity_level,
                "coordination_density": op_state.coordination_density,
                "effectiveness": op_state.effectiveness,
                "resource_consumption": op_state.resource_consumption,
                "system_health": op_state.system_health,
                # Virtue (7D)
                "truthfulness": virtue_state.truthfulness,
                "justice": virtue_state.justice,
                "trustworthiness": virtue_state.trustworthiness,
                "unity": virtue_state.unity,
                "service": virtue_state.service,
                "detachment": virtue_state.detachment,
                "understanding": virtue_state.understanding,
                # Metadata
                "metadata": json.dumps(metadata or {})
            }

            query = """
            MERGE (agent:Servant {agent_id: $agent_id})
            CREATE (state:AgentState $state_props)
            CREATE (agent)-[:HAS_STATE {recorded_at: $timestamp}]->(state)
            RETURN state
            """

            params = {
                "agent_id": agent_id,
                "state_props": state_props,
                "timestamp": state_props["timestamp"]
            }

            result = self.graph.query(query, params)
            logger.debug(f"Recorded state for agent {agent_id}")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record state for agent {agent_id}: {e}")
            return False

    def record_transition(
        self,
        agent_id: str,
        from_state: PhaseSpaceState,
        to_state: PhaseSpaceState,
        action_hash: str,
        gating_result: str,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a state transition.

        Creates transition relationship between two consecutive states.

        Args:
            agent_id: Agent identifier
            from_state: Starting state
            to_state: Ending state
            action_hash: Content hash of the action
            gating_result: "allowed", "blocked", "corrected"
            action_metadata: Optional action metadata

        Returns:
            True if successful
        """
        try:
            # First, record both states
            self.record_state(agent_id, from_state, {"role": "from"})
            self.record_state(agent_id, to_state, {"role": "to"})

            # Create transition relationship
            transition_props = {
                "action_hash": action_hash,
                "gating_result": gating_result,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": json.dumps(action_metadata or {})
            }

            query = """
            MATCH (agent:Servant {agent_id: $agent_id})-[:HAS_STATE]->(from:AgentState)
            MATCH (agent)-[:HAS_STATE]->(to:AgentState)
            WHERE from.metadata CONTAINS '"role": "from"'
            AND to.metadata CONTAINS '"role": "to"'
            AND datetime(from.timestamp) < datetime(to.timestamp)
            WITH from, to
            ORDER BY datetime(from.timestamp) DESC, datetime(to.timestamp) DESC
            LIMIT 1
            CREATE (from)-[t:TRANSITIONS_TO $transition_props]->(to)
            RETURN t
            """

            params = {
                "agent_id": agent_id,
                "transition_props": transition_props
            }

            result = self.graph.query(query, params)
            logger.debug(f"Recorded transition for agent {agent_id}: {gating_result}")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record transition for agent {agent_id}: {e}")
            return False

    def record_constraint_violation(
        self,
        agent_id: str,
        state: PhaseSpaceState,
        violated_constraints: List[str],
        event_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record constraint violations for a state.

        Creates relationships between state and violated constraints.

        Args:
            agent_id: Agent identifier
            state: Phase space state at violation
            violated_constraints: List of constraint names
            event_data: Optional event metadata

        Returns:
            True if successful
        """
        try:
            # Record the state
            self.record_state(agent_id, state, {"has_violations": True})

            # Create constraint nodes and violation relationships
            for constraint_name in violated_constraints:
                query = """
                MATCH (agent:Servant {agent_id: $agent_id})-[:HAS_STATE]->(state:AgentState)
                WHERE state.metadata CONTAINS '"has_violations": true'
                WITH state
                ORDER BY datetime(state.timestamp) DESC
                LIMIT 1
                MERGE (c:Constraint {name: $constraint_name})
                CREATE (state)-[:VIOLATED {
                    timestamp: $timestamp,
                    event_data: $event_data
                }]->(c)
                RETURN state, c
                """

                params = {
                    "agent_id": agent_id,
                    "constraint_name": constraint_name,
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_data": json.dumps(event_data or {})
                }

                self.graph.query(query, params)

            logger.debug(f"Recorded {len(violated_constraints)} constraint violations for agent {agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record constraint violations for agent {agent_id}: {e}")
            return False

    def record_security_event(
        self,
        event: SecurityEvent
    ) -> bool:
        """
        Record a security event (constraint violation, timeout, projection failure).

        Args:
            event: SecurityEvent object

        Returns:
            True if successful
        """
        try:
            event_props = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "blocked": event.blocked,
                "action_hash": event.action_hash,
                "violations": json.dumps(event.violations),
                "original_virtue_state": json.dumps(event.original_virtue_state),
                "corrected_virtue_state": json.dumps(event.corrected_virtue_state) if event.corrected_virtue_state else None,
                "residual_violations": json.dumps(event.residual_violations),
                "operational_state_snapshot": json.dumps(event.operational_state_snapshot),
                "metadata": json.dumps(event.metadata)
            }

            query = """
            MERGE (agent:Servant {agent_id: $agent_id})
            CREATE (event:SecurityEvent $event_props)
            CREATE (event)-[:LOGGED_FOR {timestamp: $timestamp}]->(agent)
            RETURN event
            """

            params = {
                "agent_id": event.agent_id,
                "event_props": event_props,
                "timestamp": event_props["timestamp"]
            }

            result = self.graph.query(query, params)
            logger.debug(f"Recorded security event for agent {event.agent_id}: {event.event_type}")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record security event: {e}")
            return False

    def get_agent_trajectory(
        self,
        agent_id: str,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PhaseSpaceState]:
        """
        Get agent's state trajectory.

        Args:
            agent_id: Agent identifier
            since: Optional start time (default: last 24 hours)
            limit: Maximum number of states to return

        Returns:
            List of PhaseSpaceState objects, ordered by time
        """
        try:
            if since is None:
                since = datetime.utcnow() - timedelta(days=1)

            query = """
            MATCH (agent:Servant {agent_id: $agent_id})-[:HAS_STATE]->(state:AgentState)
            WHERE datetime(state.timestamp) > datetime($since)
            RETURN state
            ORDER BY datetime(state.timestamp) ASC
            LIMIT $limit
            """

            params = {
                "agent_id": agent_id,
                "since": since.isoformat(),
                "limit": limit
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            # Convert graph nodes to PhaseSpaceState objects
            states = []
            for row in result.result_set:
                state_node = row[0]
                # TODO: Reconstruct PhaseSpaceState from node properties
                # For now, log the raw data
                logger.debug(f"Retrieved state: {state_node}")

            return states

        except Exception as e:
            logger.error(f"Failed to get trajectory for agent {agent_id}: {e}")
            return []

    def find_constraint_violation_patterns(
        self,
        lookback_days: int = 30,
        min_co_occurrences: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find frequently co-occurring constraint violations.

        Identifies which constraints tend to be violated together,
        which can reveal systemic issues in agent behavior or
        constraint coupling.

        Args:
            lookback_days: How far back to analyze
            min_co_occurrences: Minimum co-occurrence count

        Returns:
            List of constraint pairs with co-occurrence counts
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            query = """
            MATCH (state:AgentState)-[v1:VIOLATED]->(c1:Constraint)
            MATCH (state)-[v2:VIOLATED]->(c2:Constraint)
            WHERE datetime(v1.timestamp) > datetime($since)
            AND c1.name < c2.name
            WITH c1, c2, COUNT(state) as co_violations
            WHERE co_violations >= $min_count
            RETURN c1.name as constraint1,
                   c2.name as constraint2,
                   co_violations
            ORDER BY co_violations DESC
            """

            params = {
                "since": since.isoformat(),
                "min_count": min_co_occurrences
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            patterns = []
            for row in result.result_set:
                patterns.append({
                    "constraint1": row[0],
                    "constraint2": row[1],
                    "co_violations": row[2]
                })

            logger.info(f"Found {len(patterns)} constraint violation patterns")
            return patterns

        except Exception as e:
            logger.error(f"Failed to find constraint violation patterns: {e}")
            return []

    def find_frequent_violators(
        self,
        constraint_name: Optional[str] = None,
        lookback_days: int = 30,
        min_violations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find agents that frequently violate constraints.

        Args:
            constraint_name: Optional specific constraint (None = all)
            lookback_days: How far back to analyze
            min_violations: Minimum violation count

        Returns:
            List of agents with violation counts
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            if constraint_name:
                query = """
                MATCH (agent:Servant)-[:HAS_STATE]->(state:AgentState)-[v:VIOLATED]->(c:Constraint {name: $constraint_name})
                WHERE datetime(v.timestamp) > datetime($since)
                WITH agent, c, COUNT(v) as violation_count
                WHERE violation_count >= $min_count
                RETURN agent.agent_id as agent_id,
                       c.name as constraint,
                       violation_count
                ORDER BY violation_count DESC
                """
                params = {
                    "constraint_name": constraint_name,
                    "since": since.isoformat(),
                    "min_count": min_violations
                }
            else:
                query = """
                MATCH (agent:Servant)-[:HAS_STATE]->(state:AgentState)-[v:VIOLATED]->(c:Constraint)
                WHERE datetime(v.timestamp) > datetime($since)
                WITH agent, c, COUNT(v) as violation_count
                WHERE violation_count >= $min_count
                RETURN agent.agent_id as agent_id,
                       c.name as constraint,
                       violation_count
                ORDER BY violation_count DESC
                """
                params = {
                    "since": since.isoformat(),
                    "min_count": min_violations
                }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            violators = []
            for row in result.result_set:
                violators.append({
                    "agent_id": row[0],
                    "constraint": row[1],
                    "violation_count": row[2]
                })

            logger.info(f"Found {len(violators)} frequent violators")
            return violators

        except Exception as e:
            logger.error(f"Failed to find frequent violators: {e}")
            return []

    def record_attractor(
        self,
        attractor_id: str,
        center_state: PhaseSpaceState,
        radius: float,
        member_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record a discovered attractor in phase space.

        Args:
            attractor_id: Unique attractor identifier
            center_state: Center point of the attractor
            radius: Radius of the attractor basin
            member_count: Number of states in this attractor
            metadata: Optional metadata

        Returns:
            True if successful
        """
        try:
            attractor_props = {
                "attractor_id": attractor_id,
                "discovered_at": datetime.utcnow().isoformat(),
                "radius": radius,
                "member_count": member_count,
                # Store center state as 12D vector
                "center_operational": json.dumps({
                    "activity_level": center_state.operational.activity_level,
                    "coordination_density": center_state.operational.coordination_density,
                    "effectiveness": center_state.operational.effectiveness,
                    "resource_consumption": center_state.operational.resource_consumption,
                    "system_health": center_state.operational.system_health
                }),
                "center_virtue": json.dumps({
                    "truthfulness": center_state.virtue.truthfulness,
                    "justice": center_state.virtue.justice,
                    "trustworthiness": center_state.virtue.trustworthiness,
                    "unity": center_state.virtue.unity,
                    "service": center_state.virtue.service,
                    "detachment": center_state.virtue.detachment,
                    "understanding": center_state.virtue.understanding
                }),
                "metadata": json.dumps(metadata or {})
            }

            query = """
            MERGE (attractor:Attractor {attractor_id: $attractor_id})
            SET attractor = $attractor_props
            RETURN attractor
            """

            params = {
                "attractor_id": attractor_id,
                "attractor_props": attractor_props
            }

            result = self.graph.query(query, params)
            logger.info(f"Recorded attractor {attractor_id} with {member_count} members")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record attractor {attractor_id}: {e}")
            return False

    def link_state_to_attractor(
        self,
        agent_id: str,
        attractor_id: str,
        distance: float
    ) -> bool:
        """
        Link a state to an attractor.

        Args:
            agent_id: Agent identifier
            attractor_id: Attractor identifier
            distance: Distance from state to attractor center

        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (agent:Servant {agent_id: $agent_id})-[:HAS_STATE]->(state:AgentState)
            MATCH (attractor:Attractor {attractor_id: $attractor_id})
            WITH state, attractor
            ORDER BY datetime(state.timestamp) DESC
            LIMIT 1
            CREATE (state)-[:IN_ATTRACTOR {distance: $distance, linked_at: $timestamp}]->(attractor)
            RETURN state, attractor
            """

            params = {
                "agent_id": agent_id,
                "attractor_id": attractor_id,
                "distance": distance,
                "timestamp": datetime.utcnow().isoformat()
            }

            result = self.graph.query(query, params)
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to link state to attractor: {e}")
            return False
