"""
Servant Project Management

Provides isolated project environments for servant agents with:
- Dedicated working directories
- Project-specific vector stores
- Graphiti namespace isolation
- Custom configuration and prompts
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project lifecycle status"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


@dataclass
class ServantProject:
    """
    Isolated project environment for a servant agent.
    
    Each project provides:
    - Dedicated working directory for files and artifacts
    - Project-specific vector store for RAG
    - Graphiti namespace for knowledge graph operations
    - Custom system prompts and configuration
    - Resource tracking and lifecycle management
    """
    
    id: str
    community_id: str
    servant_type: str  # "transport", "meals", "medical", etc.
    work_dir: Path
    graphiti_namespace: str
    system_prompt: str
    status: ProjectStatus
    created_at: datetime
    last_active: datetime
    
    # Optional fields
    vector_store_path: Optional[Path] = None
    secrets: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize project paths and resources"""
        # Ensure work_dir is a Path object
        if isinstance(self.work_dir, str):
            self.work_dir = Path(self.work_dir)
        
        # Set vector store path if not provided
        if self.vector_store_path is None:
            self.vector_store_path = self.work_dir / "vectors"
        
        # Create project directories
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Create additional project directories
        (self.work_dir / "logs").mkdir(exist_ok=True)
        (self.work_dir / "artifacts").mkdir(exist_ok=True)
        (self.work_dir / "config").mkdir(exist_ok=True)
    
    def get_graphiti_client(self):
        """
        Get Graphiti client for this project's namespace.
        
        Returns:
            VesselsGraphitiClient configured for this project
        """
        from vessels.knowledge.graphiti_client import VesselsGraphitiClient
        
        return VesselsGraphitiClient(
            community_id=self.community_id,
            allow_mock=False  # Projects should use real Graphiti
        )
    
    def load_vector_store(self):
        """
        Load or create project-specific vector store.
        
        Returns:
            ProjectVectorStore instance
        """
        from vessels.knowledge.vector_store import ProjectVectorStore
        
        return ProjectVectorStore(self.vector_store_path)
    
    def save_config(self):
        """Save project configuration to disk"""
        config_path = self.work_dir / "config" / "project.json"
        
        config = {
            "id": self.id,
            "community_id": self.community_id,
            "servant_type": self.servant_type,
            "work_dir": str(self.work_dir),
            "graphiti_namespace": self.graphiti_namespace,
            "system_prompt": self.system_prompt,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
            "allowed_tools": self.allowed_tools,
            "resource_limits": self.resource_limits,
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved project config: {config_path}")
    
    @classmethod
    def load_from_config(cls, config_path: Path) -> 'ServantProject':
        """Load project from saved configuration"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            id=config["id"],
            community_id=config["community_id"],
            servant_type=config["servant_type"],
            work_dir=Path(config["work_dir"]),
            graphiti_namespace=config["graphiti_namespace"],
            system_prompt=config["system_prompt"],
            status=ProjectStatus(config["status"]),
            created_at=datetime.fromisoformat(config["created_at"]),
            last_active=datetime.fromisoformat(config["last_active"]),
            metadata=config.get("metadata", {}),
            allowed_tools=config.get("allowed_tools", []),
            resource_limits=config.get("resource_limits", {}),
        )
    
    def update_activity(self):
        """Update last_active timestamp"""
        self.last_active = datetime.utcnow()
        self.save_config()
    
    def get_allowed_read_graphs(self) -> List[str]:
        """
        Get list of graph namespaces this project can read from.
        
        By default, projects can read from:
        - Their own community graph
        - Shared community knowledge (if permitted)
        
        Returns:
            List of graph namespace IDs
        """
        allowed = [self.graphiti_namespace]
        
        # Add shared graph if configured
        if self.metadata.get("allow_shared_read", False):
            allowed.append(f"shared_knowledge_graph")
        
        return allowed
    
    def log_execution(self, task: str, result: Any, duration_ms: float):
        """Log task execution for tracking and analysis"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task": task,
            "result_summary": str(result)[:200],  # Truncate for logs
            "duration_ms": duration_ms,
            "status": "success" if result else "failure"
        }
        
        log_path = self.work_dir / "logs" / "executions.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        return {
            "work_dir_size_mb": self._get_dir_size(self.work_dir) / (1024 * 1024),
            "vector_store_size_mb": self._get_dir_size(self.vector_store_path) / (1024 * 1024),
            "log_count": len(list((self.work_dir / "logs").glob("*.jsonl"))),
            "artifact_count": len(list((self.work_dir / "artifacts").glob("*"))),
        }
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        if not path.exists():
            return 0
        
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    
    def archive(self):
        """Archive project (mark as archived, preserve data)"""
        self.status = ProjectStatus.ARCHIVED
        self.save_config()
        logger.info(f"Archived project: {self.id}")
    
    def cleanup(self, preserve_logs: bool = True):
        """
        Clean up project resources.
        
        Args:
            preserve_logs: If True, keep log files
        """
        import shutil
        
        # Remove artifacts
        artifacts_dir = self.work_dir / "artifacts"
        if artifacts_dir.exists():
            shutil.rmtree(artifacts_dir)
            artifacts_dir.mkdir()
        
        # Remove vector store
        if self.vector_store_path.exists():
            shutil.rmtree(self.vector_store_path)
            self.vector_store_path.mkdir()
        
        # Optionally preserve logs
        if not preserve_logs:
            logs_dir = self.work_dir / "logs"
            if logs_dir.exists():
                shutil.rmtree(logs_dir)
                logs_dir.mkdir()
        
        logger.info(f"Cleaned up project: {self.id} (preserve_logs={preserve_logs})")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization"""
        return {
            "id": self.id,
            "community_id": self.community_id,
            "servant_type": self.servant_type,
            "work_dir": str(self.work_dir),
            "graphiti_namespace": self.graphiti_namespace,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "metadata": self.metadata,
            "resource_usage": self.get_resource_usage(),
        }
