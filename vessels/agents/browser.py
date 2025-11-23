"""
Browser Agent: External Wisdom Forager

The BrowserAgent is designed to search the outside world for wisdom, precedents,
and case studies related to moral conflicts encountered by the Vessels community.

When a Parable captures an internal conflict, the BrowserAgent can:
1. Generate appropriate search queries from the moral tension
2. Search for related history, philosophy, and real-world examples
3. Synthesize findings into digestible "External Wisdom" for the community

This creates a "Mirror of the World" - showing how others have faced similar
dilemmas and what can be learned from their experiences.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Import the Parable class
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from knowledge.parable import Parable

logger = logging.getLogger(__name__)


@dataclass
class ExternalWisdom:
    """
    A piece of wisdom, precedent, or case study from the outside world.

    Attributes:
        source: Where this wisdom came from (URL, book, etc.)
        title: Title of the source or finding
        summary: Brief summary of the relevant wisdom
        relevance_score: How relevant this is to the original parable (0-1)
        query_used: Which search query found this wisdom
        key_insights: Main takeaways from this source
    """
    source: str
    title: str
    summary: str
    relevance_score: float
    query_used: str
    key_insights: List[str]


class BrowserAgent:
    """
    Agent specialized in foraging for external wisdom related to moral conflicts.

    The BrowserAgent takes a Parable (internal conflict) and searches the outside
    world for related examples, philosophy, case studies, and historical precedents.
    It then synthesizes these findings into actionable wisdom for the community.
    """

    def __init__(self, search_client=None):
        """
        Initialize BrowserAgent.

        Args:
            search_client: Optional search client (WebSearch, etc.)
                          If not provided, will attempt to use available search tools
        """
        self.search_client = search_client
        logger.info("Initialized BrowserAgent for external wisdom foraging")

    def forage_for_wisdom(
        self,
        parable: Parable,
        max_results: int = 5,
        queries_to_use: Optional[List[str]] = None,
    ) -> List[ExternalWisdom]:
        """
        Search for external wisdom related to a parable's moral conflict.

        Args:
            parable: The Parable containing the moral tension to explore
            max_results: Maximum number of wisdom items to return
            queries_to_use: Optional specific queries to use. If not provided,
                          will use parable.generate_search_queries()

        Returns:
            List of ExternalWisdom instances, ordered by relevance
        """
        logger.info(
            f"Foraging for external wisdom related to parable: {parable.title}"
        )

        # Generate search queries if not provided
        if queries_to_use is None:
            queries_to_use = parable.generate_search_queries()

        wisdom_items = []

        # Execute searches (implementation depends on available search client)
        for query in queries_to_use[:3]:  # Use top 3 queries to avoid overwhelming
            try:
                results = self._execute_search(query, max_results=2)
                for result in results:
                    wisdom = self._process_search_result(result, query, parable)
                    if wisdom:
                        wisdom_items.append(wisdom)
            except Exception as e:
                logger.warning(f"Search failed for query '{query}': {e}")
                continue

        # Sort by relevance and limit results
        wisdom_items.sort(key=lambda x: x.relevance_score, reverse=True)
        return wisdom_items[:max_results]

    def _execute_search(self, query: str, max_results: int = 2) -> List[Dict]:
        """
        Execute a search query using available search client.

        Args:
            query: The search query
            max_results: Maximum number of results to return

        Returns:
            List of search result dictionaries

        Note:
            This is a placeholder that should be implemented with actual
            search capabilities (WebSearch, API calls, etc.)
        """
        logger.debug(f"Executing search for: {query}")

        # Placeholder - in real implementation, would use WebSearch or similar
        # For now, return empty list (agent will need actual search integration)
        if self.search_client:
            return self.search_client.search(query, limit=max_results)
        else:
            logger.warning("No search client configured - returning empty results")
            return []

    def _process_search_result(
        self,
        result: Dict,
        query: str,
        parable: Parable,
    ) -> Optional[ExternalWisdom]:
        """
        Process a search result into an ExternalWisdom object.

        Args:
            result: Raw search result dictionary
            query: The query that produced this result
            parable: The original parable for context

        Returns:
            ExternalWisdom instance or None if result is not relevant
        """
        try:
            # Extract key information from result
            # (structure depends on search client implementation)
            source = result.get("url", result.get("source", "Unknown"))
            title = result.get("title", "Untitled")
            content = result.get("content", result.get("snippet", ""))

            # Calculate relevance based on content matching conflict dimensions
            relevance = self._calculate_relevance(content, parable)

            # Extract key insights (simple implementation - could be enhanced with LLM)
            insights = self._extract_insights(content, parable)

            return ExternalWisdom(
                source=source,
                title=title,
                summary=content[:500],  # First 500 chars as summary
                relevance_score=relevance,
                query_used=query,
                key_insights=insights,
            )

        except Exception as e:
            logger.warning(f"Failed to process search result: {e}")
            return None

    def _calculate_relevance(self, content: str, parable: Parable) -> float:
        """
        Calculate how relevant a piece of content is to the parable.

        Args:
            content: The content to evaluate
            parable: The parable to compare against

        Returns:
            Relevance score between 0 and 1
        """
        # Simple keyword-based relevance (could be enhanced with embeddings)
        content_lower = content.lower()
        score = 0.0

        # Check for dimension mentions
        for dimension in parable.conflict_pair:
            dim_value = dimension.value.lower().replace('_', ' ')
            if dim_value in content_lower:
                score += 0.3

        # Check for ethics/moral keywords
        moral_keywords = ['ethics', 'moral', 'dilemma', 'principle', 'value']
        for keyword in moral_keywords:
            if keyword in content_lower:
                score += 0.1

        return min(score, 1.0)  # Cap at 1.0

    def _extract_insights(self, content: str, parable: Parable) -> List[str]:
        """
        Extract key insights from content that relate to the parable.

        Args:
            content: The content to analyze
            parable: The parable for context

        Returns:
            List of insight strings
        """
        # Simple implementation - could be enhanced with LLM-based extraction
        insights = []

        # Look for sentences containing both dimension keywords
        dim1 = parable.conflict_pair[0].value.lower().replace('_', ' ')
        dim2 = parable.conflict_pair[1].value.lower().replace('_', ' ')

        sentences = content.split('.')
        for sentence in sentences[:5]:  # First 5 sentences
            sentence_lower = sentence.lower()
            if dim1 in sentence_lower or dim2 in sentence_lower:
                insights.append(sentence.strip())

        return insights[:3]  # Return top 3 insights

    def synthesize_mirror_of_world(
        self,
        parable: Parable,
        wisdom_items: List[ExternalWisdom],
    ) -> str:
        """
        Synthesize external wisdom into a "Mirror of the World" narrative.

        This creates a teachable moment by showing how the world has dealt
        with similar moral tensions.

        Args:
            parable: The original parable
            wisdom_items: List of ExternalWisdom found through foraging

        Returns:
            Formatted narrative string for presentation to humans
        """
        dim1 = parable.conflict_pair[0].value.replace('_', ' ').title()
        dim2 = parable.conflict_pair[1].value.replace('_', ' ').title()

        narrative = f"# Mirror of the World\n\n"
        narrative += f"## Your Conflict: {dim1} vs {dim2}\n\n"
        narrative += f"**Your Situation:**\n{parable.situation_summary}\n\n"
        narrative += f"---\n\n"
        narrative += f"## How Others Have Faced This Dilemma\n\n"

        if not wisdom_items:
            narrative += "*No external precedents found. This may be a novel situation.*\n"
            return narrative

        for i, wisdom in enumerate(wisdom_items, 1):
            narrative += f"### {i}. {wisdom.title}\n"
            narrative += f"**Source:** {wisdom.source}\n\n"
            narrative += f"{wisdom.summary}\n\n"

            if wisdom.key_insights:
                narrative += "**Key Insights:**\n"
                for insight in wisdom.key_insights:
                    narrative += f"- {insight}\n"
                narrative += "\n"

        narrative += "---\n\n"
        narrative += "**Reflection Question:** How do these external examples "
        narrative += "inform your understanding of this conflict?\n"

        return narrative
