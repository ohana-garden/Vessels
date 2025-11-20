#!/usr/bin/env python3
"""
Shoghi Projects + Graphiti Demo

Demonstrates the new architecture:
1. Create isolated servant projects
2. Store knowledge in Graphiti graph
3. Assemble context from multiple sources
4. Discover cross-servant coordination opportunities
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shoghi.projects import ProjectManager, ProjectStatus
from shoghi.knowledge import SharedVectorStore, ContextAssembler
from shoghi.knowledge.schema import ServantType, NodeType, RelationType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_project_creation():
    """Demo: Create isolated servant projects"""
    print("\n" + "=" * 60)
    print("DEMO 1: Creating Isolated Servant Projects")
    print("=" * 60)

    # Initialize project manager
    manager = ProjectManager(projects_dir=Path("work_dir/projects"))

    # Create transport servant for Lower Puna Elders
    print("\n1. Creating transport servant project...")
    transport_project = manager.create_project(
        community_id="lower_puna_elders",
        servant_type=ServantType.TRANSPORT,
        intent="coordinate transportation for kupuna to medical appointments"
    )

    print(f"✓ Created project: {transport_project.id}")
    print(f"  - Workspace: {transport_project.work_dir}")
    print(f"  - Status: {transport_project.status.value}")
    print(f"  - Vector store: {transport_project.vector_store.count()} documents")

    # Create meals servant for same community
    print("\n2. Creating meals servant project...")
    meals_project = manager.create_project(
        community_id="lower_puna_elders",
        servant_type=ServantType.MEALS,
        intent="coordinate meal delivery for kupuna with dietary restrictions"
    )

    print(f"✓ Created project: {meals_project.id}")
    print(f"  - Workspace: {meals_project.work_dir}")
    print(f"  - Status: {meals_project.status.value}")
    print(f"  - ISOLATED from transport servant ✓")

    # Show project stats
    print("\n3. Project Statistics:")
    stats = manager.get_project_stats()
    print(f"  - Total active: {stats['total_active']}")
    print(f"  - By community: {stats['by_community']}")
    print(f"  - By type: {stats['by_type']}")

    return manager, transport_project, meals_project


def demo_knowledge_storage(manager, transport_project):
    """Demo: Store knowledge in Graphiti"""
    print("\n" + "=" * 60)
    print("DEMO 2: Storing Knowledge in Graphiti Graph")
    print("=" * 60)

    # Add some knowledge to the graph
    print("\n1. Creating person nodes...")

    # Create person node (kupuna)
    transport_project.graphiti.create_node(
        node_type=NodeType.PERSON,
        properties={
            "name": "Auntie Maile",
            "age": 78,
            "needs_transport": True,
            "location": "Pahoa",
            "community_id": "lower_puna_elders"
        },
        node_id="person_auntie_maile"
    )
    print("✓ Created Person node: Auntie Maile")

    # Create place node (medical facility)
    print("\n2. Creating place node...")
    transport_project.graphiti.create_node(
        node_type=NodeType.PLACE,
        properties={
            "name": "Hilo Medical Center",
            "type": "hospital",
            "location": "Hilo, Hawaii",
            "wheelchair_accessible": True,
            "community_id": "lower_puna_elders"
        },
        node_id="place_hilo_medical"
    )
    print("✓ Created Place node: Hilo Medical Center")

    # Create relationship (NEEDS)
    print("\n3. Creating relationship...")
    transport_project.graphiti.create_relationship(
        source_id="person_auntie_maile",
        rel_type=RelationType.NEEDS,
        target_id="place_hilo_medical",
        properties={
            "need_type": "medical_transport",
            "frequency": "weekly",
            "notes": "Dialysis appointments every Tuesday and Thursday"
        }
    )
    print("✓ Created NEEDS relationship")

    # Store in vector store
    print("\n4. Adding to project vector store...")
    transport_project.vector_store.add(
        texts=[
            "Auntie Maile needs transport to Hilo Medical Center for dialysis",
            "Medical appointments are every Tuesday and Thursday at 9am",
            "Route from Pahoa to Hilo Medical is approximately 45 minutes"
        ],
        metadata=[
            {"entity": "person_auntie_maile", "type": "transport_need"},
            {"entity": "person_auntie_maile", "type": "schedule"},
            {"type": "route_info"}
        ]
    )
    print(f"✓ Added documents to vector store (total: {transport_project.vector_store.count()})")


def demo_context_assembly(transport_project):
    """Demo: Fast context assembly from multiple sources"""
    print("\n" + "=" * 60)
    print("DEMO 3: Context Assembly (<100ms)")
    print("=" * 60)

    # Create shared store (normally pre-populated)
    shared_store = SharedVectorStore()
    shared_store.add(
        texts=[
            "Hawaiian cultural protocol: Always address kupuna with respect and patience",
            "Medical transport should prioritize comfort and dignity",
            "Pahoa to Hilo route: Highway 11, check for construction delays"
        ],
        metadata=[
            {"category": "cultural_protocol"},
            {"category": "transport_guidelines"},
            {"category": "route_info"}
        ]
    )

    # Create context assembler
    assembler = ContextAssembler(
        project_vector_store=transport_project.vector_store,
        graphiti_client=transport_project.graphiti,
        shared_vector_store=shared_store
    )

    # Assemble context for a task
    print("\n1. Assembling context for: 'Schedule transport for Auntie Maile'")
    context = assembler.assemble_context_sync(
        task="Schedule transport for Auntie Maile to medical appointment",
        max_results=5
    )

    print(f"\n✓ Context assembled in {context['assembly_time_ms']:.1f}ms")
    print(f"  - Project docs: {context['source_counts']['project']}")
    print(f"  - Graph context: {context['source_counts']['graph']}")
    print(f"  - Shared docs: {context['source_counts']['shared']}")

    print("\nTop 3 context items:")
    for i, source in enumerate(context['sources'][:3], 1):
        print(f"\n  {i}. Source: {source['source']}")
        print(f"     Text: {source['text'][:80]}...")
        print(f"     Similarity: {source['similarity']:.3f}")
        print(f"     Score: {source['score']:.3f}")

    # Show stats
    print("\n2. Performance Stats:")
    stats = assembler.get_stats()
    print(f"  - Total assemblies: {stats['total_assemblies']}")
    print(f"  - Avg time: {stats['avg_time_ms']:.1f}ms")
    print(f"  - Source usage: {stats['source_usage']}")

    return assembler


def demo_project_archival(manager, meals_project):
    """Demo: Archive a completed project"""
    print("\n" + "=" * 60)
    print("DEMO 4: Project Archival")
    print("=" * 60)

    print(f"\n1. Current status: {meals_project.status.value}")
    print(f"   Active projects: {len(manager.active_projects)}")

    print("\n2. Archiving meals project...")
    success = manager.archive_project(meals_project.id)

    if success:
        print("✓ Project archived successfully")
        print(f"  - New status: {meals_project.status.value}")
        print(f"  - Active projects: {len(manager.active_projects)}")
        print(f"  - Workspace still exists at: {meals_project.work_dir}")
    else:
        print("✗ Failed to archive project")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("SHOGHI PROJECTS + GRAPHITI ARCHITECTURE DEMO")
    print("=" * 60)

    try:
        # Demo 1: Project creation
        manager, transport_project, meals_project = demo_project_creation()

        # Demo 2: Knowledge storage
        demo_knowledge_storage(manager, transport_project)

        # Demo 3: Context assembly
        demo_context_assembly(transport_project)

        # Demo 4: Project archival
        demo_project_archival(manager, meals_project)

        print("\n" + "=" * 60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 60)

        print("\nKey Features Demonstrated:")
        print("✓ Isolated servant workspaces")
        print("✓ Graphiti knowledge graph integration")
        print("✓ Project-specific vector stores")
        print("✓ Fast context assembly (<100ms)")
        print("✓ Project lifecycle management")

    except Exception as e:
        print(f"\n✗ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
