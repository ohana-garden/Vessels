"""
FalkorDB Grants Discovery and Matching

Graph-native implementation of grant matching with:
- Semantic grant-person matching based on capabilities
- Application pipeline tracking
- Deadline management
- Funder relationship tracking
- Success rate analysis
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class ApplicationStatus(Enum):
    """Grant application status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FUNDED = "funded"


class FalkorDBGrantsDiscovery:
    """
    Graph-native grants discovery and matching system.

    Graph structure:
        (grant:Grant) -[MATCHES {score}]-> (person:Person)
        (grant) -[REQUIRES {mandatory}]-> (capability:Capability)
        (person) -[HAS {level}]-> (capability)
        (grant) -[OFFERED_BY]-> (funder:Organization)
        (application:Application) -[FOR]-> (grant)
        (application) -[SUBMITTED_BY]-> (person)
        (application) -[HAS_SECTION]-> (section:ApplicationSection)
    """

    def __init__(self, falkor_client, graph_name: str = "vessels_grants"):
        """
        Initialize FalkorDB grants discovery.

        Args:
            falkor_client: FalkorDBClient instance
            graph_name: Graph namespace for grants data
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        logger.info(f"Using FalkorDB Grants Discovery with graph '{graph_name}'")

    def register_grant(
        self,
        grant_id: str,
        title: str,
        description: str,
        funder: str,
        amount: float,
        deadline: datetime,
        required_capabilities: List[Dict[str, Any]],
        preferred_capabilities: Optional[List[Dict[str, Any]]] = None,
        eligibility_criteria: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a grant opportunity.

        Args:
            grant_id: Unique grant identifier
            title: Grant title
            description: Grant description
            funder: Funder organization name
            amount: Grant amount (USD)
            deadline: Application deadline
            required_capabilities: List of required capabilities
            preferred_capabilities: Optional preferred capabilities
            eligibility_criteria: Optional eligibility requirements
            metadata: Optional additional metadata

        Returns:
            True if successful
        """
        try:
            grant_props = {
                "grant_id": grant_id,
                "title": title,
                "description": description,
                "amount": amount,
                "deadline": deadline.isoformat(),
                "registered_at": datetime.utcnow().isoformat(),
                "status": "active",
                "eligibility_criteria": json.dumps(eligibility_criteria or {}),
                "metadata": json.dumps(metadata or {})
            }

            # Create grant and funder
            query = """
            CREATE (grant:Grant $grant_props)
            MERGE (funder:Organization {name: $funder})
            CREATE (grant)-[:OFFERED_BY]->(funder)
            RETURN grant
            """

            params = {
                "grant_props": grant_props,
                "funder": funder
            }

            self.graph.query(query, params)

            # Add required capabilities
            for cap in required_capabilities:
                cap_query = """
                MATCH (grant:Grant {grant_id: $grant_id})
                MERGE (capability:Capability {name: $cap_name})
                CREATE (grant)-[:REQUIRES {
                    mandatory: true,
                    level: $level,
                    description: $description
                }]->(capability)
                """

                cap_params = {
                    "grant_id": grant_id,
                    "cap_name": cap.get("name"),
                    "level": cap.get("level", "intermediate"),
                    "description": cap.get("description", "")
                }

                self.graph.query(cap_query, cap_params)

            # Add preferred capabilities
            if preferred_capabilities:
                for cap in preferred_capabilities:
                    cap_query = """
                    MATCH (grant:Grant {grant_id: $grant_id})
                    MERGE (capability:Capability {name: $cap_name})
                    CREATE (grant)-[:PREFERS {
                        mandatory: false,
                        level: $level,
                        description: $description
                    }]->(capability)
                    """

                    cap_params = {
                        "grant_id": grant_id,
                        "cap_name": cap.get("name"),
                        "level": cap.get("level", "intermediate"),
                        "description": cap.get("description", "")
                    }

                    self.graph.query(cap_query, cap_params)

            logger.debug(f"Registered grant {grant_id}: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to register grant {grant_id}: {e}")
            return False

    def register_person_capability(
        self,
        person_id: str,
        capability_name: str,
        level: str = "intermediate",
        evidence: Optional[str] = None
    ) -> bool:
        """
        Register a person's capability.

        Args:
            person_id: Person identifier
            capability_name: Capability name
            level: Skill level (beginner, intermediate, advanced, expert)
            evidence: Optional evidence/proof

        Returns:
            True if successful
        """
        try:
            query = """
            MERGE (person:Person {person_id: $person_id})
            MERGE (capability:Capability {name: $cap_name})
            MERGE (person)-[has:HAS {level: $level}]->(capability)
            ON CREATE SET has.registered_at = $timestamp,
                          has.evidence = $evidence
            ON MATCH SET has.level = $level,
                         has.evidence = $evidence,
                         has.updated_at = $timestamp
            RETURN person, capability
            """

            params = {
                "person_id": person_id,
                "cap_name": capability_name,
                "level": level,
                "evidence": evidence or "",
                "timestamp": datetime.utcnow().isoformat()
            }

            result = self.graph.query(query, params)
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to register capability for {person_id}: {e}")
            return False

    def find_matching_grants(
        self,
        person_id: str,
        include_past_deadline: bool = False,
        min_match_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find grants matching a person's capabilities.

        Args:
            person_id: Person identifier
            include_past_deadline: Include grants with past deadlines
            min_match_score: Minimum match score (0-1)

        Returns:
            List of matching grants with match scores
        """
        try:
            deadline_filter = "" if include_past_deadline else "AND datetime(grant.deadline) > datetime()"

            query = f"""
            MATCH (person:Person {{person_id: $person_id}})-[has:HAS]->(capability:Capability)
            MATCH (grant:Grant)-[requires:REQUIRES]->(capability)
            WHERE grant.status = 'active'
            {deadline_filter}
            WITH grant,
                 COUNT(DISTINCT capability) as matched_capabilities,
                 SUM(CASE WHEN requires.mandatory = true THEN 1 ELSE 0 END) as matched_required
            MATCH (grant)-[req:REQUIRES {{mandatory: true}}]->(required_cap:Capability)
            WITH grant,
                 matched_capabilities,
                 matched_required,
                 COUNT(DISTINCT required_cap) as total_required
            WHERE (total_required = 0 OR matched_required >= total_required)
            WITH grant,
                 (matched_capabilities * 1.0 / CASE WHEN total_required > 0 THEN total_required ELSE 1 END) as match_score
            WHERE match_score >= $min_score
            MATCH (grant)-[:OFFERED_BY]->(funder:Organization)
            RETURN grant.grant_id as grant_id,
                   grant.title as title,
                   grant.amount as amount,
                   grant.deadline as deadline,
                   funder.name as funder,
                   match_score
            ORDER BY match_score DESC, datetime(grant.deadline) ASC
            """

            result = self.graph.query(query, {
                "person_id": person_id,
                "min_score": min_match_score
            })

            if not result or not result.result_set:
                return []

            grants = []
            for row in result.result_set:
                grants.append({
                    "grant_id": row[0],
                    "title": row[1],
                    "amount": row[2],
                    "deadline": row[3],
                    "funder": row[4],
                    "match_score": row[5]
                })

            logger.debug(f"Found {len(grants)} matching grants for person {person_id}")
            return grants

        except Exception as e:
            logger.error(f"Failed to find matching grants: {e}")
            return []

    def create_application(
        self,
        application_id: str,
        grant_id: str,
        person_id: str,
        sections: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a grant application.

        Args:
            application_id: Unique application identifier
            grant_id: Grant being applied for
            person_id: Person applying
            sections: Application sections (list of {name, content, complete})
            metadata: Optional metadata

        Returns:
            True if successful
        """
        try:
            app_props = {
                "application_id": application_id,
                "status": ApplicationStatus.DRAFT.value,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": json.dumps(metadata or {})
            }

            # Create application
            query = """
            MATCH (grant:Grant {grant_id: $grant_id})
            MATCH (person:Person {person_id: $person_id})
            CREATE (app:Application $app_props)
            CREATE (app)-[:FOR]->(grant)
            CREATE (app)-[:SUBMITTED_BY]->(person)
            RETURN app
            """

            params = {
                "grant_id": grant_id,
                "person_id": person_id,
                "app_props": app_props
            }

            self.graph.query(query, params)

            # Add sections
            for section in sections:
                section_query = """
                MATCH (app:Application {application_id: $app_id})
                CREATE (section:ApplicationSection {
                    name: $name,
                    content: $content,
                    complete: $complete,
                    created_at: $timestamp
                })
                CREATE (app)-[:HAS_SECTION]->(section)
                """

                section_params = {
                    "app_id": application_id,
                    "name": section.get("name"),
                    "content": section.get("content", ""),
                    "complete": section.get("complete", False),
                    "timestamp": datetime.utcnow().isoformat()
                }

                self.graph.query(section_query, section_params)

            logger.debug(f"Created application {application_id} for grant {grant_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create application: {e}")
            return False

    def update_application_status(
        self,
        application_id: str,
        status: ApplicationStatus
    ) -> bool:
        """
        Update application status.

        Args:
            application_id: Application identifier
            status: New status

        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (app:Application {application_id: $app_id})
            SET app.status = $status,
                app.updated_at = $timestamp
            RETURN app
            """

            result = self.graph.query(query, {
                "app_id": application_id,
                "status": status.value,
                "timestamp": datetime.utcnow().isoformat()
            })

            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to update application status: {e}")
            return False

    def get_application_pipeline(
        self,
        person_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get application pipeline for a person.

        Args:
            person_id: Person identifier

        Returns:
            Dictionary with applications grouped by status
        """
        try:
            query = """
            MATCH (person:Person {person_id: $person_id})
            MATCH (app:Application)-[:SUBMITTED_BY]->(person)
            MATCH (app)-[:FOR]->(grant:Grant)
            OPTIONAL MATCH (app)-[:HAS_SECTION]->(section:ApplicationSection)
            WITH app, grant,
                 COUNT(section) as total_sections,
                 SUM(CASE WHEN section.complete = true THEN 1 ELSE 0 END) as complete_sections
            RETURN app.application_id as app_id,
                   app.status as status,
                   grant.title as grant_title,
                   grant.deadline as deadline,
                   total_sections,
                   complete_sections,
                   (complete_sections * 1.0 / CASE WHEN total_sections > 0 THEN total_sections ELSE 1 END) as completion_percent
            ORDER BY datetime(grant.deadline) ASC
            """

            result = self.graph.query(query, {"person_id": person_id})

            if not result or not result.result_set:
                return {}

            # Group by status
            pipeline = {}
            for row in result.result_set:
                status = row[1]
                if status not in pipeline:
                    pipeline[status] = []

                pipeline[status].append({
                    "application_id": row[0],
                    "grant_title": row[2],
                    "deadline": row[3],
                    "total_sections": row[4],
                    "complete_sections": row[5],
                    "completion_percent": row[6]
                })

            logger.debug(f"Retrieved application pipeline for {person_id}")
            return pipeline

        except Exception as e:
            logger.error(f"Failed to get application pipeline: {e}")
            return {}

    def analyze_funder_success_rate(
        self,
        funder_name: str
    ) -> Dict[str, Any]:
        """
        Analyze success rate with a specific funder.

        Args:
            funder_name: Funder organization name

        Returns:
            Dictionary with success statistics
        """
        try:
            query = """
            MATCH (funder:Organization {name: $funder})
            MATCH (grant:Grant)-[:OFFERED_BY]->(funder)
            MATCH (app:Application)-[:FOR]->(grant)
            WITH funder,
                 COUNT(app) as total_applications,
                 SUM(CASE WHEN app.status IN ['approved', 'funded'] THEN 1 ELSE 0 END) as successful,
                 SUM(CASE WHEN app.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                 SUM(CASE WHEN app.status IN ['draft', 'in_progress', 'submitted', 'under_review'] THEN 1 ELSE 0 END) as pending
            RETURN total_applications,
                   successful,
                   rejected,
                   pending,
                   (successful * 1.0 / CASE WHEN total_applications > 0 THEN total_applications ELSE 1 END) as success_rate
            """

            result = self.graph.query(query, {"funder": funder_name})

            if not result or not result.result_set:
                return {
                    "total_applications": 0,
                    "successful": 0,
                    "rejected": 0,
                    "pending": 0,
                    "success_rate": 0.0
                }

            row = result.result_set[0]
            return {
                "total_applications": row[0],
                "successful": row[1],
                "rejected": row[2],
                "pending": row[3],
                "success_rate": row[4]
            }

        except Exception as e:
            logger.error(f"Failed to analyze funder success rate: {e}")
            return {
                "total_applications": 0,
                "successful": 0,
                "rejected": 0,
                "pending": 0,
                "success_rate": 0.0
            }

    def find_grants_by_deadline(
        self,
        days_until_deadline: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find grants with upcoming deadlines.

        Args:
            days_until_deadline: Number of days to look ahead

        Returns:
            List of grants ordered by deadline
        """
        try:
            future_date = datetime.utcnow() + timedelta(days=days_until_deadline)

            query = """
            MATCH (grant:Grant)
            WHERE grant.status = 'active'
            AND datetime(grant.deadline) > datetime()
            AND datetime(grant.deadline) < datetime($future_date)
            MATCH (grant)-[:OFFERED_BY]->(funder:Organization)
            RETURN grant.grant_id as grant_id,
                   grant.title as title,
                   grant.amount as amount,
                   grant.deadline as deadline,
                   funder.name as funder
            ORDER BY datetime(grant.deadline) ASC
            """

            result = self.graph.query(query, {
                "future_date": future_date.isoformat()
            })

            if not result or not result.result_set:
                return []

            grants = []
            for row in result.result_set:
                grants.append({
                    "grant_id": row[0],
                    "title": row[1],
                    "amount": row[2],
                    "deadline": row[3],
                    "funder": row[4]
                })

            logger.debug(f"Found {len(grants)} grants with deadlines in next {days_until_deadline} days")
            return grants

        except Exception as e:
            logger.error(f"Failed to find grants by deadline: {e}")
            return []
