"""Web search service using external search APIs"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import aiohttp


class WebSearchError(Exception):
    """Exception raised when web search fails"""

    pass


@dataclass
class SearchResult:
    """Single search result from web search API"""

    title: str
    url: str
    description: str
    thumbnail_url: Optional[str] = None


class WebSearchClient(ABC):
    """Abstract base class for web search clients"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Create aiohttp session"""
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session"""
        if self._session:
            await self._session.close()
            self._session = None

    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Search for query and return results.

        Args:
            query: Search query string
            num_results: Maximum number of results to return (default: 5)

        Returns:
            List of SearchResult objects (empty list if no results)

        Raises:
            WebSearchError: If API request fails
        """
        pass


class BraveSearchClient(WebSearchClient):
    """Brave Search API client implementation"""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Search using Brave Search API.

        Args:
            query: Search query string
            num_results: Maximum number of results to return (default: 5)

        Returns:
            List of SearchResult objects (empty list if no results)

        Raises:
            WebSearchError: If API request fails
        """
        if not self._session:
            raise RuntimeError(
                "BraveSearchClient must be used as async context manager"
            )

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "count": num_results,
        }

        try:
            async with self._session.get(
                    self.BASE_URL, headers=headers, params=params
            ) as response:
                response.raise_for_status()
                data = await response.json()

                # Parse Brave Search API response
                results = []
                web_results = data.get("web", {}).get("results", [])

                for item in web_results[:num_results]:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        description=item.get("description", ""),
                        thumbnail_url=item.get("thumbnail", {}).get("src"),
                    )
                    results.append(result)

                return results

        except aiohttp.ClientResponseError as e:
            raise WebSearchError(
                f"Brave Search API request failed with status {e.status}: {e.message}"
            ) from e
        except aiohttp.ClientError as e:
            raise WebSearchError(f"Failed to connect to Brave Search API: {e}") from e
        except (ValueError, KeyError) as e:
            raise WebSearchError(
                f"Failed to parse Brave Search API response: {e}"
            ) from e


class TavilySearchClient(WebSearchClient):
    """Tavily Search API client (placeholder)"""

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Search using Tavily API (not implemented).

        Args:
            query: Search query string
            num_results: Maximum number of results to return (default: 5)

        Returns:
            List of SearchResult objects

        Raises:
            NotImplementedError: This provider is not yet implemented
        """
        raise NotImplementedError("Tavily search provider not yet implemented")


class SerpAPISearchClient(WebSearchClient):
    """SerpAPI Search client (placeholder)"""

    async def search(self, query: str, num_results: int = 5) -> list[SearchResult]:
        """
        Search using SerpAPI (not implemented).

        Args:
            query: Search query string
            num_results: Maximum number of results to return (default: 5)

        Returns:
            List of SearchResult objects

        Raises:
            NotImplementedError: This provider is not yet implemented
        """
        raise NotImplementedError("SerpAPI search provider not yet implemented")


def create_client(api_type: str, api_key: str) -> WebSearchClient:
    """
    Factory function to create web search client based on API type.

    Args:
        api_type: Type of search API ("brave", "tavily", or "serpapi")
        api_key: API key for the search service

    Returns:
        WebSearchClient instance for the specified provider

    Raises:
        ValueError: If api_type is not supported or if api_key is missing
    """
    if not api_key:
        raise ValueError(
            f"API key is required for {api_type}. Please set WEB_SEARCH_API_KEY in your .env file."
        )

    api_type = api_type.lower().strip()

    if api_type == "brave":
        return BraveSearchClient(api_key)
    elif api_type == "tavily":
        raise ValueError(
            "Tavily search provider is not yet implemented. Please use 'brave' instead."
        )
    elif api_type == "serpapi":
        raise ValueError(
            "SerpAPI search provider is not yet implemented. Please use 'brave' instead."
        )
    else:
        raise ValueError(
            f"Unsupported API type: {api_type}. Currently supported: brave. "
            f"Planned: tavily, serpapi"
        )
