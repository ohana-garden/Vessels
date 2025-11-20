"""
Multi-class vector store architecture with knowledge isolation.

Commercial agents get separate vector stores to prevent contamination
of community knowledge. This ensures:
1. Commercial agents cannot access community servant knowledge
2. Community knowledge remains unbiased
3. Clear separation of commercial vs community information
4. Servants can access both (with permission) to help users compare
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ..knowledge.vector_stores import ProjectVectorStore, VectorDocument
from .taxonomy import AgentClass

logger = logging.getLogger(__name__)


class MultiClassVectorStores:
    """
    Manages separate vector stores for different agent classes.

    Architecture:
    - Community servants: Full access to community knowledge + can read commercial
    - Commercial agents: Only access to commercial knowledge (their own products/services)
    - Hybrid consultants: Access to hybrid knowledge + limited commercial
    - Community members: Full access to community knowledge

    This prevents commercial agents from:
    - Contaminating community knowledge with biased information
    - Accessing private community discussions
    - Learning from community servant interactions
    """

    def __init__(self, community_id: str, base_dir: Path):
        """
        Initialize multi-class vector stores.

        Args:
            community_id: Community identifier
            base_dir: Base directory for vector stores
        """
        self.community_id = community_id
        self.base_dir = Path(base_dir) / community_id

        # Create separate stores for each agent class
        self.servant_store = ProjectVectorStore(
            self.base_dir / "servants"
        )
        self.commercial_store = ProjectVectorStore(
            self.base_dir / "commercial"
        )
        self.hybrid_store = ProjectVectorStore(
            self.base_dir / "hybrid"
        )
        # Public store for general community knowledge
        self.public_store = ProjectVectorStore(
            self.base_dir / "public"
        )

    def add_document(
        self,
        agent_class: AgentClass,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any]
    ):
        """
        Add document to appropriate vector store based on agent class.

        Args:
            agent_class: Class of agent adding document
            doc_id: Document identifier
            text: Document text
            metadata: Document metadata
        """
        store = self._get_store_for_class(agent_class)

        # Add agent_class to metadata for tracking
        metadata['agent_class'] = agent_class.value

        store.add_document(
            doc_id=doc_id,
            text=text,
            metadata=metadata
        )

        logger.info(
            f"Added document {doc_id} to {agent_class.value} store "
            f"in community {self.community_id}"
        )

    def query(
        self,
        agent_class: AgentClass,
        query: str,
        top_k: int = 5,
        include_commercial: bool = False
    ) -> List[VectorDocument]:
        """
        Query vector stores based on agent class permissions.

        Args:
            agent_class: Class of agent querying
            query: Query text
            top_k: Number of results to return
            include_commercial: Whether to include commercial results (servants only)

        Returns:
            List of matching documents
        """
        if agent_class == AgentClass.COMMERCIAL_AGENT:
            # Commercial agents ONLY see commercial store
            return self._query_commercial_only(query, top_k)

        elif agent_class == AgentClass.COMMUNITY_SERVANT:
            # Servants can see everything (with permission)
            return self._query_servant(query, top_k, include_commercial)

        elif agent_class == AgentClass.HYBRID_CONSULTANT:
            # Hybrid sees public + hybrid + limited commercial
            return self._query_hybrid(query, top_k)

        else:  # COMMUNITY_MEMBER
            # Community members see public + servant knowledge
            return self._query_community_member(query, top_k)

    def _query_commercial_only(
        self,
        query: str,
        top_k: int
    ) -> List[VectorDocument]:
        """
        Query for commercial agents - ONLY commercial store.

        Commercial agents cannot access community knowledge.
        """
        return self.commercial_store.query(query, top_k=top_k)

    def _query_servant(
        self,
        query: str,
        top_k: int,
        include_commercial: bool
    ) -> List[VectorDocument]:
        """
        Query for community servants - can access all stores.

        Servants can see:
        - Community servant knowledge
        - Public knowledge
        - Commercial knowledge (to help compare options)
        """
        # Query servant store
        servant_results = self.servant_store.query(query, top_k=top_k)

        # Query public store
        public_results = self.public_store.query(query, top_k=top_k)

        # Optionally query commercial store (for comparison)
        commercial_results = []
        if include_commercial:
            commercial_results = self.commercial_store.query(query, top_k=top_k)

        # Combine and deduplicate
        all_results = servant_results + public_results + commercial_results

        # Re-rank and return top_k
        # In real implementation, would re-score combined results
        return all_results[:top_k]

    def _query_hybrid(
        self,
        query: str,
        top_k: int
    ) -> List[VectorDocument]:
        """
        Query for hybrid consultants.

        Hybrid consultants can see:
        - Public knowledge
        - Hybrid knowledge
        - Limited commercial (only their own expertise area)
        """
        # Query hybrid store
        hybrid_results = self.hybrid_store.query(query, top_k=top_k)

        # Query public store
        public_results = self.public_store.query(query, top_k=top_k)

        # Combine
        all_results = hybrid_results + public_results

        return all_results[:top_k]

    def _query_community_member(
        self,
        query: str,
        top_k: int
    ) -> List[VectorDocument]:
        """
        Query for community members.

        Community members can see:
        - Public knowledge
        - Community servant knowledge (what servants share publicly)
        """
        # Query public store
        public_results = self.public_store.query(query, top_k=top_k)

        # Query servant store (only publicly shared knowledge)
        # In real implementation, would filter by visibility
        servant_results = self.servant_store.query(query, top_k=top_k // 2)

        # Combine
        all_results = public_results + servant_results

        return all_results[:top_k]

    def _get_store_for_class(self, agent_class: AgentClass) -> ProjectVectorStore:
        """
        Get the appropriate vector store for an agent class.

        This determines WHERE documents get written.
        """
        if agent_class == AgentClass.COMMERCIAL_AGENT:
            return self.commercial_store
        elif agent_class == AgentClass.HYBRID_CONSULTANT:
            return self.hybrid_store
        elif agent_class == AgentClass.COMMUNITY_SERVANT:
            return self.servant_store
        else:  # COMMUNITY_MEMBER
            return self.public_store

    def check_access(
        self,
        agent_class: AgentClass,
        store_type: str
    ) -> bool:
        """
        Check if agent class has access to a store type.

        Args:
            agent_class: Agent class to check
            store_type: Type of store ("servant", "commercial", "hybrid", "public")

        Returns:
            True if access allowed
        """
        access_matrix = {
            AgentClass.COMMERCIAL_AGENT: {
                "commercial": True,
                "servant": False,
                "hybrid": False,
                "public": False,
            },
            AgentClass.COMMUNITY_SERVANT: {
                "commercial": True,  # Can read to help compare
                "servant": True,
                "hybrid": True,
                "public": True,
            },
            AgentClass.HYBRID_CONSULTANT: {
                "commercial": False,  # Limited access in real implementation
                "servant": False,
                "hybrid": True,
                "public": True,
            },
            AgentClass.COMMUNITY_MEMBER: {
                "commercial": False,
                "servant": True,  # Can read public servant knowledge
                "hybrid": False,
                "public": True,
            },
        }

        return access_matrix.get(agent_class, {}).get(store_type, False)

    def get_stats(self) -> Dict[str, int]:
        """
        Get statistics about vector stores.

        Returns:
            Dictionary with document counts per store
        """
        return {
            "servant_docs": len(self.servant_store._documents),
            "commercial_docs": len(self.commercial_store._documents),
            "hybrid_docs": len(self.hybrid_store._documents),
            "public_docs": len(self.public_store._documents),
            "total_docs": (
                len(self.servant_store._documents) +
                len(self.commercial_store._documents) +
                len(self.hybrid_store._documents) +
                len(self.public_store._documents)
            )
        }


class CommercialKnowledgeIsolation:
    """
    Enforces isolation between commercial and community knowledge.

    This is a critical security boundary to prevent:
    - Commercial agents from learning community secrets
    - Biased commercial information from contaminating community knowledge
    - Commercial agents from accessing user data without consent
    """

    @staticmethod
    def validate_write_access(
        agent_class: AgentClass,
        store_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that agent can write to a store.

        Commercial agents can ONLY write to commercial store.

        Returns:
            (allowed, reason)
        """
        if agent_class == AgentClass.COMMERCIAL_AGENT:
            if store_type != "commercial":
                return False, "Commercial agents can only write to commercial store"

        return True, None

    @staticmethod
    def validate_read_access(
        agent_class: AgentClass,
        store_type: str,
        user_consented: bool = False
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that agent can read from a store.

        Args:
            agent_class: Agent class requesting access
            store_type: Store being accessed
            user_consented: Whether user has explicitly consented

        Returns:
            (allowed, reason)
        """
        if agent_class == AgentClass.COMMERCIAL_AGENT:
            # Commercial agents CANNOT read servant knowledge
            if store_type == "servant":
                return False, "Commercial agents cannot access community servant knowledge"

            # Cannot read public without consent
            if store_type == "public" and not user_consented:
                return False, "Commercial agents need user consent to access public knowledge"

        return True, None

    @staticmethod
    def sanitize_for_commercial(
        doc: VectorDocument
    ) -> Optional[VectorDocument]:
        """
        Sanitize document before sharing with commercial agent.

        Removes sensitive information, personal data, private community details.

        Args:
            doc: Document to sanitize

        Returns:
            Sanitized document or None if cannot be shared
        """
        # Check if document can be shared with commercial
        if doc.metadata.get('private', False):
            return None

        if doc.metadata.get('contains_personal_data', False):
            return None

        # Remove sensitive metadata
        sanitized_metadata = {
            k: v for k, v in doc.metadata.items()
            if k not in ['user_id', 'location', 'personal_info', 'private_notes']
        }

        # Create sanitized copy
        return VectorDocument(
            id=doc.id,
            text=doc.text,
            metadata=sanitized_metadata,
            created_at=doc.created_at
        )
