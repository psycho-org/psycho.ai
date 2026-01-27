"""AI client service for communicating with AI server"""

import aiohttp
from typing import Optional


class AIClient:
    """Client for interacting with AI server API"""

    def __init__(self, base_url: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    # Implementation will be added in next task
    pass
