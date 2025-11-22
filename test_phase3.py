#!/usr/bin/env python3
"""
Test Phase 3 Components

Tests project-based servant isolation implementation.
"""

import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all Phase 3 modules import correctly"""
    logger.info("=" * 60)
    logger.info("Testing Phase 3 Imports")
    logger.info("=" * 60)
    
    try:
        from vessels.projects import ServantProject, ProjectStatus, ProjectManager
        logger.info("✓ vessels.projects imports OK")
        
        from vessels.knowledge.vector_store import ProjectVectorStore, SharedVectorStore
        logger.info("✓ vessels.knowledge.vector_store imports OK")
        
        from vessels.knowledge.context_assembly import ContextAssembler
        logger.info("✓ vessels.knowledge.context_assembly imports OK")
        
        from vessels.projects.project_based_factory import ProjectBasedAgentFactory
        logger.info("✓ vessels.projects.project_based_factory imports OK")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_project_creation():
    """Test creating a project"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Testing Project Creation")
    logger.info("=" * 60)
    
    try:
        from vessels.projects import ProjectManager, ProjectStatus
        
        # Create project manager
        manager = ProjectManager(base_dir=Path("work_dir/test_projects"))
        logger.info("✓ ProjectManager created")
        
        # Create a transport project
        project = manager.create_project(
            community_id="test_community",
            servant_type="transport"
        )
        
        logger.info(f"✓ Project created: {project.id}")
        logger.info(f"  Type: {project.servant_type}")
        logger.info(f"  Work dir: {project.work_dir}")
        logger.info(f"  Status: {project.status.value}")
        
        # Verify directories created
        assert project.work_dir.exists(), "Work directory not created"
        assert (project.work_dir / "logs").exists(), "Logs directory not created"
        assert (project.work_dir / "artifacts").exists(), "Artifacts directory not created"
        logger.info("✓ Project directories created")
        
        # Verify config saved
        config_path = project.work_dir / "config" / "project.json"
        assert config_path.exists(), "Config not saved"
        logger.info("✓ Project config saved")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Project creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """Test vector store operations"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Testing Vector Store")
    logger.info("=" * 60)
    
    try:
        from vessels.knowledge.vector_store import ProjectVectorStore
        
        # Create vector store
        store_path = Path("work_dir/test_projects/test_vectors")
        store = ProjectVectorStore(store_path)
        logger.info("✓ ProjectVectorStore created")
        
        # Add documents
        texts = [
            "Transport coordination for kupuna medical appointments",
            "Meal delivery schedule for elders",
            "Volunteer driver availability"
        ]
        metadata = [
            {"type": "transport", "category": "medical"},
            {"type": "meals", "category": "delivery"},
            {"type": "transport", "category": "volunteers"}
        ]
        
        doc_ids = store.add(texts=texts, metadata=metadata)
        logger.info(f"✓ Added {len(doc_ids)} documents")
        
        # Query store
        results = store.query("transport kupuna", top_k=2)
        logger.info(f"✓ Query returned {len(results)} results")
        
        if results:
            logger.info(f"  Top result: {results[0]['text'][:50]}...")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_factory():
    """Test project-based agent factory"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Testing ProjectBasedAgentFactory")
    logger.info("=" * 60)
    
    try:
        from vessels.projects.project_based_factory import ProjectBasedAgentFactory
        
        # Create factory
        factory = ProjectBasedAgentFactory(base_dir=Path("work_dir/test_projects"))
        logger.info("✓ ProjectBasedAgentFactory created")
        
        # Create agent from intent
        result = factory.create_agent_from_intent(
            intent="coordinate transport for kupuna medical appointments",
            community_id="lower_puna_elders"
        )
        
        logger.info(f"✓ Agent created from intent")
        logger.info(f"  Project ID: {result['project_id']}")
        logger.info(f"  Servant type: {result['servant_type']}")
        logger.info(f"  Community: {result['community_id']}")
        
        # Verify project was created
        project = result['project']
        assert project.work_dir.exists(), "Project directory not created"
        logger.info("✓ Project directory exists")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Factory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    logger.info("Phase 3: Projects-Based Servant Isolation Tests")
    logger.info("")
    
    results = {
        "imports": test_imports(),
        "project_creation": test_project_creation(),
        "vector_store": test_vector_store(),
        "factory": test_factory(),
    }
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name:20s} {status}")
    
    logger.info("=" * 60)
    logger.info(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ ALL TESTS PASSED")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
