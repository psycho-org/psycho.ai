# psycho.ai

Discord bot that adds AI-powered summaries, decision extraction, catch-up narratives, web search, and reaction-based highlights to a server.

## Services

- AI client (`bot/services/ai_client.py`)
    - Talks to an external AI server via HTTP.
    - Endpoints used: `/api/summarize`, `/api/decisions`, `/api/catchup`.
    - Provides structured results for summaries, decisions, and catch-up narratives.
- History collector (`bot/services/history_collector.py`)
    - Fetches Discord message history by time window (e.g., last 30 minutes) or from a message link/ID.
    - Returns messages in chronological order and respects a configurable limit.

## Slash commands

### AI-powered commands

- `/summarize`
    - Summarizes recent conversation in a channel.
    - Scope options: time window (e.g., `30m`, `1h`) or a message link/ID.
- `/catch-up`
    - Generates an ephemeral catch-up narrative and key points for missed messages.
    - Scope options: time window or message link/ID.

### Non-AI commands

- `/highlights`
    - Shows top 3 most-reacted messages from the last 24 hours in the current channel.
    - Scoring: Unique human reactors (deduplicated across all emojis).
    - Privacy-preserving: Only shows author name, reaction count, and jump link (no message content).
    - Excludes: Bot/webhook-authored messages, bot reactors, author self-reactions.

All commands can be restricted by role via `ALLOWED_ROLE_IDS` (see configuration).

## Configuration (.env)

Create a `.env` file in the project root with these variables:

- `DISCORD_TOKEN` (required)
- `DISCORD_GUILD_ID` (optional; if set, commands sync to that guild only)
- `AI_SERVER_URL` (required; base URL for the AI server)
- `AI_TIMEOUT_SECONDS` (optional; default: 60)
- `MESSAGE_LIMIT` (optional; default: 500)
- `ALLOWED_ROLE_IDS` (optional; comma-separated role IDs)
- `WEB_SEARCH_API_KEY` (required for web search)
- `WEB_SEARCH_API_TYPE` (optional; default: `brave`)

## Project layout

- `bot/`: Application package.
    - `bot/main.py`: Discord client setup and command registration.
    - `bot/commands/`: Slash command definitions.
    - `bot/services/`: External service clients (AI, history, web search).
    - `bot/utils/`: Helper utilities (permissions).
- `docs/`: Project docs and notes.
- `pyproject.toml`, `uv.lock`, `requirements.txt`: Dependency metadata.
