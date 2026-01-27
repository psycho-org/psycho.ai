# Discord Bot Service (discord.py + AI)

## Context

### Original Request
Discord.py 오픈소스 라이브러리를 사용하여 디스코드 서버에 붙일 수 있는 Bot service를 구현. AI를 활용하는 기능들을 가지고 있으며, AI 추론 모델을 실행하는 인스턴스에 HTTP API 요청을 보내고 받은 결과를 가공하거나, 봇이 참여하고 있는 디스코드 서버에 업로드.

### Interview Summary
**Key Discussions**:
- Bot structure: `commands.Bot` + Cogs with `app_commands` (slash commands)
- AI inference: self-hosted FastAPI + PyTorch, JSON response, **no streaming**
- Summary data source: channel/thread history with **user-specified scope** (time-based or message link)
- No retry on failure (user must re-request)
- Command permissions: **specific roles only** (role-based check)
- Hosting: Docker container
- Test strategy: tests later (manual verification now)

**Research Findings**:
- discord.py 2.6.4 is latest stable (2025-10-08)
- Use `interaction.response.defer()` then `interaction.followup.send()` for AI calls
- `aiohttp` for async HTTP (already dependency)
- Embed limits: max 10 embeds, 6000 chars total
- Discord interaction timeout: 3s initial, 15min token validity
- Recommended AI timeout: 60-120s

### Metis Review
**Identified Gaps** (addressed):
- AI server API contract undefined → Design flexible interface with configurable endpoint
- Command permission model → Role-based permission checks added
- Message limits undefined → Cap at 500 messages max
- Error handling patterns → Included in each command task
- Edge cases (empty history, timeout, etc.) → Explicit error handling added

---

## Work Objectives

### Core Objective
Build a Discord bot using discord.py 2.6.4 that provides AI-powered conversation summarization, decision extraction, and web search summary features via slash commands.

### Concrete Deliverables
- `bot/main.py` - Bot entry point with async startup
- `bot/cogs/summary.py` - AI summary commands cog
- `bot/cogs/websearch.py` - Web search command cog
- `bot/services/ai_client.py` - AI inference HTTP client
- `bot/services/history_collector.py` - Channel history collection service
- `bot/services/web_search.py` - Web search API client
- `bot/utils/permissions.py` - Role-based permission checks
- `bot/config.py` - Configuration management
- `.env.example` - Environment variables template
- `Dockerfile` - Container configuration
- `docs/web-search-implementation.md` - Web search API comparison doc

### Definition of Done
- [x] Bot starts and syncs commands within 30 seconds
- [x] All 4 commands respond with "thinking..." within 3 seconds
- [x] AI timeout errors handled gracefully with user message
- [x] Docker container builds and runs successfully
- [x] Manual verification of each command passes

### Must Have
- Slash commands: `/summarize`, `/decision-template`, `/catch-up`, `/web-search`
- Role-based permission checks (configurable via env)
- `defer()` pattern for all AI calls
- Graceful error handling for timeouts and failures
- User-specified summary scope (time-based, message link)
- Docker container support

### Must NOT Have (Guardrails)
- NO button/modal interactions (slash commands only)
- NO persistent storage/database
- NO retry logic for AI calls
- NO streaming responses
- NO auto-triggering or scheduled summaries
- NO multi-guild configuration
- NO caching layer in MVP
- NO pagination in responses (truncate at limit)

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO
- **User wants tests**: Tests-after (manual verification now)
- **Framework**: pytest + dpytest (for future)

### Manual QA Procedures

Each TODO includes detailed verification procedures with:
- Commands to run
- Expected outputs
- Interactive verification steps

---

## Task Flow

```
Task 1 (Project Structure)
    ↓
Task 2 (Config + Permissions) ──────┐
    ↓                               │
Task 3 (History Collector)          │
    ↓                               │
Task 4 (AI Client) ─────────────────┤
    ↓                               │
Task 5 (Summary Cog) ←──────────────┘
    ↓
Task 6 (Web Search Service)
    ↓
Task 7 (Web Search Cog)
    ↓
Task 8 (Docker + Docs)
    ↓
Task 9 (Integration Verification)
```

## Parallelization

| Group | Tasks | Reason |
|-------|-------|--------|
| A | 3, 4 | History collector and AI client are independent services |

| Task | Depends On | Reason |
|------|------------|--------|
| 5 | 2, 3, 4 | Summary cog needs config, history collector, and AI client |
| 7 | 6 | Web search cog needs web search service |
| 9 | All | Integration test needs all components |

---

## TODOs

- [x] 1. Project Structure + Bot Entry Point

  **What to do**:
  - Create directory structure:
    ```
    bot/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── cogs/
    │   ├── __init__.py
    │   ├── summary.py
    │   └── websearch.py
    ├── services/
    │   ├── __init__.py
    │   ├── ai_client.py
    │   ├── history_collector.py
    │   └── web_search.py
    └── utils/
        ├── __init__.py
        └── permissions.py
    ```
  - Implement `bot/main.py`:
    - Subclass `commands.Bot`
    - Configure intents: `default()` + `message_content=True`
    - Implement `setup_hook()` to load cogs and sync commands
    - Add `on_ready` event logging
  - Create `.env.example` with required variables:
    ```
    DISCORD_TOKEN=
    DISCORD_GUILD_ID=
    AI_SERVER_URL=
    AI_TIMEOUT_SECONDS=60
    ALLOWED_ROLE_IDS=
    WEB_SEARCH_API_KEY=
    WEB_SEARCH_API_TYPE=brave
    ```

  **Must NOT do**:
  - Do not add any command implementations yet
  - Do not add database/persistence layer
  - Do not add multiple guild support

  **Parallelizable**: NO (foundation task)

  **References**:
  - `main.py:1` - Existing stub to replace
  - `pyproject.toml` - Dependencies already configured
  - Official pattern: https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py

  **Acceptance Criteria**:
  - [ ] Directory structure created as specified
  - [ ] `python -c "from bot.main import Bot; print('OK')"` → prints "OK"
  - [ ] `.env.example` contains all required variables

  **Commit**: YES
  - Message: `feat(bot): add project structure and bot entry point`
  - Files: `bot/`, `.env.example`

---

- [x] 2. Configuration + Permission Utils

  **What to do**:
  - Implement `bot/config.py`:
    - Load environment variables with validation
    - Dataclass or Pydantic model for type safety
    - Required: `DISCORD_TOKEN`, `DISCORD_GUILD_ID`, `AI_SERVER_URL`
    - Optional with defaults: `AI_TIMEOUT_SECONDS=60`, `MESSAGE_LIMIT=500`
    - Parse `ALLOWED_ROLE_IDS` as comma-separated list
  - Implement `bot/utils/permissions.py`:
    - `has_allowed_role(interaction: Interaction) -> bool` check
    - Decorator or check function for commands
    - Return helpful error message if permission denied

  **Must NOT do**:
  - Do not implement per-guild configuration
  - Do not add database-backed permissions

  **Parallelizable**: YES (with 3, 4)

  **References**:
  - discord.py checks: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#checks

  **Acceptance Criteria**:
  - [ ] `python -c "from bot.config import Config; c = Config(); print(c.ai_timeout)"` → prints timeout value (with .env set)
  - [ ] Missing required env var raises clear `ValueError`
  - [ ] Permission check returns `False` for user without role

  **Commit**: YES
  - Message: `feat(bot): add configuration and permission utilities`
  - Files: `bot/config.py`, `bot/utils/permissions.py`

---

- [x] 3. History Collector Service

  **What to do**:
  - Implement `bot/services/history_collector.py`:
    - `async def collect_history(channel, scope: HistoryScope) -> list[Message]`
    - Support scope types:
      - `TimeScope(minutes: int)` - last N minutes
      - `MessageLinkScope(message_id: int)` - from specific message onward
    - Use `channel.history(limit=100, after=datetime/message)` with pagination
    - Cap at `MESSAGE_LIMIT` (default 500) even if user requests more
    - Filter out bot messages (optional, configurable)
    - Return messages in chronological order
  - Create dataclass for scope types
  - Handle edge cases:
    - Empty history → return empty list
    - Invalid message link → raise `ValueError`
    - Rate limit → let discord.py handle automatically

  **Must NOT do**:
  - Do not store/persist fetched messages
  - Do not fetch unbounded history (always limit)

  **Parallelizable**: YES (with 4)

  **References**:
  - discord.py history: https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel.history
  - Max 100 per API call, need pagination for more

  **Acceptance Criteria**:
  - [ ] Unit test (manual REPL):
    ```python
    # With bot connected to test server
    from bot.services.history_collector import collect_history, TimeScope
    messages = await collect_history(channel, TimeScope(minutes=30))
    assert len(messages) <= 500
    assert messages[0].created_at < messages[-1].created_at  # chronological
    ```
  - [ ] Empty channel returns empty list (no exception)

  **Commit**: YES
  - Message: `feat(services): add history collector with scoped fetching`
  - Files: `bot/services/history_collector.py`

---

- [x] 4. AI Client Service

  **What to do**:
  - Implement `bot/services/ai_client.py`:
    - `AIClient` class with async context manager pattern
    - Methods for each AI operation:
      - `async def summarize(messages: list[str]) -> SummaryResult`
      - `async def extract_decisions(messages: list[str]) -> DecisionResult`
      - `async def generate_catchup(messages: list[str]) -> CatchupResult`
    - Use `aiohttp.ClientSession` for HTTP requests
    - Configurable endpoint URL and timeout from Config
    - Return typed dataclasses (not raw dicts)
  - Create response dataclasses:
    ```python
    @dataclass
    class SummaryResult:
        summary: str
        message_count: int
        time_range: str

    @dataclass
    class DecisionResult:
        decisions: list[Decision]  # Decision(title, owner, deadline, context)

    @dataclass
    class CatchupResult:
        narrative: str
        key_points: list[str]
    ```
  - Error handling:
    - Timeout → raise `AITimeoutError`
    - Connection error → raise `AIConnectionError`
    - Invalid response → raise `AIResponseError`
  - **NOTE**: Actual API endpoints TBD by team. Use configurable paths:
    - `{AI_SERVER_URL}/api/summarize`
    - `{AI_SERVER_URL}/api/decisions`
    - `{AI_SERVER_URL}/api/catchup`

  **Must NOT do**:
  - Do not implement retry logic
  - Do not implement caching
  - Do not implement streaming

  **Parallelizable**: YES (with 3)

  **References**:
  - aiohttp usage: https://docs.aiohttp.org/en/stable/client_quickstart.html
  - Timeout pattern: `async with session.post(url, timeout=aiohttp.ClientTimeout(total=60))`

  **Acceptance Criteria**:
  - [ ] Mock server test:
    ```python
    # Start mock FastAPI server returning {"summary": "test", "message_count": 10, "time_range": "1h"}
    async with AIClient(config) as client:
        result = await client.summarize(["msg1", "msg2"])
        assert isinstance(result, SummaryResult)
        assert result.summary == "test"
    ```
  - [ ] Timeout after configured seconds raises `AITimeoutError`
  - [ ] Connection refused raises `AIConnectionError`

  **Commit**: YES
  - Message: `feat(services): add AI client with typed responses`
  - Files: `bot/services/ai_client.py`

---

- [x] 5. Summary Commands Cog

  **What to do**:
  - Implement `bot/cogs/summary.py`:
    - Three slash commands: `/summarize`, `/decision-template`, `/catch-up`
    - Each command:
      1. Check role permission
      2. Defer response (ephemeral based on command)
      3. Parse scope option (time: 30m/1h/2h or message_link)
      4. Collect history using HistoryCollector
      5. Call appropriate AI client method
      6. Format result as Discord Embed
      7. Send followup
    - Command options:
      ```python
      @app_commands.command(name="summarize", description="Summarize conversation")
      @app_commands.describe(
          scope_type="How to determine scope",
          scope_value="Time (30m/1h/2h) or message link"
      )
      @app_commands.choices(scope_type=[
          Choice(name="Time-based", value="time"),
          Choice(name="From message link", value="link")
      ])
      async def summarize(self, interaction, scope_type: str, scope_value: str):
      ```
  - Visibility per command:
    - `/summarize`: public (everyone sees result)
    - `/decision-template`: public
    - `/catch-up`: ephemeral (only requester sees)
  - Error handling:
    - Permission denied → ephemeral error message
    - AI timeout → "Request timed out. Please try again."
    - Empty history → "No messages found in specified range"
    - Invalid scope → "Invalid scope format. Use 30m/1h/2h or message link"
  - Embed formatting:
    - Title: "Conversation Summary" / "Decision Template" / "Catch Up"
    - Description: AI result (truncate at 4000 chars with "...")
    - Footer: "Covering X messages from [time range]"
    - Color: branded color (configurable)

  **Must NOT do**:
  - Do not add buttons or reactions
  - Do not add pagination
  - Do not cache results

  **Parallelizable**: NO (depends on 2, 3, 4)

  **References**:
  - `bot/services/history_collector.py` - collect_history function
  - `bot/services/ai_client.py` - AIClient class
  - `bot/utils/permissions.py` - permission check
  - Embed API: https://discordpy.readthedocs.io/en/stable/api.html#discord.Embed

  **Acceptance Criteria**:
  - [ ] Using Playwright browser or Discord client:
    - Type `/summarize` in test channel
    - Select scope_type=time, scope_value=1h
    - Bot shows "thinking..." within 3 seconds
    - Bot responds with embed containing summary
  - [ ] `/catch-up` response is ephemeral (only visible to caller)
  - [ ] User without allowed role gets permission error
  - [ ] Empty channel returns friendly message

  **Commit**: YES
  - Message: `feat(cogs): add summary commands with AI integration`
  - Files: `bot/cogs/summary.py`

---

- [x] 6. Web Search Service

  **What to do**:
  - Implement `bot/services/web_search.py`:
    - `WebSearchClient` class supporting multiple providers:
      - Brave Search API (recommended)
      - Tavily (alternative)
      - SerpAPI (fallback)
    - Factory pattern: `create_client(api_type: str, api_key: str) -> WebSearchClient`
    - Common interface:
      ```python
      @dataclass
      class SearchResult:
          title: str
          url: str
          description: str
          thumbnail_url: Optional[str]

      async def search(query: str, num_results: int = 5) -> list[SearchResult]
      ```
    - Error handling:
      - API error → raise `WebSearchError`
      - No results → return empty list
  - **NOTE**: Only implement the provider selected by team. Placeholder for others.

  **Must NOT do**:
  - Do not implement caching
  - Do not implement fallback between providers

  **Parallelizable**: YES (independent service)

  **References**:
  - Brave Search API: https://brave.com/search/api/
  - Tavily API: https://tavily.com/
  - See `docs/web-search-implementation.md` for comparison

  **Acceptance Criteria**:
  - [ ] With valid API key:
    ```python
    client = create_client("brave", os.getenv("WEB_SEARCH_API_KEY"))
    results = await client.search("python discord bot tutorial", num_results=5)
    assert len(results) <= 5
    assert all(r.title and r.url for r in results)
    ```
  - [ ] Invalid API key raises `WebSearchError`

  **Commit**: YES
  - Message: `feat(services): add web search client`
  - Files: `bot/services/web_search.py`

---

- [x] 7. Web Search Commands Cog

  **What to do**:
  - Implement `bot/cogs/websearch.py`:
    - `/web-search` command:
      1. Check role permission
      2. Defer response (public)
      3. Call web search service
      4. Format results as Discord Embed
      5. Send followup
    - Command options:
      ```python
      @app_commands.command(name="web-search", description="Search the web and summarize results")
      @app_commands.describe(
          query="Search query",
          num_results="Number of results (1-10)"
      )
      async def web_search(self, interaction, query: str, num_results: int = 5):
      ```
    - Embed formatting:
      - Title: f"Search: {query}"
      - Fields: One per result (title as field name, description + URL as value)
      - Thumbnail: First result's thumbnail if available
      - Footer: "Powered by [provider name]"
  - Optional AI enhancement (if time permits):
    - After fetching results, send to AI for summary
    - Add summary as embed description before individual results

  **Must NOT do**:
  - Do not implement pagination
  - Do not cache results

  **Parallelizable**: NO (depends on 6)

  **References**:
  - `bot/services/web_search.py` - WebSearchClient
  - `bot/utils/permissions.py` - permission check

  **Acceptance Criteria**:
  - [ ] Using Discord client:
    - Type `/web-search query:"discord bot python" num_results:3`
    - Bot shows "thinking..." within 3 seconds
    - Bot responds with embed containing search results
  - [ ] Results include clickable URLs
  - [ ] User without allowed role gets permission error

  **Commit**: YES
  - Message: `feat(cogs): add web search command`
  - Files: `bot/cogs/websearch.py`

---

- [x] 8. Docker + Documentation

  **What to do**:
  - Create `Dockerfile`:
    ```dockerfile
    FROM python:3.12-slim
    WORKDIR /app
    COPY pyproject.toml uv.lock ./
    RUN pip install uv && uv sync --frozen
    COPY . .
    CMD ["uv", "run", "python", "-m", "bot.main"]
    ```
  - Create `docker-compose.yml` (optional, for local dev):
    ```yaml
    services:
      bot:
        build: .
        env_file: .env
        restart: unless-stopped
    ```
  - Create `docs/web-search-implementation.md`:
    - Copy content from research (Web search API comparison)
    - Include team decision checklist

  **Must NOT do**:
  - Do not add volume mounts for persistence
  - Do not add health checks (keep simple for MVP)

  **Parallelizable**: YES (independent of code logic)

  **References**:
  - Research content from planning session (web search comparison)
  - Python Docker best practices: https://docs.docker.com/language/python/

  **Acceptance Criteria**:
  - [ ] `docker build -t psycho-bot .` → builds successfully
  - [ ] `docker run --env-file .env psycho-bot` → bot starts (with valid .env)
  - [ ] `docs/web-search-implementation.md` exists with comparison table

  **Commit**: YES
  - Message: `feat(deploy): add Docker configuration and web search docs`
  - Files: `Dockerfile`, `docker-compose.yml`, `docs/web-search-implementation.md`

---

- [x] 9. Integration Verification

  **What to do**:
  - End-to-end manual verification:
    1. Start AI mock server (or real server if available)
    2. Build and run Docker container
    3. Invite bot to test Discord server
    4. Verify each command works:
       - `/summarize` with time scope
       - `/summarize` with message link scope
       - `/decision-template`
       - `/catch-up`
       - `/web-search`
    5. Verify error handling:
       - User without role → permission denied
       - AI server down → connection error message
       - Empty channel → no messages found
  - Create `VERIFICATION.md` with test results

  **Must NOT do**:
  - Do not write automated tests (future task)

  **Parallelizable**: NO (final verification task)

  **References**:
  - All previous tasks
  - `.env.example` for required variables

  **Acceptance Criteria**:
  - [ ] All 4 commands execute successfully in test server
  - [ ] Error messages are user-friendly (not stack traces)
  - [ ] Bot reconnects after brief network interruption
  - [ ] `VERIFICATION.md` documents all test results

  **Commit**: YES
  - Message: `docs: add integration verification results`
  - Files: `VERIFICATION.md`

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(bot): add project structure and bot entry point` | bot/, .env.example | Import test |
| 2 | `feat(bot): add configuration and permission utilities` | bot/config.py, bot/utils/permissions.py | Config load test |
| 3 | `feat(services): add history collector with scoped fetching` | bot/services/history_collector.py | Manual REPL test |
| 4 | `feat(services): add AI client with typed responses` | bot/services/ai_client.py | Mock server test |
| 5 | `feat(cogs): add summary commands with AI integration` | bot/cogs/summary.py | Discord command test |
| 6 | `feat(services): add web search client` | bot/services/web_search.py | API test |
| 7 | `feat(cogs): add web search command` | bot/cogs/websearch.py | Discord command test |
| 8 | `feat(deploy): add Docker configuration and web search docs` | Dockerfile, docker-compose.yml, docs/ | Docker build test |
| 9 | `docs: add integration verification results` | VERIFICATION.md | Manual verification |

---

## Success Criteria

### Verification Commands
```bash
# Build test
docker build -t psycho-bot .

# Start test (requires .env)
docker run --env-file .env psycho-bot

# Import test
python -c "from bot.main import Bot; print('OK')"
```

### Final Checklist
- [x] All 4 slash commands functional
- [x] Role-based permissions working
- [x] AI integration working (with mock or real server)
- [x] Web search integration working
- [x] Docker container builds and runs
- [x] Error handling graceful (no stack traces to users)
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
