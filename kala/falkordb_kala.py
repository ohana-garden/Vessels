"""
FalkorDB Kala Contribution Network

Graph-native implementation of Kala contribution tracking with:
- Person-to-person contribution networks
- Community value flow analysis
- Reciprocity detection
- Contribution type categorization
- Time series value tracking
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ContributionType(Enum):
    """Types of contributions."""
    TIME = "time"                    # Volunteer time
    MATERIAL = "material"            # Physical goods
    SPACE = "space"                  # Location/facility use
    KNOWLEDGE = "knowledge"          # Teaching, expertise
    CARE = "care"                    # Caregiving services
    COORDINATION = "coordination"    # Organizing, planning
    FINANCIAL = "financial"          # Money donations
    ADVOCACY = "advocacy"            # Speaking up, representing


class FalkorDBKalaNetwork:
    """
    Graph-native Kala contribution network.

    Graph structure:
        (person1:Person) -[MADE_CONTRIBUTION {value, date}]-> (contribution:Contribution)
        (contribution) -[RECEIVED_BY]-> (person2:Person)
        (contribution) -[IN_COMMUNITY]-> (community:Community)
        (contribution) -[VALUED_AT {kala, usd}]-> (value:Value)
        (person:Person) -[HAS_ACCOUNT]-> (account:KalaAccount)
    """

    def __init__(self, falkor_client, graph_name: str = "vessels_kala"):
        """
        Initialize FalkorDB Kala network.

        Args:
            falkor_client: FalkorDBClient instance
            graph_name: Graph namespace for Kala data
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        logger.info(f"Using FalkorDB Kala Network with graph '{graph_name}'")

    def record_contribution(
        self,
        contribution_id: str,
        contributor_id: str,
        recipient_id: Optional[str],
        contribution_type: ContributionType,
        description: str,
        kala_value: float,
        usd_equivalent: float,
        community_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        verified: bool = False
    ) -> bool:
        """
        Record a contribution in the network.

        Args:
            contribution_id: Unique contribution identifier
            contributor_id: Person making the contribution
            recipient_id: Person receiving (None for community-level)
            contribution_type: Type of contribution
            description: Human-readable description
            kala_value: Value in Kala units
            usd_equivalent: Equivalent USD value
            community_id: Optional community context
            tags: Optional categorization tags
            metadata: Optional additional data
            verified: Whether contribution is verified

        Returns:
            True if successful
        """
        try:
            contribution_props = {
                "contribution_id": contribution_id,
                "type": contribution_type.value,
                "description": description,
                "timestamp": datetime.utcnow().isoformat(),
                "kala_value": kala_value,
                "usd_equivalent": usd_equivalent,
                "verified": verified,
                "metadata": json.dumps(metadata or {})
            }

            # Build query
            query_parts = []
            params = {
                "contribution_props": contribution_props,
                "contributor_id": contributor_id
            }

            # Core contribution creation
            query_parts.append("""
                MERGE (contributor:Person {person_id: $contributor_id})
                CREATE (contribution:Contribution $contribution_props)
                CREATE (contributor)-[:MADE_CONTRIBUTION {
                    timestamp: $timestamp,
                    value: $kala_value
                }]->(contribution)
            """)

            # Add recipient relationship if provided
            if recipient_id:
                query_parts.append("""
                    MERGE (recipient:Person {person_id: $recipient_id})
                    CREATE (contribution)-[:RECEIVED_BY]->(recipient)
                """)
                params["recipient_id"] = recipient_id

            # Add community relationship if provided
            if community_id:
                query_parts.append("""
                    MERGE (community:Community {community_id: $community_id})
                    CREATE (contribution)-[:IN_COMMUNITY]->(community)
                """)
                params["community_id"] = community_id

            # Add tags
            if tags:
                for i, tag in enumerate(tags):
                    query_parts.append(f"""
                        MERGE (tag{i}:Tag {{name: $tag{i}}})
                        CREATE (contribution)-[:TAGGED_WITH]->(tag{i})
                    """)
                    params[f"tag{i}"] = tag

            query_parts.append("RETURN contribution")

            query = "\n".join(query_parts)
            result = self.graph.query(query, params)

            logger.debug(f"Recorded contribution {contribution_id}: {kala_value} Kala from {contributor_id}")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record contribution {contribution_id}: {e}")
            return False

    def get_contribution_network(
        self,
        person_id: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get contribution network for a person.

        Finds all people connected through giving/receiving relationships.

        Args:
            person_id: Starting person ID
            max_depth: Maximum network depth

        Returns:
            List of connected people with relationship details
        """
        try:
            query = f"""
            MATCH path = (start:Person {{person_id: $person_id}})-[r:MADE_CONTRIBUTION|RECEIVED_BY*1..{max_depth}]-(connected:Person)
            WHERE connected.person_id <> $person_id
            WITH connected,
                 [rel IN relationships(path) | type(rel)] as relationship_path,
                 length(path) as distance
            RETURN DISTINCT connected.person_id as person_id,
                   relationship_path,
                   distance
            ORDER BY distance ASC
            """

            result = self.graph.query(query, {"person_id": person_id})

            if not result or not result.result_set:
                return []

            network = []
            for row in result.result_set:
                network.append({
                    "person_id": row[0],
                    "relationship_path": row[1],
                    "distance": row[2]
                })

            logger.debug(f"Found {len(network)} people in contribution network for {person_id}")
            return network

        except Exception as e:
            logger.error(f"Failed to get contribution network: {e}")
            return []

    def find_highly_connected_contributors(
        self,
        community_id: Optional[str] = None,
        min_connections: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find people who contribute to many others.

        Args:
            community_id: Optional community filter
            min_connections: Minimum unique recipients

        Returns:
            List of highly connected contributors
        """
        try:
            community_filter = ""
            params = {"min_connections": min_connections}

            if community_id:
                community_filter = """
                MATCH (c)-[:IN_COMMUNITY]->(comm:Community {community_id: $community_id})
                """
                params["community_id"] = community_id

            query = f"""
            MATCH (p:Person)-[:MADE_CONTRIBUTION]->(c:Contribution)-[:RECEIVED_BY]->(recipient:Person)
            {community_filter}
            WITH p, COUNT(DISTINCT recipient) as people_served,
                 SUM(c.kala_value) as total_kala
            WHERE people_served >= $min_connections
            RETURN p.person_id as person_id,
                   people_served,
                   total_kala
            ORDER BY people_served DESC, total_kala DESC
            """

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            contributors = []
            for row in result.result_set:
                contributors.append({
                    "person_id": row[0],
                    "people_served": row[1],
                    "total_kala": row[2]
                })

            logger.info(f"Found {len(contributors)} highly connected contributors")
            return contributors

        except Exception as e:
            logger.error(f"Failed to find highly connected contributors: {e}")
            return []

    def analyze_reciprocity(
        self,
        person1_id: str,
        person2_id: str
    ) -> Dict[str, Any]:
        """
        Analyze reciprocity between two people.

        Calculates total value exchanged in both directions.

        Args:
            person1_id: First person ID
            person2_id: Second person ID

        Returns:
            Dictionary with reciprocity analysis
        """
        try:
            query = """
            // Person1 to Person2
            MATCH (p1:Person {person_id: $person1_id})-[:MADE_CONTRIBUTION]->(c1:Contribution)-[:RECEIVED_BY]->(p2:Person {person_id: $person2_id})
            WITH SUM(c1.kala_value) as p1_to_p2

            // Person2 to Person1
            MATCH (p2:Person {person_id: $person2_id})-[:MADE_CONTRIBUTION]->(c2:Contribution)-[:RECEIVED_BY]->(p1:Person {person_id: $person1_id})
            WITH p1_to_p2, SUM(c2.kala_value) as p2_to_p1

            RETURN p1_to_p2, p2_to_p1, p1_to_p2 + p2_to_p1 as total_exchange
            """

            params = {
                "person1_id": person1_id,
                "person2_id": person2_id
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return {
                    "person1_to_person2": 0.0,
                    "person2_to_person1": 0.0,
                    "total_exchange": 0.0,
                    "balance": 0.0
                }

            row = result.result_set[0]
            p1_to_p2 = row[0] or 0.0
            p2_to_p1 = row[1] or 0.0
            total = row[2] or 0.0

            return {
                "person1_to_person2": p1_to_p2,
                "person2_to_person1": p2_to_p1,
                "total_exchange": total,
                "balance": p1_to_p2 - p2_to_p1
            }

        except Exception as e:
            logger.error(f"Failed to analyze reciprocity: {e}")
            return {
                "person1_to_person2": 0.0,
                "person2_to_person1": 0.0,
                "total_exchange": 0.0,
                "balance": 0.0
            }

    def get_community_value_flow(
        self,
        community_id: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze value flow within a community.

        Args:
            community_id: Community identifier
            lookback_days: How far back to analyze

        Returns:
            Dictionary with value flow statistics
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            query = """
            MATCH (c:Contribution)-[:IN_COMMUNITY]->(comm:Community {community_id: $community_id})
            WHERE datetime(c.timestamp) > datetime($since)
            WITH c.type as contrib_type,
                 COUNT(c) as count,
                 SUM(c.kala_value) as total_kala,
                 SUM(c.usd_equivalent) as total_usd
            RETURN contrib_type, count, total_kala, total_usd
            ORDER BY total_kala DESC
            """

            params = {
                "community_id": community_id,
                "since": since.isoformat()
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return {"types": [], "total_kala": 0.0, "total_usd": 0.0}

            types = []
            total_kala = 0.0
            total_usd = 0.0

            for row in result.result_set:
                types.append({
                    "type": row[0],
                    "count": row[1],
                    "total_kala": row[2],
                    "total_usd": row[3]
                })
                total_kala += row[2]
                total_usd += row[3]

            return {
                "types": types,
                "total_kala": total_kala,
                "total_usd": total_usd,
                "period_days": lookback_days
            }

        except Exception as e:
            logger.error(f"Failed to get community value flow: {e}")
            return {"types": [], "total_kala": 0.0, "total_usd": 0.0}

    def get_contribution_timeline(
        self,
        person_id: Optional[str] = None,
        community_id: Optional[str] = None,
        contribution_type: Optional[ContributionType] = None,
        lookback_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get contribution timeline (velocity over time).

        Args:
            person_id: Optional filter by person
            community_id: Optional filter by community
            contribution_type: Optional filter by type
            lookback_days: How far back to analyze

        Returns:
            List of daily contribution summaries
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            # Build filters
            filters = ["WHERE datetime(c.timestamp) > datetime($since)"]
            params = {"since": since.isoformat()}

            if person_id:
                filters.append("AND (p.person_id = $person_id OR r.person_id = $person_id)")
                params["person_id"] = person_id

            if community_id:
                filters.append("AND comm.community_id = $community_id")
                params["community_id"] = community_id

            if contribution_type:
                filters.append("AND c.type = $contrib_type")
                params["contrib_type"] = contribution_type.value

            query = f"""
            MATCH (p:Person)-[:MADE_CONTRIBUTION]->(c:Contribution)
            OPTIONAL MATCH (c)-[:RECEIVED_BY]->(r:Person)
            OPTIONAL MATCH (c)-[:IN_COMMUNITY]->(comm:Community)
            {' '.join(filters)}
            WITH substring(c.timestamp, 0, 10) as day,
                 COUNT(c) as contributions,
                 SUM(c.kala_value) as total_kala
            RETURN day, contributions, total_kala
            ORDER BY day ASC
            """

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            timeline = []
            for row in result.result_set:
                timeline.append({
                    "date": row[0],
                    "contributions": row[1],
                    "total_kala": row[2]
                })

            logger.debug(f"Generated timeline with {len(timeline)} days")
            return timeline

        except Exception as e:
            logger.error(f"Failed to get contribution timeline: {e}")
            return []

    def get_person_balance(
        self,
        person_id: str
    ) -> Dict[str, float]:
        """
        Get person's Kala balance (given vs received).

        Args:
            person_id: Person identifier

        Returns:
            Dictionary with balance information
        """
        try:
            query = """
            // Calculate given
            MATCH (p:Person {person_id: $person_id})-[:MADE_CONTRIBUTION]->(c1:Contribution)
            WITH SUM(c1.kala_value) as given

            // Calculate received
            MATCH (c2:Contribution)-[:RECEIVED_BY]->(p:Person {person_id: $person_id})
            WITH given, SUM(c2.kala_value) as received

            RETURN given, received, given - received as balance
            """

            result = self.graph.query(query, {"person_id": person_id})

            if not result or not result.result_set:
                return {"given": 0.0, "received": 0.0, "balance": 0.0}

            row = result.result_set[0]
            return {
                "given": row[0] or 0.0,
                "received": row[1] or 0.0,
                "balance": row[2] or 0.0
            }

        except Exception as e:
            logger.error(f"Failed to get person balance: {e}")
            return {"given": 0.0, "received": 0.0, "balance": 0.0}

    def find_contribution_patterns(
        self,
        community_id: str,
        min_occurrences: int = 3,
        lookback_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Find recurring contribution patterns.

        Identifies sequences like "time contribution → material contribution".

        Args:
            community_id: Community identifier
            min_occurrences: Minimum pattern occurrences
            lookback_days: How far back to analyze

        Returns:
            List of discovered patterns
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            query = """
            MATCH (c1:Contribution)-[:IN_COMMUNITY]->(comm:Community {community_id: $community_id})
            MATCH (c2:Contribution)-[:IN_COMMUNITY]->(comm)
            WHERE datetime(c1.timestamp) > datetime($since)
            AND datetime(c2.timestamp) > datetime(c1.timestamp)
            AND datetime(c2.timestamp) < datetime(c1.timestamp) + duration({days: 7})
            WITH c1.type as first_type, c2.type as second_type, COUNT(*) as occurrences
            WHERE occurrences >= $min_count
            RETURN first_type, second_type, occurrences
            ORDER BY occurrences DESC
            """

            params = {
                "community_id": community_id,
                "since": since.isoformat(),
                "min_count": min_occurrences
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            patterns = []
            for row in result.result_set:
                patterns.append({
                    "first_type": row[0],
                    "second_type": row[1],
                    "occurrences": row[2]
                })

            logger.info(f"Found {len(patterns)} contribution patterns")
            return patterns

        except Exception as e:
            logger.error(f"Failed to find contribution patterns: {e}")
            return []
