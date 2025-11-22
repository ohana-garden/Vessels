"""
Project Manager

Manages lifecycle of servant projects:
- Create new projects from templates
- Load existing projects
- Archive completed projects
- Track project resources and status
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid
import logging
import yaml

from .project import ServantProject, ProjectStatus

logger = logging.getLogger(__name__)


class ProjectManager:
    """
    Manages lifecycle of servant projects.
    
    Responsibilities:
    - Create new projects from templates
    - Load existing projects from disk
    - Track active projects
    - Archive/cleanup completed projects
    - Resource monitoring
    """
    
    def __init__(
        self,
        base_dir: Path = Path("work_dir/projects"),
        templates_dir: Optional[Path] = None
    ):
        """
        Initialize ProjectManager.
        
        Args:
            base_dir: Base directory for all projects
            templates_dir: Directory containing project templates
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Templates directory
        if templates_dir is None:
            # Default to templates/ in this package
            templates_dir = Path(__file__).parent / "templates"
        self.templates_dir = Path(templates_dir)
        
        # Track active projects
        self.active_projects: Dict[str, ServantProject] = {}
        
        # Load existing projects
        self._discover_existing_projects()
    
    def _discover_existing_projects(self):
        """Discover and load existing projects from disk"""
        for community_dir in self.base_dir.iterdir():
            if not community_dir.is_dir():
                continue
            
            for project_dir in community_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                
                config_path = project_dir / "config" / "project.json"
                if config_path.exists():
                    try:
                        project = ServantProject.load_from_config(config_path)
                        
                        # Only load active/paused projects
                        if project.status in [ProjectStatus.ACTIVE, ProjectStatus.PAUSED]:
                            self.active_projects[project.id] = project
                            logger.info(f"Loaded existing project: {project.id} ({project.servant_type})")
                    
                    except Exception as e:
                        logger.error(f"Failed to load project from {config_path}: {e}")
    
    def create_project(
        self,
        community_id: str,
        servant_type: str,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ServantProject:
        """
        Create a new servant project.
        
        Args:
            community_id: Community this project serves
            servant_type: Type of servant (transport, meals, medical, etc.)
            system_prompt: Custom system prompt (uses template if not provided)
            metadata: Additional project metadata
        
        Returns:
            ServantProject instance
        """
        # Generate unique project ID
        project_id = self._generate_project_id()
        
        # Create work directory
        work_dir = self.base_dir / community_id / f"{servant_type}_{project_id[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # Load template
        template = self._load_template(servant_type)
        
        # Use template system prompt if not provided
        if system_prompt is None:
            system_prompt = template.get("system_prompt", self._get_default_prompt(servant_type))
        
        # Create project
        project = ServantProject(
            id=project_id,
            community_id=community_id,
            servant_type=servant_type,
            work_dir=work_dir,
            graphiti_namespace=f"{community_id}_graph",
            system_prompt=system_prompt,
            status=ProjectStatus.INITIALIZING,
            created_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            metadata=metadata or {},
            allowed_tools=template.get("allowed_tools", []),
            resource_limits=template.get("resource_limits", {}),
        )
        
        # Initialize Graphiti node for this servant
        try:
            graphiti = project.get_graphiti_client()
            
            # Create Servant node in knowledge graph
            servant_node_id = graphiti.create_node(
                node_type="Servant",
                properties={
                    "id": project_id,
                    "type": servant_type,
                    "community_id": community_id,
                    "created_at": project.created_at.isoformat(),
                    "status": "active"
                },
                node_id=project_id
            )
            
            logger.info(f"Created Servant node in graph: {servant_node_id}")
        
        except Exception as e:
            logger.warning(f"Could not create Servant node in Graphiti: {e}")
        
        # Mark as active
        project.status = ProjectStatus.ACTIVE
        
        # Save configuration
        project.save_config()
        
        # Track in active projects
        self.active_projects[project_id] = project
        
        logger.info(f"Created project: {project_id} ({servant_type}) for {community_id}")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[ServantProject]:
        """Get project by ID"""
        return self.active_projects.get(project_id)
    
    def list_projects(
        self,
        community_id: Optional[str] = None,
        servant_type: Optional[str] = None,
        status: Optional[ProjectStatus] = None
    ) -> List[ServantProject]:
        """
        List projects with optional filtering.
        
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
    
    def archive_project(self, project_id: str, preserve_logs: bool = True):
        """
        Archive a project.
        
        Args:
            project_id: Project to archive
            preserve_logs: Whether to keep log files
        """
        project = self.active_projects.get(project_id)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            return
        
        # Archive project
        project.archive()
        
        # Optionally cleanup
        if not preserve_logs:
            project.cleanup(preserve_logs=False)
        
        # Remove from active tracking
        del self.active_projects[project_id]
        
        logger.info(f"Archived project: {project_id}")
    
    def cleanup_all(self, older_than_days: int = 30):
        """
        Clean up old archived projects.
        
        Args:
            older_than_days: Archive projects older than this many days
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(days=older_than_days)
        
        cleaned = 0
        for project in list(self.active_projects.values()):
            if project.status == ProjectStatus.ARCHIVED and project.last_active < cutoff:
                project.cleanup(preserve_logs=True)
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} archived projects older than {older_than_days} days")
    
    def get_resource_summary(self) -> Dict:
        """Get resource usage summary for all projects"""
        total_disk = 0
        project_count = len(self.active_projects)
        
        by_type = {}
        by_community = {}
        
        for project in self.active_projects.values():
            usage = project.get_resource_usage()
            total_disk += usage["work_dir_size_mb"]
            
            # Track by type
            if project.servant_type not in by_type:
                by_type[project.servant_type] = 0
            by_type[project.servant_type] += 1
            
            # Track by community
            if project.community_id not in by_community:
                by_community[project.community_id] = 0
            by_community[project.community_id] += 1
        
        return {
            "total_projects": project_count,
            "total_disk_mb": total_disk,
            "by_type": by_type,
            "by_community": by_community,
        }
    
    def _generate_project_id(self) -> str:
        """Generate unique project ID"""
        return str(uuid.uuid4())
    
    def _load_template(self, servant_type: str) -> Dict:
        """Load project template for servant type"""
        template_path = self.templates_dir / f"{servant_type}.yaml"
        
        if not template_path.exists():
            logger.warning(f"Template not found: {template_path}, using defaults")
            return {}
        
        try:
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)
            
            logger.info(f"Loaded template: {servant_type}")
            return template
        
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return {}
    
    def _get_default_prompt(self, servant_type: str) -> str:
        """Get default system prompt for servant type"""
        default_prompts = {
            "transport": """You are a transport coordination servant for this community.
Your role is to help coordinate transportation needs for kupuna (elders) and community members.
You work with other servants to ensure everyone can get where they need to go safely and efficiently.""",
            
            "meals": """You are a meals coordination servant for this community.
Your role is to help coordinate meal preparation and delivery for kupuna (elders) and community members.
You work with other servants to ensure everyone has access to nutritious meals.""",
            
            "medical": """You are a medical coordination servant for this community.
Your role is to help coordinate medical appointments and health services for kupuna (elders) and community members.
You work with other servants to ensure everyone can access needed healthcare.""",
        }
        
        return default_prompts.get(
            servant_type,
            f"You are a {servant_type} servant for this community. Your role is to serve the community's needs."
        )
