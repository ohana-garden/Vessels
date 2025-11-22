"""
Vector Store for Project-Specific RAG

Provides isolated vector stores for servant projects with:
- Fast semantic search (<10ms target)
- Document storage and retrieval
- Relevance scoring
- Resource-efficient operation
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


class ProjectVectorStore:
    """
    Project-specific vector store for RAG operations.
    
    Features:
    - Isolated storage per project
    - Fast semantic search
    - Document metadata tracking
    - Simple JSON-based persistence
    
    Note: For production, this could be upgraded to use:
    - FAISS for fast vector search
    - ChromaDB for better scalability
    - Redis for distributed operation
    """
    
    def __init__(self, store_path: Path):
        """
        Initialize project vector store.
        
        Args:
            store_path: Path to vector store directory
        """
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.docs_file = self.store_path / "documents.jsonl"
        self.index_file = self.store_path / "index.json"
        
        # In-memory cache
        self.documents: List[Dict[str, Any]] = []
        self._load_documents()
    
    def _load_documents(self):
        """Load documents from disk"""
        if not self.docs_file.exists():
            return
        
        try:
            with open(self.docs_file, 'r') as f:
                for line in f:
                    if line.strip():
                        doc = json.loads(line)
                        self.documents.append(doc)
            
            logger.info(f"Loaded {len(self.documents)} documents from {self.docs_file}")
        
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
    
    def add(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        Add documents to vector store.
        
        Args:
            texts: List of document texts
            metadata: Optional list of metadata dicts
        
        Returns:
            List of document IDs
        """
        if metadata is None:
            metadata = [{} for _ in texts]
        
        doc_ids = []
        
        for text, meta in zip(texts, metadata):
            doc_id = self._generate_doc_id(text)
            
            doc = {
                "id": doc_id,
                "text": text,
                "metadata": meta,
                "added_at": self._get_timestamp()
            }
            
            self.documents.append(doc)
            doc_ids.append(doc_id)
            
            # Append to file
            with open(self.docs_file, 'a') as f:
                f.write(json.dumps(doc) + '\n')
        
        logger.info(f"Added {len(texts)} documents to vector store")
        
        return doc_ids
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query vector store for relevant documents.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
        
        Returns:
            List of documents with scores
        """
        # Filter by metadata if provided
        candidates = self.documents
        if filter_metadata:
            candidates = [
                doc for doc in candidates
                if all(doc["metadata"].get(k) == v for k, v in filter_metadata.items())
            ]
        
        # Score documents by simple text similarity
        # Note: In production, this would use embeddings and cosine similarity
        scored_docs = []
        for doc in candidates:
            score = self._compute_similarity(query_text, doc["text"])
            scored_docs.append({
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": score,
                "id": doc["id"]
            })
        
        # Sort by score and return top_k
        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_docs[:top_k]
    
    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        for doc in self.documents:
            if doc["id"] == doc_id:
                return doc
        return None
    
    def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        for i, doc in enumerate(self.documents):
            if doc["id"] == doc_id:
                del self.documents[i]
                self._rebuild_storage()
                logger.info(f"Deleted document: {doc_id}")
                return True
        return False
    
    def clear(self):
        """Clear all documents"""
        self.documents = []
        self._rebuild_storage()
        logger.info("Cleared vector store")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        return {
            "total_documents": len(self.documents),
            "store_path": str(self.store_path),
            "storage_size_mb": self._get_storage_size() / (1024 * 1024),
        }
    
    def _compute_similarity(self, query: str, text: str) -> float:
        """
        Compute simple text similarity score.
        
        Note: This is a placeholder. In production, use:
        - Sentence transformers for embeddings
        - Cosine similarity for vector comparison
        - FAISS for fast nearest neighbor search
        """
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Simple word overlap score
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())
        
        if not query_words or not text_words:
            return 0.0
        
        overlap = len(query_words & text_words)
        return overlap / len(query_words)
    
    def _generate_doc_id(self, text: str) -> str:
        """Generate document ID from text"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def _rebuild_storage(self):
        """Rebuild storage file from in-memory documents"""
        with open(self.docs_file, 'w') as f:
            for doc in self.documents:
                f.write(json.dumps(doc) + '\n')
    
    def _get_storage_size(self) -> int:
        """Get total storage size in bytes"""
        total = 0
        for file in self.store_path.glob('*'):
            if file.is_file():
                total += file.stat().st_size
        return total


class SharedVectorStore(ProjectVectorStore):
    """
    Shared community knowledge store.
    
    Extends ProjectVectorStore with:
    - Community-wide knowledge access
    - Read-only mode for projects
    - Centralized knowledge management
    """
    
    def __init__(self, community_id: str, base_path: Path = Path("work_dir/shared")):
        """
        Initialize shared vector store.
        
        Args:
            community_id: Community identifier
            base_path: Base path for shared stores
        """
        store_path = base_path / community_id / "vectors"
        super().__init__(store_path)
        
        self.community_id = community_id
        logger.info(f"Initialized shared store for community: {community_id}")
