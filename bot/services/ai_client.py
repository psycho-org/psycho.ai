"""AI client service for communicating with AI server"""

import logging
from dataclasses import dataclass

import aiohttp

logger = logging.getLogger(__name__)


# Custom exceptions
class AITimeoutError(Exception):
    """Raised when AI server request times out"""

    pass


class AIConnectionError(Exception):
    """Raised when connection to AI server fails"""

    pass


class AIResponseError(Exception):
    """Raised when AI server returns invalid response"""

    pass


# Response dataclasses
@dataclass
class Decision:
    """Represents a single decision extracted from messages"""

    title: str
    owner: str
    deadline: str
    context: str


@dataclass
class SummaryResult:
    """Result from summarize operation"""

    summary: str
    message_count: int
    time_range: str


@dataclass
class DecisionResult:
    """Result from extract_decisions operation"""

    decisions: list[Decision]


@dataclass
class CatchupResult:
    """Result from generate_catchup operation"""

    narrative: str
    key_points: list[str]


class AIClient:
    """Client for interacting with AI server API"""

    def __init__(self, base_url: str, timeout: int = 60):
        """
        Initialize AI client

        Args:
            base_url: Base URL of AI server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds (default: 60)
        """
        self.base_url: str = base_url.rstrip("/")
        self.timeout: aiohttp.ClientTimeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "AIClient":
        """Create aiohttp session when entering context"""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close aiohttp session when exiting context"""
        if self._session:
            await self._session.close()
            self._session = None

    async def summarize(self, messages: list[str]) -> SummaryResult:
        """
        Generate summary from messages

        Args:
            messages: List of message strings to summarize

        Returns:
            SummaryResult with summary text, message count, and time range

        Raises:
            AITimeoutError: Request timed out
            AIConnectionError: Connection to AI server failed
            AIResponseError: Invalid response from AI server
        """
        if not self._session:
            raise RuntimeError("AIClient must be used as async context manager")

        url = f"{self.base_url}/api/summarize"
        payload = {"messages": messages}

        logger.info(f"[AI Request] POST {url} | messages: {len(messages)}")

        try:
            async with self._session.post(url, json=payload) as response:
                logger.info(f"[AI Response] Status: {response.status}")
                response.raise_for_status()
                data = await response.json()
                logger.info(f"[AI Response] Data keys: {list(data.keys())}")

                # Validate response structure
                if not isinstance(data, dict):
                    raise AIResponseError("Response is not a JSON object")

                if "summary" not in data or "message_count" not in data:
                    raise AIResponseError(
                        "Response missing required fields: summary, message_count"
                    )

                # Validate field types
                if not isinstance(data["summary"], str):
                    raise AIResponseError("summary field must be a string")
                if (
                    not isinstance(data["message_count"], int)
                    or data["message_count"] < 0
                ):
                    raise AIResponseError(
                        "message_count must be a non-negative integer"
                    )

                return SummaryResult(
                    summary=data["summary"],
                    message_count=data["message_count"],
                    time_range=data.get("time_range", ""),
                )

        except aiohttp.ServerTimeoutError as e:
            logger.error(f"[AI Error] ServerTimeoutError: {e}")
            raise AITimeoutError(f"Request to {url} timed out") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"[AI Error] ClientResponseError: {e.status} {e.message}")
            raise AIResponseError(
                f"AI server returned error {e.status}: {e.message}"
            ) from e
        except aiohttp.ClientError as e:
            logger.error(f"[AI Error] ClientError: {e}")
            raise AIConnectionError(f"Failed to connect to {url}: {e}") from e
        except ValueError as e:
            logger.error(f"[AI Error] ValueError: {e}")
            raise AIResponseError(f"Invalid JSON response: {e}") from e

    async def extract_decisions(self, messages: list[str]) -> DecisionResult:
        """
        Extract decisions from messages

        Args:
            messages: List of message strings to analyze

        Returns:
            DecisionResult with list of Decision objects

        Raises:
            AITimeoutError: Request timed out
            AIConnectionError: Connection to AI server failed
            AIResponseError: Invalid response from AI server
        """
        if not self._session:
            raise RuntimeError("AIClient must be used as async context manager")

        url = f"{self.base_url}/api/decisions"
        payload = {"messages": messages}

        logger.info(f"[AI Request] POST {url} | messages: {len(messages)}")

        try:
            async with self._session.post(url, json=payload) as response:
                logger.info(f"[AI Response] Status: {response.status}")
                response.raise_for_status()
                data = await response.json()
                logger.info(f"[AI Response] Data keys: {list(data.keys())}")

                # Validate response structure
                if not isinstance(data, dict):
                    raise AIResponseError("Response is not a JSON object")

                if "decisions" not in data:
                    raise AIResponseError("Response missing required field: decisions")

                if not isinstance(data["decisions"], list):
                    raise AIResponseError("decisions field must be a list")

                # Parse decisions
                decisions = []
                for decision_data in data["decisions"]:
                    if not isinstance(decision_data, dict):
                        raise AIResponseError("Each decision must be a JSON object")

                    required_fields = ["title", "owner", "deadline", "context"]
                    for field in required_fields:
                        if field not in decision_data:
                            raise AIResponseError(
                                f"Decision missing required field: {field}"
                            )
                        if not isinstance(decision_data[field], str):
                            raise AIResponseError(
                                f"Decision field '{field}' must be a string"
                            )

                    decisions.append(
                        Decision(
                            title=decision_data["title"],
                            owner=decision_data["owner"],
                            deadline=decision_data["deadline"],
                            context=decision_data["context"],
                        )
                    )

                return DecisionResult(decisions=decisions)

        except aiohttp.ServerTimeoutError as e:
            logger.error(f"[AI Error] ServerTimeoutError: {e}")
            raise AITimeoutError(f"Request to {url} timed out") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"[AI Error] ClientResponseError: {e.status} {e.message}")
            raise AIResponseError(
                f"AI server returned error {e.status}: {e.message}"
            ) from e
        except aiohttp.ClientError as e:
            logger.error(f"[AI Error] ClientError: {e}")
            raise AIConnectionError(f"Failed to connect to {url}: {e}") from e
        except ValueError as e:
            logger.error(f"[AI Error] ValueError: {e}")
            raise AIResponseError(f"Invalid JSON response: {e}") from e

    async def generate_catchup(self, messages: list[str]) -> CatchupResult:
        """
        Generate catchup narrative from messages

        Args:
            messages: List of message strings to generate catchup from

        Returns:
            CatchupResult with narrative and key points

        Raises:
            AITimeoutError: Request timed out
            AIConnectionError: Connection to AI server failed
            AIResponseError: Invalid response from AI server
        """
        if not self._session:
            raise RuntimeError("AIClient must be used as async context manager")

        url = f"{self.base_url}/api/catchup"
        payload = {"messages": messages}

        logger.info(f"[AI Request] POST {url} | messages: {len(messages)}")

        try:
            async with self._session.post(url, json=payload) as response:
                logger.info(f"[AI Response] Status: {response.status}")
                response.raise_for_status()
                data = await response.json()
                logger.info(f"[AI Response] Data keys: {list(data.keys())}")

                # Validate response structure
                if not isinstance(data, dict):
                    raise AIResponseError("Response is not a JSON object")

                if "narrative" not in data or "key_points" not in data:
                    raise AIResponseError(
                        "Response missing required fields: narrative, key_points"
                    )

                if not isinstance(data["narrative"], str):
                    raise AIResponseError("narrative field must be a string")
                if not isinstance(data["key_points"], list):
                    raise AIResponseError("key_points field must be a list")

                # Validate key_points are strings
                for i, point in enumerate(data["key_points"]):
                    if not isinstance(point, str):
                        raise AIResponseError(
                            f"key_points[{i}] must be a string, got {type(point).__name__}"
                        )

                return CatchupResult(
                    narrative=data["narrative"], key_points=data["key_points"]
                )

        except aiohttp.ServerTimeoutError as e:
            logger.error(f"[AI Error] ServerTimeoutError: {e}")
            raise AITimeoutError(f"Request to {url} timed out") from e
        except aiohttp.ClientResponseError as e:
            logger.error(f"[AI Error] ClientResponseError: {e.status} {e.message}")
            raise AIResponseError(
                f"AI server returned error {e.status}: {e.message}"
            ) from e
        except aiohttp.ClientError as e:
            logger.error(f"[AI Error] ClientError: {e}")
            raise AIConnectionError(f"Failed to connect to {url}: {e}") from e
        except ValueError as e:
            logger.error(f"[AI Error] ValueError: {e}")
            raise AIResponseError(f"Invalid JSON response: {e}") from e
