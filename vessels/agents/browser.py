"""
Parable Browser Agent: External Wisdom Forager

A specialized agent that enriches local Parables by finding related external
wisdom - historical examples, case studies, philosophical discussions, and
real-world precedents from across the web.

This agent transforms internal moral conflicts into search queries, retrieves
relevant external examples, and attaches them as "External Wisdom" to help
humans contextualize their decisions within broader historical and ethical
frameworks.
"""

import logging
from typing import List, Dict, Optional, Protocol
from vessels.knowledge.parable import Parable

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
    """

    def __init__(self, search_tool_interface: SearchToolInterface):
        """
        Initialize the Parable Browser Agent.

        Args:
            search_tool_interface: Implementation of SearchToolInterface
        """
        self.search = search_tool_interface
        logger.info("Initialized ParableBrowserAgent")

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
