"""
Project Manager - Servant Project Lifecycle

Manages creation, tracking, and archival of servant projects:
- Creates isolated project workspaces
- Tracks active projects
- Seeds projects with initial knowledge
- Archives completed projects

REQUIRES AgentZeroCore - all project operations are coordinated through A0.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
import uuid

from .project import ServantProject, ProjectStatus
from vessels.knowledge import VesselsGraphitiClient, SharedVectorStore
from vessels.knowledge.schema import ServantType, NodeType, RelationType

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class ProjectManager:
    """
    Manages servant project lifecycle

    Responsibilities:
    - Create isolated projects
    - Track active projects
    - Seed project knowledge
    - Archive completed projects
    - Query project status

    REQUIRES AgentZeroCore - all project operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        projects_dir: Path = Path("work_dir/projects")
    ):
        """
        Initialize project manager

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            projects_dir: Root directory for all projects
        """
        if agent_zero is None:
            raise ValueError("ProjectManager requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # In-memory project registry
        self.active_projects: Dict[str, ServantProject] = {}

        # Shared knowledge store for seeding
        self.shared_store = SharedVectorStore()

        # Register with A0
        self.agent_zero.project_manager = self
        logger.info(f"Project Manager initialized with A0 (root: {self.projects_dir})")

    def create_project(
        self,
        community_id: str,
        servant_type: ServantType,
        intent: Optional[str] = None,
        read_only_communities: Optional[List[str]] = None
    ) -> ServantProject:
        """
        Create a new servant project

        Args:
            community_id: Community this servant serves
            servant_type: Type of servant (transport, meals, etc.)
            intent: Optional intent/task description for knowledge seeding
            read_only_communities: Optional list of communities servant can read

        Returns:
            Initialized ServantProject
        """
        # Generate project ID
        project_id = self._generate_project_id(community_id, servant_type)

        # Create project directory
        project_dir = self.projects_dir / community_id / f"{servant_type.value}_{project_id[:8]}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # Load system prompt template
        system_prompt = self._load_system_prompt(servant_type, community_id)

        # Create project
        project = ServantProject(
            id=project_id,
            community_id=community_id,
            servant_type=servant_type,
            work_dir=project_dir,
            graphiti_namespace=f"{community_id}_graph",
            system_prompt=system_prompt,
            status=ProjectStatus.INITIALIZING,
            read_only_communities=read_only_communities or []
        )

        # Save project config
        project.save_config()

        # Create servant node in graph
        try:
            project.graphiti.create_node(
                node_type=NodeType.SERVANT,
                properties={
                    "name": f"{servant_type.value}_{project_id[:8]}",
                    "type": servant_type.value,
                    "status": ProjectStatus.INITIALIZING.value,
                    "community_id": community_id,
                    "created_at": datetime.utcnow().isoformat()
                },
                node_id=project_id
            )
            logger.info(f"Created servant node {project_id} in {community_id}_graph")

        except Exception as e:
            logger.error(f"Error creating servant node in graph: {e}")

        # Seed project knowledge
        if intent:
            self._seed_project_knowledge(project, intent)

        # Update status to active
        project.update_status(ProjectStatus.ACTIVE)

        # Register project
        self.active_projects[project_id] = project

        logger.info(
            f"Created project {project_id} for {servant_type.value} in {community_id} at {project_dir}"
        )

        return project

    def get_project(self, project_id: str) -> Optional[ServantProject]:
        """Get project by ID"""
        return self.active_projects.get(project_id)

    def list_projects(
        self,
        community_id: Optional[str] = None,
        servant_type: Optional[ServantType] = None,
        status: Optional[ProjectStatus] = None
    ) -> List[ServantProject]:
        """
        List projects with optional filters

        Args:
            community_id: Filter by community
            servant_type: Filter by servant type
            status: Filter by status

        Returns:
            List of matching projects
        """
        projects = list(self.active_projects.values())

        if community_id:
            projects = [p for p in projects if p.community_id == community_id]

        if servant_type:
            projects = [p for p in projects if p.servant_type == servant_type]

        if status:
            projects = [p for p in projects if p.status == status]

        return projects

    def archive_project(self, project_id: str) -> bool:
        """
        Archive a project

        Args:
            project_id: ID of project to archive

        Returns:
            True if successful
        """
        project = self.active_projects.get(project_id)
        if not project:
            logger.error(f"Project {project_id} not found")
            return False

        try:
            # Archive project
            project.archive()

            # Remove from active registry
            del self.active_projects[project_id]

            logger.info(f"Archived project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Error archiving project {project_id}: {e}")
            return False

    def load_all_projects(self):
        """Load all projects from disk"""
        logger.info("Loading projects from disk...")

        count = 0
        for community_dir in self.projects_dir.iterdir():
            if not community_dir.is_dir():
                continue

            for project_dir in community_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                config_file = project_dir / "project.json"
                if not config_file.exists():
                    continue

                try:
                    project = ServantProject.load_from_dir(project_dir)

                    # Only load non-archived projects
                    if project.status != ProjectStatus.ARCHIVED:
                        self.active_projects[project.id] = project
                        count += 1

                except Exception as e:
                    logger.error(f"Error loading project from {project_dir}: {e}")

        logger.info(f"Loaded {count} active projects")

    def _generate_project_id(self, community_id: str, servant_type: ServantType) -> str:
        """Generate unique project ID"""
        return f"{community_id}_{servant_type.value}_{uuid.uuid4().hex[:16]}"

    def _load_system_prompt(self, servant_type: ServantType, community_id: str) -> str:
        """
        Load system prompt template for servant type

        Args:
            servant_type: Type of servant
            community_id: Community context

        Returns:
            System prompt string
        """
        # Default prompts by type
        prompts = {
            ServantType.TRANSPORT: f"""You are a transport coordination servant for {community_id}.

Your role:
- Coordinate transportation for kupuna (elders) and community members
- Schedule rides, track driver availability
- Optimize routes for efficiency and accessibility
- Respect Hawaiian cultural protocols and values
- Always prioritize safety and dignity

Moral constraints (12D phase space):
- Truthfulness: Always provide accurate information about availability and timing
- Justice: Ensure fair access to transport resources
- Service: Prioritize community needs over efficiency metrics
- Understanding: Consider mobility limitations, cultural practices

You operate with isolation - no access to other servants' context.
Use the knowledge graph to discover coordination opportunities with other servants.
""",

            ServantType.MEALS: f"""You are a meal coordination servant for {community_id}.

Your role:
- Coordinate meal delivery for kupuna and families in need
- Track dietary restrictions, allergies, preferences
- Connect with food sources (gardens, food hubs, kitchens)
- Respect cultural food practices and preferences
- Ensure nutrition and dignity in all meal coordination

Moral constraints:
- Truthfulness: Accurate information about dietary restrictions
- Justice: Equitable access to nutritious food
- Service: Prioritize nourishment and cultural appropriateness
- Unity: Coordinate across food providers

You operate with isolation. Use the graph to find coordination opportunities.
""",

            ServantType.MEDICAL: f"""You are a medical appointment coordination servant for {community_id}.

Your role:
- Schedule and coordinate medical appointments
- Track medical facility locations, hours, specialties
- Coordinate with transport servants when needed
- Respect privacy and medical confidentiality
- Always maintain dignity and cultural sensitivity

Moral constraints:
- Truthfulness: Critical for medical information accuracy
- Justice: Fair access to healthcare resources
- Trustworthiness: Maintain confidentiality
- Understanding: Be sensitive to medical anxiety and cultural beliefs

You operate with isolation. Use the graph for coordination.
""",

            ServantType.GRANT_WRITER: f"""You are a grant writing servant for {community_id}.

Your role:
- Identify relevant grant opportunities
- Draft grant proposals highlighting community needs
- Track grant application deadlines and requirements
- Coordinate with community members for input
- Celebrate Hawaiian culture and community strengths in proposals

Moral constraints:
- Truthfulness: Accurate representation of community needs
- Justice: Ensure benefits flow to those in need
- Service: Proposals serve community, not just funding
- Unity: Collaborative approach with community input

You operate with isolation. Use the graph to gather community context.
""",
        }

        return prompts.get(
            servant_type,
            f"You are a {servant_type.value} servant for {community_id}. "
            f"Serve with aloha, maintain isolation, use the graph for coordination."
        )

    def _seed_project_knowledge(self, project: ServantProject, intent: str):
        """
        Seed project vector store with relevant knowledge from shared store

        Args:
            project: Project to seed
            intent: Intent/task description to guide seeding
        """
        try:
            # Query shared knowledge store for relevant documents
            relevant_docs = self.shared_store.query(intent, top_k=10, min_similarity=0.5)

            if relevant_docs:
                texts = [doc["text"] for doc in relevant_docs]
                metadata = [doc["metadata"] for doc in relevant_docs]

                # Add to project vector store
                project.vector_store.add(texts=texts, metadata=metadata)

                logger.info(
                    f"Seeded project {project.id} with {len(relevant_docs)} documents from shared store"
                )
            else:
                logger.info(f"No relevant shared knowledge found for seeding project {project.id}")

        except Exception as e:
            logger.error(f"Error seeding project knowledge: {e}")

    def get_project_stats(self) -> Dict:
        """Get statistics about projects"""
        stats = {
            "total_active": len(self.active_projects),
            "by_community": {},
            "by_type": {},
            "by_status": {}
        }

        for project in self.active_projects.values():
            # By community
            if project.community_id not in stats["by_community"]:
                stats["by_community"][project.community_id] = 0
            stats["by_community"][project.community_id] += 1

            # By type
            type_key = project.servant_type.value
            if type_key not in stats["by_type"]:
                stats["by_type"][type_key] = 0
            stats["by_type"][type_key] += 1

            # By status
            status_key = project.status.value
            if status_key not in stats["by_status"]:
                stats["by_status"][status_key] = 0
            stats["by_status"][status_key] += 1

        return stats
