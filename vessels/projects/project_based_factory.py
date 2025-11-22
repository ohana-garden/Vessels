"""
Project-Based Agent Factory

Extends DynamicAgentFactory to create agents with isolated project environments.

Each agent gets:
- Dedicated project directory
- Isolated vector store
- Graphiti namespace
- Project-specific configuration
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .manager import ProjectManager
from .project import ServantProject
from vessels.knowledge.vector_store import SharedVectorStore

logger = logging.getLogger(__name__)


class ProjectBasedAgentFactory:
    """
    Factory that creates agents with isolated project environments.
    
    Extends agent creation to:
    - Create isolated project for each agent
    - Seed project with relevant community knowledge
    - Configure project-specific tools and permissions
    - Enable cross-project coordination via graph
    """
    
    def __init__(
        self,
        project_manager: Optional[ProjectManager] = None,
        base_dir: Path = Path("work_dir/projects")
    ):
        """
        Initialize factory.
        
        Args:
            project_manager: ProjectManager instance (creates if not provided)
            base_dir: Base directory for projects
        """
        self.project_manager = project_manager or ProjectManager(base_dir=base_dir)
        
        # Servant type mappings
        self.intent_to_servant_type = {
            "transport": "transport",
            "ride": "transport",
            "pickup": "transport",
            "dropoff": "transport",
            "meals": "meals",
            "food": "meals",
            "kitchen": "meals",
            "cooking": "meals",
            "medical": "medical",
            "appointment": "medical",
            "doctor": "medical",
            "health": "medical",
        }
    
    def create_agent_from_intent(
        self,
        intent: str,
        community_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create agent with isolated project from natural language intent.
        
        Args:
            intent: Natural language description of need
            community_id: Community this agent serves
            metadata: Optional metadata for project
        
        Returns:
            Dict with project and agent information
        """
        # Determine servant type from intent
        servant_type = self._classify_intent(intent)
        
        logger.info(f"Creating {servant_type} agent for community: {community_id}")
        logger.info(f"Intent: {intent}")
        
        # Create isolated project
        project = self.project_manager.create_project(
            community_id=community_id,
            servant_type=servant_type,
            metadata=metadata or {}
        )
        
        # Seed project with relevant knowledge
        self._seed_project_knowledge(project, intent)
        
        # Create agent configuration
        agent_config = self._create_agent_config(project, intent)
        
        logger.info(f"Created project: {project.id}")
        logger.info(f"  Type: {servant_type}")
        logger.info(f"  Work dir: {project.work_dir}")
        logger.info(f"  Graph namespace: {project.graphiti_namespace}")
        
        return {
            "project": project,
            "agent_config": agent_config,
            "project_id": project.id,
            "servant_type": servant_type,
            "community_id": community_id,
        }
    
    def _classify_intent(self, intent: str) -> str:
        """
        Classify intent to determine servant type.
        
        Args:
            intent: Natural language intent
        
        Returns:
            Servant type (transport, meals, medical, etc.)
        """
        intent_lower = intent.lower()
        
        # Check for keyword matches
        for keyword, servant_type in self.intent_to_servant_type.items():
            if keyword in intent_lower:
                return servant_type
        
        # Default to general community coordination
        logger.warning(f"Could not classify intent: {intent}, using default 'transport'")
        return "transport"
    
    def _seed_project_knowledge(self, project: ServantProject, intent: str):
        """
        Seed project vector store with relevant community knowledge.
        
        Args:
            project: Project to seed
            intent: Original intent for context
        """
        try:
            # Get shared knowledge store
            shared_store = SharedVectorStore(community_id=project.community_id)
            
            # Query shared store for relevant docs
            relevant_docs = shared_store.query(intent, top_k=10)
            
            if relevant_docs:
                # Get project vector store
                project_store = project.load_vector_store()
                
                # Add to project store
                texts = [doc["text"] for doc in relevant_docs]
                metadata = [doc["metadata"] for doc in relevant_docs]
                
                project_store.add(texts=texts, metadata=metadata)
                
                logger.info(f"Seeded project {project.id} with {len(relevant_docs)} docs")
            else:
                logger.info(f"No shared knowledge found for seeding project {project.id}")
        
        except Exception as e:
            logger.warning(f"Could not seed project knowledge: {e}")
    
    def _create_agent_config(
        self,
        project: ServantProject,
        intent: str
    ) -> Dict[str, Any]:
        """
        Create agent configuration for project.
        
        Args:
            project: Project instance
            intent: Original intent
        
        Returns:
            Agent configuration dict
        """
        return {
            "id": project.id,
            "type": project.servant_type,
            "system_prompt": project.system_prompt,
            "work_dir": str(project.work_dir),
            "tools": project.allowed_tools,
            "resource_limits": project.resource_limits,
            "created_at": project.created_at.isoformat(),
            "intent": intent,
            "graphiti_namespace": project.graphiti_namespace,
        }
    
    def get_project(self, project_id: str) -> Optional[ServantProject]:
        """Get project by ID"""
        return self.project_manager.get_project(project_id)
    
    def list_projects(
        self,
        community_id: Optional[str] = None,
        servant_type: Optional[str] = None
    ):
        """List projects with optional filtering"""
        return self.project_manager.list_projects(
            community_id=community_id,
            servant_type=servant_type
        )
    
    def archive_project(self, project_id: str):
        """Archive a project"""
        self.project_manager.archive_project(project_id)
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource usage summary"""
        return self.project_manager.get_resource_summary()
