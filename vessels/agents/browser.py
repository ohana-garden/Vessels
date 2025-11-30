"""
Parable Browser Agent: External Wisdom Forager

A specialized agent that enriches local Parables by finding related external
wisdom - historical examples, case studies, philosophical discussions, and
real-world precedents from across the web.

This agent transforms internal moral conflicts into search queries, retrieves
relevant external examples, and attaches them as "External Wisdom" to help
humans contextualize their decisions within broader historical and ethical
frameworks.

REQUIRES AgentZeroCore - all browser operations are coordinated through A0.
"""

import logging
from typing import List, Dict, Optional, Protocol, TYPE_CHECKING
from dataclasses import dataclass

from vessels.knowledge.parable import Parable

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class SearchToolInterface(Protocol):
    """
    Protocol defining the interface for search tools.

    This allows the browser agent to work with different search backends
    (Google, Bing, DuckDuckGo, etc.) as long as they implement this interface.
    """

    def execute(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Execute a search query.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results, each containing at minimum:
                - title: str
                - url: str
                - snippet: str (brief excerpt)
        """
        ...


class ParableBrowserAgent:
    """
    A specialized agent that uses local Parables as seeds to find
    external wisdom (articles, historical examples, papers).

    The agent takes a Parable representing an internal moral conflict,
    generates appropriate search queries, retrieves relevant external
    examples, and enriches the Parable with this wisdom.

    REQUIRES AgentZeroCore - all browser operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        search_tool_interface: SearchToolInterface
    ):
        """
        Initialize the Parable Browser Agent.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            search_tool_interface: Implementation of SearchToolInterface
        """
        if agent_zero is None:
            raise ValueError("ParableBrowserAgent requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.search = search_tool_interface

        # Register with A0
        self.agent_zero.browser_agent = self
        logger.info("Initialized ParableBrowserAgent with A0")

    def enrich_parable(
        self,
        parable: Parable,
        max_queries: int = 2,
        results_per_query: int = 2,
    ) -> Parable:
        """
        Takes a local parable, searches the web for related concepts,
        and attaches 'External Wisdom' to the parable.

        Args:
            parable: The Parable to enrich
            max_queries: Maximum number of search queries to execute
            results_per_query: Maximum results to retrieve per query

        Returns:
            The enriched Parable with external_wisdom populated
        """
        queries = parable.generate_search_templates()
        logger.info(
            f"Browsing for external wisdom on: '{queries[0]}' "
            f"(conflict: {parable.conflict_pair[0].value} vs {parable.conflict_pair[1].value})"
        )

        found_examples = []

        # Execute searches with configured limits
        for query in queries[:max_queries]:
            try:
                results = self.search.execute(query, limit=results_per_query)

                for res in results:
                    # Validate result has required fields
                    if not all(key in res for key in ['title', 'url', 'snippet']):
                        logger.warning(f"Skipping incomplete search result: {res}")
                        continue

                    found_examples.append({
                        "title": res.get('title', 'Untitled'),
                        "url": res.get('url'),
                        "snippet": res.get('snippet', ''),
                        "relevance": self._estimate_relevance(res, parable),
                        "source_query": query,
                    })

            except Exception as e:
                logger.error(f"Search failed for query '{query}': {e}")
                continue

        # Deduplicate by URL and sort by relevance
        unique_examples = self._deduplicate_and_sort(found_examples)

        parable.external_wisdom = unique_examples
        logger.info(
            f"Enriched parable '{parable.title}' with {len(unique_examples)} "
            f"unique external examples"
        )

        return parable

    def _deduplicate_and_sort(self, examples: List[Dict]) -> List[Dict]:
        """
        Remove duplicate URLs and sort by relevance.

        Args:
            examples: List of example dictionaries

        Returns:
            Deduplicated and sorted list
        """
        seen_urls = set()
        unique_examples = []

        for ex in examples:
            url = ex.get('url')
            if url and url not in seen_urls:
                unique_examples.append(ex)
                seen_urls.add(url)

        # Sort by relevance (high to low)
        relevance_order = {"High": 0, "Medium": 1, "Low": 2}
        unique_examples.sort(
            key=lambda x: relevance_order.get(x.get('relevance', 'Low'), 3)
        )

        return unique_examples

    def _estimate_relevance(self, result: Dict, parable: Parable) -> str:
        """
        Estimate relevance of a search result to the parable.

        This is a simple heuristic. In production, this could use
        semantic similarity, ML models, or more sophisticated scoring.

        Args:
            result: Search result dictionary
            parable: The Parable being enriched

        Returns:
            Relevance score: "High", "Medium", or "Low"
        """
        # Simple keyword matching heuristic
        snippet = result.get('snippet', '').lower()
        title = result.get('title', '').lower()

        # Check if both dimension values appear in snippet or title
        dim1 = parable.conflict_pair[0].value.lower()
        dim2 = parable.conflict_pair[1].value.lower()

        text = f"{snippet} {title}"

        if dim1 in text and dim2 in text:
            return "High"
        elif dim1 in text or dim2 in text:
            return "Medium"
        else:
            return "Low"

    def format_discovery_report(self, parable: Parable, max_examples: int = 3) -> str:
        """
        Creates a readable summary for the humans.

        Formats the external wisdom into a beautiful, readable report
        that helps contextualize the local conflict within broader
        historical and philosophical frameworks.

        Args:
            parable: Enriched Parable with external_wisdom
            max_examples: Maximum number of examples to include

        Returns:
            Formatted markdown report
        """
        if not parable.external_wisdom:
            return (
                "**🌫️ The Mists Were Thick**\n\n"
                "I searched the world's wisdom but found no clear mirrors for "
                f"this particular tension between {parable.conflict_pair[0].value} "
                f"and {parable.conflict_pair[1].value}. This may be a novel dilemma, "
                "or one not well-documented in accessible sources."
            )

        report = f"**🌍 The World as a Mirror**\n\n"
        report += (
            f"Your conflict ({parable.conflict_pair[0].value} vs "
            f"{parable.conflict_pair[1].value}) echoes through history and "
            "philosophy:\n\n"
        )

        # Include top examples up to max_examples
        for i, example in enumerate(parable.external_wisdom[:max_examples], 1):
            relevance_emoji = {
                "High": "🎯",
                "Medium": "📌",
                "Low": "📍"
            }.get(example.get('relevance', 'Low'), "📍")

            report += (
                f"{i}. {relevance_emoji} **[{example['title']}]({example['url']})**\n"
                f"   _{example['snippet']}_\n\n"
            )

        # Add context about search methodology
        total_found = len(parable.external_wisdom)
        if total_found > max_examples:
            report += (
                f"_({total_found - max_examples} additional examples found but "
                f"not shown)_\n\n"
            )

        return report


class MockSearchTool:
    """
    Mock search tool for testing and development.

    Returns placeholder results to demonstrate the browser agent
    without making real API calls.
    """

    def execute(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Return mock search results.

        Args:
            query: Search query (logged but not used)
            limit: Number of results to return

        Returns:
            List of mock search results
        """
        logger.debug(f"MockSearchTool: Query '{query}' (limit={limit})")

        # Return placeholder results
        return [
            {
                "title": f"Example Article on '{query}'",
                "url": f"https://example.com/article/{hash(query)}",
                "snippet": f"This article discusses the ethical implications of {query}...",
            }
            for _ in range(min(limit, 2))
        ]
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

    REQUIRES AgentZeroCore - all browser operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        search_client=None
    ):
        """
        Initialize BrowserAgent.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            search_client: Optional search client (WebSearch, etc.)
        """
        if agent_zero is None:
            raise ValueError("BrowserAgent requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.search_client = search_client

        # Register with A0
        self.agent_zero.browser_agent = self
        logger.info("Initialized BrowserAgent with A0")

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
